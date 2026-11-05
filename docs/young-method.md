# Getting Young's counts exactly right

Rule: a Young's count enters the graph only when independent checks agree. Anything else is queued and left out. The graph
never holds a Young's count that rests on one reading of the OCR.

## What we measured

| Step | Result |
|---|---|
| Whole-page OCR (first attempt) | 1,061 entries found; 288 of 810 joined entries matched the KJV count |
| Column-by-column OCR (6 columns/page) | about 4,500 entries found; about 2,600 matched |
| Both readings and the KJV agree | **2,236 Strong's numbers verified** |
| Not verified (queued) | 640 where one reading matches KJV; 858 where A = B but differ from KJV; 468 other |
| In Strong's NT but not found in either reading | 1,316 (mostly Young's lemma differs from Strong's, for example ἀνεμίζομαι vs ἀνεμίζω) |

## The checks

1. **Reading A**: Tesseract psm 6 on each column. **Reading B**: psm 4 on the same columns.
2. **Independent count K**: occurrences of each Strong's number in the tagged KJV (`kjv_counts.py`), a different source and method.
3. **Accept only if A = B = K** for the Strong's number, summed over all Young's entries for it (Young's splits some words, for example HORAO).
4. **Join** by Young's capital transliteration against a vocabulary built from the Strong's lemmas; a transliteration that matches
   more than one Strong's number is queued, never guessed.
5. **Gold set** (`pipeline/ingest/gold/young_gold.json`): 23 entries read by eye from page images. Scored on every change.
6. **Random audit** of accepted entries against the page images (`gold/young_audit_2026-11-05.json`).

## Results of the checks

- Gold set: of the 21 entries that join, 10 verified and correct, 11 queued, **0 false accepts**. All three entries the parser got
  wrong (ANDRAPODISTES, ANECHOMAI, ANEKDIEGETOS) were caught because they disagreed with the KJV count.
- Audit: 23 randomly chosen accepted entries, **23 of 23 match the page image**.
- Together 33 accepted entries checked by eye, 0 wrong. That is a small sample: with 0 errors in 33 we can say the false-accept rate
  is below about 9% at 95% confidence. The argument for it being far lower is structural: a wrong count is accepted only if two
  OCR errors and a KJV difference cancel to the same total. Keep auditing as the set grows.

## Known weaknesses

- Readings A and B use the same engine on the same pixels, so their errors are correlated (858 numbers have A = B but differ from the KJV).
  The KJV count is what supplies independence. A shape classifier for the numerals is the next independent reader.
- Young's and the tagged KJV can legitimately differ (different tagging of some words); those stay queued for a person to resolve from the image.
- Coverage is 41% of Strong's numbers so far. The queue is the work list: the fixes are better headword recovery, a numeral shape classifier, and image review.
