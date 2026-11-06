# Bullinger: A Critical Lexicon and Concordance to the English and Greek New Testament

- Edition: 5th edition, 1908 (archive.org item `Criticallexiconconcordanceenggreeknt.5thed1908`, scan digitised by Google).
- `ocr/NNNN.txt`: OCR of every page image, where NNNN is the PDF page number (the printed page number is about 5 lower; for example the LOVE entry is on PDF pages 474 to 475, printed 469).
- Produced by `pipeline/ingest/ocr_pdf.py` with Tesseract 5.3.4 (`eng+grc`, 300 dpi, page segmentation mode 1). Settings are in `ocr/meta.json`.
- The scan itself is not in the repo (81 MB). The PDF's built-in text layer is unusable because its Greek recogniser turned English text into Greek-looking noise, which is why the pages were re-read from the images.

OCR text contains errors. Spot checks on the LOVE entry found dropped or misread words (for example "rofane" for "profane", "devotiun" for "devotion", and a skipped phrase). Anything quoted from here is tagged as OCR-derived, and entries that go into the dataset need a check against the page image.

**Update 2026-11-06:** `ocr/` (whole-page) loses the right-hand column of many pages. Use `ocr_columns/` (column OCR at 400 dpi with line boxes) and read `docs/bullinger-method.md` for the measured error rate (about 4 to 7 words in 100).
