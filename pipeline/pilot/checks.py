"""Deterministic checks for drafted lexicon fields. Standard library only.

Source-lock rule: a drafted statement is accepted only if it is backed by a
verbatim QUOTE from the SOURCE it was written from. Nothing from general
knowledge gets through.

Every drafted statement is {"text": ..., "quote": ...}. Two result levels:

  fails  the draft is rejected and retried: wrong shape; a quote that is not
         verbatim inside a single field of the source; a Strong's number, bare
         number, Greek or Hebrew word, or verse reference that is not in the source.
  flags  for a person or the verifier: content words in a statement that appear
         nowhere in the source (this is where padded wording shows up).
"""
import json
import re
import unicodedata

FIELDS = ("etymology_note", "distinctions", "semantic_contrasts", "key_theological_notes")

_STATEMENT = {
    "type": "object",
    "properties": {"text": {"type": "string"}, "quote": {"type": "string"}},
    "required": ["text", "quote"],
}

# Passed to Ollama as the `format` so the model must return this shape.
DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "etymology_note": {"type": "array", "items": _STATEMENT},
        "distinctions": {"type": "array", "items": _STATEMENT},
        "semantic_contrasts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "strongs": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["strongs", "summary", "quote"],
            },
        },
        "key_theological_notes": {"type": "array", "items": _STATEMENT},
    },
    "required": list(FIELDS),
}

BOOKS = (
    "Song of Solomon|Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|"
    "Chronicles|Ezra|Nehemiah|Esther|Job|Psalms|Psalm|Proverbs|Ecclesiastes|Isaiah|Jeremiah|"
    "Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|"
    "Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|"
    "Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|Jude|Revelation"
)
_STRONGS = re.compile(r"\b[GH]\d{1,4}\b")
_REF = re.compile(rf"(?:[1-3] )?(?:{BOOKS}) \d{{1,3}}(?::\d{{1,3}}(?:[-–]\d{{1,3}})?)?")
_BARE_REF = re.compile(r"\b\d{1,3}:\d{1,3}(?:[-–]\d{1,3})?")
_DIGITS = re.compile(r"\d+")
_SCRIPT = re.compile(r"[Ͱ-Ͽἀ-῿֐-׿]+")
_WORD = re.compile(r"[A-Za-z]{6,}")

MIN_QUOTE = 12
MAX_QUOTE = 400


def _norm(token):
    """Compare Greek and Hebrew words without accents, vowel points or case."""
    decomposed = unicodedata.normalize("NFD", token)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return stripped.lower().replace("ς", "σ")


def _qnorm(text):
    """Normalise a quote or field for matching: quotes, dashes, spacing, case."""
    text = unicodedata.normalize("NFC", text)
    for a, b in (("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'), ("–", "-"), ("—", "-")):
        text = text.replace(a, b)
    return " ".join(text.split()).casefold()


def _leaves(obj):
    """Every string value in the source, one by one. A quote must sit inside ONE of these."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _leaves(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _leaves(v)


def _statements(draft):
    """Yield (label, text, quote) for every drafted statement."""
    for field in ("etymology_note", "distinctions", "key_theological_notes"):
        for i, s in enumerate(draft[field]):
            yield f"{field}[{i}]", s["text"], s["quote"]
    for i, c in enumerate(draft["semantic_contrasts"]):
        yield f"semantic_contrasts[{i}]", c["summary"], c["quote"]


def _bad_str(value, low, high):
    return not isinstance(value, str) or not low <= len(value.strip()) <= high


def validate_shape(draft):
    if not isinstance(draft, dict):
        return ["draft is not a JSON object"]
    if set(draft) != set(FIELDS):
        return [f"fields must be exactly {sorted(FIELDS)} (got {sorted(draft)})"]
    problems = []
    limits = {"etymology_note": (0, 2), "distinctions": (0, 3), "semantic_contrasts": (0, 4),
              "key_theological_notes": (0, 6)}
    for field, (lo, hi) in limits.items():
        items = draft[field]
        if not isinstance(items, list) or not lo <= len(items) <= hi:
            problems.append(f"{field} must be a list of {lo}-{hi} items; use an empty list if the source has nothing")
            continue
        for i, item in enumerate(items):
            keys = {"strongs", "summary", "quote"} if field == "semantic_contrasts" else {"text", "quote"}
            if not isinstance(item, dict) or set(item) != keys:
                problems.append(f"{field}[{i}] must have exactly {sorted(keys)}")
                continue
            body = item["summary" if field == "semantic_contrasts" else "text"]
            if _bad_str(body, 20, 600):
                problems.append(f"{field}[{i}] statement must be 20-600 characters")
            if field == "semantic_contrasts" and (
                    not isinstance(item["strongs"], list) or not item["strongs"]
                    or not all(isinstance(s, str) for s in item["strongs"])):
                problems.append(f"{field}[{i}].strongs must be a non-empty list of strings")
    return problems


def draft_text(draft):
    parts = []
    for _, text, _ in _statements(draft):
        parts.append(text)
    for c in draft["semantic_contrasts"]:
        parts.extend(c["strongs"])
    return "\n".join(parts)


def to_fields(draft):
    """Plain-string form of a checked draft, plus the quotes that back each statement."""
    def join(items):
        return " ".join(i["text"].strip() for i in items)
    return {
        "etymology_note": join(draft["etymology_note"]),
        "distinctions": join(draft["distinctions"]),
        "semantic_contrasts": [{"strongs": c["strongs"], "summary": c["summary"]}
                               for c in draft["semantic_contrasts"]],
        "key_theological_notes": [i["text"] for i in draft["key_theological_notes"]],
        "evidence": [{"statement": label, "quote": quote} for label, _, quote in _statements(draft)],
    }


def check_text(blob, source):
    """Source-lock checks on free text: returns a list of problems (empty means clean)."""
    text = json.dumps(source, ensure_ascii=False)
    problems = []
    allowed = set(_STRONGS.findall(text))
    for s in sorted(set(_STRONGS.findall(blob)) - allowed):
        problems.append(f"Strong's number {s} is not in the source")
    scrubbed = _BARE_REF.sub(" ", _STRONGS.sub(" ", _REF.sub(" ", blob)))
    source_numbers = set(_DIGITS.findall(text))
    for n in sorted(set(_DIGITS.findall(scrubbed)) - source_numbers):
        problems.append(f"number {n} is not in the source")
    source_words = {_norm(t) for t in _SCRIPT.findall(text)}
    for t in sorted(set(_SCRIPT.findall(blob))):
        if _norm(t) not in source_words:
            problems.append(f"Greek/Hebrew word not in source: {t}")
    for ref in sorted(set(_REF.findall(blob))):
        if ref not in text:
            problems.append(f"reference not in source: {ref}")
    return problems


def check_draft(draft, source):
    """Return {"fails": [...], "flags": [...]} for a draft against its source dict."""
    fails = validate_shape(draft)
    if fails:
        return {"fails": fails, "flags": []}

    leaves = [_qnorm(x) for x in _leaves(source)]
    for label, _, quote in _statements(draft):
        if _bad_str(quote, MIN_QUOTE, MAX_QUOTE):
            fails.append(f"{label}: quote must be {MIN_QUOTE}-{MAX_QUOTE} characters copied from the source")
        elif not any(_qnorm(quote) in leaf for leaf in leaves):
            fails.append(f"{label}: quote is not verbatim inside one source field: {quote[:60]!r}")
    fails += check_text(draft_text(draft), source)

    flags = []
    source_blob = _qnorm(json.dumps(source, ensure_ascii=False))
    for label, text, _ in _statements(draft):
        missing = sorted({w.lower() for w in _WORD.findall(text) if w.lower()[:5] not in source_blob})
        if missing:
            flags.append(f"{label}: words not found in source: {', '.join(missing)}")
    return {"fails": fails, "flags": flags}
