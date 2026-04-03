"""
Analyse authority bias experiment results.

Metrics:
  1. Recommendation Flip Rate (RQ1)
  1a. Flip Direction Analysis — do flips move toward higher authority?
  1b. Topic-Level Breakdown — which topics show most bias?
  2. Dose-Response Relationship (Sub-RQ1.1)
  2a. Expected vs Observed Boosted Rate
  3. Model Differences (Sub-RQ1.2)
  4. Instruction Effect (RQ3)
  4a. Model × Instruction Interaction Effects
  5. Justification Analysis (Qualitative)
  6. Statistical Significance Tests

Usage:
  python3 Scripts/analyse_results.py
"""

import json
import math
import os
import re
from collections import defaultdict
from scipy import stats as scipy_stats

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "data", "results")
SETS_FILE = os.path.join(BASE_DIR, "data", "experiment_sets.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "analysis_report.json")

EXCLUDE_MODELS = {"phi3:mini"}

AUTHORITY_PATTERNS = [
    (r'\bh[- ]?index\b', 'h-index'),
    (r'\bcitation(?:s| count)\b', 'citations'),
    (r'\bhighly cited\b', 'citations'),
    (r'\b(?:top|prestigious|leading|premier|renowned|elite)\s+(?:venue|conference|journal|institution|university|lab)\b', 'venue_prestige'),
    (r'\b(?:NeurIPS|ICML|ICLR|ACL|EMNLP|CVPR|AAAI|ECCV|KDD)\b', 'venue_name'),
    (r'\b(?:Stanford|MIT|Carnegie Mellon|Berkeley|Oxford|Harvard|Princeton|Google|DeepMind|OpenAI|Microsoft Research|Tsinghua|Peking)\b', 'institution_name'),
    (r'\b(?:famous|well[- ]known|prominent|established|senior|leading|expert|authority|influential)\b', 'author_prestige'),
    (r'\b(?:impact|impactful|significant impact|high impact)\b', 'impact'),
    (r'\b(?:credib(?:le|ility)|reputation|prestige)\b', 'credibility'),
    (r'\b(?:recent|latest|newest|up[- ]to[- ]date|cutting[- ]edge|state[- ]of[- ]the[- ]art|most\s+recent|recently\s+published|more\s+recent|newer)\b', 'recency'),
]


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def load_results():
    """Load and merge all main experiment result files, excluding specified models."""
    all_results = []
    for fname in sorted(os.listdir(RESULTS_DIR)):
        if not fname.endswith(".json") or fname.startswith("1n_pilot"):
            continue
        path = os.path.join(RESULTS_DIR, fname)
        if os.path.isdir(path):
            continue
        with open(path, "r") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print(f"  Skipping {fname}: not a results list")
            continue
        all_results.extend(data)
        print(f"  Loaded {fname}: {len(data)} entries")

    before = len(all_results)
    all_results = [r for r in all_results if r["model"] not in EXCLUDE_MODELS]
    excluded = before - len(all_results)
    if excluded:
        print(f"  Excluded {excluded} entries from models: {EXCLUDE_MODELS}")

    print(f"  Total entries for analysis: {len(all_results)}")
    return all_results


def load_experiment_sets():
    with open(SETS_FILE, "r") as f:
        return json.load(f)


def build_lookup(results):
    """Index results by (model, variant, query_id, condition)."""
    lookup = {}
    for r in results:
        key = (r["model"], r["variant"], r["query_id"], r["condition"])
        lookup[key] = r
    return lookup


def build_sets_lookup(experiment_sets):
    """Index experiment sets by (topic, query_id) for fast candidate lookup."""
    lookup = {}
    for topic, q_sets in experiment_sets.items():
        for qs in q_sets:
            lookup[(topic, qs["query_id"])] = qs
    return lookup


def paper_authority_score(paper):
    """Use the pre-computed composite authority score from generate_conditions.py."""
    components = paper.get("authority_components", {})
    if "composite" in components:
        return components["composite"]
    return 0.0


def confidence_interval_proportion(successes, total, confidence=0.95):
    """Wilson score interval for a proportion."""
    if total == 0:
        return (0, 0)
    p = successes / total
    z = scipy_stats.norm.ppf(1 - (1 - confidence) / 2)
    denom = 1 + z ** 2 / total
    centre = (p + z ** 2 / (2 * total)) / denom
    margin = z * math.sqrt((p * (1 - p) + z ** 2 / (4 * total)) / total) / denom
    return (round(max(0, centre - margin), 4), round(min(1, centre + margin), 4))


# ──────────────────────────────────────────────────────────────
# Metric 1: Recommendation Flip Rate
# ──────────────────────────────────────────────────────────────

def metric_1_flip_rate(results, lookup):
    """Compute how often the recommendation changes between conditions."""
    print("\n" + "=" * 70)
    print("METRIC 1: RECOMMENDATION FLIP RATE (RQ1)")
    print("=" * 70)

    comparisons = [
        ("original", "flipped", "Original → Flipped"),
        ("original", "boosted", "Original → Boosted"),
    ]

    models = sorted(set(r["model"] for r in results))
    summary = {}

    for cond_a, cond_b, label in comparisons:
        flipped_count = 0
        total_count = 0
        per_model = {m: {"flipped": 0, "total": 0} for m in models}

        for r in results:
            if r["condition"] != cond_a:
                continue
            key_b = (r["model"], r["variant"], r["query_id"], cond_b)
            r_b = lookup.get(key_b)
            if not r_b:
                continue
            if r.get("recommended") is None or r_b.get("recommended") is None:
                continue

            total_count += 1
            per_model[r["model"]]["total"] += 1
            if r["recommended_paper_id"] != r_b["recommended_paper_id"]:
                flipped_count += 1
                per_model[r["model"]]["flipped"] += 1

        flip_rate = flipped_count / total_count if total_count else 0
        consistency_rate = 1 - flip_rate
        ci = confidence_interval_proportion(flipped_count, total_count)

        model_breakdown = {}
        for m in models:
            mt, mf = per_model[m]["total"], per_model[m]["flipped"]
            mr = mf / mt if mt else 0
            mci = confidence_interval_proportion(mf, mt)
            model_breakdown[m] = {
                "total_pairs": mt, "flipped": mf,
                "flip_rate": round(mr, 4), "flip_rate_95ci": list(mci),
            }

        summary[label] = {
            "total_pairs": total_count,
            "flipped": flipped_count,
            "consistent": total_count - flipped_count,
            "flip_rate": round(flip_rate, 4),
            "consistency_rate": round(consistency_rate, 4),
            "flip_rate_95ci": list(ci),
            "per_model": model_breakdown,
        }

        print(f"\n  {label}:")
        print(f"    Total pairs:      {total_count}")
        print(f"    Flipped:          {flipped_count} ({flip_rate:.1%})")
        print(f"    Consistent:       {total_count - flipped_count} ({consistency_rate:.1%})")
        print(f"    95% CI:           [{ci[0]:.1%}, {ci[1]:.1%}]")
        print(f"\n    {'Model':<20s} {'Flip%':>7s} {'95% CI':>15s} {'n':>5s}")
        print(f"    {'-'*20} {'-'*7} {'-'*15} {'-'*5}")
        for m in models:
            s = model_breakdown[m]
            mci = f"[{s['flip_rate_95ci'][0]:.1%},{s['flip_rate_95ci'][1]:.1%}]"
            print(f"    {m:<20s} {s['flip_rate']:>6.1%} {mci:>15s} {s['total_pairs']:>5d}")

    return summary


# ──────────────────────────────────────────────────────────────
# Metric 1a: Flip Direction Analysis
# ──────────────────────────────────────────────────────────────

def metric_1a_flip_direction(results, lookup, sets_lookup):
    """When recommendations flip, do they move toward higher authority?"""
    print("\n" + "=" * 70)
    print("METRIC 1a: FLIP DIRECTION ANALYSIS")
    print("=" * 70)

    comparisons = [
        ("original", "flipped", "Original → Flipped"),
        ("original", "boosted", "Original → Boosted"),
    ]

    models = sorted(set(r["model"] for r in results))
    summary = {}

    for cond_a, cond_b, label in comparisons:
        toward_higher = 0
        toward_lower = 0
        same_authority = 0
        total_flips = 0
        per_model = {m: {"higher": 0, "lower": 0, "same": 0, "total": 0} for m in models}

        for r in results:
            if r["condition"] != cond_a:
                continue
            key_b = (r["model"], r["variant"], r["query_id"], cond_b)
            r_b = lookup.get(key_b)
            if not r_b:
                continue
            if r.get("recommended") is None or r_b.get("recommended") is None:
                continue
            if r["recommended_paper_id"] == r_b["recommended_paper_id"]:
                continue

            total_flips += 1
            per_model[r["model"]]["total"] += 1

            q_set = sets_lookup.get((r["topic"], r["query_id"]))
            if not q_set:
                continue

            cands_b = q_set["candidates"].get(cond_b, [])
            cands_a = q_set["candidates"].get(cond_a, [])

            rec_a_idx = r["recommended"] - 1
            rec_b_idx = r_b["recommended"] - 1

            if rec_a_idx < 0 or rec_a_idx >= len(cands_a):
                continue
            if rec_b_idx < 0 or rec_b_idx >= len(cands_b):
                continue

            score_a = paper_authority_score(cands_a[rec_a_idx])
            score_b = paper_authority_score(cands_b[rec_b_idx])

            if score_b > score_a:
                toward_higher += 1
                per_model[r["model"]]["higher"] += 1
            elif score_b < score_a:
                toward_lower += 1
                per_model[r["model"]]["lower"] += 1
            else:
                same_authority += 1
                per_model[r["model"]]["same"] += 1

        toward_higher_pct = toward_higher / total_flips if total_flips else 0
        toward_lower_pct = toward_lower / total_flips if total_flips else 0

        model_breakdown = {}
        for m in models:
            pm = per_model[m]
            t = pm["total"]
            h_pct = pm["higher"] / t if t else 0
            model_breakdown[m] = {
                "total_flips": t,
                "toward_higher": pm["higher"],
                "toward_lower": pm["lower"],
                "toward_higher_pct": round(h_pct, 4),
            }

        summary[label] = {
            "total_flips": total_flips,
            "toward_higher_authority": toward_higher,
            "toward_lower_authority": toward_lower,
            "same_authority": same_authority,
            "toward_higher_pct": round(toward_higher_pct, 4),
            "toward_lower_pct": round(toward_lower_pct, 4),
            "per_model": model_breakdown,
        }

        print(f"\n  {label} (n={total_flips} flips):")
        print(f"    → Higher authority: {toward_higher} ({toward_higher_pct:.1%})")
        print(f"    → Lower authority:  {toward_lower} ({toward_lower_pct:.1%})")
        print(f"    → Same level:       {same_authority}")

        if toward_higher + toward_lower > 0:
            btest = scipy_stats.binomtest(toward_higher, toward_higher + toward_lower, 0.5)
            p_val = float(btest.pvalue)
            summary[label]["direction_binomial_p"] = round(p_val, 6)
            sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "n.s."
            print(f"    Binomial test (H₀: 50/50): p={p_val:.4f} {sig}")

        print(f"\n    {'Model':<20s} {'Flips':>6s} {'→Higher':>8s} {'→Lower':>8s} {'Higher%':>8s}")
        print(f"    {'-'*20} {'-'*6} {'-'*8} {'-'*8} {'-'*8}")
        for m in models:
            mb = model_breakdown[m]
            print(f"    {m:<20s} {mb['total_flips']:>6d} {mb['toward_higher']:>8d} {mb['toward_lower']:>8d} {mb['toward_higher_pct']:>7.1%}")

    return summary


# ──────────────────────────────────────────────────────────────
# Metric 1b: Topic-Level Breakdown
# ──────────────────────────────────────────────────────────────

def metric_1b_topic_breakdown(results, lookup):
    """Flip rate broken down by research topic, with per-model detail."""
    print("\n" + "=" * 70)
    print("METRIC 1b: TOPIC-LEVEL FLIP RATE BREAKDOWN")
    print("=" * 70)

    topics = sorted(set(r["topic"] for r in results))
    models = sorted(set(r["model"] for r in results))
    topic_stats = {}

    for topic in topics:
        topic_results = [r for r in results if r["topic"] == topic and r["condition"] == "original"]
        flip_total, flip_changed = 0, 0
        boost_total, boost_changed = 0, 0
        per_model = {m: {"ft": 0, "fc": 0, "bt": 0, "bc": 0} for m in models}

        for r in topic_results:
            if r.get("recommended") is None:
                continue
            key_f = (r["model"], r["variant"], r["query_id"], "flipped")
            key_b = (r["model"], r["variant"], r["query_id"], "boosted")
            r_f = lookup.get(key_f)
            r_b = lookup.get(key_b)

            if r_f and r_f.get("recommended") is not None:
                flip_total += 1
                per_model[r["model"]]["ft"] += 1
                if r["recommended_paper_id"] != r_f["recommended_paper_id"]:
                    flip_changed += 1
                    per_model[r["model"]]["fc"] += 1
            if r_b and r_b.get("recommended") is not None:
                boost_total += 1
                per_model[r["model"]]["bt"] += 1
                if r["recommended_paper_id"] != r_b["recommended_paper_id"]:
                    boost_changed += 1
                    per_model[r["model"]]["bc"] += 1

        fr = flip_changed / flip_total if flip_total else 0
        br = boost_changed / boost_total if boost_total else 0

        model_breakdown = {}
        for m in models:
            pm = per_model[m]
            mfr = pm["fc"] / pm["ft"] if pm["ft"] else 0
            mbr = pm["bc"] / pm["bt"] if pm["bt"] else 0
            model_breakdown[m] = {
                "flip_rate": round(mfr, 4),
                "boost_rate": round(mbr, 4),
            }

        topic_stats[topic] = {
            "flip_rate": round(fr, 4),
            "boost_rate": round(br, 4),
            "flip_pairs": flip_total,
            "boost_pairs": boost_total,
            "per_model": model_breakdown,
        }

    # Aggregate table
    sorted_topics = sorted(topic_stats.items(), key=lambda x: x[1]["flip_rate"], reverse=True)
    print(f"\n  {'Topic':<35s} {'Flip%':>7s} {'Boost%':>7s} {'n':>5s}")
    print(f"  {'-'*35} {'-'*7} {'-'*7} {'-'*5}")
    for topic, s in sorted_topics:
        print(f"  {topic:<35s} {s['flip_rate']:>6.1%} {s['boost_rate']:>6.1%} {s['flip_pairs']:>5d}")

    rates = [s["flip_rate"] for s in topic_stats.values()]
    spread = max(rates) - min(rates) if rates else 0
    print(f"\n  Flip rate range: {min(rates):.1%} – {max(rates):.1%} (spread: {spread:.1%})")

    # Per-model topic table
    print(f"\n  Per-model flip rates by topic (top 5 & bottom 5 topics):")
    header = f"  {'Topic':<30s}"
    for m in models:
        short = m.split(":")[0][:10]
        header += f" {short:>10s}"
    print(header)
    print(f"  {'-'*30}" + f" {'-'*10}" * len(models))

    top5 = sorted_topics[:5]
    bot5 = sorted_topics[-5:]
    for topic, s in top5:
        row = f"  {topic[:30]:<30s}"
        for m in models:
            row += f" {s['per_model'][m]['flip_rate']:>9.1%}"
        print(row)
    print(f"  {'...':<30s}")
    for topic, s in bot5:
        row = f"  {topic[:30]:<30s}"
        for m in models:
            row += f" {s['per_model'][m]['flip_rate']:>9.1%}"
        print(row)

    return topic_stats


# ──────────────────────────────────────────────────────────────
# Metric 2: Dose-Response Relationship
# ──────────────────────────────────────────────────────────────

def metric_2_dose_response(results, experiment_sets, sets_lookup):
    """Analyse whether LLMs shift toward papers with higher authority signals."""
    print("\n" + "=" * 70)
    print("METRIC 2: DOSE-RESPONSE RELATIONSHIP (Sub-RQ1.1)")
    print("=" * 70)

    models = sorted(set(r["model"] for r in results))
    tier_picks = defaultdict(lambda: defaultdict(int))
    tier_picks_model = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    boosted_pick_count = 0
    boosted_available_count = 0
    total_boosted_in_sets = 0
    total_candidates_in_sets = 0
    authority_scores_picked = defaultdict(list)
    model_boosted = {m: {"picked": 0, "available": 0} for m in models}

    for r in results:
        if r.get("recommended") is None:
            continue

        topic = r["topic"]
        query_id = r["query_id"]
        condition = r["condition"]
        model = r["model"]

        q_set = sets_lookup.get((topic, query_id))
        if not q_set:
            continue

        candidates = q_set["candidates"].get(condition, [])
        rec_idx = r["recommended"] - 1
        if rec_idx < 0 or rec_idx >= len(candidates):
            continue

        picked = candidates[rec_idx]
        tier_picks[condition][picked.get("tier", "unknown")] += 1
        tier_picks_model[condition][model][picked.get("tier", "unknown")] += 1

        if condition == "boosted":
            n_boosted_available = sum(1 for c in candidates if c.get("boosted"))
            total_boosted_in_sets += n_boosted_available
            total_candidates_in_sets += len(candidates)
            if n_boosted_available > 0:
                boosted_available_count += 1
                model_boosted[model]["available"] += 1
                if picked.get("boosted"):
                    boosted_pick_count += 1
                    model_boosted[model]["picked"] += 1

        author_h = [a.get("h_index") or 0 for a in picked.get("authors", [])]
        max_h = max(author_h) if author_h else 0
        authority_scores_picked[condition].append({
            "max_h_index": max_h,
            "citation_count": picked.get("citation_count", 0) or 0,
            "model": model,
        })

    print("\n  Tier distribution of recommended papers by condition:")
    for condition in ["original", "flipped", "boosted"]:
        tiers = tier_picks.get(condition, {})
        total = sum(tiers.values())
        print(f"\n    {condition.upper()} (n={total}):")
        for tier in ["top", "mid", "low", "emerging", "fill", "unknown"]:
            count = tiers.get(tier, 0)
            if count > 0:
                print(f"      {tier:10s}: {count:4d} ({count/total:.1%})")

    # Per-model tier preference for original condition
    print(f"\n  Per-model tier preference (ORIGINAL condition — % picking top-tier):")
    print(f"  {'Model':<20s} {'Top%':>7s} {'Mid%':>7s} {'Low%':>7s} {'Emerging%':>10s}")
    print(f"  {'-'*20} {'-'*7} {'-'*7} {'-'*7} {'-'*10}")
    model_tier_report = {}
    for m in models:
        mt = tier_picks_model.get("original", {}).get(m, {})
        total_m = sum(mt.values())
        if total_m == 0:
            continue
        top_pct = mt.get("top", 0) / total_m
        mid_pct = mt.get("mid", 0) / total_m
        low_pct = mt.get("low", 0) / total_m
        emg_pct = mt.get("emerging", 0) / total_m
        print(f"  {m:<20s} {top_pct:>6.1%} {mid_pct:>6.1%} {low_pct:>6.1%} {emg_pct:>9.1%}")
        model_tier_report[m] = {
            "top": round(top_pct, 4), "mid": round(mid_pct, 4),
            "low": round(low_pct, 4), "emerging": round(emg_pct, 4),
        }

    boost_pick_rate = boosted_pick_count / boosted_available_count if boosted_available_count else 0
    expected_rate = total_boosted_in_sets / total_candidates_in_sets if total_candidates_in_sets else 0
    lift = boost_pick_rate / expected_rate if expected_rate else 0

    print(f"\n  Boosted paper selection rate:")
    print(f"    When boosted papers available:   {boosted_available_count} queries")
    print(f"    Picked a boosted paper:          {boosted_pick_count} ({boost_pick_rate:.1%})")
    print(f"    Expected by random chance:       {expected_rate:.1%} (avg proportion of boosted in candidate sets)")
    print(f"    Lift over random:                {lift:.2f}x")

    if boosted_available_count > 0:
        binom_result = scipy_stats.binomtest(boosted_pick_count, boosted_available_count, expected_rate, alternative='greater')
        sig = "***" if binom_result.pvalue < 0.001 else "**" if binom_result.pvalue < 0.01 else "*" if binom_result.pvalue < 0.05 else "n.s."
        print(f"    Binomial test (H₀: random):      p={binom_result.pvalue:.6f} {sig}")

    # Per-model boosted pick rate
    print(f"\n    Per-model boosted pick rate:")
    print(f"    {'Model':<20s} {'Picked':>7s} {'Avail':>6s} {'Rate':>7s} {'Lift':>6s}")
    print(f"    {'-'*20} {'-'*7} {'-'*6} {'-'*7} {'-'*6}")
    model_boost_report = {}
    for m in models:
        mb = model_boosted[m]
        mr = mb["picked"] / mb["available"] if mb["available"] else 0
        ml = mr / expected_rate if expected_rate else 0
        print(f"    {m:<20s} {mb['picked']:>7d} {mb['available']:>6d} {mr:>6.1%} {ml:>5.2f}x")
        model_boost_report[m] = {
            "picked": mb["picked"], "available": mb["available"],
            "rate": round(mr, 4), "lift": round(ml, 4),
        }

    print(f"\n  Average authority of recommended papers by condition:")
    summary_scores = {}
    for condition in ["original", "flipped", "boosted"]:
        scores = authority_scores_picked.get(condition, [])
        if scores:
            h_vals = sorted(s["max_h_index"] for s in scores)
            cite_vals = sorted(s["citation_count"] for s in scores)
            avg_h = sum(h_vals) / len(h_vals)
            avg_cite = sum(cite_vals) / len(cite_vals)
            median_h = h_vals[len(h_vals) // 2]
            median_cite = cite_vals[len(cite_vals) // 2]
            print(f"    {condition.upper():10s}: avg_max_h={avg_h:.1f}  median_max_h={median_h}  avg_cite={avg_cite:.0f}  median_cite={median_cite}")
            summary_scores[condition] = {
                "avg_max_h_index": round(avg_h, 2),
                "median_max_h_index": median_h,
                "avg_citation_count": round(avg_cite, 1),
                "median_citation_count": median_cite,
                "n": len(scores),
            }

    # Per-model authority of picked papers (original condition)
    print(f"\n  Per-model avg authority of picked papers (ORIGINAL condition):")
    print(f"  {'Model':<20s} {'Avg Max h':>10s} {'Avg Cites':>10s}")
    print(f"  {'-'*20} {'-'*10} {'-'*10}")
    model_auth_report = {}
    for m in models:
        m_scores = [s for s in authority_scores_picked.get("original", []) if s["model"] == m]
        if m_scores:
            avg_h = sum(s["max_h_index"] for s in m_scores) / len(m_scores)
            avg_c = sum(s["citation_count"] for s in m_scores) / len(m_scores)
            print(f"  {m:<20s} {avg_h:>9.1f} {avg_c:>9.0f}")
            model_auth_report[m] = {"avg_max_h": round(avg_h, 2), "avg_cites": round(avg_c, 1)}

    if "original" in authority_scores_picked and "boosted" in authority_scores_picked:
        orig_h = [s["max_h_index"] for s in authority_scores_picked["original"]]
        boost_h = [s["max_h_index"] for s in authority_scores_picked["boosted"]]
        t_stat, p_val = scipy_stats.mannwhitneyu(boost_h, orig_h, alternative='greater')
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "n.s."
        print(f"\n    Mann-Whitney U (boosted vs original max h-index): U={t_stat:.0f}, p={p_val:.6f} {sig}")
        summary_scores["mann_whitney_h_index_p"] = round(p_val, 6)

    return {
        "tier_distribution": {c: dict(v) for c, v in tier_picks.items()},
        "per_model_tier_original": model_tier_report,
        "boosted_pick_rate": {
            "available": boosted_available_count,
            "picked": boosted_pick_count,
            "observed_rate": round(boost_pick_rate, 4),
            "expected_random_rate": round(expected_rate, 4),
            "lift_over_random": round(lift, 4),
            "per_model": model_boost_report,
        },
        "authority_of_picked": summary_scores,
        "per_model_authority_original": model_auth_report,
    }


# ──────────────────────────────────────────────────────────────
# Metric 3: Model Differences
# ──────────────────────────────────────────────────────────────

def metric_3_model_differences(results, lookup):
    """Compare flip rate, boost rate, and susceptibility per model."""
    print("\n" + "=" * 70)
    print("METRIC 3: MODEL DIFFERENCES (Sub-RQ1.2)")
    print("=" * 70)

    models = sorted(set(r["model"] for r in results))
    model_stats = {}

    for model in models:
        model_results = [r for r in results if r["model"] == model]

        flip_total, flip_changed = 0, 0
        boost_total, boost_changed = 0, 0
        latencies = []

        for r in model_results:
            if r["condition"] != "original":
                continue
            if r.get("recommended") is None:
                continue

            key_f = (model, r["variant"], r["query_id"], "flipped")
            key_b = (model, r["variant"], r["query_id"], "boosted")
            r_f = lookup.get(key_f)
            r_b = lookup.get(key_b)

            if r_f and r_f.get("recommended") is not None:
                flip_total += 1
                if r["recommended_paper_id"] != r_f["recommended_paper_id"]:
                    flip_changed += 1

            if r_b and r_b.get("recommended") is not None:
                boost_total += 1
                if r["recommended_paper_id"] != r_b["recommended_paper_id"]:
                    boost_changed += 1

        for r in model_results:
            if r.get("elapsed_seconds"):
                latencies.append(r["elapsed_seconds"])

        flip_rate = flip_changed / flip_total if flip_total else 0
        boost_rate = boost_changed / boost_total if boost_total else 0
        susceptibility = (flip_rate + boost_rate) / 2

        parse_total = len(model_results)
        parse_success = sum(1 for r in model_results if r.get("recommended") is not None)
        parse_rate = parse_success / parse_total if parse_total else 0

        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        median_latency = sorted(latencies)[len(latencies) // 2] if latencies else 0

        flip_ci = confidence_interval_proportion(flip_changed, flip_total)
        boost_ci = confidence_interval_proportion(boost_changed, boost_total)

        model_stats[model] = {
            "flip_rate": round(flip_rate, 4),
            "flip_rate_95ci": list(flip_ci),
            "boost_rate": round(boost_rate, 4),
            "boost_rate_95ci": list(boost_ci),
            "susceptibility": round(susceptibility, 4),
            "parse_rate": round(parse_rate, 4),
            "avg_latency_s": round(avg_latency, 2),
            "median_latency_s": round(median_latency, 2),
            "total_runs": parse_total,
        }

    print(f"\n  {'Model':<20s} {'Flip%':>7s} {'95% CI':>15s} {'Boost%':>7s} {'95% CI':>15s} {'Suscept.':>9s} {'Parse%':>7s} {'Avg Lat':>8s}")
    print(f"  {'-'*20} {'-'*7} {'-'*15} {'-'*7} {'-'*15} {'-'*9} {'-'*7} {'-'*8}")
    for model in models:
        s = model_stats[model]
        fci = f"[{s['flip_rate_95ci'][0]:.1%},{s['flip_rate_95ci'][1]:.1%}]"
        bci = f"[{s['boost_rate_95ci'][0]:.1%},{s['boost_rate_95ci'][1]:.1%}]"
        print(f"  {model:<20s} {s['flip_rate']:>6.1%} {fci:>15s} {s['boost_rate']:>6.1%} {bci:>15s} {s['susceptibility']:>8.1%} {s['parse_rate']:>6.1%} {s['avg_latency_s']:>7.1f}s")

    # Chi-squared test: are model differences significant?
    flip_table = [[0, 0] for _ in models]
    for i, model in enumerate(models):
        for r in results:
            if r["model"] != model or r["condition"] != "original" or r.get("recommended") is None:
                continue
            key_f = (model, r["variant"], r["query_id"], "flipped")
            r_f = lookup.get(key_f)
            if r_f and r_f.get("recommended") is not None:
                if r["recommended_paper_id"] != r_f["recommended_paper_id"]:
                    flip_table[i][0] += 1
                else:
                    flip_table[i][1] += 1

    chi2, p_val = scipy_stats.chi2_contingency(flip_table)[:2]
    sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "n.s."
    print(f"\n  Chi-squared test (H₀: all models have same flip rate): χ²={chi2:.2f}, p={p_val:.6f} {sig}")
    model_stats["chi2_homogeneity_flip"] = {"chi2": round(chi2, 4), "p_value": round(p_val, 6)}

    return model_stats


# ──────────────────────────────────────────────────────────────
# Metric 4: Instruction Effect
# ──────────────────────────────────────────────────────────────

def metric_4_instruction_effect(results, lookup):
    """Analyse whether instruction variants reduce authority bias."""
    print("\n" + "=" * 70)
    print("METRIC 4: INSTRUCTION EFFECT (RQ3)")
    print("=" * 70)

    variants = sorted(set(r["variant"] for r in results))
    variant_stats = {}

    for variant in variants:
        var_results = [r for r in results if r["variant"] == variant]

        flip_total, flip_changed = 0, 0
        boost_total, boost_changed = 0, 0

        for r in var_results:
            if r["condition"] != "original":
                continue
            if r.get("recommended") is None:
                continue

            key_f = (r["model"], variant, r["query_id"], "flipped")
            key_b = (r["model"], variant, r["query_id"], "boosted")
            r_f = lookup.get(key_f)
            r_b = lookup.get(key_b)

            if r_f and r_f.get("recommended") is not None:
                flip_total += 1
                if r["recommended_paper_id"] != r_f["recommended_paper_id"]:
                    flip_changed += 1

            if r_b and r_b.get("recommended") is not None:
                boost_total += 1
                if r["recommended_paper_id"] != r_b["recommended_paper_id"]:
                    boost_changed += 1

        flip_rate = flip_changed / flip_total if flip_total else 0
        boost_rate = boost_changed / boost_total if boost_total else 0
        flip_ci = confidence_interval_proportion(flip_changed, flip_total)
        boost_ci = confidence_interval_proportion(boost_changed, boost_total)

        variant_stats[variant] = {
            "flip_rate": round(flip_rate, 4),
            "flip_rate_95ci": list(flip_ci),
            "flip_pairs": flip_total,
            "boost_rate": round(boost_rate, 4),
            "boost_rate_95ci": list(boost_ci),
            "boost_pairs": boost_total,
        }

    baseline_flip = variant_stats.get("baseline", {}).get("flip_rate", 0)
    baseline_boost = variant_stats.get("baseline", {}).get("boost_rate", 0)

    print(f"\n  {'Instruction':<20s} {'Flip%':>7s} {'Δ Flip':>8s} {'Boost%':>7s} {'Δ Boost':>9s}")
    print(f"  {'-'*20} {'-'*7} {'-'*8} {'-'*7} {'-'*9}")
    for variant in variants:
        s = variant_stats[variant]
        flip_reduction = baseline_flip - s["flip_rate"]
        boost_reduction = baseline_boost - s["boost_rate"]
        variant_stats[variant]["flip_reduction_from_baseline"] = round(flip_reduction, 4)
        variant_stats[variant]["boost_reduction_from_baseline"] = round(boost_reduction, 4)

        flip_delta = f"{flip_reduction:>+7.1%}" if variant != "baseline" else "   base"
        boost_delta = f"{boost_reduction:>+7.1%}" if variant != "baseline" else "    base"
        print(f"  {variant:<20s} {s['flip_rate']:>6.1%} {flip_delta} {s['boost_rate']:>6.1%} {boost_delta}")

    # Pairwise significance: each variant vs baseline
    print(f"\n  Pairwise McNemar tests (variant vs baseline) on flip decisions:")
    baseline_results = [r for r in results if r["variant"] == "baseline" and r["condition"] == "original"]
    for variant in variants:
        if variant == "baseline":
            continue
        b_c, c_b = 0, 0  # discordant pairs
        for r_base in baseline_results:
            if r_base.get("recommended") is None:
                continue
            key_base_f = (r_base["model"], "baseline", r_base["query_id"], "flipped")
            key_var_o = (r_base["model"], variant, r_base["query_id"], "original")
            key_var_f = (r_base["model"], variant, r_base["query_id"], "flipped")

            r_base_f = lookup.get(key_base_f)
            r_var_o = lookup.get(key_var_o)
            r_var_f = lookup.get(key_var_f)

            if not all([r_base_f, r_var_o, r_var_f]):
                continue
            if r_base_f.get("recommended") is None or r_var_o.get("recommended") is None or r_var_f.get("recommended") is None:
                continue

            base_flipped = r_base["recommended_paper_id"] != r_base_f["recommended_paper_id"]
            var_flipped = r_var_o["recommended_paper_id"] != r_var_f["recommended_paper_id"]

            if base_flipped and not var_flipped:
                b_c += 1
            elif not base_flipped and var_flipped:
                c_b += 1

        if b_c + c_b > 0:
            mcnemar_result = scipy_stats.binomtest(b_c, b_c + c_b, 0.5)
            sig = "***" if mcnemar_result.pvalue < 0.001 else "**" if mcnemar_result.pvalue < 0.01 else "*" if mcnemar_result.pvalue < 0.05 else "n.s."
            print(f"    baseline vs {variant}: b→c={b_c}, c→b={c_b}, p={mcnemar_result.pvalue:.4f} {sig}")
            variant_stats[variant]["mcnemar_vs_baseline_p"] = round(mcnemar_result.pvalue, 6)

    # Per-model × variant breakdown
    models = sorted(set(r["model"] for r in results))
    print(f"\n  Per-model instruction effectiveness:")
    print(f"  {'Model':<20s} {'Variant':<20s} {'Flip%':>7s} {'Boost%':>7s}")
    print(f"  {'-'*20} {'-'*20} {'-'*7} {'-'*7}")

    model_variant_stats = {}
    for model in models:
        model_baseline_flip = None
        model_baseline_boost = None
        for variant in variants:
            mv_results = [r for r in results if r["model"] == model and r["variant"] == variant]
            ft, fc, bt, bc = 0, 0, 0, 0
            for r in mv_results:
                if r["condition"] != "original" or r.get("recommended") is None:
                    continue
                key_f = (model, variant, r["query_id"], "flipped")
                key_b = (model, variant, r["query_id"], "boosted")
                r_f = lookup.get(key_f)
                r_b = lookup.get(key_b)
                if r_f and r_f.get("recommended") is not None:
                    ft += 1
                    if r["recommended_paper_id"] != r_f["recommended_paper_id"]:
                        fc += 1
                if r_b and r_b.get("recommended") is not None:
                    bt += 1
                    if r["recommended_paper_id"] != r_b["recommended_paper_id"]:
                        bc += 1

            fr = fc / ft if ft else 0
            br = bc / bt if bt else 0

            if variant == "baseline":
                model_baseline_flip = fr
                model_baseline_boost = br

            print(f"  {model:<20s} {variant:<20s} {fr:>6.1%} {br:>6.1%}")
            model_variant_stats[f"{model}|{variant}"] = {
                "flip_rate": round(fr, 4),
                "boost_rate": round(br, 4),
            }

        if model_baseline_flip is not None:
            for variant in variants:
                if variant == "baseline":
                    continue
                key = f"{model}|{variant}"
                if key in model_variant_stats:
                    model_variant_stats[key]["flip_reduction"] = round(model_baseline_flip - model_variant_stats[key]["flip_rate"], 4)
                    model_variant_stats[key]["boost_reduction"] = round(model_baseline_boost - model_variant_stats[key]["boost_rate"], 4)

    # Interaction effect: which model benefits most from instructions?
    print(f"\n  Instruction responsiveness (baseline → content_first flip reduction):")
    print(f"  {'Model':<20s} {'Baseline Flip%':>14s} {'Content Flip%':>14s} {'Reduction':>10s}")
    print(f"  {'-'*20} {'-'*14} {'-'*14} {'-'*10}")
    for model in models:
        base_key = f"{model}|baseline"
        cf_key = f"{model}|content_first"
        if base_key in model_variant_stats and cf_key in model_variant_stats:
            bf = model_variant_stats[base_key]["flip_rate"]
            cf = model_variant_stats[cf_key]["flip_rate"]
            reduction = bf - cf
            print(f"  {model:<20s} {bf:>13.1%} {cf:>13.1%} {reduction:>+9.1%}")

    return {"by_variant": variant_stats, "by_model_variant": model_variant_stats}


# ──────────────────────────────────────────────────────────────
# Metric 5: Justification Analysis
# ──────────────────────────────────────────────────────────────

def metric_5_justification(results):
    """Analyse how often LLM justifications cite authority markers."""
    print("\n" + "=" * 70)
    print("METRIC 5: JUSTIFICATION ANALYSIS (Qualitative)")
    print("=" * 70)

    compiled = [(re.compile(pat, re.IGNORECASE), label) for pat, label in AUTHORITY_PATTERNS]

    stats_by_condition = defaultdict(lambda: {"total": 0, "with_authority_mention": 0, "pattern_counts": defaultdict(int)})
    stats_by_cond_variant = defaultdict(lambda: {"total": 0, "with_authority_mention": 0, "pattern_counts": defaultdict(int)})
    stats_by_model = defaultdict(lambda: {"total": 0, "with_authority_mention": 0})

    for r in results:
        response = r.get("response", "")
        if not response:
            continue

        condition = r["condition"]
        variant = r["variant"]
        model = r["model"]
        key_cv = f"{condition}|{variant}"

        stats_by_condition[condition]["total"] += 1
        stats_by_cond_variant[key_cv]["total"] += 1
        stats_by_model[model]["total"] += 1

        found_any = False
        for pattern, label in compiled:
            if pattern.search(response):
                found_any = True
                stats_by_condition[condition]["pattern_counts"][label] += 1
                stats_by_cond_variant[key_cv]["pattern_counts"][label] += 1

        if found_any:
            stats_by_condition[condition]["with_authority_mention"] += 1
            stats_by_cond_variant[key_cv]["with_authority_mention"] += 1
            stats_by_model[model]["with_authority_mention"] += 1

    print(f"\n  Authority mention rate by condition:")
    print(f"  {'Condition':<12s} {'Total':>6s} {'Mentions':>9s} {'Rate':>7s} {'95% CI':>17s}")
    print(f"  {'-'*12} {'-'*6} {'-'*9} {'-'*7} {'-'*17}")
    for cond in ["original", "flipped", "boosted"]:
        s = stats_by_condition[cond]
        rate = s["with_authority_mention"] / s["total"] if s["total"] else 0
        ci = confidence_interval_proportion(s["with_authority_mention"], s["total"])
        print(f"  {cond:<12s} {s['total']:>6d} {s['with_authority_mention']:>9d} {rate:>6.1%} [{ci[0]:.1%}, {ci[1]:.1%}]")

    print(f"\n  Authority mention rate by condition × instruction:")
    print(f"  {'Condition':<12s} {'Instruction':<20s} {'Rate':>7s} {'n':>5s}")
    print(f"  {'-'*12} {'-'*20} {'-'*7} {'-'*5}")
    for cond in ["original", "flipped", "boosted"]:
        for var in ["baseline", "anti_authority", "content_first"]:
            key = f"{cond}|{var}"
            s = stats_by_cond_variant.get(key, {"total": 0, "with_authority_mention": 0})
            rate = s["with_authority_mention"] / s["total"] if s["total"] else 0
            print(f"  {cond:<12s} {var:<20s} {rate:>6.1%} {s['total']:>5d}")

    print(f"\n  Authority mention rate by model:")
    print(f"  {'Model':<20s} {'Rate':>7s} {'n':>6s}")
    print(f"  {'-'*20} {'-'*7} {'-'*6}")
    for model in sorted(stats_by_model.keys()):
        s = stats_by_model[model]
        rate = s["with_authority_mention"] / s["total"] if s["total"] else 0
        print(f"  {model:<20s} {rate:>6.1%} {s['total']:>6d}")

    print(f"\n  Most common authority patterns cited:")
    all_patterns = defaultdict(int)
    for s in stats_by_condition.values():
        for pat, count in s["pattern_counts"].items():
            all_patterns[pat] += count
    total_mentions = sum(all_patterns.values())
    for pat, count in sorted(all_patterns.items(), key=lambda x: -x[1]):
        pct = count / total_mentions if total_mentions else 0
        print(f"    {pat:<20s}: {count:>5d} ({pct:.1%} of all mentions)")

    report = {}
    for cond in ["original", "flipped", "boosted"]:
        s = stats_by_condition[cond]
        rate = s["with_authority_mention"] / s["total"] if s["total"] else 0
        report[cond] = {
            "total": s["total"],
            "with_authority_mention": s["with_authority_mention"],
            "mention_rate": round(rate, 4),
            "top_patterns": dict(sorted(s["pattern_counts"].items(), key=lambda x: -x[1])[:5]),
        }

    return report


# ──────────────────────────────────────────────────────────────
# Metric 6: Statistical Summary
# ──────────────────────────────────────────────────────────────

def metric_6_statistical_summary(results, lookup):
    """Consolidated statistical significance tests."""
    print("\n" + "=" * 70)
    print("METRIC 6: STATISTICAL SIGNIFICANCE SUMMARY")
    print("=" * 70)

    tests = []

    # Test 1: Overall flip rate significantly > 0?
    flip_total, flip_changed = 0, 0
    boost_total, boost_changed = 0, 0
    for r in results:
        if r["condition"] != "original" or r.get("recommended") is None:
            continue
        key_f = (r["model"], r["variant"], r["query_id"], "flipped")
        key_b = (r["model"], r["variant"], r["query_id"], "boosted")
        r_f = lookup.get(key_f)
        r_b = lookup.get(key_b)
        if r_f and r_f.get("recommended") is not None:
            flip_total += 1
            if r["recommended_paper_id"] != r_f["recommended_paper_id"]:
                flip_changed += 1
        if r_b and r_b.get("recommended") is not None:
            boost_total += 1
            if r["recommended_paper_id"] != r_b["recommended_paper_id"]:
                boost_changed += 1

    # Flip rate significantly different from 0?
    flip_binom = scipy_stats.binomtest(flip_changed, flip_total, 0.0001, alternative='greater')
    boost_binom = scipy_stats.binomtest(boost_changed, boost_total, 0.0001, alternative='greater')

    tests.append({
        "test": "Flip rate > 0 (original→flipped)",
        "statistic": f"{flip_changed}/{flip_total} = {flip_changed/flip_total:.1%}",
        "p_value": round(float(flip_binom.pvalue), 10),
        "significant": bool(flip_binom.pvalue < 0.05),
    })
    tests.append({
        "test": "Boost rate > 0 (original→boosted)",
        "statistic": f"{boost_changed}/{boost_total} = {boost_changed/boost_total:.1%}",
        "p_value": round(float(boost_binom.pvalue), 10),
        "significant": bool(boost_binom.pvalue < 0.05),
    })

    # Flip rate > boost rate? (metadata swap has stronger effect than inflation)
    flip_vs_boost = scipy_stats.chi2_contingency([
        [flip_changed, flip_total - flip_changed],
        [boost_changed, boost_total - boost_changed],
    ])
    tests.append({
        "test": "Flip rate ≠ Boost rate",
        "statistic": f"flip={flip_changed/flip_total:.1%} vs boost={boost_changed/boost_total:.1%}",
        "chi2": round(float(flip_vs_boost[0]), 4),
        "p_value": round(float(flip_vs_boost[1]), 6),
        "significant": bool(flip_vs_boost[1] < 0.05),
    })

    print(f"\n  {'Test':<50s} {'Result':>20s} {'p-value':>12s} {'Sig.':>5s}")
    print(f"  {'-'*50} {'-'*20} {'-'*12} {'-'*5}")
    for t in tests:
        sig = "YES" if t["significant"] else "no"
        print(f"  {t['test']:<50s} {t['statistic']:>20s} {t['p_value']:>12.6f} {sig:>5s}")

    return tests


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    print("Loading results...")
    results = load_results()
    experiment_sets = load_experiment_sets()
    lookup = build_lookup(results)
    sets_lookup = build_sets_lookup(experiment_sets)

    models = sorted(set(r["model"] for r in results))
    variants = sorted(set(r["variant"] for r in results))
    topics = sorted(set(r["topic"] for r in results))

    print(f"\nDataset overview:")
    print(f"  Models:     {models}")
    print(f"  Variants:   {variants}")
    print(f"  Topics:     {len(topics)}")
    print(f"  Total runs: {len(results)}")

    report = {}
    report["overview"] = {
        "models": models,
        "variants": variants,
        "topics": topics,
        "total_runs": len(results),
        "excluded_models": list(EXCLUDE_MODELS),
    }

    report["metric_1_flip_rate"] = metric_1_flip_rate(results, lookup)
    report["metric_1a_flip_direction"] = metric_1a_flip_direction(results, lookup, sets_lookup)
    report["metric_1b_topic_breakdown"] = metric_1b_topic_breakdown(results, lookup)
    report["metric_2_dose_response"] = metric_2_dose_response(results, experiment_sets, sets_lookup)
    report["metric_3_model_differences"] = metric_3_model_differences(results, lookup)
    report["metric_4_instruction_effect"] = metric_4_instruction_effect(results, lookup)
    report["metric_5_justification"] = metric_5_justification(results)
    report["metric_6_statistical_tests"] = metric_6_statistical_summary(results, lookup)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"Full report saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
