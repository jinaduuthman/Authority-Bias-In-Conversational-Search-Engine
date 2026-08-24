"""
Run the authority-bias experiment against closed-weight, API-served models.

Mirrors Scripts/run_experiment.py one-for-one in prompt construction, parsing,
and output schema. The only differences are:

  - Models are accessed over HTTPS (OpenAI Chat Completions or Gemini
    generateContent) instead of via local Ollama
  - Provider-aware rate limiting between calls
  - --limit N caps the number of cells (for budget-bounded incremental runs)
  - Results are written to data/extension/closed_weight_results/

Existing prompt templates and the formatter/parser are imported from
run_experiment.py so prompts are bit-identical to the open-weight runs.

Usage:
  export OPENAI_API_KEY=sk-...
  export GEMINI_API_KEY=...
  python3 Scripts/extension_closed_weight/run_closed_weight_experiment.py --model gpt-4o-mini
  python3 Scripts/extension_closed_weight/run_closed_weight_experiment.py --model gemini-1.5-flash
  python3 Scripts/extension_closed_weight/run_closed_weight_experiment.py --model gpt-4o-mini --limit 50  # smoke
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "Scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_experiment import (  # noqa: E402
    VARIANTS,
    CONDITIONS,
    format_papers_list,
    parse_recommendation,
)
from api_clients import call_model, APIError  # noqa: E402

SETS_FILE = PROJECT_ROOT / "data" / "experiment_sets.json"
RESULTS_DIR = PROJECT_ROOT / "data" / "extension" / "closed_weight_results"

SUPPORTED_MODELS = [
    "gpt-4o-mini",
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.5",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
    "claude-opus-4-7",
]

# Conservative inter-call delays.
# Gemini paid tier: 1,000 RPM -> 1.0s/call leaves huge headroom.
# OpenAI gpt-4o-mini, gpt-5.x: paid tiers are generous; small delay smooths bursts.
# Anthropic free-credit accounts default to 50 RPM on Tier 1 -> 1.5s/call is safe;
# for Tier 2+ this is over-conservative but adds <1h to a 2,250-cell run.
RATE_LIMIT_SECONDS = {
    "gpt-4o-mini": 0.0,
    "gpt-5.4": 0.3,
    "gpt-5.4-mini": 0.0,
    "gpt-5.5": 0.3,
    "gemini-2.5-flash": 1.0,
    "gemini-2.5-flash-lite": 1.0,
    "gemini-3-flash-preview": 1.0,
    "gemini-3.1-flash-lite": 1.0,
    "claude-haiku-4-5-20251001": 1.5,
    "claude-sonnet-4-6": 1.5,
    "claude-opus-4-7": 1.5,
}


def run_single(model: str, variant: str, condition: str, query_set: dict, dry_run: bool = False):
    candidates = query_set["candidates"].get(condition, [])
    if not candidates:
        return None

    prompt = VARIANTS[variant].format(
        query=query_set["query"],
        papers_list=format_papers_list(candidates),
    )

    if dry_run:
        return {"recommended": None, "response": "[dry run]", "prompt_length": len(prompt)}

    start = time.time()
    try:
        response = call_model(model, prompt)
    except APIError as e:
        print(f"      FATAL: {e}")
        sys.exit(1)
    elapsed = time.time() - start

    if response is None:
        return None

    recommended = parse_recommendation(response)

    return {
        "recommended": recommended,
        "recommended_paper_id": candidates[recommended - 1]["paper_id"] if recommended else None,
        "recommended_title": candidates[recommended - 1]["title"] if recommended else None,
        "response": response,
        "elapsed_seconds": round(elapsed, 2),
        "prompt_length": len(prompt),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run closed-weight authority-bias experiment")
    parser.add_argument("--model", required=True, choices=SUPPORTED_MODELS)
    parser.add_argument("--variant", choices=VARIANTS.keys(), help="Single variant (default: all)")
    parser.add_argument("--condition", choices=CONDITIONS, help="Single condition (default: all)")
    parser.add_argument("--topic", help="Single topic (default: all)")
    parser.add_argument("--limit", type=int, default=None, help="Cap total cells (for budget control)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not SETS_FILE.exists():
        sys.exit(f"Missing experiment sets: {SETS_FILE}")

    with SETS_FILE.open() as f:
        experiment_sets = json.load(f)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    variants = [args.variant] if args.variant else list(VARIANTS.keys())
    conditions = [args.condition] if args.condition else list(CONDITIONS)
    topics = [args.topic] if args.topic else list(experiment_sets.keys())

    total_runs = sum(
        len(experiment_sets[t]) * len(variants) * len(conditions)
        for t in topics if t in experiment_sets
    )
    if args.limit is not None:
        total_runs = min(total_runs, args.limit)

    print("=" * 64)
    print("Closed-Weight Experiment")
    print("=" * 64)
    print(f"Model      : {args.model}")
    print(f"Variants   : {variants}")
    print(f"Conditions : {conditions}")
    print(f"Topics     : {len(topics)}")
    print(f"Total cells: {total_runs}")
    print(f"Rate limit : {RATE_LIMIT_SECONDS.get(args.model, 0.0):.2f}s/call")
    print()

    safe_model = args.model.replace(":", "_").replace("/", "_")
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"closed_weight_{safe_model}_{run_id}.json"

    payload = {
        "metadata": {
            "model": args.model,
            "run_id": run_id,
            "started_at": datetime.now().isoformat(),
            "variants": variants,
            "conditions": conditions,
            "topics_count": len(topics),
            "decoding": "provider-default (no temperature/top_p override)",
            "experiment_sets_path": str(SETS_FILE.relative_to(PROJECT_ROOT)),
            "limit": args.limit,
        },
        "results": [],
    }
    completed = 0
    fatal_errors = 0
    delay = RATE_LIMIT_SECONDS.get(args.model, 0.0)

    try:
        for variant in variants:
            for topic in topics:
                if topic not in experiment_sets:
                    continue
                for q_set in experiment_sets[topic]:
                    for condition in conditions:
                        if args.limit is not None and completed >= args.limit:
                            raise StopIteration
                        completed += 1
                        qid = q_set["query_id"]
                        print(f"  [{completed}/{total_runs}] {args.model} | {variant} | "
                              f"{condition} | {qid}")

                        result = run_single(
                            args.model, variant, condition, q_set, dry_run=args.dry_run
                        )

                        if result is None:
                            fatal_errors += 1
                            if fatal_errors > 10:
                                print("Too many failures (>10). Aborting.")
                                raise StopIteration
                        else:
                            entry = {
                                "model": args.model,
                                "variant": variant,
                                "condition": condition,
                                "topic": topic,
                                "query_id": qid,
                                "query": q_set["query"],
                                **result,
                            }
                            payload["results"].append(entry)
                            rec = result.get("recommended", "?")
                            elapsed = result.get("elapsed_seconds", 0)
                            print(f"    -> Paper {rec} ({elapsed:.1f}s)")

                        if completed % 25 == 0:
                            with results_file.open("w") as f:
                                json.dump(payload, f, indent=2, ensure_ascii=False)

                        if delay and not args.dry_run:
                            time.sleep(delay)
    except StopIteration:
        pass
    except KeyboardInterrupt:
        print("\nInterrupted; saving partial results.")

    payload["metadata"]["completed_at"] = datetime.now().isoformat()
    payload["metadata"]["completed_cells"] = completed
    payload["metadata"]["successful_cells"] = len(payload["results"])
    payload["metadata"]["fatal_errors"] = fatal_errors

    with results_file.open("w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 64)
    print(f"Cells attempted : {completed}")
    print(f"Cells succeeded : {len(payload['results'])}")
    print(f"Fatal errors    : {fatal_errors}")
    print(f"Results saved   : {results_file.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
