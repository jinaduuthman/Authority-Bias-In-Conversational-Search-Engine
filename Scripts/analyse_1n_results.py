"""
Analyse 1:N Flip Pilot Experiment results.

Derives empirical authority score weights via:
1. Logistic regression — P(recommended) ~ metadata components
2. Standardized coefficients → relative importance weights
3. Dominance analysis — robustness check for multicollinearity
4. VIF — variance inflation factor diagnostics

References:
  - Menard (2004): Standardized logistic regression coefficients
  - Tonidandel & LeBreton (2011): Relative importance analysis
  - Budescu (1993), Azen & Budescu (2003): Dominance analysis
  - Bertrand & Mullainathan (2004): Audit study methodology

Reads:  data/results/1n_pilot_*.json
Writes: data/1n_analysis_report.json
"""

import json
import os
import glob
import numpy as np
from collections import defaultdict
from itertools import combinations

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "data", "results", "1n_pilot")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "1n_analysis_report.json")

PREDICTOR_KEYS = ["max_h", "median_h", "citations", "venue_score", "affiliation_score"]


def load_results():
    """Load all 1:N pilot result files."""
    pattern = os.path.join(RESULTS_DIR, "1n_pilot_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print("ERROR: No 1n_pilot_*.json files found in data/results/")
        return []

    all_results = []
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        print(f"Loaded {f}: {len(data.get('results', []))} results")
        all_results.extend(data.get("results", []))

    print(f"Total results: {len(all_results)}")
    return all_results


def prepare_regression_data(results):
    """
    Build feature matrix X and target vector y for logistic regression.

    X: metadata components of the fixed paper (what it's "wearing")
    y: 1 if fixed paper was recommended, 0 otherwise
    """
    X = []
    y = []
    valid = 0
    skipped = 0

    for r in results:
        if not r.get("parse_success"):
            skipped += 1
            continue

        meta = r.get("fixed_paper_wearing_meta", {})
        features = [meta.get(k, 0) for k in PREDICTOR_KEYS]

        if any(v is None for v in features):
            skipped += 1
            continue

        X.append(features)
        y.append(1 if r.get("recommended_fixed_paper") else 0)
        valid += 1

    print(f"Regression data: {valid} valid, {skipped} skipped")
    print(f"Positive rate: {sum(y)}/{len(y)} ({100*sum(y)/max(len(y),1):.1f}%)")

    return np.array(X, dtype=float), np.array(y, dtype=float)


def standardize(X):
    """Z-score standardize each column."""
    means = X.mean(axis=0)
    stds = X.std(axis=0)
    stds[stds == 0] = 1
    return (X - means) / stds, means, stds


def logistic_regression_manual(X, y, lr=0.01, max_iter=5000, tol=1e-6):
    """
    Fit logistic regression via gradient descent.
    Returns coefficients (including intercept as last element).
    """
    n, p = X.shape
    X_aug = np.column_stack([X, np.ones(n)])
    w = np.zeros(p + 1)

    for iteration in range(max_iter):
        z = X_aug @ w
        z = np.clip(z, -500, 500)
        pred = 1 / (1 + np.exp(-z))
        gradient = X_aug.T @ (pred - y) / n
        w -= lr * gradient

        if np.max(np.abs(gradient)) < tol:
            break

    return w


def compute_vif(X):
    """Compute Variance Inflation Factor for each predictor."""
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
        r_squared = 1 - ss_res / max(ss_tot, 1e-10)
        vif = 1 / max(1 - r_squared, 1e-10)
        vifs.append(round(vif, 3))

    return vifs


def log_likelihood(X, y, w):
    """Compute log-likelihood for logistic regression."""
    n = X.shape[0]
    X_aug = np.column_stack([X, np.ones(n)])
    z = np.clip(X_aug @ w, -500, 500)
    pred = 1 / (1 + np.exp(-z))
    pred = np.clip(pred, 1e-10, 1 - 1e-10)
    return np.sum(y * np.log(pred) + (1 - y) * np.log(1 - pred))


def mcfadden_r2(X, y, w):
    """McFadden's pseudo R-squared."""
    ll_model = log_likelihood(X, y, w)
    p_null = y.mean()
    ll_null = np.sum(y * np.log(max(p_null, 1e-10)) + (1 - y) * np.log(max(1 - p_null, 1e-10)))
    return 1 - ll_model / ll_null if ll_null != 0 else 0


def dominance_analysis(X_std, y):
    """
    Dominance analysis: for each predictor, compute average marginal R² 
    contribution across all subset models (Budescu, 1993; Azen & Budescu, 2003).
    """
    p = X_std.shape[1]
    predictor_indices = list(range(p))
    marginal_contributions = defaultdict(list)

    null_w = logistic_regression_manual(
        np.zeros((X_std.shape[0], 0)).reshape(X_std.shape[0], 0),
        y, max_iter=1
    )

    for size in range(p):
        for subset in combinations(predictor_indices, size):
            subset_set = set(subset)

            if size == 0:
                r2_without = 0.0
            else:
                X_sub = X_std[:, list(subset)]
                w_sub = logistic_regression_manual(X_sub, y)
                r2_without = mcfadden_r2(X_sub, y, w_sub)

            for j in predictor_indices:
                if j in subset_set:
                    continue
                new_subset = list(subset) + [j]
                X_sub = X_std[:, new_subset]
                w_sub = logistic_regression_manual(X_sub, y)
                r2_with = mcfadden_r2(X_sub, y, w_sub)

                marginal_contributions[j].append(r2_with - r2_without)

    dominance_scores = {}
    for j in predictor_indices:
        contribs = marginal_contributions[j]
        dominance_scores[PREDICTOR_KEYS[j]] = round(np.mean(contribs), 6) if contribs else 0.0

    return dominance_scores


def derive_weights(coefficients, method="standardized_coef"):
    """Normalize absolute values of coefficients to sum to 1."""
    abs_vals = {k: abs(v) for k, v in coefficients.items()}
    total = sum(abs_vals.values())
    if total == 0:
        n = len(abs_vals)
        return {k: round(1.0 / n, 4) for k in abs_vals}
    return {k: round(v / total, 4) for k, v in abs_vals.items()}


def descriptive_stats(results):
    """Compute descriptive statistics on the 1:N experiment."""
    stats = {
        "total_runs": len(results),
        "parse_success": sum(1 for r in results if r.get("parse_success")),
        "baseline_runs": sum(1 for r in results if r.get("is_baseline")),
        "swap_runs": sum(1 for r in results if not r.get("is_baseline")),
        "fixed_recommended_total": sum(1 for r in results if r.get("recommended_fixed_paper")),
    }

    baseline_recs = sum(
        1 for r in results
        if r.get("is_baseline") and r.get("recommended_fixed_paper") and r.get("parse_success")
    )
    baseline_total = sum(1 for r in results if r.get("is_baseline") and r.get("parse_success"))

    swap_recs = sum(
        1 for r in results
        if not r.get("is_baseline") and r.get("recommended_fixed_paper") and r.get("parse_success")
    )
    swap_total = sum(1 for r in results if not r.get("is_baseline") and r.get("parse_success"))

    stats["baseline_rec_rate"] = round(baseline_recs / max(baseline_total, 1), 4)
    stats["swap_rec_rate"] = round(swap_recs / max(swap_total, 1), 4)
    stats["random_chance"] = 0.1

    by_topic = defaultdict(lambda: {"total": 0, "recommended": 0})
    for r in results:
        if r.get("parse_success"):
            t = r.get("topic", "unknown")
            by_topic[t]["total"] += 1
            if r.get("recommended_fixed_paper"):
                by_topic[t]["recommended"] += 1

    stats["by_topic"] = {
        t: {"total": v["total"], "recommended": v["recommended"],
            "rec_rate": round(v["recommended"] / max(v["total"], 1), 4)}
        for t, v in by_topic.items()
    }

    return stats


def main():
    print("=" * 60)
    print("1:N Flip Pilot — Analysis")
    print("=" * 60)

    results = load_results()
    if not results:
        return

    print("\n--- Descriptive Statistics ---")
    stats = descriptive_stats(results)
    for k, v in stats.items():
        if k != "by_topic":
            print(f"  {k}: {v}")
    print("  By topic:")
    for t, v in stats.get("by_topic", {}).items():
        print(f"    {t}: {v['recommended']}/{v['total']} ({v['rec_rate']:.1%})")

    print("\n--- Logistic Regression ---")
    X, y = prepare_regression_data(results)

    if len(X) == 0:
        print("ERROR: No valid data for regression.")
        return

    X_std, means, stds = standardize(X)

    w = logistic_regression_manual(X_std, y)
    coefs = {PREDICTOR_KEYS[i]: round(float(w[i]), 6) for i in range(len(PREDICTOR_KEYS))}
    intercept = round(float(w[-1]), 6)

    print(f"  Intercept: {intercept}")
    print(f"  Standardized coefficients:")
    for k, v in coefs.items():
        direction = "↑ MORE recs" if v > 0 else "↓ FEWER recs"
        print(f"    {k}: {v:+.4f} ({direction})")

    r2 = mcfadden_r2(X_std, y, w)
    print(f"  McFadden R²: {r2:.4f}")

    print("\n--- Variance Inflation Factors ---")
    vifs = compute_vif(X_std)
    vif_dict = {}
    for i, k in enumerate(PREDICTOR_KEYS):
        vif_dict[k] = vifs[i]
        flag = " ⚠ HIGH" if vifs[i] > 5 else ""
        print(f"  {k}: {vifs[i]:.2f}{flag}")

    print("\n--- Dominance Analysis ---")
    print("  (This may take a minute...)")
    dom_scores = dominance_analysis(X_std, y)
    print(f"  Average marginal R² contributions:")
    for k, v in sorted(dom_scores.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v:.6f}")

    print("\n--- Derived Weights ---")
    weights_from_coefs = derive_weights(coefs, "standardized_coef")
    weights_from_dominance = derive_weights(dom_scores, "dominance")

    print(f"  From standardized coefficients:")
    for k, v in sorted(weights_from_coefs.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v:.4f}")

    print(f"  From dominance analysis:")
    for k, v in sorted(weights_from_dominance.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v:.4f}")

    avg_weights = {}
    for k in PREDICTOR_KEYS:
        avg_weights[k] = round((weights_from_coefs[k] + weights_from_dominance[k]) / 2, 4)
    total_w = sum(avg_weights.values())
    avg_weights = {k: round(v / total_w, 4) for k, v in avg_weights.items()}

    print(f"\n  RECOMMENDED WEIGHTS (average of both methods):")
    for k, v in sorted(avg_weights.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v:.4f}")

    report = {
        "descriptive_stats": stats,
        "logistic_regression": {
            "standardized_coefficients": coefs,
            "intercept": intercept,
            "mcfadden_r2": round(r2, 6),
            "feature_means": {PREDICTOR_KEYS[i]: round(float(means[i]), 4) for i in range(len(PREDICTOR_KEYS))},
            "feature_stds": {PREDICTOR_KEYS[i]: round(float(stds[i]), 4) for i in range(len(PREDICTOR_KEYS))},
        },
        "vif": vif_dict,
        "dominance_analysis": dom_scores,
        "derived_weights": {
            "from_standardized_coefficients": weights_from_coefs,
            "from_dominance_analysis": weights_from_dominance,
            "recommended": avg_weights,
        },
        "justification": {
            "logistic_regression": "Standard model for binary outcomes (Hosmer & Lemeshow, 2000). "
                                   "Follows audit study methodology (Bertrand & Mullainathan, 2004) "
                                   "where the same content is presented with different metadata attributes.",
            "standardized_coefficients": "Puts all predictors on the same scale (SD units) for "
                                         "direct magnitude comparison (Menard, 2004).",
            "dominance_analysis": "Computes average marginal R² contribution across all subset models, "
                                  "robust to multicollinearity (Budescu, 1993; Azen & Budescu, 2003).",
            "weight_derivation": "Final weights are the average of standardized coefficient-based and "
                                 "dominance-based relative importance (Tonidandel & LeBreton, 2011), "
                                 "normalized to sum to 1.",
            "vif_threshold": "VIF > 5 indicates problematic multicollinearity. "
                             "If all VIF < 5, standardized coefficients are reliable.",
        },
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
