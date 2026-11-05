#!/usr/bin/env python3
"""Read Young's Index-Lexicon counts from OCR and accept a count ONLY when independent checks agree.

For each Strong's number three numbers are compared:
  A  summed counts from OCR reading A (Tesseract psm 6, one column at a time)
  B  summed counts from OCR reading B (Tesseract psm 4, same columns)
  K  count of that number in the tagged KJV (kjv_counts.py), a different source and method

  verified  A == B == K   -> may enter the graph as Young's count
  queued    anything else -> NOT used; a person (or a later, independent reader) resolves it from the page image

Entries are joined to Strong's numbers by Young's capital-letter transliteration, matched against a vocabulary built from
the Strong's Greek lemmas. Numbers whose transliteration maps to more than one Strong's number are queued, not guessed.

  python3 young_check.py --cols data/raw/youngs/ocr_columns --strongs strongs-greek-dictionary.js \
      --kjv-counts counts.json --gold pipeline/ingest/gold/young_gold.json --out data/raw/youngs/checked
"""
import argparse
import collections
import difflib
import json
import re
import unicodedata
from pathlib import Path

from young_parse import num_options

LM = {'α': 'A', 'β': 'B', 'γ': 'G', 'δ': 'D', 'ε': 'E', 'ζ': 'Z', 'η': 'E', 'θ': 'TH', 'ι': 'I', 'κ': 'K', 'λ': 'L',
      'μ': 'M', 'ν': 'N', 'ξ': 'X', 'ο': 'O', 'π': 'P', 'ρ': 'R', 'σ': 'S', 'τ': 'T', 'υ': 'U', 'φ': 'PH', 'χ': 'CH',
      'ψ': 'PS', 'ω': 'O'}
# Greek capitals that Tesseract returns for Latin capitals (and the reverse)
GL = str.maketrans({'Α': 'A', 'Β': 'B', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H', 'Ι': 'I', 'Κ': 'K', 'Μ': 'M', 'Ν': 'N', 'Ο': 'O',
                    'Ρ': 'P', 'Τ': 'T', 'Υ': 'Y', 'Χ': 'X', 'Ό': 'O', 'Ί': 'I', 'Ά': 'A', 'Έ': 'E', 'Ή': 'H', 'Θ': 'C',
                    'Ω': 'O', 'Π': 'P', 'Σ': 'S', 'Λ': 'L', 'Δ': 'D', 'Γ': 'G', 'Φ': 'F', 'Ψ': 'P', 'Ξ': 'X',
                    'Ῑ': 'I', 'Ὁ': 'O'})
HEAD = re.compile(r"^[|!'’.,:;\s\"“‘_\-—]*([A-ZΑ-ΩΌ][A-ZΑ-ΩΌΊΉ()'’\-]{2,}(?:\s[A-ZΑ-ΩΌΊΉ()'’\-]{2,})?)\b(.*)$")
GREEK_ANY = re.compile(r"[Ͱ-Ͽἀ-῿]")


def asc(s):
    d = unicodedata.normalize("NFD", s)
    return "".join(c for c in d if unicodedata.category(c) != "Mn").upper()


def lemma_translits(g):
    g = unicodedata.normalize("NFD", g)
    g = "".join(c for c in g if unicodedata.category(c) != "Mn").lower().replace('ς', 'σ')
    outs, i = [''], 0
    while i < len(g):
        ch, nx = g[i], g[i + 1] if i + 1 < len(g) else ''
        if ch == 'γ' and nx in 'γκξχ':          # γγ is NG (angelos) or GG; γκ is NK or GK
            outs = [o + x for o in outs for x in ('N', 'G')]
            i += 1
            continue
        outs = [o + LM.get(ch, '') for o in outs]
        i += 1
    return set(outs)


def build_vocab(strongs_js, kjv):
    src = Path(strongs_js).read_text(encoding='utf-8')
    dic = json.loads(src[src.index('{'):src.rindex('}')+1])
    by = collections.defaultdict(list)
    for k, v in dic.items():
        if k in kjv:
            by[asc(v['translit']).replace('Ē', 'E')].append(k)
            for t in lemma_translits(v['lemma']):
                if k not in by[t]:
                    by[t].append(k)
    return by


def parse_cols(text, page, by):
    voc = set(by)
    ents, cur = [], None
    for l in (x.strip() for x in text.splitlines()):
        if not l:
            continue
        m = HEAD.match(l)
        key, unknown = None, False
        if m:
            w = re.sub(r"[()'’]", "", m.group(1)).strip().translate(GL)
            for cand in (w, w.replace(' ', '')):
                if cand in voc:
                    key = cand
                    break
            if key is None and ' ' in w and w.split()[0] in voc:
                key = w.split()[0]
            if key is None:
                cm = difflib.get_close_matches(w.replace(' ', ''), voc, n=2, cutoff=0.8)
                if len(cm) == 1 or (len(cm) == 2 and difflib.SequenceMatcher(None, w, cm[0]).ratio()
                                    - difflib.SequenceMatcher(None, w, cm[1]).ratio() > 0.05):
                    key = cm[0]
            if key is None and len(w) >= 5 and GREEK_ANY.search(m.group(2)[:30]):
                unknown = True
        if unknown:                      # a headword we cannot name still ends the previous entry
            cur = {'translit': None, 'pdf_page': page, 'lines': []}
            ents.append(cur)
        elif key:
            cur = {'translit': key, 'pdf_page': page, 'lines': [m.group(2).strip()] if m.group(2).strip() else []}
            ents.append(cur)
        elif cur is not None:
            cur['lines'].append(l)
    return ents


def total(entry):
    nums = []
    for l in entry['lines']:
        toks, prev_num = l.split(), False
        if len(toks) == 1 or (len(toks) == 2 and not re.search(r"[A-Za-z]{3}", l)):
            o = num_options(toks[0], True)              # a count wrapped onto a line of its own
            if o:
                nums.append(o[0])
                continue
        for j, t in enumerate(toks):
            o = num_options(t, j == len(toks) - 1)
            if (o is None and j > 0 and j == len(toks) - 1 and re.search(r"[A-Za-z]{3}", toks[j - 1])
                    and re.fullmatch(r"[Ͱ-Ͽἀ-῿]{1,2}[.,;]?", t)):
                o = [1]                                  # a 1 read as a short Greek letter
            if o and j > 0 and not prev_num and re.search(r"[A-Za-z]", toks[j - 1]):
                nums.append(o[0])                        # a count must follow a word
                prev_num = True
            else:
                prev_num = bool(o)                       # a second numeral right after a numeral is column-edge noise
    return sum(nums)


def read(cols_dir, psm, by):
    sums = collections.defaultdict(lambda: [0, []])
    skipped = collections.Counter()
    for f in sorted(Path(cols_dir).glob(f"[0-9]*_psm{psm}.txt")):
        for e in parse_cols(f.read_text(encoding='utf-8'), int(f.name.split('_')[0]), by):
            if e['translit'] is None:
                skipped['unknown headword'] += 1
                continue
            cands = by[e['translit']]
            if len(cands) != 1:
                skipped['transliteration matches several Strong\'s numbers'] += 1
                continue
            sums[cands[0]][0] += total(e)
            sums[cands[0]][1].append({'page': e['pdf_page'], 'translit': e['translit'], 'lines': e['lines']})
    return sums, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cols', required=True)
    ap.add_argument('--strongs', required=True, help='strongs-greek-dictionary.js')
    ap.add_argument('--kjv-counts', required=True)
    ap.add_argument('--gold')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    kjv = json.load(open(a.kjv_counts))
    by = build_vocab(a.strongs, kjv)
    A, skA = read(a.cols, 6, by)
    B, skB = read(a.cols, 4, by)
    verified, queue, status = {}, {}, collections.Counter()
    for k in sorted(set(A) | set(B)):
        ta = A[k][0] if k in A else None
        tb = B[k][0] if k in B else None
        if ta == tb == kjv[k]:
            verified[k] = {'young_count': kjv[k], 'pages': sorted({e['page'] for e in A[k][1]})}
            status['verified (A = B = KJV)'] += 1
        else:
            why = ('one reading equals KJV' if kjv[k] in (ta, tb) else
                   'A = B but differs from KJV' if ta == tb else 'readings disagree or one is missing')
            queue[k] = {'A': ta, 'B': tb, 'kjv': kjv[k], 'why': why, 'pages': sorted({e['page'] for e in A.get(k, [0, []])[1]})}
            status[why] += 1
    status['never found in either reading'] = sum(1 for k in kjv if k.startswith('G') and k not in A and k not in B)
    report = {'status': dict(status), 'skipped_A': dict(skA), 'skipped_B': dict(skB)}
    if a.gold:
        gold = json.load(open(a.gold))
        res = collections.Counter()
        for pg, d in gold.items():
            for tr, g in d.items():
                for k in by.get(tr, []):
                    if k in verified:
                        res['verified and correct' if verified[k]['young_count'] == g else 'FALSE ACCEPT'] += 1
                    else:
                        res['queued'] += 1
        report['gold'] = dict(res)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'verified.json').write_text(json.dumps(verified, indent=0, sort_keys=True))
    (out / 'queue.json').write_text(json.dumps(queue, indent=0, sort_keys=True))
    (out / 'report.json').write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
