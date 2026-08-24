"""
Cross-model agreement on the merged 8-model dataset.

Imports functions from analyse_cross_model_agreement.py without modifying it.
Loads from BOTH data/results/ (open-weight) AND
data/extension/closed_weight_results/ (closed-weight).

Outputs:
  data/extension/cross_model_agreement_merged.json (matrices + aggregates)
"""

from __future__ import annotations

import json
import sys
import itertools
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "Scripts"))

from analyse_cross_model_agreement import selection_agreement, flip_agreement  # noqa: E402

OPEN_DIR = PROJECT_ROOT / "data" / "results"
CLOSED_DIR = PROJECT_ROOT / "data" / "extension" / "closed_weight_results"
EXTENSION_DIR = PROJECT_ROOT / "data" / "extension"
OUTPUT = EXTENSION_DIR / "cross_model_agreement_merged.json"

HEADLINE_MODELS = {
    "gemma2:9b", "llama3.1:8b", "mistral:7b", "qwen2.5:7b", "deepseek-r1:8b",
    "gpt-5.4", "gemini-3-flash-preview", "claude-sonnet-4-6",
}
# gemini-2.5-flash data archived but not analyzed; same convention as analyse_merged.py
ARCHIVED_MODELS = {"gemini-2.5-flash"}


def load_all_rows() -> list[dict]:
    rows: list[dict] = []
    for p in sorted(OPEN_DIR.glob("*.json")):
        if p.name.startswith("1n_pilot") or p.is_dir():
            continue
        with p.open() as f:
            data = json.load(f)
        if isinstance(data, list):
            rows.extend(data)
    for p in sorted(CLOSED_DIR.glob("closed_weight_*.json")):
        with p.open() as f:
            for r in json.load(f).get("results", []):
                if r.get("model") in ARCHIVED_MODELS:
                    continue
                rows.append(r)
    return [r for r in rows if r["model"] in HEADLINE_MODELS]


def main() -> None:
    rows = load_all_rows()
    print(f"Rows: {len(rows)} across {len(set(r['model'] for r in rows))} models")

    models, agree = selection_agreement(rows)
    selection_pct = {a: {b: round(agree[a][b][0] / agree[a][b][1] * 100, 2)
                          if agree[a][b][1] else None
                          for b in models} for a in models}
    off_diag = [agree[a][b][0] / agree[a][b][1]
                for a in models for b in models
                if a != b and agree[a][b][1]]

    print(f"\nMean pairwise SELECTION agreement (off-diagonal): "
          f"{np.mean(off_diag) * 100:.1f}%  range: "
          f"{min(off_diag) * 100:.1f}% – {max(off_diag) * 100:.1f}%")

    models2, flip = flip_agreement(rows)
    flipped_kappas = [flip["flipped"]["kappa"][a][b]
                      for a, b in itertools.combinations(models2, 2)
                      if flip["flipped"]["kappa"][a][b] is not None]
    boosted_kappas = [flip["boosted"]["kappa"][a][b]
                      for a, b in itertools.combinations(models2, 2)
                      if flip["boosted"]["kappa"][a][b] is not None]
    print(f"\nMean Cohen's κ (flipped):  {np.mean(flipped_kappas):.3f}  "
          f"range {min(flipped_kappas):.3f} – {max(flipped_kappas):.3f}")
    print(f"Mean Cohen's κ (boosted):  {np.mean(boosted_kappas):.3f}  "
          f"range {min(boosted_kappas):.3f} – {max(boosted_kappas):.3f}")

    # Print NxN matrices to console
    def print_matrix(title, mat, fmt):
        print(f"\n{title}")
        hdr = " " * 22 + "  ".join(f"{m[:14]:>14}" for m in models)
        print(hdr)
        for a in models:
            cells = "  ".join(f"{fmt(mat[a][b]):>14}" for b in models)
            print(f"{a[:20]:>20}  {cells}")

    print_matrix(
        "Selection agreement (% same pick):",
        selection_pct,
        lambda v: f"{v:.1f}%" if v is not None else "—",
    )
    print_matrix(
        "Flip-agreement κ (Original → Flipped):",
        flip["flipped"]["kappa"],
        lambda v: f"{v:.2f}" if v is not None else "—",
    )

    payload = {
        "n_models": len(models),
        "models": models,
        "n_rows": len(rows),
        "selection_agreement_pct": selection_pct,
        "selection_off_diag_mean": round(float(np.mean(off_diag) * 100), 2),
        "selection_off_diag_min": round(float(min(off_diag) * 100), 2),
        "selection_off_diag_max": round(float(max(off_diag) * 100), 2),
        "flipped_kappa_matrix": flip["flipped"]["kappa"],
        "flipped_rate_matrix": flip["flipped"]["rate"],
        "flipped_n_cells": flip["flipped"]["n_cells"],
        "flipped_kappa_mean": round(float(np.mean(flipped_kappas)), 3),
        "flipped_kappa_min": round(float(min(flipped_kappas)), 3),
        "flipped_kappa_max": round(float(max(flipped_kappas)), 3),
        "boosted_kappa_matrix": flip["boosted"]["kappa"],
        "boosted_rate_matrix": flip["boosted"]["rate"],
        "boosted_n_cells": flip["boosted"]["n_cells"],
        "boosted_kappa_mean": round(float(np.mean(boosted_kappas)), 3),
        "boosted_kappa_min": round(float(min(boosted_kappas)), 3),
        "boosted_kappa_max": round(float(max(boosted_kappas)), 3),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2))
    print(f"\nWrote {OUTPUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
