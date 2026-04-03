# Authority Bias in Conversational Search Engines for Academic Paper Recommendation

This repository contains the experiment scripts for studying **authority bias** in LLM-based academic paper recommendation systems.

## Research Question

When LLMs recommend research papers, do they evaluate based on **content quality** or **authority signals** (author fame, venue prestige, h-index, citation counts)? If authority signals drive recommendations regardless of content, this creates a systemic bias that disadvantages emerging researchers and smaller institutions.

## Methodology

We use a **counterfactual audit design**: the same paper content is presented with different authority metadata across three conditions (original, flipped, boosted). Any change in recommendation is attributable to authority signals, not content.

### Experiment Design

- **5 LLMs**: llama3.1:8b, mistral:7b, gemma2:9b, qwen2.5:7b, deepseek-r1:8b (run locally via [Ollama](https://ollama.com))
- **3 Conditions**: Original (real metadata), Flipped (high↔low authority swap), Boosted (mid-tier inflation)
- **3 Instruction Variants**: Baseline, Anti-Authority, Content-First
- **25 CS Research Topics**, 10 queries each, 10 candidate papers per query
- **Authority Score**: 5-component normalized composite with empirically-derived weights from a 1:N flip pilot (15,000 runs)

```
authority_score = 0.353 × venue + 0.292 × median_h + 0.187 × max_h + 0.137 × citations + 0.031 × affiliation
```

## Scripts

| Script | Purpose |
|--------|---------|
| `collect_papers.py` | Collect papers from Semantic Scholar + OpenAlex APIs |
| `authority_mappings.py` | Venue scoring (ICORE 2026) and affiliation scoring (4icu.org/CSRankings) |
| `generate_conditions.py` | Create original/flipped/boosted experimental conditions |
| `generate_experiment_sets.py` | Build query-paper pairings with tier-diverse candidate sets |
| `setup_models.py` | Download LLM models via Ollama |
| `run_1n_experiment.py` | 1:N flip pilot to empirically derive authority signal weights |
| `analyse_1n_results.py` | Logistic regression + dominance analysis on pilot results |
| `run_experiment.py` | Execute main experiment (models × variants × conditions × queries) |
| `analyse_results.py` | Compute all metrics, statistical tests, and generate analysis report |

## Pipeline

```
1. python3 Scripts/collect_papers.py             # Collect 1,250 papers (50 per topic)
2. python3 Scripts/generate_conditions.py        # Generate experimental conditions
3. python3 Scripts/generate_experiment_sets.py   # Build query-paper pairings
4. python3 Scripts/setup_models.py               # Download models
5. ollama serve                                   # Start Ollama (separate terminal)
6. python3 Scripts/run_1n_experiment.py --all-models  # 1:N pilot (15,000 runs)
7. python3 Scripts/analyse_1n_results.py         # Derive empirical weights
8. python3 Scripts/generate_conditions.py        # Re-generate with empirical weights
9. python3 Scripts/run_experiment.py             # Main experiment (~11,250 runs)
10. python3 Scripts/analyse_results.py           # Analysis and statistical tests
```

## Requirements

- Python 3.8+
- [Ollama](https://ollama.com) installed and running
- Dependencies: `requests`, `python-dotenv`, `scipy`

```bash
pip install requests python-dotenv scipy
```

A Semantic Scholar API key (optional but recommended) can be placed in a `.env` file:

```
SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

## Key Findings

- **48.0%** of recommendations flip when authority metadata is swapped (content unchanged)
- **69.7%** of flips under boosted conditions move toward higher authority
- Model susceptibility ranges from **23.6%** (gemma2) to **49.2%** (llama3.1)
- Debiasing instructions reduce flip rate by **17.6pp** but leave **38.3%** residual bias
- Venue prestige is the strongest authority signal (weight = 0.353)
- A **say-do gap** exists: models stop citing authority in justifications but still act on it
