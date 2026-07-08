"""LLM-as-judge: scores benchmark results from runner.py.

Usage:
    cd doc-qa-system/benchmark
    python judge.py [--results results.json] [--out scores.json] [--judge-model claude-sonnet-5]

Judge model is resolved in this order:
  1. --judge-model CLI arg
  2. JUDGE_MODEL env var
  3. Default: claude-sonnet-5

Supported providers (auto-detected from model name):
  - "gpt-*" or "o*"       → OpenAI API (requires OPENAI_API_KEY)
  - anything else          → Anthropic API (requires ANTHROPIC_API_KEY)

Keeping the judge model different from the generation model (gpt-4o) avoids
self-grading bias.
"""

import argparse
import json
import os
from pathlib import Path
from collections import defaultdict

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

DEFAULT_RESULTS = Path(__file__).parent / "results.json"
DEFAULT_OUT = Path(__file__).parent / "scores.json"
DEFAULT_JUDGE_MODEL = "claude-sonnet-5"


def _call_judge(model: str, system: str, user: str) -> str:
    """Call the judge LLM and return raw text response."""
    if model.startswith(("gpt-", "o1", "o3", "o4")):
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        return resp.choices[0].message.content.strip()
    else:
        import anthropic
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=model,
            max_tokens=512,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text.strip()

JUDGE_SYSTEM = """You are an impartial judge evaluating two AI assistant responses to the same document-QA task.
Your job: score each response on 4 dimensions (scale 1-5):

- task_completion (1-5): Did the response fulfill the exact user request?
  5 = perfectly complete, nothing missing
  3 = partially complete, key parts missing
  1 = completely missed the point

- accuracy (1-5): Is the information factually consistent with what the document likely contains?
  5 = accurate, well-sourced
  3 = partially accurate, some guessing
  1 = fabricated or wrong

- format (1-5): Is the output format appropriate for the task type?
  5 = ideal format (table for data, markdown for report, etc.)
  3 = acceptable but not optimal
  1 = wrong format entirely

- conciseness (1-5): Is the response focused and concise without losing essential information?
  5 = perfectly concise
  3 = somewhat verbose or missing detail
  1 = extremely verbose or empty

Return ONLY valid JSON, no explanation:
{"A": {"task_completion": N, "accuracy": N, "format": N, "conciseness": N},
 "B": {"task_completion": N, "accuracy": N, "format": N, "conciseness": N}}"""

JUDGE_USER_TEMPLATE = """Task: {query}
Expected intent: {expected_intent}

=== Response A (multi-agent) ===
{output_a}

=== Response B (single-agent) ===
{output_b}

Score both responses."""


def judge_pair(model: str, query: str, expected_intent: str, output_a: str, output_b: str) -> dict:
    raw = _call_judge(
        model=model,
        system=JUDGE_SYSTEM,
        user=JUDGE_USER_TEMPLATE.format(
            query=query,
            expected_intent=expected_intent,
            output_a=output_a[:3000],
            output_b=output_b[:3000],
        ),
    )
    try:
        return json.loads(raw)
    except Exception:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group()) if m else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument(
        "--judge-model",
        default=os.environ.get("JUDGE_MODEL", DEFAULT_JUDGE_MODEL),
        help="Model to use as judge. Default: claude-sonnet-5 (via JUDGE_MODEL env or this flag).",
    )
    args = parser.parse_args()
    judge_model = args.judge_model
    print(f"Judge model: {judge_model}")

    with open(args.results, encoding="utf-8") as f:
        results = json.load(f)

    # Group by case_id and mode
    by_case: dict[str, dict] = defaultdict(dict)
    for r in results:
        by_case[r["id"]][r["mode"]] = r

    scored = []
    dims = ["task_completion", "accuracy", "format", "conciseness"]

    totals: dict[str, dict[str, list]] = {"multi": defaultdict(list), "single": defaultdict(list)}

    for case_id, modes in by_case.items():
        multi = modes.get("multi")
        single = modes.get("single")
        if not multi or not single:
            print(f"  SKIP {case_id} — missing one mode")
            continue

        if multi.get("error") or single.get("error"):
            print(f"  SKIP {case_id} — has error(s)")
            continue

        print(f"  Judging {case_id} ...", end=" ", flush=True)
        scores = judge_pair(
            model=judge_model,
            query=multi["query"],
            expected_intent=multi["expected_intent"],
            output_a=multi["output_text"],
            output_b=single["output_text"],
        )
        print("done")

        entry = {
            "id": case_id,
            "query": multi["query"],
            "latency_multi": multi["latency_s"],
            "latency_single": single["latency_s"],
            "scores_multi": scores.get("A", {}),
            "scores_single": scores.get("B", {}),
        }
        scored.append(entry)

        for dim in dims:
            if dim in scores.get("A", {}):
                totals["multi"][dim].append(scores["A"][dim])
            if dim in scores.get("B", {}):
                totals["single"][dim].append(scores["B"][dim])

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(scored)} scored pairs → {args.out}")

    # Summary table
    print("\n" + "=" * 60)
    print(f"{'Dimension':<20} {'Multi-agent':>12} {'Single-agent':>12}")
    print("-" * 60)
    for dim in dims:
        m_scores = totals["multi"][dim]
        s_scores = totals["single"][dim]
        m_avg = sum(m_scores) / len(m_scores) if m_scores else 0
        s_avg = sum(s_scores) / len(s_scores) if s_scores else 0
        print(f"{dim:<20} {m_avg:>12.2f} {s_avg:>12.2f}")

    all_latency_multi = [r["latency_multi"] for r in scored]
    all_latency_single = [r["latency_single"] for r in scored]
    if all_latency_multi:
        print("-" * 60)
        avg_m = sum(all_latency_multi) / len(all_latency_multi)
        avg_s = sum(all_latency_single) / len(all_latency_single)
        print(f"{'latency_avg (s)':<20} {avg_m:>12.1f} {avg_s:>12.1f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
