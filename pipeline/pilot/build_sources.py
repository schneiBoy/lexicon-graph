#!/usr/bin/env python3
"""Build pilot source records from the real source texts, with no summaries.

  python3 build_sources.py --strongs data/clean/strongs/greek.json --thayers DIR_OF_MD --bullinger data/clean/bullinger/units.json \
      --young-verified data/raw/youngs/checked/verified.json --kjv-counts counts.json --out data/pilot/lemmas.json

Each record is {"source": {...}}. Fields come straight from the texts; Thayer's is cut at a word cap (and says so) so a prompt fits the local model.
"""
import argparse, json, re
from pathlib import Path

LEMMAS = ["G26", "G25", "G5368", "G4102", "G4100", "G5485", "G1343"]
THAYER_CAP = 350
DAMAGED = {"G4100": ["surrende ing"]}
# Known errors in the digital Thayer's, found against the print scan (see SOURCES.md): the print has "δικ. καὶ ὁσιότης"; the digital copy expands δικ. wrongly
THAYER_ERRORS = {"G1343": ["δίκαιος καί ὁσιότης"]}     # print damaged in the scan itself; drafts may not quote these spans


def thayers_entry(dir_, num):
    for f in sorted(Path(dir_).glob("*.md")):
        t = f.read_text(encoding="utf-8")
        m = re.search(r"`Strong's " + num + r"`\n\n(.*?)\n---", t, re.S)
        if m:
            return m.group(1).strip()
    return None


def main():
    ap = argparse.ArgumentParser()
    for a in ("strongs", "thayers", "bullinger", "young-verified", "kjv-counts", "out"):
        ap.add_argument("--" + a, required=True)
    a = ap.parse_args()
    dic = json.loads(Path(a.strongs).read_text(encoding="utf-8"))["entries"]   # data/clean/strongs/greek.json
    bull = json.load(open(a.bullinger, encoding="utf-8"))
    young = json.load(open(a.young_verified))
    kjv = json.load(open(a.kjv_counts))
    out = {}
    for g in LEMMAS:
        s = dic[g]
        rec = {"greek": s["lemma"], "transliteration": s["translit"],
               "strongs": {"number": g, "derivation": s["derivation"], "definition": s["definition"],
                           "kjv_translations": s["kjv_def"]}}
        th = thayers_entry(a.thayers, g)
        if th:
            words = th.split()
            rec["thayers"] = {"do_not_quote": THAYER_ERRORS.get(g, []), "text": " ".join(words[:THAYER_CAP]), "edition": "digital, normalised; not checked against the print scan",
                              "truncated": len(words) > THAYER_CAP, "words_in_entry": len(words)}
        if g in bull:
            rec["bullinger"] = {"critical_lexicon_text": bull[g]["text"], "proofread_against_page_image": True,
                                "where": bull[g]["lines"], "note": bull[g]["note"]}
            if g in DAMAGED:
                rec["bullinger"]["do_not_quote"] = DAMAGED[g]
        if g in young:
            rec["youngs"] = {"count_in_nt": young[g]["young_count"], "verified": "two OCR readings and the tagged KJV agree"}
        rec["kjv"] = {"count_in_nt_tagged_kjv": kjv.get(g)}
        out[g] = {"source": rec}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    index = {n: e["lemma"] for n, e in dic.items()}      # number -> Greek lemma, so a contrast can name a word by its lemma
    Path(a.out).with_name("lemma_index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    for g, r in out.items():
        print(g, [k for k in r["source"] if k not in ("greek", "transliteration")], len(json.dumps(r["source"], ensure_ascii=False)), "chars")


if __name__ == "__main__":
    main()
