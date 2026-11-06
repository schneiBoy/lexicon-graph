# Proofread Bullinger text

`units.json`: the Bullinger passages used by the pilot, proofread line by line against the page image (2026-11-06) and then joined (line-end hyphens removed only where the joined word is in the vocabulary).
`corrections.json`: every change made to the raw OCR in `data/raw/bullinger/ocr_columns/`, with page, column, line, old text, new text and a note. Raw OCR stays untouched.

Only the lines listed in each unit's `lines` were proofread. Where the print itself is damaged (for example "surrende ing" in the BELIEVE entry) the OCR is left as printed and the unit says so; do not quote those spans.
Corrections made by one reader (Claude) from the image; a second reader has not yet checked them.
