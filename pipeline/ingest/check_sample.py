#!/usr/bin/env python3
"""Check the sample's sourced fields against the real source texts. Standard library only.

Strong's: exact match of definition and derivation against Open Scriptures' strongs-greek-dictionary.js.
Thayer's: is each sample sentence a verbatim substring of the real entry?

  python3 check_sample.py --strongs-js PATH/strongs-greek-dictionary.js --thayers-dir PATH/book
"""
import argparse
import glob
import json
import re
import sys
from pathlib import Path

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "samples" / "agape_agapao_lexical_sample.json"


def norm(s):
    return " ".join(s.replace("’", "'").split()).strip(" ;.").casefold()


def load_strongs(path):
    text = Path(path).read_text(encoding="utf-8")
    body = text[text.index("{"):text.rindex("}") + 1]
    return json.loads(body.rstrip().rstrip(";"))


def load_thayers(folder):
    text = "".join(Path(f).read_text(encoding="utf-8") for f in sorted(glob.glob(f"{folder}/[0-9]*.md")))
    return {int(m.group(1)): m.group(2) for m in
            re.finditer(r"`Strong's G(\d+)`\n\n(.*?)\n\n---", text, re.S)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strongs-js", required=True)
    ap.add_argument("--thayers-dir", required=True)
    a = ap.parse_args()
    strongs, thayers = load_strongs(a.strongs_js), load_thayers(a.thayers_dir)
    words = json.loads(SAMPLE.read_text(encoding="utf-8"))["words"]
    bad = 0
    for name, w in words.items():
        num = w["strongs"]["number"]
        real = strongs[num]
        for field, key in (("definition", "strongs_def"), ("derivation", "derivation")):
            ok = norm(w["strongs"][field]) == norm(real[key])
            bad += not ok
            print(f"{name} strongs.{field}: {'verbatim' if ok else 'DIFFERS'}")
        entry = norm(thayers[int(num[1:])])
        for field in ("definition", "key_note"):
            for sent in re.split(r"(?<=[.:])\s+", w["thayers"][field]):
                ok = norm(sent) in entry
                bad += not ok
                print(f"{name} thayers.{field}: {'verbatim' if ok else 'NOT FOUND'}: {sent[:70]}")
    print(f"\n{bad} item(s) are not verbatim in the real sources.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
