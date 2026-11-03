"""Deterministic checks for drafted lexicon fields. Standard library only.

A draft is checked against the SOURCE it was written from. Two result levels:

  fails  hard problems: wrong shape, a Strong's number or a bare number that
         is not in the source. A draft with fails is rejected and retried.
  flags  things a person or the verifier should look at: a Greek or Hebrew
         word, or a verse reference, that does not appear verbatim in the source.
"""
import json
import re
import unicodedata

FIELDS = ("etymology_note", "distinctions", "semantic_contrasts", "key_theological_notes")

# Passed to Ollama as the `format` so the model must return this shape.
DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "etymology_note": {"type": "string"},
        "distinctions": {"type": "string"},
        "semantic_contrasts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "strongs": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                },
                "required": ["strongs", "summary"],
            },
        },
        "key_theological_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": list(FIELDS),
}

_STRONGS = re.compile(r"\b[GH]\d{1,4}\b")
_REF = re.compile(r"(?:[1-3] )?[A-Z][a-z]+(?: of [A-Z][a-z]+)? \d{1,3}(?::\d{1,3}(?:[-–]\d{1,3})?)?")
_BARE_REF = re.compile(r"\b\d{1,3}:\d{1,3}(?:[-–]\d{1,3})?")
_DIGITS = re.compile(r"\d+")
_SCRIPT = re.compile(r"[Ͱ-Ͽἀ-῿֐-׿]+")


def _norm(token):
    """Compare Greek and Hebrew words without accents, vowel points or case."""
    decomposed = unicodedata.normalize("NFD", token)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return stripped.lower().replace("ς", "σ")


def _length_problem(name, value, low, high):
    if not isinstance(value, str):
        return f"{name} must be a string"
    if not low <= len(value) <= high:
        return f"{name} must be {low}-{high} characters (got {len(value)})"
    return None


def validate_shape(draft):
    if not isinstance(draft, dict):
        return ["draft is not a JSON object"]
    problems = []
    keys = set(draft)
    if keys != set(FIELDS):
        problems.append(f"fields must be exactly {sorted(FIELDS)} (got {sorted(keys)})")
        return problems
    for name in ("etymology_note", "distinctions"):
        p = _length_problem(name, draft[name], 40, 900)
        if p:
            problems.append(p)
    contrasts = draft["semantic_contrasts"]
    if not isinstance(contrasts, list) or not 1 <= len(contrasts) <= 4:
        problems.append("semantic_contrasts must be a list of 1-4 items")
    else:
        for i, c in enumerate(contrasts):
            if not isinstance(c, dict) or set(c) != {"strongs", "summary"}:
                problems.append(f"semantic_contrasts[{i}] must have exactly strongs and summary")
                continue
            if not isinstance(c["strongs"], list) or not c["strongs"] or not all(isinstance(s, str) for s in c["strongs"]):
                problems.append(f"semantic_contrasts[{i}].strongs must be a non-empty list of strings")
            p = _length_problem(f"semantic_contrasts[{i}].summary", c["summary"], 40, 900)
            if p:
                problems.append(p)
    notes = draft["key_theological_notes"]
    if not isinstance(notes, list) or not 3 <= len(notes) <= 6:
        problems.append("key_theological_notes must be a list of 3-6 items")
    else:
        for i, n in enumerate(notes):
            p = _length_problem(f"key_theological_notes[{i}]", n, 20, 400)
            if p:
                problems.append(p)
    return problems


def draft_text(draft):
    parts = [draft["etymology_note"], draft["distinctions"]]
    for c in draft["semantic_contrasts"]:
        parts.extend(c["strongs"])
        parts.append(c["summary"])
    parts.extend(draft["key_theological_notes"])
    return "\n".join(parts)


def check_draft(draft, source):
    """Return {"fails": [...], "flags": [...]} for a draft against its source dict."""
    fails = validate_shape(draft)
    if fails:
        return {"fails": fails, "flags": []}

    text = json.dumps(source, ensure_ascii=False)
    blob = draft_text(draft)

    allowed = set(_STRONGS.findall(text))
    for s in sorted(set(_STRONGS.findall(blob)) - allowed):
        fails.append(f"Strong's number {s} is not in the source")

    scrubbed = _BARE_REF.sub(" ", _STRONGS.sub(" ", _REF.sub(" ", blob)))
    source_numbers = set(_DIGITS.findall(text))
    for n in sorted(set(_DIGITS.findall(scrubbed)) - source_numbers):
        fails.append(f"number {n} is not in the source")

    flags = []
    source_words = {_norm(t) for t in _SCRIPT.findall(text)}
    for t in sorted(set(_SCRIPT.findall(blob))):
        if _norm(t) not in source_words:
            flags.append(f"Greek/Hebrew word not in source: {t}")
    for ref in sorted(set(_REF.findall(blob))):
        if ref not in text:
            flags.append(f"reference not verbatim in source: {ref}")
    return {"fails": fails, "flags": flags}
