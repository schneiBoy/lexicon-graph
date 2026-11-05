# Young's Analytical Concordance: Greek Index-Lexicon (OCR)

Tesseract 5.3.4 `eng+grc`, 300 dpi, PDF pages 1159-1196 of scan `analyticalconcor0000youn_j4x7` (sha256 in SOURCES.md).
Raw OCR text only. The 260 MB PDF is not in the repo.

Status (first parser pass, `pipeline/ingest/young_index.py`): 1061 entries found; 810 join uniquely to a Strong's lemma;
only 288 of those have a summed rendering count equal to the tagged-KJV count (`kjv_counts.py`).
The mismatches are mostly OCR numeral errors (1 read as x/τ/I, 2 as a) and wrapped lines, so these counts are
candidates only and nothing here enters the graph until the numerals are fixed and the cross-check agrees.
Verified by hand: AGAPAO 142 = KJV 142; AGAPE 27+1+86+1+1 = 116 = KJV 116.
