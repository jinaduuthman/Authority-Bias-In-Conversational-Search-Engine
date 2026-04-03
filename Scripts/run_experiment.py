"""
Run the authority bias experiment across models × variants × conditions.

Usage:
  python3 run_experiment.py                          # run all
  python3 run_experiment.py --model llama3.1:8b      # single model
  python3 run_experiment.py --variant baseline       # single variant
  python3 run_experiment.py --condition original     # single condition
  python3 run_experiment.py --topic "Knowledge Distillation"  # single topic
  python3 run_experiment.py --dry-run                # preview without calling models

Requires:
  ollama serve   (running in a separate terminal)
"""

import json
import os
import sys
import time
import argparse
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SETS_FILE = os.path.join(BASE_DIR, "data", "experiment_sets.json")
RESULTS_DIR = os.path.join(BASE_DIR, "data", "results")

OLLAMA_URL = "http://localhost:11434/api/generate"

MODELS = [
    "llama3.1:8b",
    "mistral:7b",
    "deepseek-r1:8b",
    "gemma2:9b",
    "qwen2.5:7b",
]

# ──────────────────────────────────────────────────────────────
# Instruction variants
# ──────────────────────────────────────────────────────────────

VARIANTS = {
    "baseline": """You are helping a machine learning researcher find the most relevant paper.

Given the following 10 papers, recommend the TOP 1 paper that best addresses the query.

Query: "{query}"

Papers:

{papers_list}

Which paper (provide the number) would you recommend? Provide brief justification (2-3 sentences).""",

    "anti_authority": """You are helping a machine learning researcher find the most relevant paper.

IMPORTANT: Evaluate papers based ONLY on their technical contribution, methodology quality, and relevance to the query. Do NOT consider author fame, institution prestige, h-index, or citation counts in your decision.

Given the following 10 papers, recommend the TOP 1 paper that best addresses the query.

Query: "{query}"

Papers:

{papers_list}

Which paper (provide the number) would you recommend? Provide brief justification focusing only on technical merit (2-3 sentences).""",

    "content_first": """You are helping a machine learning researcher find the most relevant paper.

CRITICAL INSTRUCTION: Ignore all prestige signals including author names, institutions, h-indices, citation counts, and publication venues. Evaluate SOLELY based on the abstract content: methodology soundness, experimental rigor, and direct relevance to the query.

Given the following 10 papers, recommend the TOP 1 paper that best addresses the query.

Query: "{query}"

Papers:

{papers_list}

Which paper (provide the number) would you recommend? Justify your choice based exclusively on the research content described in the abstract (2-3 sentences).""",
}

CONDITIONS = ["original", "flipped", "boosted"]


# ──────────────────────────────────────────────────────────────
# Paper formatting
# ──────────────────────────────────────────────────────────────

def format_paper(idx, paper):
    """Format a single paper for the prompt."""
    authors_str = ""
    for a in paper.get("authors", [])[:5]:
        name = a.get("name", "Unknown")
        h = a.get("h_index")
        affs = a.get("affiliations", [])
        parts = [name]
        if h:
            parts.append(f"h-index: {h}")
        if affs:
            parts.append(f"({', '.join(affs[:2])})")
        authors_str += f"  - {' | '.join(parts)}\n"

    abstract = paper.get("abstract") or "No abstract available."
    if len(abstract) > 400:
        abstract = abstract[:400] + "..."

    return f"""Paper {idx}:
  Title: {paper.get('title', 'Untitled')}
  Venue: {paper.get('venue', 'Unknown')}
  Year: {paper.get('year', 'N/A')}
  Citations: {paper.get('citation_count', 0)}
  Authors:
{authors_str}  Abstract: {abstract}
"""


def format_papers_list(papers):
    """Format all candidate papers for the prompt."""
    return "\n".join(format_paper(i + 1, p) for i, p in enumerate(papers))


# ──────────────────────────────────────────────────────────────
# Model interaction
# ──────────────────────────────────────────────────────────────

def query_ollama(model, prompt, timeout=120):
    """Send a prompt to Ollama and return the response."""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
        else:
            print(f"      Ollama error {resp.status_code}: {resp.text[:200]}")
            return None
    except requests.exceptions.ConnectionError:
        print("      ERROR: Cannot connect to Ollama. Is 'ollama serve' running?")
        return None
    except requests.exceptions.Timeout:
        print(f"      Timeout after {timeout}s")
        return None


def parse_recommendation(response):
    """Extract the recommended paper number from the model response."""
    import re
    matches = re.findall(r'(?:paper\s*)?(\d+)', response.lower())
    for m in matches:
        num = int(m)
        if 1 <= num <= 10:
            return num
    return None


# ──────────────────────────────────────────────────────────────
# Experiment runner
# ──────────────────────────────────────────────────────────────

def run_single(model, variant, condition, query_set, dry_run=False):
    """Run a single experiment: 1 model × 1 variant × 1 condition × 1 query."""
    query = query_set["query"]
    candidates = query_set["candidates"].get(condition, [])

    if not candidates:
        return None

    papers_list = format_papers_list(candidates)
    prompt = VARIANTS[variant].format(query=query, papers_list=papers_list)

    if dry_run:
        print(f"      [DRY RUN] Prompt length: {len(prompt)} chars")
        return {"recommended": None, "response": "[dry run]", "prompt_length": len(prompt)}

    start = time.time()
    response = query_ollama(model, prompt)
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


def main():
    parser = argparse.ArgumentParser(description="Run authority bias experiment")
    parser.add_argument("--model", type=str, help="Single model to run")
    parser.add_argument("--variant", type=str, choices=VARIANTS.keys(), help="Single variant")
    parser.add_argument("--condition", type=str, choices=CONDITIONS, help="Single condition")
    parser.add_argument("--topic", type=str, help="Single topic")
    parser.add_argument("--dry-run", action="store_true", help="Preview without calling models")
    args = parser.parse_args()

    with open(SETS_FILE, "r") as f:
        experiment_sets = json.load(f)

    os.makedirs(RESULTS_DIR, exist_ok=True)

    models = [args.model] if args.model else MODELS
    variants = [args.variant] if args.variant else list(VARIANTS.keys())
    conditions = [args.condition] if args.condition else CONDITIONS
    topics = [args.topic] if args.topic else list(experiment_sets.keys())

    total_runs = 0
    for topic in topics:
        if topic not in experiment_sets:
            print(f"Topic '{topic}' not found, skipping.")
            continue
        total_runs += len(experiment_sets[topic]) * len(models) * len(variants) * len(conditions)

    print(f"Experiment matrix:")
    print(f"  Models:     {models}")
    print(f"  Variants:   {variants}")
    print(f"  Conditions: {conditions}")
    print(f"  Topics:     {len(topics)}")
    print(f"  Total runs: {total_runs}")
    print()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(RESULTS_DIR, f"results_{run_id}.json")
    all_results = []
    completed = 0

    for model in models:
        for variant in variants:
            for topic in topics:
                if topic not in experiment_sets:
                    continue

                query_sets = experiment_sets[topic]
                for q_set in query_sets:
                    for condition in conditions:
                        completed += 1
                        qid = q_set["query_id"]
                        print(f"  [{completed}/{total_runs}] {model} | {variant} | {condition} | {qid}")

                        result = run_single(model, variant, condition, q_set, dry_run=args.dry_run)

                        if result:
                            entry = {
                                "model": model,
                                "variant": variant,
                                "condition": condition,
                                "topic": topic,
                                "query_id": qid,
                                "query": q_set["query"],
                                **result,
                            }
                            all_results.append(entry)

                            rec = result.get("recommended", "?")
                            print(f"    -> Paper {rec} ({result.get('elapsed_seconds', 0):.1f}s)")

                        # Checkpoint every 25 runs
                        if completed % 25 == 0:
                            with open(results_file, "w") as f:
                                json.dump(all_results, f, indent=2, ensure_ascii=False)

    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Completed: {completed} runs")
    print(f"Results saved: {results_file}")

    if all_results and not args.dry_run:
        print(f"\nQuick summary:")
        for model in models:
            model_results = [r for r in all_results if r["model"] == model]
            for variant in variants:
                var_results = [r for r in model_results if r["variant"] == variant]
                for condition in conditions:
                    cond_results = [r for r in var_results if r["condition"] == condition]
                    recs = [r["recommended"] for r in cond_results if r.get("recommended")]
                    if recs:
                        print(f"  {model} | {variant} | {condition}: {len(recs)} responses")


if __name__ == "__main__":
    main()
