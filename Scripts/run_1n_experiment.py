"""
1:N Flip Pilot Experiment — Empirically determine authority signal weights.

Design: For each query's 10 candidate papers, fix one paper's content and
dress it in each of the 10 papers' metadata (including its own as baseline).
This creates 10 conditions per fixed paper × 10 fixed papers = 100 conditions
per query. The LLM recommends 1 of 10 papers each time.

This directly measures: does wearing higher-authority metadata increase
recommendation probability, and which metadata components matter most?

Scope (Pilot B):
    5 topics × 10 queries × 10 fixed × 10 swaps × 1 model = 5,000 runs

Usage:
    python3 Scripts/run_1n_experiment.py                        # runs DEFAULT_MODEL
    python3 Scripts/run_1n_experiment.py --model llama3.1:8b    # specify model
    python3 Scripts/run_1n_experiment.py --all-models           # run all models sequentially
    python3 Scripts/run_1n_experiment.py --dry-run

Requires:
    ollama serve   (running in a separate terminal)
"""

import json
import os
import sys
import time
import copy
import argparse
import re
import statistics
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from authority_mappings import venue_score, paper_affiliation_score

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SETS_FILE = os.path.join(BASE_DIR, "data", "experiment_sets.json")
RESULTS_DIR = os.path.join(BASE_DIR, "data", "results", "1n_pilot")

OLLAMA_URL = "http://localhost:11434/api/generate"

PILOT_MODELS = [
    # "gemma2:9b",          # already completed
    "llama3.1:8b",
    "mistral:7b",
]

DEFAULT_MODEL = "llama3.1:8b"

PILOT_TOPICS = [
    "Knowledge Distillation",
    "Attention Mechanisms",
    "Federated Learning",
    "Image Generation",
    "Sentiment Analysis",
]

PROMPT_TEMPLATE = """You are helping a machine learning researcher find the most relevant paper.

Given the following 10 papers, recommend the TOP 1 paper that best addresses the query.

Query: "{query}"

Papers:

{papers_list}

Which paper (provide the number) would you recommend? Provide brief justification (2-3 sentences)."""


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
    return "\n".join(format_paper(i + 1, p) for i, p in enumerate(papers))


def query_ollama(model, prompt, timeout=120):
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
    matches = re.findall(r'(?:paper\s*)?(\d+)', response.lower())
    for m in matches:
        num = int(m)
        if 1 <= num <= 10:
            return num
    return None


def compute_metadata_components(paper):
    """Compute raw authority signal values for a paper's current metadata."""
    h_vals = [a.get("h_index") or 0 for a in paper.get("authors", [])]
    return {
        "max_h": max(h_vals) if h_vals else 0,
        "median_h": statistics.median(h_vals) if h_vals else 0,
        "citations": paper.get("citation_count", 0) or 0,
        "venue_score": venue_score(paper.get("venue", "")),
        "affiliation_score": paper_affiliation_score(paper),
    }


def swap_metadata(target_paper, source_paper):
    """
    Create a copy of target_paper with source_paper's authority metadata.
    Content (title, abstract, year, paper_id) stays from target.
    Metadata (authors, citations, venue) comes from source.
    """
    swapped = copy.deepcopy(target_paper)
    swapped["authors"] = copy.deepcopy(source_paper.get("authors", []))
    swapped["citation_count"] = source_paper.get("citation_count", 0)
    swapped["venue"] = source_paper.get("venue", "")
    return swapped


def run_1n_experiment(model, experiment_sets, topics, dry_run=False):
    """Run the 1:N flip experiment for the given topics."""
    results = []
    total_runs = 0
    successful = 0
    failed_parse = 0

    for topic in topics:
        if topic not in experiment_sets:
            print(f"  WARNING: Topic '{topic}' not found in experiment sets, skipping.")
            continue

        query_entries = experiment_sets[topic]
        print(f"\n{'='*60}")
        print(f"Topic: {topic} ({len(query_entries)} queries)")

        for q_idx, query_entry in enumerate(query_entries):
            query_text = query_entry["query"]
            original_papers = query_entry["candidates"]["original"]
            n_papers = len(original_papers)

            print(f"\n  Query {q_idx+1}/{len(query_entries)}: {query_text[:60]}...")

            for fixed_idx in range(n_papers):
                fixed_paper = original_papers[fixed_idx]
                fixed_title = fixed_paper.get("title", "")[:40]

                for source_idx in range(n_papers):
                    source_paper = original_papers[source_idx]
                    is_baseline = (fixed_idx == source_idx)

                    candidate_set = copy.deepcopy(original_papers)
                    if not is_baseline:
                        candidate_set[fixed_idx] = swap_metadata(
                            fixed_paper, source_paper
                        )

                    swapped_meta = compute_metadata_components(candidate_set[fixed_idx])
                    original_meta = compute_metadata_components(fixed_paper)
                    source_meta = compute_metadata_components(source_paper)

                    if dry_run:
                        total_runs += 1
                        continue

                    prompt = PROMPT_TEMPLATE.format(
                        query=query_text,
                        papers_list=format_papers_list(candidate_set),
                    )

                    t0 = time.time()
                    response = query_ollama(model, prompt)
                    latency = time.time() - t0
                    total_runs += 1

                    if response is None:
                        failed_parse += 1
                        continue

                    picked = parse_recommendation(response)
                    if picked is None:
                        failed_parse += 1

                    recommended_fixed = (picked == fixed_idx + 1) if picked else False

                    result = {
                        "topic": topic,
                        "query": query_text,
                        "model": model,
                        "fixed_paper_idx": fixed_idx,
                        "fixed_paper_id": fixed_paper.get("paper_id", ""),
                        "fixed_paper_title": fixed_paper.get("title", ""),
                        "source_paper_idx": source_idx,
                        "source_paper_id": source_paper.get("paper_id", ""),
                        "is_baseline": is_baseline,
                        "picked_paper_idx": (picked - 1) if picked else None,
                        "recommended_fixed_paper": recommended_fixed,
                        "fixed_paper_original_meta": original_meta,
                        "fixed_paper_wearing_meta": swapped_meta,
                        "source_meta": source_meta,
                        "response": response[:500],
                        "latency": round(latency, 2),
                        "parse_success": picked is not None,
                    }
                    results.append(result)
                    successful += 1

                    if total_runs % 50 == 0:
                        print(f"    [{total_runs} runs | {successful} ok | {failed_parse} failed]")

                    time.sleep(0.5)

    return results, total_runs, successful, failed_parse


def run_single_model(model, experiment_sets, topics, dry_run=False):
    """Run the 1:N pilot for a single model and save results."""
    print(f"\n{'#'*60}")
    print(f"# Model: {model}")
    print(f"# Topics: {topics}")
    print(f"# Expected: {len(topics) * 10 * 10 * 10} runs")
    print(f"{'#'*60}")

    if dry_run:
        _, total, _, _ = run_1n_experiment(model, experiment_sets, topics, dry_run=True)
        print(f"  [DRY RUN] Would run {total} calls (~{total * 10 / 3600:.1f} hours)")
        return

    os.makedirs(RESULTS_DIR, exist_ok=True)

    t_start = time.time()
    results, total, successful, failed = run_1n_experiment(
        model, experiment_sets, topics
    )
    elapsed = time.time() - t_start

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_tag = model.replace(":", "_").replace("/", "_")
    out_file = os.path.join(RESULTS_DIR, f"1n_pilot_{model_tag}_{timestamp}.json")
    with open(out_file, "w") as f:
        json.dump({
            "metadata": {
                "experiment_type": "1:N flip pilot",
                "model": model,
                "topics": topics,
                "total_runs": total,
                "successful": successful,
                "failed_parse": failed,
                "elapsed_seconds": round(elapsed, 1),
                "timestamp": timestamp,
            },
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"[{model}] Completed: {successful}/{total} runs ({failed} parse failures)")
    print(f"[{model}] Time: {elapsed/3600:.1f} hours ({elapsed:.0f}s)")
    print(f"[{model}] Avg latency: {elapsed/max(successful,1):.1f}s per run")
    print(f"[{model}] Output: {out_file}")


def main():
    parser = argparse.ArgumentParser(description="1:N Flip Pilot Experiment")
    parser.add_argument("--model", default=None,
                        help=f"Single model to run (default: {DEFAULT_MODEL})")
    parser.add_argument("--all-models", action="store_true",
                        help="Run all models in PILOT_MODELS sequentially")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--topics", nargs="+", default=None,
                        help="Override pilot topics")
    args = parser.parse_args()

    topics = args.topics or PILOT_TOPICS

    with open(SETS_FILE) as f:
        experiment_sets = json.load(f)

    if args.all_models:
        models = PILOT_MODELS
        print(f"1:N Flip Pilot — ALL MODELS mode")
        print(f"Models to run: {models}")
        print(f"Topics: {topics}")
        print(f"Total runs: {len(models)} models × {len(topics)*10*10*10} = {len(models)*len(topics)*10*10*10}")
        for model in models:
            run_single_model(model, experiment_sets, topics, dry_run=args.dry_run)
        print(f"\n{'='*60}")
        print(f"All models complete.")
    else:
        model = args.model or DEFAULT_MODEL
        print(f"1:N Flip Pilot — SINGLE MODEL mode")
        run_single_model(model, experiment_sets, topics, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
