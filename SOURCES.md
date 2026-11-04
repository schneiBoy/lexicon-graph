# Sources

The project uses exactly five sources. This file records where machine-readable copies come from and what is still missing. Last updated 2026-11-03.

The Companion Bible and its appendixes (including App-135) are not a source. The sample's source list named them, but the project does not use them.

| Source | Machine-readable copy | Licence of the copy | Status |
| --- | --- | --- | --- |
| Strong's, Greek and Hebrew | [openscriptures/strongs](https://github.com/openscriptures/strongs) (`greek/strongs-greek-dictionary.js`, `hebrew/strongs-hebrew-dictionary.js`) | The 1890 text is public domain. The JSON files carry an Open Scriptures CC-BY-SA notice, which may require share-alike on anything derived from them. Decide before publishing the dataset. | Found. Greek verified against the sample. |
| Thayer's Greek-English Lexicon (1889) | [imbennyhim/Every-Promise-Thayers](https://github.com/imbennyhim/Every-Promise-Thayers) (5,521 entries, G1 to G5624, Markdown) | CC0 | Found. Hand-digitised, so transcription artifacts are possible. |
| Young's Analytical Concordance | None found | n/a | Missing. The text is old enough to be public domain, but no open copy turned up in GitHub searches. |
| Bullinger's Critical Lexicon and Concordance to the English and Greek New Testament | None found. Scans exist at archive.org (for example the [5th edition, 1908](https://archive.org/details/Criticallexiconconcordanceenggreeknt.5thed1908)). | n/a | Missing. Needs a text copy or OCR of a scan. |
| KJV text | Not yet chosen | n/a | Open. |

## What the check against the real sources found

`pipeline/ingest/check_sample.py` compares the sample's sourced fields with the copies above.

- Strong's for ἀγάπη matches exactly.
- Strong's for ἀγαπάω does not. The sample merges in the KJV rendering, fills in ἄγαν where the source has a gap, and cross-references G5368 where the source says "compare G5689".
- Thayer's text in the sample is condensed and reworded. Only some phrases appear verbatim in the real entries, and sentences such as "Used of God's saving love (John 3:16)…" are not in Thayer's at all.
- Bullinger and Young's fields cannot be checked until copies exist.

Until the sourced fields are regenerated from the real texts, a drafted quote that matches the sample proves only that it matches the sample, not the source.
