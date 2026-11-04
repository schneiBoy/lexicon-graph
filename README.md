# lexicon-graph

A structured, source-locked graph of Biblical Greek and Hebrew lexical data, designed to power word-study apps: a tap-a-word reader, word-study builder, translation comparator, concept graph, grounded AI Q&A and more.

## Status

Early planning. The repo currently holds the product spec and a two-word sample dataset (agapē G26 and agapaō G25). The schema, pipeline and app described in the spec do not exist yet.

## Contents

- [`docs/plan.md`](docs/plan.md): the working plan: order of work, drafting pipeline, local model shortlist, cost notes, decisions and next steps
- [`docs/spec.md`](docs/spec.md): features, workflows, data model, architecture, repo layout, risks and roadmap
- [`data/samples/agape_agapao_lexical_sample.json`](data/samples/agape_agapao_lexical_sample.json): sample entries for G26 and G25, with LXX background, translation variants, morphology and KJV verse layers for John 3:16 and John 21:15–17
- [`data/samples/agape_agapao_resource_description.md`](data/samples/agape_agapao_resource_description.md): what the sample contains and which sources it draws on
- [`SOURCES.md`](SOURCES.md): where open copies of the five sources come from, their licences, and what is still missing
- [`pipeline/ingest/`](pipeline/ingest/): `check_sample.py` compares the sample's sourced fields with the real source texts
- [`pipeline/pilot/`](pipeline/pilot/): a pilot for comparing local Ollama models at drafting the compiled fields, with automated checks and token and cost reporting

## Source lock

All lexical data comes from exactly these five sources, and the project does not add to or swap them:

- Strong's Exhaustive Concordance, Greek and Hebrew
- Young's Analytical Concordance
- Bullinger's Critical Lexicon and Concordance to the English and Greek New Testament
- Thayer's Greek-English Lexicon of the New Testament
- The KJV text for the verse layer

Fields compiled rather than quoted from these sources are tagged `derived`. See the spec's design principles for how the lock is enforced.

## License

Not yet chosen. The dataset license is an open question in the spec. Until a license file is added, all rights are reserved by default.
