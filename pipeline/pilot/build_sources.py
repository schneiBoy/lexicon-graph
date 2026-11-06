#!/usr/bin/env python3
"""Build pilot source records from the real source texts, with no summaries.

  python3 build_sources.py --strongs strongs-greek-dictionary.js --thayers DIR_OF_MD --bullinger data/clean/bullinger/units.json \
      --young-verified data/raw/youngs/checked/verified.json --kjv-counts counts.json --out data/pilot/lemmas.json

Each record is {"source": {...}}. Fields come straight from the texts; Thayer's is cut at a word cap (and says so) so a prompt fits the local model.
"""
import argparse, json, re
from pathlib import Path

LEMMAS = ["G26", "G25", "G5368", "G4102", "G4100", "G5485", "G1343"]
THAYER_CAP = 350


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
    src = Path(a.strongs).read_text(encoding="utf-8")
    dic = json.loads(src[src.index("{"):src.rindex("}") + 1])
    bull = json.load(open(a.bullinger, encoding="utf-8"))
    young = json.load(open(a.young_verified))
    kjv = json.load(open(a.kjv_counts))
    out = {}
    for g in LEMMAS:
        s = dic[g]
        rec = {"greek": s["lemma"], "transliteration": s["translit"],
               "strongs": {"number": g, "derivation": s.get("derivation", ""), "definition": s.get("strongs_def", ""),
                           "kjv_translations": s.get("kjv_def", "")}}
        th = thayers_entry(a.thayers, g)
        if th:
            words = th.split()
            rec["thayers"] = {"text": " ".join(words[:THAYER_CAP]), "edition": "digital, normalised; not checked against the print scan",
                              "truncated": len(words) > THAYER_CAP, "words_in_entry": len(words)}
        if g in bull:
            rec["bullinger"] = {"critical_lexicon_text": bull[g]["text"], "proofread_against_page_image": True,
                                "where": bull[g]["lines"], "note": bull[g]["note"]}
        if g in young:
            rec["youngs"] = {"count_in_nt": young[g]["young_count"], "verified": "two OCR readings and the tagged KJV agree"}
        rec["kjv"] = {"count_in_nt_tagged_kjv": kjv.get(g)}
        out[g] = {"source": rec}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for g, r in out.items():
        print(g, [k for k in r["source"] if k not in ("greek", "transliteration")], len(json.dumps(r["source"], ensure_ascii=False)), "chars")


if __name__ == "__main__":
    main()
