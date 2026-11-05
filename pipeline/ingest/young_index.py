#!/usr/bin/env python3
"""Parse the OCR of Young's Index-Lexicon to the New Testament into entries. Standard library only.

Each entry: transliterated headword (capitals), Greek lemma, and rendering lines with counts,
plus the PDF page it came from. OCR confuses the printed numeral 1 with x, τ, I and similar, so counts
here are CANDIDATES to be checked against an independent count (see kjv_counts.py), never trusted alone.

  python3 young_index.py /path/to/ocr_dir > entries.json
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

GREEK = r"[Ͱ-Ͽἀ-῿]"
HEAD = re.compile(rf"^([A-Z][A-Z()'’\-]+(?:\s+[A-Z()'’\-]{{2,}})*)\s+({GREEK}[^\n]*)$")
ONES = set("xrτιIlɪ")


def norm(s):
    d = unicodedata.normalize("NFD", s)
    return "".join(c for c in d if unicodedata.category(c) != "Mn").lower().replace("ς", "σ")


def to_count(tok):
    tok = tok.strip(".,;")
    if tok.isdigit():
        return int(tok)
    if tok and all(ch in ONES for ch in tok.replace("ὶ", "").replace("ὸ", "")):
        return 1
    return None


def parse_page(text, page):
    entries, cur = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = HEAD.match(line)
        if m:
            greek = re.findall(rf"{GREEK}+", m.group(2))
            cur = {"translit": m.group(1), "greek": greek[:2], "pdf_page": page, "lines": []}
            entries.append(cur)
        elif cur is not None:
            cur["lines"].append(line)
    return entries


def candidate_total(entry):
    """Sum of trailing counts found on the lines. Only a candidate: wrapped lines and misread numerals break it."""
    total, seen = 0, 0
    for line in entry["lines"]:
        toks = line.replace("—", " ").split()
        if toks:
            c = to_count(toks[-1])
            if c is not None:
                total += c
                seen += 1
    return total, seen


if __name__ == "__main__":
    out = []
    for f in sorted(Path(sys.argv[1]).glob("*.txt")):
        out += parse_page(f.read_text(encoding="utf-8"), int(f.stem))
    for e in out:
        e["candidate_total"], e["counted_lines"] = candidate_total(e)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
