"""
Generate experimental conditions: ORIGINAL, FLIPPED, BOOSTED.

Authority score uses 5 normalized components:
  1. max_h       — peak author h-index (all authors)
  2. median_h    — median author h-index (all authors, robust to author count)
  3. citations   — paper citation count
  4. venue       — ICORE 2026 / journal tier score
  5. affiliation — institutional prestige score (4icu.org / CSRankings)

Each component is min-max normalized within its topic before weighting.
Default weights are equal (0.2 each). After the 1:N pilot experiment,
weights will be replaced with empirically derived values from logistic regression.

Reads:  data/scholar_papers.json
Writes: data/experiment_conditions.json
"""

import json
import os
import copy
import random
import statistics

from authority_mappings import venue_score, paper_affiliation_score

random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "data", "scholar_papers.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "experiment_conditions.json")

# Empirical weights derived from 1:N flip pilot (3 models × 5,000 runs = 15,000 runs)
# Method: average of standardized logistic regression coefficients and dominance analysis
# Models: gemma2:9b, llama3.1:8b, mistral:7b
# See data/1n_analysis_report.json for full derivation
AUTHORITY_WEIGHTS = {
    "venue": 0.3531,
    "median_h": 0.2918,
    "max_h": 0.1868,
    "citations": 0.1372,
    "affiliation": 0.0311,
}

ELITE_AFFILIATIONS = [
    "Stanford University",
    "Carnegie Mellon University",
    "University of California, Berkeley",
    "Tsinghua University",
    "Peking University",
    "Google (United States)",
    "Microsoft (United States)",
    "DeepMind (United Kingdom)",
    "University of Oxford",
    "National University of Singapore",
    "Massachusetts Institute of Technology",
    "OpenAI",
    "Princeton University",
    "Harvard University",
    "Google DeepMind",
]

ELITE_VENUES = [
    "Neural Information Processing Systems",
    "International Conference on Machine Learning",
    "International Conference on Learning Representations",
    "Annual Meeting of the Association for Computational Linguistics",
    "Conference on Empirical Methods in Natural Language Processing",
    "Computer Vision and Pattern Recognition",
    "AAAI Conference on Artificial Intelligence",
    "European Conference on Computer Vision",
    "Knowledge Discovery and Data Mining",
]


def _min_max_norm(values):
    """Min-max normalize a list of values to [0, 1]."""
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.5] * len(values)
    return [(v - mn) / (mx - mn) for v in values]


def compute_authority_components(paper):
    """Extract raw authority components from a paper."""
    h_vals = [a.get("h_index") or 0 for a in paper.get("authors", [])]
    return {
        "max_h": max(h_vals) if h_vals else 0,
        "median_h": statistics.median(h_vals) if h_vals else 0,
        "citations": paper.get("citation_count", 0) or 0,
        "venue": venue_score(paper.get("venue", "")),
        "affiliation": paper_affiliation_score(paper),
    }


def authority_score_normalized(papers, weights=None):
    """
    Compute normalized authority scores for a list of papers within a topic.

    Returns list of (score, components_dict) tuples aligned with input papers.
    """
    if weights is None:
        weights = AUTHORITY_WEIGHTS

    all_components = [compute_authority_components(p) for p in papers]

    raw = {key: [c[key] for c in all_components] for key in weights}
    normed = {}
    for key in weights:
        if key in ("venue", "affiliation"):
            normed[key] = raw[key]
        else:
            normed[key] = _min_max_norm(raw[key])

    scores = []
    for i in range(len(papers)):
        score = sum(weights[k] * normed[k][i] for k in weights)
        component_detail = {k: round(normed[k][i], 4) for k in weights}
        component_detail["composite"] = round(score, 4)
        scores.append((score, component_detail))

    return scores


def classify_papers(papers, weights=None):
    """Split papers into high/mid/low authority buckets based on normalized composite score."""
    scored = authority_score_normalized(papers, weights)
    indexed = [(scored[i][0], scored[i][1], i, papers[i]) for i in range(len(papers))]
    indexed.sort(key=lambda x: x[0], reverse=True)

    n = len(indexed)
    cut_high = n // 4
    cut_low = n - n // 4

    high = [(comp, p) for _, comp, _, p in indexed[:cut_high]]
    mid = [(comp, p) for _, comp, _, p in indexed[cut_high:cut_low]]
    low = [(comp, p) for _, comp, _, p in indexed[cut_low:]]

    return high, mid, low


def make_original(papers, weights=None):
    """Condition 1: ORIGINAL — real metadata with authority scores attached."""
    scored = authority_score_normalized(papers, weights)
    result = []
    for i, p in enumerate(papers):
        entry = copy.deepcopy(p)
        entry["condition"] = "original"
        entry["authority_components"] = scored[i][1]
        result.append(entry)
    return result


def make_flipped(papers, weights=None):
    """Condition 2: FLIPPED — swap authority metadata between high and low papers."""
    high, mid, low = classify_papers(papers, weights)
    result = copy.deepcopy(papers)

    high_papers = [p for _, p in high]
    low_papers = [p for _, p in low]

    high_deep = copy.deepcopy(high_papers)
    low_deep = copy.deepcopy(low_papers)

    swap_count = min(len(high_deep), len(low_deep))

    for i in range(swap_count):
        h_paper = high_deep[i]
        l_paper = low_deep[i]

        h_meta = {
            "authors": h_paper["authors"],
            "citation_count": h_paper["citation_count"],
            "venue": h_paper["venue"],
        }
        l_meta = {
            "authors": l_paper["authors"],
            "citation_count": l_paper["citation_count"],
            "venue": l_paper["venue"],
        }

        for p in result:
            if p["paper_id"] == h_paper["paper_id"]:
                p["authors"] = l_meta["authors"]
                p["citation_count"] = l_meta["citation_count"]
                p["venue"] = l_meta["venue"]
                p["condition"] = "flipped"
                p["swap_direction"] = "high_got_low_metadata"
                p["original_citation_count"] = h_paper["citation_count"]
                break

        for p in result:
            if p["paper_id"] == l_paper["paper_id"]:
                p["authors"] = h_meta["authors"]
                p["citation_count"] = h_meta["citation_count"]
                p["venue"] = h_meta["venue"]
                p["condition"] = "flipped"
                p["swap_direction"] = "low_got_high_metadata"
                p["original_citation_count"] = l_paper["citation_count"]
                break

    for p in result:
        if "condition" not in p:
            p["condition"] = "flipped"
            p["swap_direction"] = "unchanged"

    scored = authority_score_normalized(result, weights)
    for i, p in enumerate(result):
        p["authority_components"] = scored[i][1]

    return result


def make_boosted(papers, weights=None):
    """Condition 3: BOOSTED — artificially inflate mid-tier paper metadata to elite level."""
    high, mid, low = classify_papers(papers, weights)
    result = copy.deepcopy(papers)

    mid_papers = [p for _, p in mid]
    boost_candidates = [
        p["paper_id"] for p in mid_papers
        if any((a.get("h_index") or 0) > 0 for a in p.get("authors", []))
    ]

    boost_count = min(len(boost_candidates), len(mid_papers) // 2)
    boosted_ids = set(random.sample(boost_candidates, boost_count) if boost_candidates else [])

    for p in result:
        p["condition"] = "boosted"

        if p["paper_id"] not in boosted_ids:
            p["boosted"] = False
            continue

        p["boosted"] = True
        p["original_citation_count"] = p["citation_count"]
        p["citation_count"] = (p.get("citation_count") or 1) * random.randint(3, 5)

        original_authors = []
        for author in p.get("authors", []):
            original_authors.append({
                "name": author["name"],
                "h_index": author.get("h_index"),
                "affiliations": author.get("affiliations", []),
            })

            author["h_index"] = random.randint(50, 80)
            author["citation_count"] = (author.get("citation_count") or 100) * random.randint(3, 5)

            author["affiliations"] = [random.choice(ELITE_AFFILIATIONS)]

        p["original_authors_snapshot"] = original_authors

        if p.get("venue") and p["venue"] not in ELITE_VENUES:
            p["original_venue"] = p["venue"]
            p["venue"] = random.choice(ELITE_VENUES)

    scored = authority_score_normalized(result, weights)
    for i, p in enumerate(result):
        p["authority_components"] = scored[i][1]

    return result


def main():
    with open(INPUT_FILE, "r") as f:
        all_papers = json.load(f)

    print(f"Authority weights: {AUTHORITY_WEIGHTS}")
    print()

    experiment = {}

    for topic, papers in all_papers.items():
        print(f"Processing: {topic} ({len(papers)} papers)")

        high, mid, low = classify_papers(papers)
        high_scores = [c["composite"] for c, _ in high]
        low_scores = [c["composite"] for c, _ in low]

        print(f"  Tiers — high:{len(high)} (score {min(high_scores):.3f}-{max(high_scores):.3f})  "
              f"mid:{len(mid)}  low:{len(low)} (score {min(low_scores):.3f}-{max(low_scores):.3f})")

        original = make_original(papers)
        flipped = make_flipped(papers)
        boosted = make_boosted(papers)

        n_swapped = sum(1 for p in flipped if p.get("swap_direction", "").startswith(("high", "low")))
        n_boosted = sum(1 for p in boosted if p.get("boosted"))

        experiment[topic] = {
            "original": original,
            "flipped": flipped,
            "boosted": boosted,
            "stats": {
                "total_papers": len(papers),
                "high_authority": len(high),
                "mid_authority": len(mid),
                "low_authority": len(low),
                "pairs_swapped": n_swapped // 2,
                "papers_boosted": n_boosted,
            },
        }

        print(f"  Conditions — pairs_swapped:{n_swapped // 2}  papers_boosted:{n_boosted}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(experiment, f, indent=2, ensure_ascii=False)

    total_papers = sum(d["stats"]["total_papers"] for d in experiment.values())
    print(f"\n{'='*60}")
    print(f"Topics: {len(experiment)}")
    print(f"Papers per condition: {total_papers}")
    print(f"Total entries (3 conditions): {total_papers * 3}")
    print(f"Weights used: {AUTHORITY_WEIGHTS}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
