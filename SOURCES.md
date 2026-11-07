# Sources

The project uses exactly five sources. This file records where machine-readable copies come from and what is still missing. Last updated 2026-11-03.

The Companion Bible and its appendixes (including App-135) are not a source. The sample's source list named them, but the project does not use them.

| Source | Machine-readable copy | Licence of the copy | Status |
| --- | --- | --- | --- |
| Strong's, Greek and Hebrew | [openscriptures/strongs](https://github.com/openscriptures/strongs) (`greek/strongs-greek-dictionary.js`, `hebrew/strongs-hebrew-dictionary.js`) | The 1890 text is public domain. The JSON files carry an Open Scriptures CC-BY-SA notice, which may require share-alike on anything derived from them. Decide before publishing the dataset. | Found. Greek verified against the sample. |
| Thayer's Greek-English Lexicon (1889) | [imbennyhim/Every-Promise-Thayers](https://github.com/imbennyhim/Every-Promise-Thayers) (5,521 entries, G1 to G5624, Markdown) | CC0 | Found. Hand-digitised, so transcription artifacts are possible. |
| Young's Analytical Concordance | Scan on archive.org (`analyticalconcor0000youn_j4x7`), a revised edition with Index-Lexicons at the end; the year is not yet confirmed from the scan. The 260 MB PDF is not in the repo. | Public-domain text | Scan in hand. The built-in text layer reads English well but garbles Greek and some transliterations (it has "agapad" for "agapao"). Pages needed for each lemma are re-read at 300 dpi; a full re-read is about 3 hours. |
| Bullinger's Critical Lexicon and Concordance to the English and Greek New Testament | [5th ed., 1908 scan on archive.org](https://archive.org/details/Criticallexiconconcordanceenggreeknt.5thed1908), re-read by OCR from the page images: `data/raw/bullinger/ocr/` (1,043 pages) | Public-domain text; the OCR is ours | Done, with OCR errors. The scan's own text layer is unusable. Greek and English read well on the LOVE pages. |
| KJV text | [mattatanner/kjv_strongs](https://github.com/mattatanner/kjv_strongs): the 1769 KJV with Strong's numbers and tense, voice and mood tags, 31,102 verses, parses cleanly. | No licence file in the repo. The owner told the project owner it is meant for public use (not a written licence). The KJV text and Strong's numbers are public domain; the origin of the tense, voice and mood tags is not confirmed. A copy is kept in `data/raw/kjv/`. Ask the owner for a licence file before publishing the dataset. | Chosen for counts and verse lists. Reproduces Young's counts for G25 and G26 (see below). Replaces `kaiserlik/kjv`, where 14 of 27 NT books failed to parse. |

## Pinned scans

The page pointers in the graph refer to these exact files. They are not stored in the repo.

| Scan | SHA-256 |
| --- | --- |
| Bullinger, `CriticalLexiconConcordance.EngGrkNT..Bullinger.1908._text.pdf` (1,043 pages) | `cf34e792b85f06e0b804247657c6606af61b1d0663a8e25b0813a96dc37f8668` |
| Young's, `analyticalconcor0000youn_j4x7.pdf` (1,256 pages) | `695e2fdd7d110d55ebcd81a7640be764005ba7fb72a101a600912a289396ad6c` |
| Thayer's, `greekenglishlexi00grimuoft.pdf` (760 pages; Grimm's Wilke's Clavis translated, revised and enlarged by Thayer, **Corrected Edition**, copyright 1886 and 1889, University of Toronto copy) | `fd40321a663287edac24e1f11651aab0249d8db59c714e61a94351f7d8201ef9` |
| Strong's Exhaustive Concordance, 1890 | Not yet pinned. The scan has been downloaded by the project owner but is too large to upload to the working session. |

## Counts cross-check: Young's against the tagged KJV

Young's Index-Lexicon (PDF page 1159, read from the scan and checked against the page image) and a script count over `kjv_strongs.json` agree for both words.

| Word | Young's | Tagged KJV, raw tags | Tagged KJV, rule applied |
| --- | --- | --- | --- |
| ἀγάπη (G26) | love 86, charity 27, feast of charity 1, dear 1, charitably 1 = 116 | 116 | 116 |
| ἀγαπάω (G25) | love 135, beloved (passive participle) 7 = 142 | 147 | 142 |

For G25 the raw tag count is 147 because the tagger also marked five helper words next to the verb: "doth" (John 10:17), "have" (John 15:9), "which was" (Romans 9:25), "let" (Ephesians 5:33) and "let us" (1 John 3:18). Counting only tags followed by a verb-form (tense, voice, mood) tag gives 142: 135 non-"beloved" plus 7 "beloved", matching Young's exactly. The sample's G26 renderings list "charity (28x)" and "feasts of charity (1x)" together, which counts the feast line twice (Young's has 27 plus 1).

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


## Source errors found while checking pilot drafts (2026-11-07)

A quote that is verbatim in a digital copy can still be wrong. Two real cases:

1. **Strong's JSON (`strongs-greek-dictionary.js`) is damaged.** It drops the Greek word from 469 of 5,624 derivations (G25 reads "perhaps from (much)" where the source has "perhaps from ἄγαν (much)") and adds a lemma after every cross-reference that the source does not contain.
   The XML (`strongsgreek.xml`) it was built from has the words; but the XML labels three Hebrew cross-references as Greek (G25 to 5689, G137 to 5869, G4460 to 7343). The repo's xhtml links them as Old Testament.
   Fix: Strong's fields are now built by `pipeline/ingest/strongs_xml.py` from the XML, with the xhtml settling the language (`data/clean/strongs/greek.json`). openscriptures/strongs commit 0acd2f251c2d35ff8db2dece4e0593979d3ac223.
2. **Thayer's digital copy expands an abbreviation wrongly.** In the entry for δικαιοσύνη (G1343) the print (scan PDF page 173, printed page 149) reads "where δικ. καὶ ὁσιότης are connected", where δικ. is the entry's own abbreviated headword.
   The digital copy reads "where δίκαιος καί ὁσιότης are connected". A drafted note repeated the wrong word. The span is now marked `do_not_quote` in the pilot record, and the digital Thayer's stays a second reading only; the print scan is the authority.
