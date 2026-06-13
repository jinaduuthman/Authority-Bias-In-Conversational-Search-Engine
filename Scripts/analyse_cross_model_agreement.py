"""
Cross-model agreement analysis (paper Section 5).

Two analyses:
  (A) Selection agreement: how often do two models pick the same paper for the
      same (query, condition, variant) cell? Reported as a 5x5 matrix and as
      an aggregate.
  (B) Flip agreement: for each (query, variant) and each manipulation
      (original->flipped, original->boosted), did each model's recommendation
      change? We then compute, across queries, how often two models flip
      together (Cohen's kappa on the binary flip indicator).

The question we want to answer: is authority bias a SHARED phenomenon (high
inter-model agreement) or IDIOSYNCRATIC (low agreement)? High shared agreement
would point to a common training-data origin.
"""

import json
import itertools
from collections import defaultdict
from pathlib import Path

import numpy as np

RESULTS_FILE = Path(__file__).resolve().parent.parent / "data" / "results" / "results_20260330_180537.json"


def load_results():
    with open(RESULTS_FILE) as f:
        return json.load(f)


def _key(row, fields):
    return tuple(row[f] for f in fields)


def selection_agreement(rows):
    """For each (query_id, variant, condition) cell, list each model's pick.
    Then compute pairwise agreement between models.
    """
    cells = defaultdict(dict)  # cell_key -> {model: paper_id}
    for r in rows:
        if r.get("recommended_paper_id") is None:
            continue
        ck = _key(r, ["query_id", "variant", "condition"])
        cells[ck][r["model"]] = r["recommended_paper_id"]

    models = sorted({r["model"] for r in rows})
    agree_matrix = {a: {b: [0, 0] for b in models} for a in models}  # [match, total]

    for ck, picks in cells.items():
        for a, b in itertools.combinations_with_replacement(models, 2):
            if a in picks and b in picks:
                agree_matrix[a][b][1] += 1
                if picks[a] == picks[b]:
                    agree_matrix[a][b][0] += 1
                if a != b:
                    agree_matrix[b][a][1] += 1
                    if picks[a] == picks[b]:
                        agree_matrix[b][a][0] += 1
    return models, agree_matrix


def flip_agreement(rows):
    """For each (model, query_id, variant), pair the 'original' recommendation
    with the 'flipped' (and separately 'boosted') recommendation. Build a
    binary flip indicator per cell, then compute pairwise agreement / kappa.
    """
    by_cell = defaultdict(dict)  # (model, query_id, variant) -> {condition: paper_id}
    for r in rows:
        if r.get("recommended_paper_id") is None:
            continue
        k = (r["model"], r["query_id"], r["variant"])
        by_cell[k][r["condition"]] = r["recommended_paper_id"]

    flip_results = {"flipped": {}, "boosted": {}}  # manip -> {(query, variant): {model: 0/1}}
    for (model, query, variant), conds in by_cell.items():
        if "original" not in conds:
            continue
        for manip in ["flipped", "boosted"]:
            if manip in conds:
                flipped = int(conds["original"] != conds[manip])
                flip_results[manip].setdefault((query, variant), {})[model] = flipped

    models = sorted({r["model"] for r in rows})
    out = {}
    for manip, cells in flip_results.items():
        rate_matrix = {a: {b: None for b in models} for a in models}
        kappa_matrix = {a: {b: None for b in models} for a in models}
        for a, b in itertools.combinations(models, 2):
            xs, ys = [], []
            for cell_key, picks in cells.items():
                if a in picks and b in picks:
                    xs.append(picks[a])
                    ys.append(picks[b])
            if not xs:
                continue
            xs, ys = np.array(xs), np.array(ys)
            agree_rate = float(np.mean(xs == ys))
            # Cohen's kappa
            po = agree_rate
            p_a1 = xs.mean()
            p_b1 = ys.mean()
            pe = p_a1 * p_b1 + (1 - p_a1) * (1 - p_b1)
            kappa = (po - pe) / (1 - pe) if (1 - pe) > 1e-9 else 0.0
            rate_matrix[a][b] = round(agree_rate, 3)
            rate_matrix[b][a] = round(agree_rate, 3)
            kappa_matrix[a][b] = round(kappa, 3)
            kappa_matrix[b][a] = round(kappa, 3)
        out[manip] = {"rate": rate_matrix, "kappa": kappa_matrix, "n_cells": len(cells)}
    return models, out


def print_matrix(title, models, matrix, value_fn):
    print(f"\n{title}")
    header = "                       " + "  ".join(f"{m[:15]:>15}" for m in models)
    print(header)
    for a in models:
        row_vals = []
        for b in models:
            v = value_fn(matrix[a][b])
            row_vals.append(f"{v:>15}")
        print(f"{a[:21]:>21}  " + "  ".join(row_vals))


def main():
    rows = load_results()
    print(f"Loaded {len(rows)} rows.")

    models, agree = selection_agreement(rows)
    print("\n=== (A) SELECTION AGREEMENT ===")
    print("Fraction of cells where two models pick the SAME paper.")
    print_matrix(
        "Pairwise selection agreement (% identical pick across all cells):",
        models,
        agree,
        lambda cell: f"{(cell[0]/cell[1]*100):.1f}%" if cell[1] else "n/a",
    )
    # Aggregate (off-diagonal mean)
    off_diag = []
    for a in models:
        for b in models:
            if a != b and agree[a][b][1]:
                off_diag.append(agree[a][b][0] / agree[a][b][1])
    print(f"\nMean pairwise selection agreement (off-diagonal): {np.mean(off_diag)*100:.1f}%")
    print(f"Range: {min(off_diag)*100:.1f}% – {max(off_diag)*100:.1f}%")

    models2, flip = flip_agreement(rows)
    for manip in ["flipped", "boosted"]:
        print(f"\n=== (B) FLIP AGREEMENT — {manip.upper()} ===")
        print(f"n cells per pair (max): {flip[manip]['n_cells']}")
        print_matrix(
            f"Pairwise flip-agreement RATE (do both models flip together?):",
            models2,
            flip[manip]["rate"],
            lambda v: f"{v*100:.1f}%" if v is not None else "—",
        )
        print_matrix(
            f"Cohen's KAPPA on flip indicator (chance-corrected):",
            models2,
            flip[manip]["kappa"],
            lambda v: f"{v:.3f}" if v is not None else "—",
        )
        # Aggregate
        kappas = [flip[manip]["kappa"][a][b] for a, b in itertools.combinations(models2, 2)
                  if flip[manip]["kappa"][a][b] is not None]
        rates = [flip[manip]["rate"][a][b] for a, b in itertools.combinations(models2, 2)
                 if flip[manip]["rate"][a][b] is not None]
        print(f"\nMean pairwise flip-rate agreement: {np.mean(rates)*100:.1f}%")
        print(f"Mean pairwise Cohen's kappa: {np.mean(kappas):.3f}")
        print(f"Kappa range: {min(kappas):.3f} – {max(kappas):.3f}")


if __name__ == "__main__":
    main()
