# Authority Bias in Conversational Search Engines for Academic Paper Recommendation

Code and experiment pipeline for the paper **"Authority Bias in Conversational Search Engines for Academic Paper Recommendation"** (EMNLP 2026, Main Conference).

**Authors:** Uthman Jinadu, Parsa Ghazvinian, Anjila Budathoki, Benjamin M. Ampel, Rajshekhar Sunderraman, Yi Ding
(Georgia State University; University of Tennessee, Knoxville)

## Abstract

Large Language Models (LLMs) are increasingly used as conversational search engines for academic literature, yet whether they judge papers on content or on authority signals has not been tested causally. We investigate *authority bias*: systematic preference for papers based on author prestige, venue, and citations rather than content. Holding title and abstract constant, we vary authority metadata across three counterfactual conditions (original, flipped, boosted) over eight LLMs (five open-weight and three frontier closed-weight) in an in-context, single-turn, top-1 recommendation setting. Our experiments show that authority bias is substantial and directional, varies markedly across models, and is only partially addressable through prompt-level debiasing. We further document a *say-do gap*: debiasing instructions suppress authority mentions far faster than authority-driven flips, so surface auditing systematically underestimates behavioral bias.

## Research Question

When LLMs recommend research papers, do they evaluate on **content quality** or on **authority signals** (author fame, venue prestige, h-index, citation counts)? If authority signals drive recommendations regardless of content, this creates a systemic bias that disadvantages emerging researchers, smaller institutions, and newer work, amplifying the Matthew Effect through LLM-mediated discovery.

## Methodology

A **content-controlled counterfactual audit**: the same paper content (title + abstract) is presented with different authority metadata across three conditions, so any change in the recommendation is attributable to authority signals, not content.

- **8 LLMs** — five open-weight, served locally via [Ollama](https://ollama.com) (`llama3.1:8b`, `mistral:7b`, `gemma2:9b`, `qwen2.5:7b`, `deepseek-r1:8b`), and three frontier closed-weight, via provider APIs (`gpt-5.4`, `gemini-3-flash-preview`, `claude-sonnet-4-6`).
- **3 conditions** — Original (real metadata), Flipped (high↔low authority swap), Boosted (mid-tier inflation).
- **3 instruction variants** — Baseline, Anti-Authority (mild), Content-First (strong).
- **25 CS research topics**, 10 queries each (250 total), 10 candidate papers per query.
- **Authority score** — a 5-component normalized composite with weights derived empirically from a 1:N flip pilot (15,000 runs) via logistic regression and dominance analysis:

```
authority_score = 0.353·venue + 0.292·median_h + 0.187·max_h + 0.137·citations + 0.031·affiliation
```

## Key Findings

- **39.2%** of recommendations flip when authority metadata is swapped, with content held identical.
- Under **Boosted**, **68.3%** of flips move toward the higher-authority paper — direct evidence of authority attraction.
- Model susceptibility spans **17.4%** (`gpt-5.4`) to **49.2%** (`llama3.1`); frontier closed-weight models sit at or below the open-weight band.
- The strong Content-First instruction cuts the flip rate by **12.9pp** but leaves a **31.4%** residual; mild anti-authority prompting **backfires** on all three frontier models (cohort +3.9pp).
- **Say-do gap:** debiasing instructions reduce authority *mentions* by 24.0pp but authority-driven *flips* by only 12.9pp, so surface auditing underestimates behavioral bias.
- Venue prestige is the dominant authority signal (weight 0.353); institutional affiliation is near-zero (0.031).

## Repository Structure

```
Scripts/
  collect_papers.py               # Collect papers from Semantic Scholar + OpenAlex
  authority_mappings.py           # Venue (ICORE 2026) and affiliation (4icu.org/CSRankings) scoring
  generate_conditions.py          # Build original/flipped/boosted conditions
  generate_experiment_sets.py     # Query–paper pairings with tier-diverse candidate sets
  setup_models.py                 # Pull open-weight models via Ollama
  run_1n_experiment.py            # 1:N flip pilot (weight derivation)
  analyse_1n_results.py           # Logistic regression + dominance analysis on the pilot
  run_experiment.py               # Main experiment (open-weight, resumable)
  analyse_results.py              # Metrics, statistical tests, analysis report
  analyse_cross_model_agreement.py# Cross-model selection/flip agreement
  extension_closed_weight/        # Frontier closed-weight (API) extension
    run_closed_weight_experiment.py # gpt-5.4 / gemini-3-flash-preview / claude-sonnet-4-6 runner
    api_clients.py                # Provider API clients (keys read from environment)
    analyse_merged.py             # 8-model (open + closed) headline analysis
    cross_model_agreement_merged.py
    weight_sensitivity.py         # Robustness of the direction result to weight choice
  extension_author_score/         # Author-score (max-h vs author_score) ablation
```

## Pipeline

```
1. python3 Scripts/collect_papers.py                     # 1,250 papers (50 per topic)
2. python3 Scripts/generate_conditions.py                # Experimental conditions
3. python3 Scripts/generate_experiment_sets.py           # Query–paper pairings
4. python3 Scripts/setup_models.py                       # Pull open-weight models
5. ollama serve                                          # Start Ollama (separate terminal)
6. python3 Scripts/run_1n_experiment.py --all-models     # 1:N pilot (15,000 runs)
7. python3 Scripts/analyse_1n_results.py                 # Derive empirical weights
8. python3 Scripts/generate_conditions.py                # Re-generate with empirical weights
9. python3 Scripts/run_experiment.py                     # Open-weight main experiment
10. python3 Scripts/extension_closed_weight/run_closed_weight_experiment.py  # Frontier API runs
11. python3 Scripts/extension_closed_weight/analyse_merged.py                 # 8-model analysis
```

## Requirements

- Python 3.8+
- [Ollama](https://ollama.com) (for the open-weight models)
- API keys for the frontier models (OpenAI, Google, Anthropic), read from the environment / `.env`
- Dependencies: `requests`, `python-dotenv`, `scipy`

```bash
pip install requests python-dotenv scipy
```

Copy `.env.example` to `.env` and fill in your keys (`.env` is not committed):

```
SEMANTIC_SCHOLAR_API_KEY=...
OPENAI_API_KEY=...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
```

## Data

The full pipeline regenerates all artifacts under `data/` — the 1,250 collected papers, the three condition sets, the 250 queries and per-query candidate sets, and the parsed model responses (17,898 runs; 20,148 including the `gpt-4o-mini` tier ablation). `data/` is not tracked in git; see the release/archive linked from the paper for the frozen artifacts.

## Citation

```bibtex
@inproceedings{jinadu2026authority,
  title     = {Authority Bias in Conversational Search Engines for Academic Paper Recommendation},
  author    = {Jinadu, Uthman and Ghazvinian, Parsa and Budathoki, Anjila and
               Ampel, Benjamin M. and Sunderraman, Rajshekhar and Ding, Yi},
  booktitle = {Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing (EMNLP)},
  year      = {2026}
}
```

## License

Code is released under the MIT License. Paper content is licensed CC BY 4.0.
