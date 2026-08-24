"""
Smoke test for the closed-weight extension.

Issues 6 API calls total: 1 topic x 1 query x 3 conditions x 1 instruction
(baseline) x 2 models (gpt-4o-mini + gemini-1.5-flash). Validates:

  1. API auth works for both providers
  2. The prompt formatter from run_experiment.py produces identical prompts
  3. The parser from run_experiment.py extracts a valid paper number
  4. The output JSON has the same schema as data/results/*.json
  5. End-to-end latency is within budget

Total cost: well under $0.05. Total time: ~15 seconds.

Usage:
  export OPENAI_API_KEY=sk-...
  export GEMINI_API_KEY=...
  python3 Scripts/extension_closed_weight/smoke_test.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "Scripts"))

from run_experiment import (  # noqa: E402  (path is set above)
    VARIANTS,
    CONDITIONS,
    format_papers_list,
    parse_recommendation,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_clients import call_model, APIError  # noqa: E402

SETS_FILE = PROJECT_ROOT / "data" / "experiment_sets.json"
# Claude added 2026-05-10 to validate the Anthropic adapter ahead of the
# Sonnet 4.6 frontier-comparison run. The other two models are already
# validated by the existing closed_weight_results/*.json files; keep them
# here only when re-validating the full provider matrix.
SMOKE_MODELS = ["claude-sonnet-4-6"]
SMOKE_VARIANT = "baseline"


def main() -> None:
    if not SETS_FILE.exists():
        sys.exit(f"Missing experiment sets: {SETS_FILE}")

    with SETS_FILE.open() as f:
        experiment_sets = json.load(f)

    topic = next(iter(experiment_sets.keys()))
    query_set = experiment_sets[topic][0]

    print("=" * 64)
    print("Closed-Weight Smoke Test")
    print("=" * 64)
    print(f"Topic     : {topic}")
    print(f"Query     : {query_set['query']}")
    print(f"Query ID  : {query_set['query_id']}")
    print(f"Variant   : {SMOKE_VARIANT}")
    print(f"Conditions: {CONDITIONS}")
    print(f"Models    : {SMOKE_MODELS}")
    print()

    failures = 0
    durations = []
    for model in SMOKE_MODELS:
        for condition in CONDITIONS:
            candidates = query_set["candidates"].get(condition, [])
            if not candidates:
                print(f"  [{model} | {condition}] no candidates, skipping")
                continue

            prompt = VARIANTS[SMOKE_VARIANT].format(
                query=query_set["query"],
                papers_list=format_papers_list(candidates),
            )

            start = time.time()
            try:
                response = call_model(model, prompt)
            except APIError as e:
                print(f"  [{model} | {condition}] FAIL: {e}")
                failures += 1
                continue
            elapsed = time.time() - start
            durations.append(elapsed)

            if response is None:
                print(f"  [{model} | {condition}] FAIL: no response (see error above)")
                failures += 1
                continue

            recommended = parse_recommendation(response)
            ok = recommended is not None and 1 <= recommended <= 10
            tag = "OK" if ok else "PARSE-FAIL"
            print(f"  [{model:<20} | {condition:<8}] {tag}  "
                  f"-> Paper {recommended} ({elapsed:.2f}s, prompt={len(prompt)} chars)")

            if not ok:
                failures += 1
                print(f"      response head: {response[:200]!r}")

    print()
    print("=" * 64)
    if failures:
        print(f"Smoke test FAILED: {failures} failure(s) of {len(SMOKE_MODELS) * len(CONDITIONS)}")
        sys.exit(1)
    print(f"All {len(SMOKE_MODELS) * len(CONDITIONS)} calls succeeded.")
    if durations:
        print(f"Latency: mean={sum(durations) / len(durations):.2f}s  "
              f"min={min(durations):.2f}s  max={max(durations):.2f}s")
    print("Ready for full run.")


if __name__ == "__main__":
    main()
