# Drafting pilot

Compares local Ollama models on drafting the compiled ("derived") fields of a lexicon entry, checks every draft with deterministic rules, and reports tokens, time and cost. Standard library only; Python 3.9+.

## What it tests

Each lemma in the sample is drafted with the *other* lemma as the few-shot example (leave-one-out), then the sample's own fields serve as a control. Fields drafted: `etymology_note`, `distinctions`, `semantic_contrasts`, `key_theological_notes`. The `lxx_usage` summary is left out until raw Strong's Hebrew and Septuagint text is in `data/raw/`, because the sample has no source text to draft it from.

Everything copied from a source (Strong's number, definitions, KJV counts, verse text) is meant to be extracted by script, not drafted, so it is not part of this pilot.

## Checks (`checks.py`)

- **Fails** (draft is rejected and retried): wrong JSON shape, a Strong's number not in the source, a bare number not in the source.
- **Flags** (a person or the verifier looks): a Greek or Hebrew word, or a verse reference, not found verbatim in the source.

The control row in the report shows how many flags the sample's own fields produce. Treat that as the noise floor.

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

If a model is slow or fails to load, it may not fit in 8 GB with the context window. Lower `--num-ctx`, but note that prompts run about 4K tokens and a retry adds more; Ollama truncates silently past the limit.

## Claude verification (optional, costs money)

`--verify` sends each passing draft and its source to the Claude API and asks which statements the source does not support. It is off by default and refuses to run unless all of these are set:

1. `ANTHROPIC_API_KEY` in your environment
2. `--verify-model <model id>`
3. `--max-usd <cap>`, a hard dollar cap
4. `--confirm-spend`
5. a `pricing.json` with real prices (copy `pricing.example.json`; prices are blank on purpose)

Every call is estimated at a deliberately high token count before it is sent, skipped if it could exceed the cap, and logged to `pilot_out/cost_ledger.jsonl` afterward. This bills your API account, not your Claude subscription.
