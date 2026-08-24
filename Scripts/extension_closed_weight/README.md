# Closed-Weight Extension

Adds two closed-weight, API-served models to the authority-bias experiment:
**`gpt-4o-mini`** (OpenAI) and **`gemini-1.5-flash`** (Google AI Studio).

The extension only adds new runs. The open-weight runs in `data/results/` are
read-only — never re-executed, never modified.

## Why this exists

The submitted paper tests five open-weight 7–9B models. Reviewers will likely ask
whether the same authority bias appears in frontier closed-weight systems. This
extension answers that with a small additional set of API-based runs that use the
**identical** experiment design (same `data/experiment_sets.json`, same prompts,
same parsing rule). The combined analysis produces an apples-to-apples 7-model
comparison.

## What this extension does NOT touch

- `data/experiment_sets.json` — read-only
- `data/results/*.json` — read-only
- `Scripts/run_experiment.py` — never modified, but its formatters and parser
  are imported so prompts are bit-identical
- Any other existing analysis script or output

All extension outputs live under `data/extension/closed_weight_*`.

## Setup

Two environment variables are required:

```bash
export OPENAI_API_KEY="sk-..."          # from OpenAI dashboard
export GEMINI_API_KEY="..."             # from https://aistudio.google.com/apikey
```

No new Python dependencies — everything uses `requests`, which is already in the
project venv.

## How to run

From the project root:

```bash
source venv/bin/activate

# 1. Smoke test (6 API calls, ~15 seconds, ~$0.01 total)
python3 Scripts/extension_closed_weight/smoke_test.py

# 2. Full run for one model (~2,250 cells per model)
python3 Scripts/extension_closed_weight/run_closed_weight_experiment.py --model gpt-4o-mini
python3 Scripts/extension_closed_weight/run_closed_weight_experiment.py --model gemini-1.5-flash

# 3. Combined-model analysis (open + closed weight together)
python3 Scripts/extension_closed_weight/analyse_closed_weight.py
```

The runner supports the same flags as `run_experiment.py`: `--variant`,
`--condition`, `--topic`, `--dry-run`. Add `--limit N` to cap the number of cells
(useful for budget-bounded incremental runs).

## Output schema

Each run writes one JSON file to `data/extension/closed_weight_results/` with the
**same schema** as `data/results/results_*.json`:

```json
{
  "model": "gpt-4o-mini",
  "variant": "baseline",
  "condition": "flipped",
  "topic": "Knowledge Distillation",
  "query_id": "kd_q01",
  "query": "...",
  "recommended": 3,
  "recommended_paper_id": "...",
  "recommended_title": "...",
  "response": "...",
  "elapsed_seconds": 0.84,
  "prompt_length": 2657
}
```

Identical schema means the existing analysis scripts can ingest closed-weight
results with at most a path change.

## Cost projection

Per cell: ~2,500 input tokens + ~50 output tokens (10 paper cards + instruction).

| Model | Full run cost | Free-tier rate limit |
|---|---|---|
| `gpt-4o-mini` | ~$0.95 (2,250 cells) | 500 RPM standard |
| `gemini-1.5-flash` | $0.00 (free tier) | 15 RPM, 1M tokens/day |

Wall-clock: roughly 3 hours for Gemini (rate-limited), ~30 minutes for OpenAI.

## Decoding settings

To match the open-weight runs (which used Ollama defaults), no decoding parameters
are overridden — both APIs use their provider defaults. This is documented in the
paper's Appendix A.3 (inference setup) and noted explicitly in the run output's
`metadata` block.

## How to revert

```bash
rm -rf Scripts/extension_closed_weight/ data/extension/closed_weight_*
```

Plus revert any paper edits that referenced the closed-weight results.
