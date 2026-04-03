import json
import time
import os
import requests
import re
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

BASE_URL = "https://api.semanticscholar.org/graph/v1"
OPENALEX_URL = "https://api.openalex.org"

API_KEY = os.environ.get("S2_API_KEY", "")
OPENALEX_EMAIL = "user@example.com"

SEARCH_FIELDS = ",".join([
    "title", "abstract", "year", "venue", "citationCount",
    "url", "openAccessPdf", "paperId",
    "authors", "authors.name", "authors.authorId",
    "authors.hIndex", "authors.citationCount",
])

PAPER_DETAIL_FIELDS = "title,externalIds,authors,authors.name,authors.authorId,authors.affiliations"
PAPER_BATCH_SIZE = 500

# ──────────────────────────────────────────────────────────────
# Research topics — each topic has a list of search queries
# designed to pull papers from different venue tiers, author
# prominence levels, and institution types.
# ──────────────────────────────────────────────────────────────
RESEARCH_TOPICS = {
    "Knowledge Distillation": [
        "knowledge distillation large language models",
        "knowledge distillation vision transformers",
        "model compression distillation student teacher",
    ],
    "Prompt Engineering": [
        "prompt engineering large language models",
        "in-context learning few-shot prompting",
        "chain of thought prompting reasoning",
    ],
    "LLM Alignment": [
        "reinforcement learning human feedback alignment",
        "RLHF language model safety",
        "preference optimization large language models",
    ],
    "Text Summarization": [
        "abstractive text summarization transformer",
        "document summarization long text",
        "multi-document summarization extractive",
    ],
    "Machine Translation": [
        "neural machine translation transformer",
        "low-resource machine translation",
        "multilingual translation language models",
    ],
    "Named Entity Recognition": [
        "named entity recognition deep learning",
        "NER few-shot low-resource",
        "biomedical named entity recognition",
    ],
    "Sentiment Analysis": [
        "sentiment analysis deep learning",
        "aspect-based sentiment analysis",
        "multimodal sentiment analysis social media",
    ],
    "Question Answering": [
        "open-domain question answering retrieval",
        "reading comprehension question answering",
        "visual question answering multimodal",
    ],
    "Federated Learning": [
        "federated learning privacy deep learning",
        "federated learning heterogeneous data",
        "communication-efficient federated optimization",
    ],
    "Meta-Learning": [
        "meta-learning few-shot classification",
        "model-agnostic meta-learning optimization",
        "meta-learning task adaptation neural",
    ],
    "Reinforcement Learning": [
        "deep reinforcement learning policy optimization",
        "multi-agent reinforcement learning",
        "offline reinforcement learning batch",
    ],
    "Transfer Learning": [
        "transfer learning domain adaptation deep",
        "pre-trained models fine-tuning transfer",
        "cross-domain transfer learning",
    ],
    "Self-Supervised Learning": [
        "self-supervised learning contrastive representation",
        "masked image modeling self-supervised",
        "self-supervised speech representation learning",
    ],
    "Graph Neural Networks": [
        "graph neural networks node classification",
        "graph transformer attention networks",
        "heterogeneous graph neural network",
    ],
    "Generative Adversarial Networks": [
        "generative adversarial network image synthesis",
        "conditional GAN image-to-image translation",
        "GAN training stability mode collapse",
    ],
    "Object Detection": [
        "object detection transformer DETR",
        "real-time object detection YOLO",
        "3D object detection point cloud",
    ],
    "Image Segmentation": [
        "semantic segmentation deep learning",
        "instance segmentation panoptic",
        "medical image segmentation U-Net",
    ],
    "Image Generation": [
        "diffusion models image generation",
        "text-to-image generation stable diffusion",
        "image generation variational autoencoder",
    ],
    "Explainable AI": [
        "explainable artificial intelligence interpretability",
        "attention-based explanation neural network",
        "post-hoc explainability deep learning",
    ],
    "Fairness in Machine Learning": [
        "fairness machine learning bias mitigation",
        "algorithmic fairness classification",
        "bias detection natural language processing",
    ],
    "Adversarial Robustness": [
        "adversarial robustness deep neural networks",
        "adversarial attacks defenses image classification",
        "certified robustness adversarial perturbations",
    ],
    "Recommender Systems": [
        "deep learning recommender systems collaborative filtering",
        "sequential recommendation transformer",
        "knowledge graph recommendation",
    ],
    "Time Series Forecasting": [
        "time series forecasting transformer",
        "deep learning time series prediction",
        "multivariate time series anomaly detection",
    ],
    "Neural Architecture Search": [
        "neural architecture search efficient",
        "differentiable architecture search DARTS",
        "hardware-aware neural architecture search",
    ],
    "Attention Mechanisms": [
        "attention mechanism transformer efficient",
        "multi-head self-attention neural network",
        "linear attention transformer approximation",
    ],
}

YEAR_RANGE = "2018-2026"
PAPERS_PER_TOPIC = 50

POOL_PER_QUERY = 60         # fetch large pool per query for stratified sampling
EMERGING_YEAR = "2024-2026"
EMERGING_PER_QUERY = 15     # recent papers to add per query

# Stratified sampling targets from the pool
TARGET_HIGH_CITE = 15       # highly cited -> top venues (NeurIPS, ACL, ICML, CVPR...)
TARGET_MID_CITE = 15        # medium cited -> mid venues (AAAI, COLING, Neurocomputing...)
TARGET_LOW_CITE = 10        # lower cited -> workshops, regional, newer journals
TARGET_RECENT = 10          # very recent (2024-2026) regardless of citations

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PAPERS_FILE = os.path.join(OUTPUT_DIR, "scholar_papers.json")

RATE_LIMIT_DELAY = 3.0


# ──────────────────────────────────────────────────────────────
# API helpers
# ──────────────────────────────────────────────────────────────

def get_headers():
    headers = {}
    if API_KEY:
        headers["x-api-key"] = API_KEY
    return headers


def api_get(url, params=None, retries=5, headers=None):
    for attempt in range(1, retries + 1):
        resp = requests.get(url, params=params, headers=headers or get_headers())
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = 10 * attempt
            print(f"      Rate limited, waiting {wait}s... (attempt {attempt}/{retries})")
            time.sleep(wait)
        else:
            print(f"      HTTP {resp.status_code}: {resp.text[:200]}")
            time.sleep(3)
    return None


def api_post(url, payload, params=None, retries=5):
    for attempt in range(1, retries + 1):
        resp = requests.post(url, json=payload, params=params, headers=get_headers())
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = 10 * attempt
            print(f"      Rate limited, waiting {wait}s... (attempt {attempt}/{retries})")
            time.sleep(wait)
        else:
            print(f"      HTTP {resp.status_code}: {resp.text[:200]}")
            time.sleep(3)
    return None


# ──────────────────────────────────────────────────────────────
# Paper collection
# ──────────────────────────────────────────────────────────────

def _parse_paper(raw):
    return {
        "paper_id": raw.get("paperId", ""),
        "title": raw.get("title", ""),
        "abstract": raw.get("abstract", ""),
        "year": raw.get("year"),
        "venue": raw.get("venue", ""),
        "citation_count": raw.get("citationCount", 0),
        "url": raw.get("url", ""),
        "open_access_pdf": (raw.get("openAccessPdf") or {}).get("url", ""),
        "authors": [
            {
                "name": a.get("name", ""),
                "author_id": a.get("authorId", ""),
                "affiliations": [],
                "h_index": a.get("hIndex"),
                "citation_count": a.get("citationCount"),
            }
            for a in raw.get("authors", [])
        ],
    }


def _fetch_batch(query, limit, offset=0, year=YEAR_RANGE):
    papers = []
    batch_size = min(limit, 100)

    while len(papers) < limit:
        data = api_get(
            f"{BASE_URL}/paper/search",
            params={
                "query": query, "limit": batch_size,
                "offset": offset, "fields": SEARCH_FIELDS, "year": year,
            },
        )
        if not data:
            break

        batch = data.get("data", [])
        if not batch:
            break

        for raw in batch:
            papers.append(_parse_paper(raw))

        offset += len(batch)
        time.sleep(RATE_LIMIT_DELAY)

        if offset >= data.get("total", 0):
            break

    return papers[:limit]


def collect_topic_papers(topic, queries):
    """Fetch a large pool across queries, then stratified-sample by citation count."""
    seen_ids = set()
    pool = []

    def add_unique(papers):
        for p in papers:
            if p["paper_id"] and p["paper_id"] not in seen_ids:
                seen_ids.add(p["paper_id"])
                pool.append(p)

    # Build a large pool from all queries
    for q_idx, query in enumerate(queries, 1):
        print(f"    Query {q_idx}/{len(queries)}: \"{query}\"")
        batch = _fetch_batch(query, POOL_PER_QUERY, offset=0)
        add_unique(batch)

        recent = _fetch_batch(query, EMERGING_PER_QUERY, offset=0, year=EMERGING_YEAR)
        add_unique(recent)

    print(f"    Pool: {len(pool)} unique papers")

    # Sort pool by citation count descending for stratified sampling
    pool.sort(key=lambda p: p.get("citation_count", 0) or 0, reverse=True)

    # Split into citation tiers
    third = len(pool) // 3
    high_pool = pool[:third]
    mid_pool = pool[third:2 * third]
    low_pool = pool[2 * third:]

    # Separate recent papers (2024-2026)
    recent_pool = [p for p in pool if p.get("year") and p["year"] >= 2024]

    selected = []
    selected_ids = set()

    def pick(source, count, tier):
        picked = 0
        for p in source:
            if picked >= count:
                break
            if p["paper_id"] not in selected_ids:
                selected_ids.add(p["paper_id"])
                p["tier"] = tier
                selected.append(p)
                picked += 1
        return picked

    n_high = pick(high_pool, TARGET_HIGH_CITE, "top")
    n_mid = pick(mid_pool, TARGET_MID_CITE, "mid")
    n_low = pick(low_pool, TARGET_LOW_CITE, "low")
    n_recent = pick(recent_pool, TARGET_RECENT, "emerging")

    # If any tier fell short, fill from remaining pool
    remaining = [p for p in pool if p["paper_id"] not in selected_ids]
    target = PAPERS_PER_TOPIC - len(selected)
    if target > 0 and remaining:
        pick(remaining, target, "fill")

    tier_counts = {}
    for p in selected:
        tier_counts[p["tier"]] = tier_counts.get(p["tier"], 0) + 1
    tier_str = "  ".join(f"{k}:{v}" for k, v in sorted(tier_counts.items()))
    print(f"    Selected: {len(selected)} papers  ({tier_str})")

    if selected:
        cites = [p.get("citation_count", 0) or 0 for p in selected]
        print(f"    Citations — max:{max(cites)}  median:{sorted(cites)[len(cites)//2]}  min:{min(cites)}")
        venues = set(p.get("venue", "") for p in selected if p.get("venue"))
        print(f"    Unique venues: {len(venues)}")

    return selected


# ──────────────────────────────────────────────────────────────
# Affiliation enrichment
# ──────────────────────────────────────────────────────────────

def enrich_affiliations_s2(all_papers):
    paper_ids = []
    for papers in all_papers.values():
        for paper in papers:
            pid = paper.get("paper_id")
            if pid:
                paper_ids.append(pid)

    if not paper_ids:
        return

    affiliation_map = {}
    total = len(paper_ids)
    print(f"\n[Phase 2] Semantic Scholar affiliations for {total} papers...")

    for start in range(0, total, PAPER_BATCH_SIZE):
        chunk = paper_ids[start : start + PAPER_BATCH_SIZE]
        batch_num = start // PAPER_BATCH_SIZE + 1
        print(f"  Batch {batch_num} — papers {start + 1}..{start + len(chunk)} of {total}")

        data = api_post(
            f"{BASE_URL}/paper/batch",
            payload={"ids": chunk},
            params={"fields": PAPER_DETAIL_FIELDS},
        )

        if data:
            for item in data:
                if not item or not item.get("paperId"):
                    continue
                pid = item["paperId"]
                affiliation_map[pid] = {"affs": {}, "doi": None}

                ext_ids = item.get("externalIds") or {}
                affiliation_map[pid]["doi"] = ext_ids.get("DOI")

                for author in item.get("authors", []):
                    aid = author.get("authorId")
                    affs = author.get("affiliations", [])
                    if aid and affs:
                        affiliation_map[pid]["affs"][aid] = affs

        time.sleep(RATE_LIMIT_DELAY)

    patched = 0
    for papers in all_papers.values():
        for paper in papers:
            pid = paper.get("paper_id")
            entry = affiliation_map.get(pid, {})

            if entry.get("doi") and not paper.get("doi"):
                paper["doi"] = entry["doi"]

            paper_affs = entry.get("affs", {})
            for author in paper.get("authors", []):
                aid = author.get("author_id")
                if aid and aid in paper_affs:
                    author["affiliations"] = paper_affs[aid]
                    patched += 1

    with open(PAPERS_FILE, "w") as f:
        json.dump(all_papers, f, indent=2, ensure_ascii=False)
    print(f"  S2 patched: {patched} author entries.")


def normalize(name):
    name = name.lower().strip()
    name = re.sub(r"[^a-z\s]", "", name)
    return " ".join(name.split())


def last_name(name):
    parts = normalize(name).split()
    return parts[-1] if parts else ""


def match_author_name(s2_name, oa_name):
    s2 = normalize(s2_name)
    oa = normalize(oa_name)
    if s2 == oa:
        return True
    if last_name(s2_name) == last_name(oa_name):
        s2_parts = s2.split()
        oa_parts = oa.split()
        if len(s2_parts) >= 1 and len(oa_parts) >= 1:
            if s2_parts[0] == oa_parts[0]:
                return True
            if s2_parts[0][:1] == oa_parts[0][:1]:
                return True
    return False


def _extract_oa_affiliations(work):
    """Extract {author_name: [affiliations]} from an OpenAlex work object."""
    author_affs = {}
    for authorship in work.get("authorships", []):
        author_name = authorship.get("author", {}).get("display_name", "")
        institutions = authorship.get("institutions", [])
        affs = [inst.get("display_name", "") for inst in institutions if inst.get("display_name")]
        if author_name and affs:
            author_affs[author_name] = affs
    return author_affs


def fetch_openalex_by_doi(doi):
    """Lookup a paper on OpenAlex by DOI (exact match)."""
    data = api_get(f"{OPENALEX_URL}/works/doi:{doi}", params={"mailto": OPENALEX_EMAIL}, headers={})
    if not data or "authorships" not in data:
        return {}
    return _extract_oa_affiliations(data)


def fetch_openalex_by_title(title):
    """Search OpenAlex by title (fuzzy match, no year filter)."""
    params = {
        "search": title,
        "per_page": 3,
        "mailto": OPENALEX_EMAIL,
    }

    data = api_get(f"{OPENALEX_URL}/works", params=params, headers={})
    if not data:
        return {}

    results = data.get("results", [])
    if not results:
        return {}

    search_lower = title.lower().strip()
    for work in results:
        oa_title = (work.get("title") or "").lower().strip()
        if oa_title == search_lower:
            return _extract_oa_affiliations(work)
        # Relaxed check: match if titles share 70%+ leading characters
        shorter = min(len(oa_title), len(search_lower))
        if shorter > 10:
            overlap = sum(1 for a, b in zip(oa_title, search_lower) if a == b)
            if overlap / shorter >= 0.7:
                return _extract_oa_affiliations(work)

    return {}


def _patch_authors(paper, oa_affs):
    """Patch missing affiliations into a paper's author list."""
    patched = 0
    if not oa_affs:
        return 0
    for author in paper.get("authors", []):
        if author.get("affiliations"):
            continue
        for oa_name, affs in oa_affs.items():
            if match_author_name(author["name"], oa_name):
                author["affiliations"] = affs
                patched += 1
                break
    return patched


def enrich_affiliations_openalex(all_papers):
    papers_needing_enrichment = []
    for papers in all_papers.values():
        for paper in papers:
            has_gaps = any(
                not author.get("affiliations")
                for author in paper.get("authors", [])
            )
            if has_gaps and paper.get("title"):
                papers_needing_enrichment.append(paper)

    if not papers_needing_enrichment:
        print("\n[Phase 3] All authors already have affiliations.")
        return

    total = len(papers_needing_enrichment)
    with_doi = sum(1 for p in papers_needing_enrichment if p.get("doi"))
    print(f"\n[Phase 3] OpenAlex enrichment for {total} papers ({with_doi} have DOIs)...")

    patched = 0
    for idx, paper in enumerate(papers_needing_enrichment, 1):
        oa_affs = {}

        # Try DOI lookup first (exact match, most reliable)
        if paper.get("doi"):
            oa_affs = fetch_openalex_by_doi(paper["doi"])

        # Fall back to title search (no year filter, relaxed matching)
        if not oa_affs:
            oa_affs = fetch_openalex_by_title(paper["title"])

        patched += _patch_authors(paper, oa_affs)

        if idx % 50 == 0:
            with open(PAPERS_FILE, "w") as f:
                json.dump(all_papers, f, indent=2, ensure_ascii=False)
            print(f"  [{idx}/{total}] checkpoint — {patched} affiliations filled")

        time.sleep(0.15)

    with open(PAPERS_FILE, "w") as f:
        json.dump(all_papers, f, indent=2, ensure_ascii=False)
    print(f"  OpenAlex patched: {patched} author entries.")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if API_KEY:
        print(f"Using S2 API key: {API_KEY[:8]}...")
    else:
        print("No S2 API key set (optional). Using unauthenticated mode.\n")

    all_papers = {}
    if os.path.exists(PAPERS_FILE):
        with open(PAPERS_FILE, "r") as f:
            all_papers = json.load(f)
        total = sum(len(p) for p in all_papers.values())
        print(f"Resuming — {total} papers across {len(all_papers)} topics\n")

    # --- Phase 1: collect papers by research topic ---
    topic_items = list(RESEARCH_TOPICS.items())
    for i, (topic, queries) in enumerate(topic_items, 1):
        if topic in all_papers and len(all_papers[topic]) >= PAPERS_PER_TOPIC:
            print(f"  Skipping {topic} (already have {len(all_papers[topic])} papers)")
            continue

        print(f"\n[{i}/{len(RESEARCH_TOPICS)}] {topic}")
        papers = collect_topic_papers(topic, queries)
        all_papers[topic] = [dict(p, topic=topic) for p in papers]

        with open(PAPERS_FILE, "w") as f:
            json.dump(all_papers, f, indent=2, ensure_ascii=False)
        print(f"  -> {len(papers)} papers saved")

        time.sleep(RATE_LIMIT_DELAY)

    # --- Phase 2: Semantic Scholar affiliations ---
    enrich_affiliations_s2(all_papers)

    # --- Phase 3: OpenAlex backfill ---
    enrich_affiliations_openalex(all_papers)

    # --- Summary ---
    total_papers = sum(len(p) for p in all_papers.values())
    total_authors = 0
    with_affs = 0
    tier_counts = {}
    for papers in all_papers.values():
        for paper in papers:
            t = paper.get("tier", "unknown")
            tier_counts[t] = tier_counts.get(t, 0) + 1
            for author in paper.get("authors", []):
                total_authors += 1
                if author.get("affiliations"):
                    with_affs += 1

    print(f"\n{'='*60}")
    print(f"Total papers:      {total_papers}")
    for t, c in sorted(tier_counts.items()):
        print(f"  {t}: {c}")
    print(f"Author entries:    {total_authors}")
    print(f"With affiliations: {with_affs} ({100*with_affs//max(total_authors,1)}%)")
    print(f"Output:            {PAPERS_FILE}\n")
    for topic, papers in all_papers.items():
        print(f"  {topic}: {len(papers)} papers")


if __name__ == "__main__":
    main()
