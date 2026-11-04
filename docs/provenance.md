# Provenance: pointing every field back to the page

Every sourced field and every quote in the graph carries a pointer to the exact place it came from, so a person or a script can open the original and recheck it at any time, without searching.

## Record

Each sourced field or quote has a `provenance` object:

```json
{
  "source": "bullinger-critical-lexicon-1908",
  "scan_sha256": "cf34e792b85f06e0b804247657c6606af61b1d0663a8e25b0813a96dc37f8668",
  "pdf_page": 474,
  "printed_page": "469",
  "box": {"left": 906, "top": 415, "width": 106, "height": 42, "dpi": 300},
  "ocr": {"run": "bullinger-ocr-2026-11-04", "engine": "tesseract 5.3.4 eng+grc psm1", "min_confidence": 93.2},
  "raw_text": "…as read by OCR…",
  "text": "…after cleanup…",
  "corrections": [{"from": "devotiun", "to": "devotion", "how": "vocabulary", "evidence": "KJV word list"}],
  "checked": {"by": "claude-image-audit", "date": "2026-11-04", "result": "match"}
}
```

- `scan_sha256` pins the exact PDF the page number refers to, so a pointer cannot silently drift to a different scan.
- `pdf_page` is the page of the PDF, not the printed number; both are stored.
- `box` is in pixels at the stated `dpi`, taken from the OCR's word boxes (`ocr_pdf.py --boxes`).
- `raw_text` is never edited; `text` is the cleaned version, and every change is listed in `corrections`.
- `checked` records who looked at the image and what they found, so the audit trail lives with the data.

## Lookups

- **Field to page:** the record is on the field, so the lookup is a direct read.
- **Page to everything on it:** an index keyed by `(source, pdf_page)` lists every field that points there, so a bad page can be rechecked in one pass.
- **Show me the original:** `pipeline/ingest/crop.py` renders the box from the scan. The same call feeds the vision model and the Claude image audit.
- **RAG:** a retrieved chunk carries its `provenance`, so an answer can show the page crop beside any quotation.

## What is not in the repo

The scans are too large (81 MB and 260 MB). They are pinned by hash in [`SOURCES.md`](../SOURCES.md) and re-fetched from archive.org when needed. Records for the OCR'd books point into the scans; records for Strong's and Thayer's point to the file and entry in the copies listed in SOURCES.md, since no scan is in hand for those.
