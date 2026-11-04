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

## Pinned scans

The page pointers in the graph refer to these exact files. They are not stored in the repo.

| Scan | SHA-256 |
| --- | --- |
| Bullinger, `CriticalLexiconConcordance.EngGrkNT..Bullinger.1908._text.pdf` (1,043 pages) | `cf34e792b85f06e0b804247657c6606af61b1d0663a8e25b0813a96dc37f8668` |
| Young's, `analyticalconcor0000youn_j4x7.pdf` (1,256 pages) | `695e2fdd7d110d55ebcd81a7640be764005ba7fb72a101a600912a289396ad6c` |
| Thayer's, `greekenglishlexi00grimuoft.pdf` (760 pages; Grimm's Wilke's Clavis translated, revised and enlarged by Thayer, **Corrected Edition**, copyright 1886 and 1889, University of Toronto copy) | `fd40321a663287edac24e1f11651aab0249d8db59c714e61a94351f7d8201ef9` |
| Strong's Exhaustive Concordance, 1890 | Not yet pinned. The scan has been downloaded by the project owner but is too large to upload to the working session. |

## Thayer's: the digital copy is not the print text

Comparing the ἀγάπη entry (PDF page 28 of the scan) with the digital copy in `imbennyhim/Every-Promise-Thayers` shows the copy is a normalised edition, not a transcription:

- Abbreviations are expanded ("bibl. and eccles." becomes "Biblical and ecclesiastical", "Mk." becomes "Mark", "Sap." becomes "Wis", "s. v." becomes "under the word").
- Scripture references are reformatted ("Cant. ii. 4, 5, 7" becomes "Son 2:4-5; Son 2:7").
- Word-sequence similarity with the print, after removing accents, was 0.80 for this entry, and some details differ.

So a quote that is "verbatim from Thayer's" is verbatim to the digital copy, not to the book. The page scan is the authority; the digital copy is a readable second reading. Any difference between the two is a flagged spot checked against the page image. Example: the OCR of the scan read "p. 885" where the digital copy says "p. 835"; the page image shows 835, so the OCR was wrong, at 90% reported confidence.

## What the check against the real sources found

`pipeline/ingest/check_sample.py` compares the sample's sourced fields with the copies above.

- Strong's for ἀγάπη matches exactly.
- Strong's for ἀγαπάω does not. The sample merges in the KJV rendering, fills in ἄγαν where the source has a gap, and cross-references G5368 where the source says "compare G5689".
- Thayer's text in the sample is condensed and reworded. Only some phrases appear verbatim in the real entries, and sentences such as "Used of God's saving love (John 3:16)…" are not in Thayer's at all.
- Bullinger and Young's fields cannot be checked until copies exist.

Until the sourced fields are regenerated from the real texts, a drafted quote that matches the sample proves only that it matches the sample, not the source.
