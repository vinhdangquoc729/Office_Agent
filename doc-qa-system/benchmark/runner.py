"""Benchmark runner: sends each test case to both multi-agent and single-agent systems.

Usage:
    cd doc-qa-system/backend
    python ../benchmark/runner.py [--cases test_cases.json] [--out results.json] [--url ws://localhost:8000]

Prerequisites:
    - Backend running: uvicorn main:app --port 8000
    - Update test_cases.json: replace file_name with actual uploaded file names in uploads/
    - Or set BENCH_FILE_PDF / BENCH_FILE_XLSX / BENCH_FILE_DOCX env vars to actual file IDs
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import websockets

DEFAULT_URL = "ws://localhost:8000"
DEFAULT_CASES = Path(__file__).parent / "test_cases.json"
DEFAULT_OUT = Path(__file__).parent / "results.json"

SESSION_PREFIX = "bench"


async def run_single_case(ws_url: str, case: dict, mode: str, file_ids: dict) -> dict:
    """Connect via WebSocket, send one test case, collect full response."""
    file_type = case.get("file_type", "pdf")
    file_id = file_ids.get(file_type)
    if not file_id:
        return {
            "id": case["id"],
            "mode": mode,
            "error": f"No file_id for file_type={file_type}",
        }

    session_id = f"{SESSION_PREFIX}_{case['id']}_{mode}_{int(time.time())}"
    payload = {
        "file_ids": [file_id],
        "file_names": [case.get("file_name", f"file.{file_type}")],
        "message": case["query"],
        "session_id": session_id,
        "lang": "vi",
        "mode": mode,
    }

    tokens: list[str] = []
    activities: list[str] = []
    output_files: list = []
    error_text = ""
    input_tokens = 0
    output_tokens = 0
    cost_usd = 0.0
    t_start = time.monotonic()

    try:
        async with websockets.connect(f"{ws_url}/chat/ws", ping_timeout=None) as ws:
            await ws.send(json.dumps(payload))
            async for raw in ws:
                event = json.loads(raw)
                etype = event.get("type")
                if etype == "token":
                    tokens.append(event.get("text", ""))
                elif etype == "activity":
                    activities.append(event.get("text", ""))
                elif etype == "done":
                    output_files = event.get("output_files", [])
                    final_content = event.get("content", "")
                    if final_content:
                        tokens = [final_content]
                    input_tokens = event.get("input_tokens", 0)
                    output_tokens = event.get("output_tokens", 0)
                    cost_usd = event.get("cost_usd", 0.0)
                    break
                elif etype == "error":
                    error_text = event.get("text", "")
                    break
    except Exception as exc:
        error_text = str(exc)

    latency = time.monotonic() - t_start
    output_text = "".join(tokens)

    return {
        "id": case["id"],
        "mode": mode,
        "query": case["query"],
        "expected_intent": case.get("expected_intent", ""),
        "output_text": output_text,
        "output_files": output_files,
        "activities": activities,
        "latency_s": round(latency, 2),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "error": error_text,
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--mode", choices=["both", "multi", "single"], default="both",
                        help="Which mode(s) to benchmark")
    parser.add_argument("--id", default="", help="Run only the case with this id")
    parser.add_argument("--pdf-id", default=os.environ.get("BENCH_FILE_PDF", ""),
                        help="Uploaded file ID for PDF test cases")
    parser.add_argument("--xlsx-id", default=os.environ.get("BENCH_FILE_XLSX", ""),
                        help="Uploaded file ID for Excel test cases")
    parser.add_argument("--docx-id", default=os.environ.get("BENCH_FILE_DOCX", ""),
                        help="Uploaded file ID for Word/DOCX test cases")
    args = parser.parse_args()

    if not args.pdf_id and not args.xlsx_id and not args.docx_id:
        print("ERROR: Provide at least one file ID via --pdf-id / --xlsx-id / --docx-id or env vars.")
        print("  Upload a file first:  curl -X POST http://localhost:8000/upload -F 'file=@your.pdf'")
        sys.exit(1)

    file_ids = {"pdf": args.pdf_id, "xlsx": args.xlsx_id, "docx": args.docx_id}

    with open(args.cases, encoding="utf-8") as f:
        cases = json.load(f)

    modes = ["multi", "single"] if args.mode == "both" else [args.mode]
    if args.id:
        cases = [c for c in cases if c["id"] == args.id]
        if not cases:
            print(f"ERROR: No case with id='{args.id}'")
            sys.exit(1)

    # Load existing results and index by (id, mode) so we can merge
    out_path = Path(args.out)
    existing: dict[tuple, dict] = {}
    if out_path.exists():
        try:
            with open(out_path, encoding="utf-8") as f:
                for r in json.load(f):
                    existing[(r["id"], r["mode"])] = r
        except Exception:
            pass

    new_results = []
    for case in cases:
        ft = case.get("file_type", "pdf")
        if not file_ids.get(ft):
            print(f"  SKIP {case['id']} — no file_id for type={ft}")
            continue
        for mode in modes:
            print(f"  Running [{mode}] {case['id']} ...", end=" ", flush=True)
            result = await run_single_case(args.url, case, mode, file_ids)
            existing[(result["id"], result["mode"])] = result
            new_results.append(result)
            if result.get("error"):
                print(f"ERROR: {result['error']}")
            else:
                print(f"{result['latency_s']}s  [{result.get('input_tokens',0):,} in / {result.get('output_tokens',0):,} out / ${result.get('cost_usd',0):.4f}]")

    # Write merged results preserving original order from test_cases.json
    with open(args.cases, encoding="utf-8") as f:
        case_order = [(c["id"], m) for c in json.load(f) for m in ["multi", "single"]]
    results = [existing[k] for k in case_order if k in existing]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(results)} results ({len(new_results)} new/updated) → {args.out}")

    # Token / cost summary per mode (across all merged results)
    from collections import defaultdict
    totals: dict[str, dict] = defaultdict(lambda: {"input": 0, "output": 0, "cost": 0.0, "n": 0})
    for r in results:
        if r.get("error"):
            continue
        m = r["mode"]
        totals[m]["input"] += r.get("input_tokens", 0)
        totals[m]["output"] += r.get("output_tokens", 0)
        totals[m]["cost"] += r.get("cost_usd", 0.0)
        totals[m]["n"] += 1
    if totals:
        print(f"\n{'Mode':<10} {'Cases':>6} {'Input tok':>10} {'Output tok':>11} {'Cost USD':>10}")
        print("-" * 50)
        for mode_name, t in sorted(totals.items()):
            print(f"{mode_name:<10} {t['n']:>6} {t['input']:>10,} {t['output']:>11,} ${t['cost']:>9.4f}")


if __name__ == "__main__":
    asyncio.run(main())
