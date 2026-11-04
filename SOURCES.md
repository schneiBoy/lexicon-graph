# Sources

The project uses exactly five sources. This file records where machine-readable copies come from and what is still missing. Last updated 2026-11-03.

The Companion Bible and its appendixes (including App-135) are not a source. The sample's source list named them, but the project does not use them.

| Source | Machine-readable copy | Licence of the copy | Status |
| --- | --- | --- | --- |
| Strong's, Greek and Hebrew | [openscriptures/strongs](https://github.com/openscriptures/strongs) (`greek/strongs-greek-dictionary.js`, `hebrew/strongs-hebrew-dictionary.js`) | The 1890 text is public domain. The JSON files carry an Open Scriptures CC-BY-SA notice, which may require share-alike on anything derived from them. Decide before publishing the dataset. | Found. Greek verified against the sample. |
| Thayer's Greek-English Lexicon (1889) | [imbennyhim/Every-Promise-Thayers](https://github.com/imbennyhim/Every-Promise-Thayers) (5,521 entries, G1 to G5624, Markdown) | CC0 | Found. Hand-digitised, so transcription artifacts are possible. |
| Young's Analytical Concordance | Scan on archive.org (`analyticalconcor0000youn_j4x7`), a revised edition with Index-Lexicons at the end; the year is not yet confirmed from the scan. The 260 MB PDF is not in the repo. | Public-domain text | Scan in hand. The built-in text layer reads English well but garbles Greek and some transliterations (it has "agapad" for "agapao"). Pages needed for each lemma are re-read at 300 dpi; a full re-read is about 3 hours. |
| Bullinger's Critical Lexicon and Concordance to the English and Greek New Testament | [5th ed., 1908 scan on archive.org](https://archive.org/details/Criticallexiconconcordanceenggreeknt.5thed1908), re-read by OCR from the page images: `data/raw/bullinger/ocr/` (1,043 pages) | Public-domain text; the OCR is ours | Done, with OCR errors. The scan's own text layer is unusable. Greek and English read well on the LOVE pages. |
| KJV text | Not yet chosen | n/a | Open. |

## What the check against the real sources found

`pipeline/ingest/check_sample.py` compares the sample's sourced fields with the copies above.

- Strong's for ἀγάπη matches exactly.
- Strong's for ἀγαπάω does not. The sample merges in the KJV rendering, fills in ἄγαν where the source has a gap, and cross-references G5368 where the source says "compare G5689".
- Thayer's text in the sample is condensed and reworded. Only some phrases appear verbatim in the real entries, and sentences such as "Used of God's saving love (John 3:16)…" are not in Thayer's at all.
- Bullinger and Young's fields cannot be checked until copies exist.

Until the sourced fields are regenerated from the real texts, a drafted quote that matches the sample proves only that it matches the sample, not the source.
