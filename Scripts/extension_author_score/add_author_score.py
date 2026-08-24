"""
Annotate every paper in scholar_papers.json with an author_score derived from the
maximum h-index across its authors.

This is part of an isolated extension (see Scripts/extension_author_score/README.md).
It only ever READS data/scholar_papers.json. Output is written to
data/extension/scholar_papers_with_author_score.json.

Tier definition (per project lead, 2026-05-09):

    Tier  max h-index  author_score
    A*    >= 70        1.00
    A     40 - 69      0.85
    B     20 - 39      0.65
    C      5 - 19      0.45
    D      0 -  4      0.15
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PAPERS = PROJECT_ROOT / "data" / "scholar_papers.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "extension" / "scholar_papers_with_author_score.json"


def author_max_h(paper: dict) -> int:
    """Maximum h-index across all listed authors. 0 when no h-index is available."""
    authors = paper.get("authors") or []
    h_values = [a.get("h_index") for a in authors if isinstance(a.get("h_index"), int)]
    return max(h_values) if h_values else 0


def h_to_tier(max_h: int) -> tuple[str, float]:
    if max_h >= 70:
        return "A*", 1.00
    if max_h >= 40:
        return "A", 0.85
    if max_h >= 20:
        return "B", 0.65
    if max_h >= 5:
        return "C", 0.45
    return "D", 0.15


def main() -> None:
    if not SOURCE_PAPERS.exists():
        raise SystemExit(f"Source not found: {SOURCE_PAPERS}")

    with SOURCE_PAPERS.open() as f:
        papers_by_topic = json.load(f)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    tier_counts: Counter[str] = Counter()
    total = 0
    h_distribution = []

    for topic, papers in papers_by_topic.items():
        for paper in papers:
            mh = author_max_h(paper)
            tier, score = h_to_tier(mh)
            paper["author_max_h"] = mh
            paper["author_tier"] = tier
            paper["author_score"] = score
            tier_counts[tier] += 1
            h_distribution.append(mh)
            total += 1

    with OUTPUT_PATH.open("w") as f:
        json.dump(papers_by_topic, f, indent=2)

    h_distribution.sort()
    print("=" * 60)
    print("Author Score Annotation")
    print("=" * 60)
    print(f"Papers annotated: {total}")
    print(f"max h-index range: {h_distribution[0]} - {h_distribution[-1]}")
    print(f"max h-index median: {h_distribution[len(h_distribution) // 2]}")
    print()
    print("Tier distribution:")
    for tier in ["A*", "A", "B", "C", "D"]:
        n = tier_counts[tier]
        pct = 100.0 * n / total if total else 0.0
        print(f"  {tier:<3} ({n:>4}, {pct:5.1f}%)")
    print()
    print(f"Wrote: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
