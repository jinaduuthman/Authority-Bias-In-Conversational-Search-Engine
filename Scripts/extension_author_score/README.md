# Author-Score Extension

Isolated extension that adds a 6th categorical predictor (`author_score`) to the
authority-score regression and tests whether it adds explanatory power beyond the
existing 5 numeric/categorical signals.

## What this is

Currently the authority score uses 5 predictors:

```
P(rec = 1) = σ(β₀ + β₁·max_h + β₂·median_h + β₃·citations + β₄·venue + β₅·affiliation)
```

This extension introduces a 6th predictor — `author_score` — which is a categorical
tier derived from the maximum h-index across all listed authors:

| Tier  | max h-index | Score |
|-------|-------------|-------|
| A*    | ≥ 70        | 1.00  |
| A     | 40 – 69     | 0.85  |
| B     | 20 – 39     | 0.65  |
| C     | 5 – 19      | 0.45  |
| D     | 0 – 4       | 0.15  |

The new specification (added alongside `max_h`, *not* replacing it):

```
P(rec = 1) = σ(β₀ + β₁·max_h + β₂·median_h + β₃·citations + β₄·venue
              + β₅·affiliation + β₆·author_score)
```

Because `author_score` is a transformation of `max_h`, the two will share variance.
Multicollinearity diagnostics (VIF) will tell us whether the regression can still
estimate them separately. The extension makes its own decision based on the result:

- **Outcome (a) — author_score is redundant** (VIF > 5 on max_h or author_score; ΔR² ≈ 0):
  drop `author_score`, report as ablation showing categorical framing adds nothing.
- **Outcome (b) — modest additional signal** (VIF manageable; small but nonzero β₆ and ΔR²):
  add as ablation in Appendix D of the paper. No re-run of the main experiment.
- **Outcome (c) — consequential** (β₆ rivals or exceeds existing signals; ΔR² meaningful):
  trigger Phase 4 — re-run the main experiment with the updated 6-component score.

## What this extension does NOT touch

- `data/scholar_papers.json` — read-only
- `data/results/1n_pilot/` — read-only
- `data/1n_analysis_report.json` — read-only
- `Scripts/analyse_1n_results.py` — never modified
- Any other existing analysis script or output

All extension outputs live under `data/extension/`. All extension scripts live in
this directory. Both directories are independent of the rest of the project.

## How to run

From the project root:

```bash
source venv/bin/activate
python3 Scripts/extension_author_score/add_author_score.py
python3 Scripts/extension_author_score/refit_pilot_with_author_score.py
```

The first script writes:
- `data/extension/scholar_papers_with_author_score.json` — augmented copy of papers
  with a new `author_score` field per paper.

The second script writes:
- `data/extension/pilot_regression_with_author_score.json` — full output of the
  6-predictor regression, including standardized coefficients, VIF, dominance R²,
  derived weights, and the verdict (a / b / c).
- `data/extension/pilot_regression_comparison.md` — side-by-side markdown table
  comparing the original 5-component regression to this 6-component extension,
  with the decision-gate verdict at the bottom.

## How to revert (one command)

```bash
rm -rf Scripts/extension_author_score/ data/extension/
```

After this, the project state is bit-for-bit identical to before the extension
was added. Every existing script, data file, and analysis output is untouched.

## Decision gate

Once `pilot_regression_comparison.md` is written, read it and look at the verdict.
The verdict is one of:

- `KEEP_5_COMPONENT` — author_score is redundant; original 5-component score is the
  preferred specification. Treat extension as an ablation in Appendix D.
- `ADD_AS_ABLATION` — author_score adds modest signal but the original 5-component
  score is still defensible. Treat extension as an ablation in Appendix D.
- `RERUN_REQUIRED` — author_score is consequential; the 5-component score used in
  the main experiment is methodologically incomplete. Phase 4 (full re-run with
  the updated 6-component score) is required for a defensible publication.

The verdict is auto-computed from VIF, ΔR², and coefficient magnitude using the
thresholds documented at the top of `refit_pilot_with_author_score.py`.
