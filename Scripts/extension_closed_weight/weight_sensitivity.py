#!/usr/bin/env python3
"""
weight_sensitivity.py — robustness of the flip-direction result to the choice of
authority weights (camera-ready reviewer request, ywjG).

The composite authority score alpha(p) = sum_d w_d * x_d feeds the flip-direction
analysis (Table: flip direction). This script recomputes the directional pull
(% of flips landing on a higher-composite paper) on the 8-model headline set
under three weighting schemes:

  * empirical  — the derived weights (Table: weights); reproduces the paper's numbers
  * uniform    — all five dimensions weighted equally (0.2 each)
  * single-dim — each dimension alone (venue-only, median_h-only, ...)

Dimensions are read from each candidate's stored authority_components, so no
new model runs are needed; this is a pure re-analysis.
"""
from __future__ import annotations
import json, os
from pathlib import Path
from scipy import stats as scipy_stats

ROOT = Path(__file__).resolve().parents[2]
OPEN_DIR = ROOT / "data" / "results"
CLOSED_DIR = ROOT / "data" / "extension" / "closed_weight_results"
SETS_FILE = ROOT / "data" / "experiment_sets.json"

HEADLINE = {
    "gemma2:9b", "llama3.1:8b", "mistral:7b", "qwen2.5:7b", "deepseek-r1:8b",
    "gpt-5.4", "gemini-3-flash-preview", "claude-sonnet-4-6",
}
ARCHIVED = {"gemini-2.5-flash", "gpt-4o-mini"}

DIMS = ["venue", "median_h", "max_h", "citations", "affiliation"]

SCHEMES = {
    "empirical":   {"venue": 0.3531, "median_h": 0.2918, "max_h": 0.1868,
                    "citations": 0.1372, "affiliation": 0.0311},
    "uniform":     {d: 0.2 for d in DIMS},
    "venue-only":       {d: (1.0 if d == "venue" else 0.0) for d in DIMS},
    "median_h-only":    {d: (1.0 if d == "median_h" else 0.0) for d in DIMS},
    "max_h-only":       {d: (1.0 if d == "max_h" else 0.0) for d in DIMS},
    "citations-only":   {d: (1.0 if d == "citations" else 0.0) for d in DIMS},
    "affiliation-only": {d: (1.0 if d == "affiliation" else 0.0) for d in DIMS},
}


def score(paper: dict, w: dict) -> float:
    c = paper.get("authority_components", {})
    return sum(w[d] * c.get(d, 0.0) for d in DIMS)


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for p in sorted(OPEN_DIR.glob("*.json")):
        if p.name.startswith("1n_pilot") or p.is_dir():
            continue
        data = json.load(open(p))
        if isinstance(data, list):
            rows.extend(data)
    for p in sorted(CLOSED_DIR.glob("closed_weight_*.json")):
        data = json.load(open(p))
        rows.extend(data.get("results", []))
    rows = [r for r in rows if r.get("model") in HEADLINE and r.get("model") not in ARCHIVED]
    return rows


def main():
    rows = load_rows()
    sets = json.load(open(SETS_FILE))
    sets_lookup = {(t, qs["query_id"]): qs for t, qss in sets.items() for qs in qss}
    lookup = {(r["model"], r["variant"], r["query_id"], r["condition"]): r for r in rows}

    print(f"headline rows: {len(rows)}  models: {sorted(set(r['model'] for r in rows))}\n")

    def tally(cond_b, w):
        higher = lower = total = 0
        for r in rows:
            if r["condition"] != "original":
                continue
            rb = lookup.get((r["model"], r["variant"], r["query_id"], cond_b))
            if not rb or r.get("recommended") is None or rb.get("recommended") is None:
                continue
            if r["recommended_paper_id"] == rb["recommended_paper_id"]:
                continue
            q = sets_lookup.get((r["topic"], r["query_id"]))
            if not q:
                continue
            ca = q["candidates"].get("original", [])
            cb = q["candidates"].get(cond_b, [])
            ia, ib = r["recommended"] - 1, rb["recommended"] - 1
            if not (0 <= ia < len(ca) and 0 <= ib < len(cb)):
                continue
            total += 1
            sa, sb = score(ca[ia], w), score(cb[ib], w)
            if sb > sa:
                higher += 1
            elif sb < sa:
                lower += 1
        return higher, lower, total

    hdr = (f"{'scheme':<17}"
           f"{'FLIP %tot':>10}{'FLIP %dec':>10}{'FLIP p':>10}"
           f"{'BOOST %tot':>11}{'BOOST %dec':>11}{'BOOST p':>10}")
    print(hdr); print("-" * len(hdr))
    for sname, w in SCHEMES.items():
        out = [sname.ljust(17)]
        for cond_b in ("flipped", "boosted"):
            h, l, t = tally(cond_b, w)
            dec = h + l
            p = scipy_stats.binomtest(h, dec, 0.5).pvalue if dec else float("nan")
            out.append(f"{h/t*100:>9.1f}%{h/dec*100:>9.1f}%{p:>10.1e}")
        print("".join(out))
    print("\n%tot = toward-higher / all flips ; %dec = toward-higher / (higher+lower), ties excluded")


if __name__ == "__main__":
    main()
