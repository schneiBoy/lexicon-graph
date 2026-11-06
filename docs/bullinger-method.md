# Getting Bullinger's text right

Measured 2026-11-06 on pages from the scan (PDF pages 276 to 737), column OCR at 400 dpi.

## What we found

| Test | Result |
|---|---|
| Old method (whole page, 300 dpi) | drops or interleaves the right-hand column; unusable for entries in column 2 |
| Column-by-column OCR, 300 dpi, psm 6 | 7.6% word error on the LOVE (noun) paragraph |
| Same, 400 dpi, psm 6 | **4.2%** (best single reading); 500 dpi 6.8%, 600 dpi 5.1%, binarised 5.9%, psm 4 5.9% |
| Voting across six readings | **no gain** (4.2%): the engine makes the same mistakes on the same pixels |
| Second hand-checked sample (grace entry, 22 lines, about 170 words) | about 6.5% word error (11 errors) |
| Vocabulary check (English from KJV/Thayer's/Strong's, Greek from Thayer's/Strong's) | caught **5 of 11** real errors; misses the ones that look like valid short words (`tt`, `8`, `ete`, `ag`) and punctuation errors |

The better Tesseract models (`tessdata_best`) could not be downloaded here (blocked), so this is the `fast` model.

## What follows

Bullinger's OCR carries roughly **4 to 7 errors per hundred words**, and neither voting nor vocabulary checks removes them. So:

1. Nothing from Bullinger enters the graph on OCR alone. Every quote a draft relies on is **proofread against the page image**: the lines are cut from the scan
   (`pipeline/ingest/proof_crop.py`), compared with the OCR text, and corrected. The correction is stored with the raw OCR (see `docs/provenance.md`).
2. The vocabulary flags are used to prioritise, never to clear text.
3. Scripture references are never taken from Bullinger's reference lists; they come from the tagged KJV.
4. Work is done lemma by lemma at ingest, not over all 900 pages: a full 400 dpi pass takes hours, and only entries we use need to be right.

## Files

- `pipeline/ingest/bullinger_columns.py`: column OCR with line boxes (`<page>_lines.json`, `<page>_psm6.txt`).
- `pipeline/ingest/proof_crop.py`: cut the image strip behind a range of OCR lines.
- `pipeline/ingest/bullinger_vocab.py`, `bullinger_flags.py`: the vocabulary check.
- `pipeline/ingest/gold/bullinger_love_noun.txt`: hand-corrected LOVE (noun) paragraph used for the measurements above.
- `data/raw/bullinger/ocr_columns/`: column OCR of the 30 pages around the candidate pilot words (love, faith, grace, hope, righteousness, soul, sin, life, peace, fellowship, spirit).
