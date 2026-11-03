#!/usr/bin/env python3
"""Pilot: draft derived lexicon fields with local Ollama models, check them, and
report tokens, time and (optional) cost. Standard library only.

Leave-one-out on the sample: each lemma is drafted with the OTHER lemma as the
few-shot example, then compared with the sample's own derived fields as a control.

Nothing here calls the Claude API unless you pass --verify with every spend guard
(see README.md). Without --verify, the script only talks to your local Ollama.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import DRAFT_SCHEMA, check_draft  # noqa: E402

HERE = Path(__file__).resolve().parent
DEFAULT_SAMPLE = HERE.parents[1] / "data" / "samples" / "agape_agapao_lexical_sample.json"

SOURCE_KEYS = ("greek", "transliteration", "strongs", "youngs", "bullinger", "thayers",
               "related_words", "morphology_common_forms", "occurrences_sample")

SYSTEM = (
    "You write short reference notes for a Biblical Greek lexicon dataset. "
    "Use ONLY the SOURCE JSON you are given. Do not add facts, Greek or Hebrew words, "
    "Strong's numbers, verse references or numbers that are not in the SOURCE. "
    "If the SOURCE does not support a statement, leave it out. "
    "Write plain, neutral English and do not argue for any doctrine. "
    "Return JSON only, matching the schema."
)

VERIFY_SYSTEM = (
    "You audit a DRAFT against its SOURCE. List every statement in the DRAFT that the SOURCE "
    "does not directly support. Do not use outside knowledge to excuse a statement. "
    'Reply with JSON only: {"unsupported": [{"field": "...", "claim": "...", "reason": "..."}]}. '
    "Use an empty list if everything is supported."
)

TOTAL_KEYS = ("prompt_tokens", "output_tokens", "seconds", "gen_seconds")


def load_lemmas(path):
    words = json.loads(Path(path).read_text(encoding="utf-8"))["words"]
    lemmas = {}
    for name, w in words.items():
        lemmas[name] = {
            "source": {k: w[k] for k in SOURCE_KEYS if k in w},
            "gold": {
                "etymology_note": w["etymology_note"],
                "distinctions": w["distinctions"],
                "semantic_contrasts": [{"strongs": c["strongs"], "summary": c["summary"]}
                                       for c in w["semantic_contrasts"]],
                "key_theological_notes": w["key_theological_notes"],
            },
        }
    return lemmas


def build_messages(example, source):
    def dump(obj, indent=None):
        return json.dumps(obj, ensure_ascii=False, indent=indent)
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "SOURCE:\n" + dump(example["source"], 1)},
        {"role": "assistant", "content": dump(example["gold"])},
        {"role": "user", "content": "SOURCE:\n" + dump(source, 1)},
    ]


def post_json(url, body, headers=None, timeout=900):
    req = urllib.request.Request(
        url, json.dumps(body).encode("utf-8"),
        {"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def ollama_chat(host, model, messages, num_ctx):
    body = {"model": model, "messages": messages, "stream": False, "format": DRAFT_SCHEMA,
            "think": False,
            "options": {"temperature": 0, "num_ctx": num_ctx, "num_predict": 1200}}
    try:
        try:
            r = post_json(f"{host}/api/chat", body)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            if "think" not in detail.lower():
                raise RuntimeError(f"Ollama error {e.code}: {detail[:300]}")
            body.pop("think")  # model has no thinking mode
            r = post_json(f"{host}/api/chat", body)
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach Ollama at {host}: {e.reason}")
    metrics = {"prompt_tokens": r.get("prompt_eval_count", 0),
               "output_tokens": r.get("eval_count", 0),
               "seconds": r.get("total_duration", 0) / 1e9,
               "gen_seconds": r.get("eval_duration", 0) / 1e9}
    return r["message"]["content"], metrics


def draft_lemma(host, model, example, target, num_ctx, retries):
    messages = build_messages(example, target["source"])
    totals = dict.fromkeys(TOTAL_KEYS, 0)
    first = None
    for attempt in range(retries + 1):
        content, m = ollama_chat(host, model, messages, num_ctx)
        for k in TOTAL_KEYS:
            totals[k] += m[k]
        try:
            draft = json.loads(content)
            result = check_draft(draft, target["source"])
        except json.JSONDecodeError:
            draft, result = None, {"fails": ["output is not valid JSON"], "flags": []}
        if attempt == 0:
            first = result
        if not result["fails"]:
            break
        messages += [{"role": "assistant", "content": content},
                     {"role": "user", "content": "Fix these problems and return corrected JSON only: "
                      + "; ".join(result["fails"])}]
    return {"draft": draft, "first_pass_ok": not first["fails"], "final": result,
            "attempts": attempt + 1, **totals}


class Budget:
    """Hard cap on Claude API spend. Every call is estimated first and logged after."""

    def __init__(self, cap_usd, prices, ledger_path):
        self.cap, self.prices, self.ledger = cap_usd, prices, ledger_path
        self.spent = 0.0

    def cost(self, input_tokens, output_tokens):
        return (input_tokens * self.prices["input_per_mtok"]
                + output_tokens * self.prices["output_per_mtok"]) / 1e6

    def worst_case(self, chars, max_output):
        return self.cost(chars / 2.5, max_output)  # 2.5 chars/token overestimates on purpose

    def check(self, chars, max_output):
        need = self.worst_case(chars, max_output)
        if self.spent + need > self.cap:
            raise RuntimeError(f"Stopping: next call could cost ${need:.4f}; "
                               f"${self.spent:.4f} of the ${self.cap:.2f} cap is already spent")

    def record(self, label, usage):
        c = self.cost(usage["input_tokens"], usage["output_tokens"])
        self.spent += c
        with open(self.ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "label": label,
                                "input_tokens": usage["input_tokens"],
                                "output_tokens": usage["output_tokens"], "usd": round(c, 6)}) + "\n")
        return c


def verify(budget, model, source, draft, label):
    user = ("SOURCE:\n" + json.dumps(source, ensure_ascii=False)
            + "\n\nDRAFT:\n" + json.dumps(draft, ensure_ascii=False))
    max_out = 600
    budget.check(len(user) + len(VERIFY_SYSTEM), max_out)
    r = post_json("https://api.anthropic.com/v1/messages",
                  {"model": model, "max_tokens": max_out, "system": VERIFY_SYSTEM,
                   "messages": [{"role": "user", "content": user}]},
                  {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    text = "".join(b.get("text", "") for b in r["content"] if b.get("type") == "text")
    usd = budget.record(label, r["usage"])
    try:
        unsupported = json.loads(text).get("unsupported", [])
    except (json.JSONDecodeError, AttributeError):
        unsupported = [{"field": "?", "claim": "verifier reply was not valid JSON", "reason": text[:200]}]
    return {"unsupported": unsupported, "usd": usd}


def verify_problems(args):
    problems = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        problems.append("ANTHROPIC_API_KEY is not set")
    if not args.verify_model:
        problems.append("--verify-model is required")
    if not args.max_usd or args.max_usd <= 0:
        problems.append("--max-usd must be a positive dollar cap")
    if not args.confirm_spend:
        problems.append("--confirm-spend is required: this will bill your API account")
    try:
        prices = json.loads(Path(args.pricing).read_text())
        if not all(isinstance(prices.get(k), (int, float)) for k in ("input_per_mtok", "output_per_mtok")):
            problems.append(f"fill in input_per_mtok and output_per_mtok in {args.pricing}")
    except (OSError, json.JSONDecodeError):
        problems.append(f"cannot read pricing file {args.pricing}")
    return problems


def write_report(out, rows, control, projection_n):
    lines = ["# Pilot report", "",
             "| Model | Lemmas | First-pass OK | Final OK | Flags/lemma | Output tokens | Prompt tokens | Seconds | Out tok/s |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for model, rs in rows.items():
        n = len(rs)
        gen = sum(r["gen_seconds"] for r in rs) or 1e-9
        lines.append(
            f"| {model} | {n} | {sum(r['first_pass_ok'] for r in rs)}/{n} | "
            f"{sum(not r['final']['fails'] for r in rs)}/{n} | "
            f"{sum(len(r['final']['flags']) for r in rs) / n:.1f} | "
            f"{sum(r['output_tokens'] for r in rs)} | {sum(r['prompt_tokens'] for r in rs)} | "
            f"{sum(r['seconds'] for r in rs):.0f} | {sum(r['output_tokens'] for r in rs) / gen:.1f} |")
    lines += ["", f"Control (the sample's own fields): {control['fails']} hard fails, "
              f"{control['flags']} flags across {control['n']} lemmas. Flags in the control are "
              "the noise floor: they come from the sample using words and references that its source "
              "fields do not contain.", "", f"## Projection to {projection_n} lemmas (local drafting)", ""]
    for model, rs in rows.items():
        per = sum(r["seconds"] for r in rs) / len(rs)
        lines.append(f"- {model}: about {per * projection_n / 3600:.1f} hours "
                     f"({sum(r['output_tokens'] for r in rs) / len(rs):.0f} output tokens per lemma, "
                     "retries included)")
    verified = [r for rs in rows.values() for r in rs if "verify" in r]
    if verified:
        per = sum(r["verify"]["usd"] for r in verified) / len(verified)
        lines += ["", "## Claude verification",
                  f"- {len(verified)} calls, ${sum(r['verify']['usd'] for r in verified):.4f} actual spend",
                  f"- Projected for {projection_n} lemmas at this rate: ${per * projection_n:,.2f} "
                  "(one verification per lemma, no retries)"]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", default=str(DEFAULT_SAMPLE))
    ap.add_argument("--models", nargs="+", required=True, help="Ollama model tags to compare")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--num-ctx", type=int, default=8192,
                    help="context window; prompts are ~4K tokens plus retries, and Ollama silently "
                         "truncates anything beyond this")
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--project-lemmas", type=int, default=8000)
    ap.add_argument("--out", default="pilot_out")
    ap.add_argument("--dry-run", action="store_true", help="print prompt sizes; call nothing")
    ap.add_argument("--verify", action="store_true", help="also verify drafts with the Claude API (costs money)")
    ap.add_argument("--verify-model", default=None)
    ap.add_argument("--max-usd", type=float, default=None)
    ap.add_argument("--pricing", default=str(HERE / "pricing.json"))
    ap.add_argument("--confirm-spend", action="store_true")
    args = ap.parse_args()

    lemmas = load_lemmas(args.sample)
    names = list(lemmas)
    if len(names) < 2:
        sys.exit("Need at least two lemmas for leave-one-out drafting.")

    if args.verify:
        problems = verify_problems(args)
        if problems:
            sys.exit("Refusing to run --verify:\n  - " + "\n  - ".join(problems))

    if args.dry_run:
        for name in names:
            other = lemmas[next(n for n in names if n != name)]
            chars = sum(len(m["content"]) for m in build_messages(other, lemmas[name]["source"]))
            print(f"{name}: prompt is {chars} characters, about {int(chars / 2.5)} tokens (rough upper estimate)")
        print("Dry run: nothing was called.")
        return

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    budget = None
    if args.verify:
        budget = Budget(args.max_usd, json.loads(Path(args.pricing).read_text()), out / "cost_ledger.jsonl")
        print(f"Claude verification enabled with a hard cap of ${args.max_usd:.2f}. "
              f"Every call is logged to {out / 'cost_ledger.jsonl'}.")

    control = {"n": len(names), "fails": 0, "flags": 0}
    for name in names:
        res = check_draft(lemmas[name]["gold"], lemmas[name]["source"])
        control["fails"] += len(res["fails"])
        control["flags"] += len(res["flags"])

    rows = {}
    for model in args.models:
        rows[model] = []
        for name in names:
            example = lemmas[next(n for n in names if n != name)]
            print(f"[{model}] drafting {name} ...", flush=True)
            r = draft_lemma(args.host, model, example, lemmas[name], args.num_ctx, args.retries)
            r["lemma"] = name
            if budget and r["draft"] is not None and not r["final"]["fails"]:
                r["verify"] = verify(budget, args.verify_model, lemmas[name]["source"], r["draft"],
                                     f"{model}:{name}")
            rows[model].append(r)
        safe = model.replace(":", "_").replace("/", "_")
        (out / f"{safe}.json").write_text(json.dumps(rows[model], ensure_ascii=False, indent=1), encoding="utf-8")

    print(write_report(out, rows, control, args.project_lemmas))
    if budget:
        print(f"\nClaude spend this run: ${budget.spent:.4f} of ${args.max_usd:.2f} cap.")


if __name__ == "__main__":
    main()
