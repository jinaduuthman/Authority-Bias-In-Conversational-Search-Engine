"""
Re-fit the 1:N pilot regression with a 6th predictor (author_score) added
alongside the original 5 predictors.

This is part of an isolated extension (see Scripts/extension_author_score/README.md).
It does NOT modify any existing analysis script or output. All inputs are
read-only; all outputs go to data/extension/.

Inputs (read-only):
  data/results/1n_pilot/1n_pilot_*.json   pilot result rows
  data/1n_analysis_report.json             original 5-component report (for comparison)

Outputs:
  data/extension/pilot_regression_with_author_score.json   full 6-component report
  data/extension/pilot_regression_comparison.md            5-component vs 6-component
                                                           markdown comparison + verdict

Decision-gate thresholds (auto-applied at end of script):

  RERUN_REQUIRED  if McFadden R2 increases by >= 0.01 AND author_score |std-coef|
                  is at least the median of the existing 5 predictors AND VIF for
                  author_score is < 5 (i.e. estimable as a separate effect).
  ADD_AS_ABLATION if McFadden R2 increases by 0.002-0.01 OR author_score has a
                  nonzero coefficient with VIF < 5.
  KEEP_5_COMPONENT otherwise (author_score is redundant or unestimable).

Tier mapping is identical to add_author_score.py (max h-index -> [1.00, 0.85, 0.65,
0.45, 0.15]).
"""

from __future__ import annotations

import glob
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "data" / "results" / "1n_pilot"
BASELINE_REPORT = PROJECT_ROOT / "data" / "1n_analysis_report.json"
EXTENSION_DIR = PROJECT_ROOT / "data" / "extension"
OUTPUT_JSON = EXTENSION_DIR / "pilot_regression_with_author_score.json"
OUTPUT_MD = EXTENSION_DIR / "pilot_regression_comparison.md"

PREDICTOR_KEYS_5 = ["max_h", "median_h", "citations", "venue_score", "affiliation_score"]
PREDICTOR_KEYS_6 = PREDICTOR_KEYS_5 + ["author_score"]


# ---------------------------------------------------------------------------
# Helpers (mirrors of analyse_1n_results.py; copied to keep this fully isolated)
# ---------------------------------------------------------------------------


def h_to_author_score(max_h: int | float | None) -> float:
    if max_h is None:
        return 0.15
    mh = int(max_h)
    if mh >= 70:
        return 1.00
    if mh >= 40:
        return 0.85
    if mh >= 20:
        return 0.65
    if mh >= 5:
        return 0.45
    return 0.15


def load_results() -> list[dict]:
    files = sorted(glob.glob(str(RESULTS_DIR / "1n_pilot_*.json")))
    if not files:
        raise SystemExit(f"No 1n_pilot_*.json files in {RESULTS_DIR}")
    out = []
    for f in files:
        with open(f) as fh:
            out.extend(json.load(fh).get("results", []))
        print(f"Loaded {Path(f).name}")
    print(f"Total rows: {len(out)}")
    return out


def prepare_regression_data(results: list[dict], predictor_keys: list[str]):
    X, y = [], []
    skipped = 0
    for r in results:
        if not r.get("parse_success"):
            skipped += 1
            continue
        meta = dict(r.get("fixed_paper_wearing_meta") or {})
        meta["author_score"] = h_to_author_score(meta.get("max_h"))
        features = [meta.get(k) for k in predictor_keys]
        if any(v is None for v in features):
            skipped += 1
            continue
        X.append(features)
        y.append(1 if r.get("recommended_fixed_paper") else 0)
    print(f"Regression rows: {len(X)} kept, {skipped} skipped")
    return np.array(X, dtype=float), np.array(y, dtype=float)


def standardize(X: np.ndarray):
    means = X.mean(axis=0)
    stds = X.std(axis=0)
    stds[stds == 0] = 1
    return (X - means) / stds, means, stds


def logistic_regression_manual(X: np.ndarray, y: np.ndarray, lr=0.01, max_iter=5000, tol=1e-6):
    n, p = X.shape
    X_aug = np.column_stack([X, np.ones(n)])
    w = np.zeros(p + 1)
    for _ in range(max_iter):
        z = np.clip(X_aug @ w, -500, 500)
        pred = 1.0 / (1.0 + np.exp(-z))
        grad = X_aug.T @ (pred - y) / n
        w -= lr * grad
        if np.max(np.abs(grad)) < tol:
            break
    return w


def compute_vif(X: np.ndarray) -> list[float]:
    n, p = X.shape
    vifs = []
    for j in range(p):
        y_j = X[:, j]
        X_others = np.delete(X, j, axis=1)
        X_aug = np.column_stack([X_others, np.ones(n)])
        beta = np.linalg.lstsq(X_aug, y_j, rcond=None)[0]
        y_pred = X_aug @ beta
        ss_res = np.sum((y_j - y_pred) ** 2)
        ss_tot = np.sum((y_j - y_j.mean()) ** 2)
        r2 = 1.0 - ss_res / max(ss_tot, 1e-10)
        vifs.append(round(1.0 / max(1.0 - r2, 1e-10), 3))
    return vifs


def log_likelihood(X: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    n = X.shape[0]
    X_aug = np.column_stack([X, np.ones(n)])
    z = np.clip(X_aug @ w, -500, 500)
    pred = np.clip(1.0 / (1.0 + np.exp(-z)), 1e-10, 1 - 1e-10)
    return float(np.sum(y * np.log(pred) + (1 - y) * np.log(1 - pred)))


def mcfadden_r2(X: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    ll_model = log_likelihood(X, y, w)
    p_null = float(y.mean())
    ll_null = float(np.sum(y * np.log(max(p_null, 1e-10)) + (1 - y) * np.log(max(1 - p_null, 1e-10))))
    return 1.0 - ll_model / ll_null if ll_null != 0 else 0.0


def dominance_analysis(X_std: np.ndarray, y: np.ndarray, predictor_keys: list[str]):
    p = X_std.shape[1]
    indices = list(range(p))
    contribs = defaultdict(list)
    for size in range(p):
        for subset in combinations(indices, size):
            subset_set = set(subset)
            if size == 0:
                r2_without = 0.0
            else:
                X_sub = X_std[:, list(subset)]
                w_sub = logistic_regression_manual(X_sub, y)
                r2_without = mcfadden_r2(X_sub, y, w_sub)
            for j in indices:
                if j in subset_set:
                    continue
                new_subset = list(subset) + [j]
                X_sub = X_std[:, new_subset]
                w_sub = logistic_regression_manual(X_sub, y)
                r2_with = mcfadden_r2(X_sub, y, w_sub)
                contribs[j].append(r2_with - r2_without)
    return {predictor_keys[j]: round(float(np.mean(contribs[j])), 6) for j in indices}


def derive_weights(coefficients: dict[str, float]) -> dict[str, float]:
    abs_vals = {k: abs(v) for k, v in coefficients.items()}
    total = sum(abs_vals.values())
    if total == 0:
        n = len(abs_vals)
        return {k: round(1.0 / n, 4) for k in abs_vals}
    return {k: round(v / total, 4) for k, v in abs_vals.items()}


# ---------------------------------------------------------------------------
# Decision gate
# ---------------------------------------------------------------------------


def decide_verdict(
    r2_5: float,
    r2_6: float,
    coefs_6: dict[str, float],
    vifs_6: dict[str, float],
) -> tuple[str, str]:
    delta_r2 = r2_6 - r2_5
    coef_author = abs(coefs_6.get("author_score", 0.0))
    vif_author = vifs_6.get("author_score", float("inf"))
    vif_max_h = vifs_6.get("max_h", float("inf"))

    other_coefs = [abs(v) for k, v in coefs_6.items() if k != "author_score"]
    median_other = float(np.median(other_coefs)) if other_coefs else 0.0

    if vif_author >= 5 or vif_max_h >= 5:
        if delta_r2 < 0.002:
            return (
                "KEEP_5_COMPONENT",
                f"VIF on max_h ({vif_max_h:.2f}) or author_score ({vif_author:.2f}) "
                f">= 5 and ΔR² ({delta_r2:+.4f}) is below the 0.002 noise floor. "
                "author_score does not add identifiable signal beyond the existing 5 "
                "predictors. Treat as ablation in Appendix D; do not re-run the main "
                "experiment.",
            )
        return (
            "ADD_AS_ABLATION",
            f"VIF is high (max_h={vif_max_h:.2f}, author_score={vif_author:.2f}) but "
            f"ΔR² ({delta_r2:+.4f}) is not negligible. The 5-component score is still "
            "the cleaner specification; report the 6-component fit as a robustness "
            "check in Appendix D and keep the main experiment as-is.",
        )

    if delta_r2 >= 0.01 and coef_author >= median_other:
        return (
            "RERUN_REQUIRED",
            f"ΔR² ({delta_r2:+.4f}) is ≥ 0.01 and |β(author_score)| ({coef_author:.4f}) "
            f"is at least the median of the other 5 predictors ({median_other:.4f}), "
            f"with VIF estimable (max_h={vif_max_h:.2f}, author_score={vif_author:.2f}). "
            "The 5-component score is methodologically incomplete; Phase 4 (full "
            "re-run with the 6-component score) is recommended for publication.",
        )

    if delta_r2 >= 0.002 or coef_author > 0.001:
        return (
            "ADD_AS_ABLATION",
            f"ΔR² ({delta_r2:+.4f}) and |β(author_score)| ({coef_author:.4f}) indicate "
            "modest additional signal but not enough to invalidate the 5-component "
            "score. Report the 6-component fit as Appendix D ablation; no re-run needed.",
        )

    return (
        "KEEP_5_COMPONENT",
        f"ΔR² ({delta_r2:+.4f}) and |β(author_score)| ({coef_author:.4f}) are both "
        "negligible. author_score adds nothing the 5-component score does not already "
        "capture. Report briefly as ablation if space allows; no re-run needed.",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    EXTENSION_DIR.mkdir(parents=True, exist_ok=True)

    results = load_results()
    X, y = prepare_regression_data(results, PREDICTOR_KEYS_6)
    if len(X) == 0:
        raise SystemExit("No valid rows for regression.")

    X_std, means, stds = standardize(X)

    print("\n--- Logistic regression (6 predictors) ---")
    w = logistic_regression_manual(X_std, y)
    coefs = {PREDICTOR_KEYS_6[i]: round(float(w[i]), 6) for i in range(len(PREDICTOR_KEYS_6))}
    intercept = round(float(w[-1]), 6)
    r2_6 = mcfadden_r2(X_std, y, w)
    print(f"  intercept: {intercept}")
    for k, v in coefs.items():
        print(f"  {k:<18} {v:+.4f}")
    print(f"  McFadden R²: {r2_6:.4f}")

    print("\n--- VIF ---")
    vifs_list = compute_vif(X_std)
    vifs = {PREDICTOR_KEYS_6[i]: vifs_list[i] for i in range(len(PREDICTOR_KEYS_6))}
    for k, v in vifs.items():
        flag = "  ⚠ HIGH" if v > 5 else ""
        print(f"  {k:<18} {v:.2f}{flag}")

    print("\n--- Dominance analysis (slow, this enumerates subset models) ---")
    dom = dominance_analysis(X_std, y, PREDICTOR_KEYS_6)
    for k, v in dom.items():
        print(f"  {k:<18} {v:+.6f}")

    weights_std = derive_weights(coefs)
    weights_dom = derive_weights({k: float(v) for k, v in dom.items()})
    weights_recommended = {
        k: round((weights_std[k] + weights_dom[k]) / 2, 4) for k in PREDICTOR_KEYS_6
    }

    # Load original 5-component baseline for comparison
    with BASELINE_REPORT.open() as f:
        baseline = json.load(f)
    coefs_5 = baseline["logistic_regression"]["standardized_coefficients"]
    vifs_5 = baseline["vif"]
    dom_5 = baseline["dominance_analysis"]
    r2_5 = baseline["logistic_regression"]["mcfadden_r2"]
    weights_5 = baseline["derived_weights"]["recommended"]

    verdict, reasoning = decide_verdict(r2_5, r2_6, coefs, vifs)

    payload = {
        "predictor_keys": PREDICTOR_KEYS_6,
        "n_rows": int(len(y)),
        "positive_rate": round(float(y.mean()), 4),
        "logistic_regression": {
            "standardized_coefficients": coefs,
            "intercept": intercept,
            "mcfadden_r2": round(r2_6, 6),
            "feature_means": {PREDICTOR_KEYS_6[i]: round(float(means[i]), 4) for i in range(len(PREDICTOR_KEYS_6))},
            "feature_stds": {PREDICTOR_KEYS_6[i]: round(float(stds[i]), 4) for i in range(len(PREDICTOR_KEYS_6))},
        },
        "vif": vifs,
        "dominance_analysis": dom,
        "derived_weights": {
            "from_standardized_coefficients": weights_std,
            "from_dominance_analysis": weights_dom,
            "recommended": weights_recommended,
        },
        "comparison_to_5_component": {
            "delta_mcfadden_r2": round(r2_6 - r2_5, 6),
            "baseline_mcfadden_r2": r2_5,
            "baseline_coefficients": coefs_5,
            "baseline_vif": vifs_5,
            "baseline_dominance": dom_5,
            "baseline_weights": weights_5,
        },
        "verdict": verdict,
        "verdict_reasoning": reasoning,
        "tier_mapping": {"A* (>=70)": 1.00, "A (40-69)": 0.85, "B (20-39)": 0.65,
                         "C (5-19)": 0.45, "D (0-4)": 0.15},
    }

    with OUTPUT_JSON.open("w") as f:
        json.dump(payload, f, indent=2)

    write_comparison_md(payload)

    print()
    print("=" * 60)
    print(f"Verdict: {verdict}")
    print("=" * 60)
    print(reasoning)
    print()
    print(f"Wrote: {OUTPUT_JSON.relative_to(PROJECT_ROOT)}")
    print(f"Wrote: {OUTPUT_MD.relative_to(PROJECT_ROOT)}")


def write_comparison_md(payload: dict) -> None:
    coefs_6 = payload["logistic_regression"]["standardized_coefficients"]
    vifs_6 = payload["vif"]
    dom_6 = payload["dominance_analysis"]
    w_6 = payload["derived_weights"]["recommended"]
    r2_6 = payload["logistic_regression"]["mcfadden_r2"]

    cmp = payload["comparison_to_5_component"]
    coefs_5 = cmp["baseline_coefficients"]
    vifs_5 = cmp["baseline_vif"]
    dom_5 = cmp["baseline_dominance"]
    w_5 = cmp["baseline_weights"]
    r2_5 = cmp["baseline_mcfadden_r2"]

    def fmt(x: float, sign: bool = False) -> str:
        if sign:
            return f"{x:+.4f}"
        return f"{x:.4f}"

    lines: list[str] = []
    lines.append("# Pilot Regression: 5-Component vs 6-Component\n")
    lines.append(
        "Side-by-side comparison of the original 5-predictor authority-score regression "
        "(`data/1n_analysis_report.json`) and the extended 6-predictor regression that "
        "adds `author_score` (categorical tier of max h-index, see "
        "`Scripts/extension_author_score/README.md`).\n"
    )
    lines.append(f"- Rows used: **{payload['n_rows']}**  ")
    lines.append(f"- Positive rate (recommended_fixed_paper = 1): **{payload['positive_rate']:.4f}**\n")

    lines.append("## Standardized coefficients\n")
    lines.append("| Predictor | 5-component | 6-component | Δ |")
    lines.append("|-----------|-------------|-------------|---|")
    for k in PREDICTOR_KEYS_5:
        v5 = coefs_5[k]
        v6 = coefs_6[k]
        lines.append(f"| {k} | {fmt(v5, True)} | {fmt(v6, True)} | {fmt(v6 - v5, True)} |")
    lines.append(f"| author_score | — | {fmt(coefs_6['author_score'], True)} | new |")
    lines.append("")

    lines.append("## VIF (multicollinearity)\n")
    lines.append("| Predictor | 5-component | 6-component | Δ |")
    lines.append("|-----------|-------------|-------------|---|")
    for k in PREDICTOR_KEYS_5:
        v5 = vifs_5[k]
        v6 = vifs_6[k]
        flag = "  ⚠" if v6 > 5 else ""
        lines.append(f"| {k} | {fmt(v5)} | {fmt(v6)}{flag} | {fmt(v6 - v5, True)} |")
    flag = "  ⚠" if vifs_6["author_score"] > 5 else ""
    lines.append(f"| author_score | — | {fmt(vifs_6['author_score'])}{flag} | new |")
    lines.append("")
    lines.append(
        "VIF > 5 conventionally flags problematic multicollinearity (O'Brien, 2007). "
        "Because `author_score` is a step function of `max_h`, both are expected to "
        "share variance; the question is whether they remain separately identifiable.\n"
    )

    lines.append("## Dominance R² (independent contribution)\n")
    lines.append("| Predictor | 5-component | 6-component | Δ |")
    lines.append("|-----------|-------------|-------------|---|")
    for k in PREDICTOR_KEYS_5:
        v5 = dom_5[k]
        v6 = dom_6[k]
        lines.append(f"| {k} | {v5:+.6f} | {v6:+.6f} | {(v6 - v5):+.6f} |")
    lines.append(f"| author_score | — | {dom_6['author_score']:+.6f} | new |")
    lines.append("")

    lines.append("## Recommended weights (mean of standardized + dominance)\n")
    lines.append("| Predictor | 5-component | 6-component | Δ |")
    lines.append("|-----------|-------------|-------------|---|")
    for k in PREDICTOR_KEYS_5:
        v5 = w_5[k]
        v6 = w_6[k]
        lines.append(f"| {k} | {fmt(v5)} | {fmt(v6)} | {fmt(v6 - v5, True)} |")
    lines.append(f"| author_score | — | {fmt(w_6['author_score'])} | new |")
    lines.append("")

    lines.append("## Model fit\n")
    lines.append("| Metric | 5-component | 6-component | Δ |")
    lines.append("|--------|-------------|-------------|---|")
    lines.append(f"| McFadden R² | {fmt(r2_5)} | {fmt(r2_6)} | {fmt(r2_6 - r2_5, True)} |")
    lines.append("")

    lines.append("## Verdict\n")
    lines.append(f"**{payload['verdict']}**\n")
    lines.append(payload["verdict_reasoning"] + "\n")

    lines.append("## Tier mapping for `author_score`\n")
    lines.append("| Tier | max h-index | author_score |")
    lines.append("|------|-------------|--------------|")
    lines.append("| A*   | ≥ 70        | 1.00 |")
    lines.append("| A    | 40 – 69     | 0.85 |")
    lines.append("| B    | 20 – 39     | 0.65 |")
    lines.append("| C    | 5 – 19      | 0.45 |")
    lines.append("| D    | 0 – 4       | 0.15 |")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
