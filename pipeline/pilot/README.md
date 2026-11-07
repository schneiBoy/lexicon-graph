# Drafting pilot

Compares local Ollama models on drafting the compiled ("derived") fields of a lexicon entry, checks every draft with deterministic rules, and reports tokens, time and cost. Standard library only; Python 3.9+.

## What it tests

Each lemma is drafted from its own source fields only. The prompt carries one made-up format example (never another lemma's text), so models cannot copy wording from a sibling entry. The sample's own derived fields are checked as a control. Fields drafted: `etymology_note`, `distinctions`, `semantic_contrasts`, `key_theological_notes`. The `lxx_usage` summary is left out until raw Strong's Hebrew and Septuagint text is in `data/raw/`, because the sample has no source text to draft it from.

Everything copied from a source (Strong's number, definitions, KJV counts, verse text) is meant to be extracted by script, not drafted, so it is not part of this pilot.

## Source lock: every statement carries a quote

Each drafted statement is `{text, quote}` (a contrast is `{strongs, summary, quote}`). The quote must be copied character for character from one field of the source. A field the source says nothing about is an empty list. `checks.to_fields(draft, source)` turns a checked draft into the plain dataset fields plus an `evidence` list: each quote with the source field it came from (for example `bullinger.critical_lexicon_summary`), so a note can be attributed to its source automatically.

## Checks (`checks.py`)

- **Fails** (draft is rejected and retried): wrong JSON shape; a quote that is not verbatim inside one source field (including one stitched from two fields); a `strongs` entry that is not exactly `G` or `H` plus digits; a Strong's number, bare number, Greek or Hebrew word, or verse reference not in the source.
- **Flags** (a person or the verifier looks): words in a statement that are not in that statement's own quote. This is where padded wording shows up. The check is crude, so flags are for review, not an automatic rejection.

The check cannot tell whether a quote supports the statement written beside it. That judgement is left to the optional Claude audit and to the human reviewer.

The control row in the report counts items in the sample's own fields that are not in the five sources. The models should score at or near zero.

## Run it

```bash
# 1. See prompt sizes. Calls nothing.
python3 pilot.py --models granite4.2:8b --dry-run

# 2. Compare candidates on your local Ollama (free, uses your GPU)
python3 pilot.py --models granite4.2:8b qwen3.5:9b llama3.1:8b

# 3. Tests
python3 -m unittest discover -s tests -v
```

Output goes to `pilot_out/`: one JSON file per model plus `report.md` with first-pass and final pass rates, tokens, seconds, output tokens per second, and a projection to 8,000 lemmas.

If a model is slow or fails to load, it may not fit in 8 GB with the context window. Lower `--num-ctx`, but note that prompts run about 2.3K tokens and a retry adds more; Ollama truncates silently past the limit.

## Claude verification (optional, costs money)

`--verify` sends each passing draft and its source to the Claude API and asks which statements the source does not support. It is off by default and refuses to run unless all of these are set:

1. `ANTHROPIC_API_KEY` in your environment
2. `--verify-model <model id>`
3. `--max-usd <cap>`, a hard dollar cap
4. `--confirm-spend`
5. a `pricing.json` with real prices (copy `pricing.example.json`; prices are blank on purpose)

Every call is estimated at a deliberately high token count before it is sent, skipped if it could exceed the cap, and logged to `pilot_out/cost_ledger.jsonl` afterward. This bills your API account, not your Claude subscription.

## Running on the real source texts (no summaries)

```
python pipeline/pilot/pilot.py --lemmas data/pilot/lemmas.json --models qwen3.5:9b llama3.1:8b --out pilot_out_real
```

`data/pilot/lemmas.json` is built by `build_sources.py` from Strong's, Thayer's (digital, cut at 350 words), proofread Bullinger units, Young's verified counts and the tagged-KJV counts. There is no gold answer and no control row; the checks are the same (quotes must be verbatim, no invented numbers or words).
Lemmas so far: G26, G25, G5368, G4102, G4100, G5485, G1343.

## Checks added after the first real-source run (2026-11-07)

A draft is now also rejected for: a statement using content words that are not in its own quote (padding; a short list of structural words such as "denotes" is exempt);
one quote used for two statements; a contrast that lists only the word's own number or names a word its own quote does not mention (by number, or by Greek lemma via `lemma_index.json`);
a quote that includes a span a source marks `do_not_quote` (damaged print, known digital-copy error). `first_pass_fails` is now saved so it is clear why retries happen.
The time projection uses the median seconds per lemma, since the first call includes loading the model.
Rerun after pulling: `python pipeline/pilot/pilot.py --lemmas data/pilot/lemmas.json --models qwen3.5:9b --out pilot_out_real2`.
