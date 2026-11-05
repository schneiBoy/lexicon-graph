# Young's Analytical Concordance: Greek Index-Lexicon (OCR)

Scan `analyticalconcor0000youn_j4x7` (sha256 in SOURCES.md), PDF pages 1159-1196. Only the 260 MB PDF stays out of the repo.

- `ocr_columns/<page>_psm6.txt`, `<page>_psm4.txt`: two independent Tesseract 5.3.4 (`eng+grc`, 300 dpi) readings of every page,
  one column at a time. Whole-page OCR scrambles these 6-column pages (page 1161 was mostly garbage), so each page is split
  into columns first (`pipeline/ingest/young_columns.py`).
- `checked/verified.json`: counts that passed every check, the only Young's counts the graph may use.
- `checked/queue.json`: counts that did NOT pass, with both OCR totals, the KJV total and the reason. Not used.
- `checked/report.json`: totals from the last run.

Method, results and the audit: `docs/young-method.md`.
