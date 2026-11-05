"""Numeral reading for Young's Index-Lexicon OCR. Counts read here are CANDIDATES;
young_check.py accepts a count only when independent checks agree.

In Young's type the numeral 1 is printed as a small roman "I", and Tesseract returns it as x, r, I, i, τ, σ, :, | and
similar. The numerals 2-9 are usually read correctly as digits; a few come back as letters (a, z for 2).
"""
import unicodedata

ONE = set("xrIlɪτ:!|ι1iσΣs[+")
TWO = set("az")


def strip(s):
    d = unicodedata.normalize("NFD", s)
    return "".join(c for c in d if unicodedata.category(c) != "Mn").lower().replace("ς", "σ")


def num_options(tok, line_end):
    """Candidate value of a token, or None. Letter-for-2 is allowed only at the end of a line."""
    bare = tok.strip(".,;:)(")
    t = bare if bare.isdigit() else strip(tok.strip(".,;:)(᾿’'"))
    t = t.replace("᾿", "").replace("’", "")
    if t.isdigit():
        return [int(t)]
    if t and all(c in ONE for c in t):
        return [1]
    if line_end and t in TWO:
        return [2]
    return None
