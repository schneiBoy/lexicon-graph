# Plan

Last updated: 2026-11-03

This is the working plan: what we build, in what order, the decisions made so far, and the next steps. The feature spec is in [`spec.md`](spec.md); the drafting pilot is in [`../pipeline/pilot/`](../pipeline/pilot/).

## Approach

Build the source-locked dataset first and the app on top of it. Each phase opens only after a quality gate passes, so the app never outruns the reviewed data.

## Order of work

1. **Foundation.** Add `SOURCES.md`, write the schema from the sample, split it into `G25.json` and `G26.json`, and add a CI check that fails if any field uses a source outside the five. *Gate: the schema validates the sample data.*
2. **Settle the open questions that touch the source lock.** Where verse-to-word mapping and parsing come from, whether other translations are allowed, and whether modern-scholarship annotations are allowed. These shape the schema, so they are decided before the dataset grows. Record each decision in `SOURCES.md`.
3. **Drafting pilot.** Run `pipeline/pilot/` on agapē and agapaō to choose the local model and measure tokens and time per lemma.
4. **Dataset growth, in this order:**
   1. Epistles: Romans through Jude, counting Hebrews as an epistle
   2. Gospels: Matthew, Mark, Luke, John
   3. Rest of the New Testament: Acts and Revelation
   4. Old Testament, Genesis to Malachi in canonical order (needs Hebrew-side raw source text in `data/raw/` first)

   *Gate: epistles fully reviewed and every field has a source.*
5. **Core study app.** Tap-a-word reader, word-study builder, translation comparator, contrast explorer. *Gate: every displayed field shows its source and status.*
6. **AI and discovery.** Write the evals first, then grounded Q&A, cross-reference engine, concept graph and heatmaps. *Gate: evals pass for citations, retrieval and refusals.*
7. **Learning, prep and scale.** Vocabulary trainer, graded reader, quizzes, sermon prep, then the full canon and the public API.

Dataset growth continues through the later books while the app is built on the reviewed epistles.

## Drafting pipeline

1. **Extract by script.** Strong's numbers, definitions, KJV counts, source quotations and verse text are copied exactly, and counts are computed. No model is involved.
2. **Draft locally.** A local Ollama model drafts only the compiled fields: etymology notes, distinctions, contrast summaries and theological notes. It sees only the raw source text for that lemma, and every statement it writes must carry a verbatim quote from that text. A field the sources say nothing about stays empty. Output is tagged `derived` and `unreviewed`, and the model is recorded in `drafted_by`.
3. **Check automatically.** A draft is rejected and retried if any quote is not verbatim in a single source field, or if it contains a Strong's number, number, Greek or Hebrew word, or verse reference that is not in the source. Statement wording that appears nowhere in the source is flagged for review.
4. **Audit with a stronger model.** Each passing draft is compared against its source text, and any unsupported statement is listed. Recorded in `verified_by`.
5. **Review.** A person checks the flagged items and a random sample, then promotes drafts to `reviewed`.

## Local model

Hardware: an 8 GB GPU, which fits roughly 7B to 9B models at 4-bit quantization.

Shortlist to compare in the pilot, from Ollama's library and a recent third-party 8 GB guide:

| Model | Size | Why it is on the list |
| --- | --- | --- |
| `granite4.2:8b` | about 5.3 GB | Described as having structured JSON output; leaves room for context |
| `qwen3.5:9b` | about 6.6 GB | Newer and widely used; tight on 8 GB once context is added |
| `llama3.1:8b` | about 4.9 GB | Most-pulled model; a stable baseline |

None of the sources reviewed tested Greek or Hebrew, so the pilot decides. If a model does not fit in VRAM it spills to system RAM and slows down.

## Cost and tokens

- Claude Pro has no published token or message count. It uses a five-hour session limit and weekly limits shared between claude.ai and Claude Code.
- Scripts that call the Claude API are billed separately through a Console API key, not through the Pro plan.
- Rough estimate (not from the docs): the verification pass is tens of millions of tokens across roughly 8,000 lemmas, too much for interactive Pro use. The pilot reports tokens per lemma so the full run can be priced before committing.
- Phases 1 to 3 are small and can be done directly with Claude.
- The pilot's Claude verifier is off by default and refuses to run without an API key, a model, a hard dollar cap, `--confirm-spend` and real prices. Every call is logged.
- Usage credits on a paid plan are opt-in and managed under Settings > Usage, where a monthly cap can be set.

## Decided

- Public repo, named `lexicon-graph`
- Source lock: Strong's, Young's, Bullinger, Thayer's and the KJV text, nothing else
- Local drafting plus automated checks and a grounded stronger-model audit, with human review
- No padded general knowledge: every drafted statement must carry a verbatim source quote, or it is rejected
- Rollout order: epistles, gospels, rest of the New Testament, then the Old Testament

## Still open

See the open questions in [`spec.md`](spec.md): verse-to-word mapping and parsing source, other translations, modern-scholarship annotations, Hebrew depth, first audience, hosting model, and dataset license.

## Next steps

- [ ] Add `SOURCES.md` listing the five sources and their editions
- [ ] Write the JSON Schema from the sample, with `source`, `derived`, `scholarly_status`, `drafted_by` and `verified_by` fields
- [ ] Split the sample into `data/lemmas/G25.json` and `G26.json`
- [ ] Add CI that validates the schema and fails on any source outside the five
- [x] Pilot round 1 (2 lemmas): qwen3.5:9b stayed closest to the source; granite and llama added outside material
- [ ] Rerun the pilot with the quote requirement, then on 15 to 20 lemmas once raw source text exists
- [ ] Decide the open questions that touch the source lock
