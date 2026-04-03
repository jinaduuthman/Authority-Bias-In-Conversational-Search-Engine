"""
Authority signal mappings for venue ranking and institutional affiliation scoring.

Venue rankings: Based on ICORE 2026 conference rankings (https://portal.core.edu.au/conf-ranks/)
               and established journal impact tiers.

Affiliation rankings: Based on 4icu.org 2025 World University Rankings
                      (https://www.4icu.org/world/top-200/) supplemented by
                      CSRankings (https://csrankings.org/) for CS-specific prominence,
                      and curated industry research lab tiers.

Score ranges: All scores are on [0, 1] to allow direct use in normalized composites.
"""

import re

# ═══════════════════════════════════════════════════════════════
# VENUE SCORING
# ═══════════════════════════════════════════════════════════════

# ICORE 2026 A* conferences (flagship) — Score: 1.0
_VENUE_ASTAR = {
    "Neural Information Processing Systems",
    "International Conference on Machine Learning",
    "International Conference on Learning Representations",
    "Annual Meeting of the Association for Computational Linguistics",
    "Conference on Empirical Methods in Natural Language Processing",
    "Computer Vision and Pattern Recognition",
    "AAAI Conference on Artificial Intelligence",
    "European Conference on Computer Vision",
    "IEEE International Conference on Computer Vision",
    "Knowledge Discovery and Data Mining",
    "International Joint Conference on Artificial Intelligence",
    "Annual International ACM SIGIR Conference on Research and Development in Information Retrieval",
    "The Web Conference",
    "ACM Multimedia",
    "International Conference on Data Engineering",
    "IEEE International Conference on Data Mining",
    "International Conference on Software Engineering",
    "Measurement and Modeling of Computer Systems",
    "Proceedings of the VLDB Endowment",
    "IEEE Symposium on Security and Privacy",
    "Conference on Computer and Communications Security",
    "International Conference on Architectural Support for Programming Languages and Operating Systems",
    "International Symposium on High-Performance Computer Architecture",
    "ACM/IEEE International Conference on Mobile Computing and Networking",
    "International Conference on Computer Graphics and Interactive Techniques",
    "International Conference on Human Factors in Computing Systems",
    "Conference on Fairness, Accountability and Transparency",
    "Conference on Learning Theory",
    "IEEE International Conference on Robotics and Automation",
    "International Conference on Automated Planning and Scheduling",
}

# ICORE 2026 A conferences (excellent) — Score: 0.75
_VENUE_A = {
    "North American Chapter of the Association for Computational Linguistics",
    "NAACL-HLT",
    "IEEE Workshop/Winter Conference on Applications of Computer Vision",
    "Web Search and Data Mining",
    "Interspeech",
    "International Conference on Medical Image Computing and Computer-Assisted Intervention",
    "Conference on Uncertainty in Artificial Intelligence",
    "IEEE/RJS International Conference on Intelligent RObots and Systems",
    "International Conference on Artificial Intelligence and Statistics",
    "Conference on Robot Learning",
    "ECML/PKDD",
    "European Conference on Artificial Intelligence",
    "European Conference on Information Retrieval",
    "ACM International Conference on Recommender Systems",
    "Annual Conference on Genetic and Evolutionary Computation",
    "International Symposium on Software Testing and Analysis",
    "IEEE International Conference on Software Analysis, Evolution, and Reengineering",
    "International Conference on Information and Knowledge Management",
    "IEEE International Conference on Acoustics, Speech, and Signal Processing",
    "Automatic Speech Recognition & Understanding",
    "ACM International Conference on Web Search and Data Mining",
    "International Conference on 3D Vision",
    "IEEE International Conference on Bioinformatics and Biomedicine",
    "Asian Conference on Computer Vision",
    "International Conference on Language Resources and Evaluation",
    "Conference of the European Chapter of the Association for Computational Linguistics",
    "Transactions of the Association for Computational Linguistics",
    "Computational Linguistics",
    "Conference on Machine Translation",
    "AAAI/ACM Conference on AI, Ethics, and Society",
    "Pacific-Asia Conference on Knowledge Discovery and Data Mining",
    "International Conference on Parallel Processing",
    "Conference on Learning for Dynamics & Control",
    "Hawaii International Conference on System Sciences",
}

# Top-tier journals — Score: 0.75
_VENUE_TOP_JOURNAL = {
    "IEEE Transactions on Pattern Analysis and Machine Intelligence",
    "International Journal of Computer Vision",
    "Journal of machine learning research",
    "Trans. Mach. Learn. Res.",
    "ACM Computing Surveys",
    "Nature",
    "Nature Communications",
    "Nature Reviews Materials",
    "IEEE Transactions on Image Processing",
    "IEEE Transactions on Neural Networks and Learning Systems",
    "IEEE Transactions on Information Forensics and Security",
    "IEEE Transactions on Knowledge and Data Engineering",
    "IEEE/ACM Transactions on Audio Speech and Language Processing",
    "IEEE Transactions on Audio, Speech, and Language Processing",
    "IEEE Transactions on Signal Processing",
    "IEEE Transactions on Medical Imaging",
    "IEEE Transactions on Visualization and Computer Graphics",
    "ACM Transactions on Information Systems",
    "ACM Trans. Inf. Syst.",
    "ACM Transactions on Intelligent Systems and Technology",
    "ACM Transactions on Software Engineering and Methodology",
    "Information Fusion",
    "Artificial Intelligence Review",
    "Medical Image Anal.",
    "Pattern Recognition",
    "Empirical Software Engineering",
    "Science China Information Sciences",
    "Machine Intelligence Research",
}

# ICORE B / Mid-tier conferences and journals — Score: 0.5
_VENUE_B = {
    "International Conference on Computational Linguistics",
    "COMAD/CODS",
    "International Conference on Artificial Neural Networks",
    "IEEE International Joint Conference on Neural Network",
    "International Conference on Machine Learning and Applications",
    "International Conference on Computational Collective Intelligence",
    "Extended Semantic Web Conference",
    "International Conference on Agents and Artificial Intelligence",
    "AutoML",
    "Pacific Rim International Conference on Artificial Intelligence",
    "ICON",
    "IJCNLP-AACL",
    "International Workshop on Spoken Language Translation",
    "Machine Translation Summit",
    "Conference of the Association for Machine Translation in the Americas",
    "Indian Conference on Computer Vision, Graphics & Image Processing",
    "Asian Conference on Intelligent Information and Database Systems",
    "International Conference on Critical Infrastructure Protection",
    "BigData Congress [Services Society]",
    "International Conference on Field-Programmable Logic and Applications",
    "Industrial Conference on Data Mining",
    "International Symposium on Search Based Software Engineering",
}

# Mid-tier journals — Score: 0.5
_VENUE_MID_JOURNAL = {
    "Neural Networks",
    "Neural computing & applications (Print)",
    "Neurocomputing",
    "Knowledge-Based Systems",
    "Expert systems with applications",
    "Information Sciences",
    "Applied Soft Computing",
    "Multimedia tools and applications",
    "Engineering applications of artificial intelligence",
    "Information Processing & Management",
    "IEEE Transactions on Geoscience and Remote Sensing",
    "IEEE Transactions on Mobile Computing",
    "IEEE Transactions on Services Computing",
    "IEEE Transactions on Industrial Informatics",
    "IEEE Transactions on Vehicular Technology",
    "IEEE Transactions on Emerging Topics in Computational Intelligence",
    "IEEE transactions on intelligent transportation systems (Print)",
    "IEEE Transactions on Instrumentation and Measurement",
    "IEEE Transactions on Computational Social Systems",
    "IEEE Transactions on Affective Computing",
    "IEEE Internet of Things Journal",
    "IEEE Sensors Journal",
    "IEEE Robotics and Automation Letters",
    "IEEE Transactions on Smart Grid",
    "IEEE transactions on multimedia",
    "IEEE Signal Processing Letters",
    "IEEE Geoscience and Remote Sensing Letters",
    "IEEE transactions on circuits and systems for video technology (Print)",
    "IEEE transactions on fuzzy systems",
    "IEEE Transactions on Wireless Communications",
    "IEEE Transactions on Communications",
    "IEEE Transactions on Dependable and Secure Computing",
    "IEEE Transactions on Automation Science and Engineering",
    "IEEE Transactions on Power Systems",
    "IEEE Transactions on Aerospace and Electronic Systems",
    "IEEE Transactions on Human-Machine Systems",
    "IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems",
    "IEEE Transactions on Artificial Intelligence",
    "IEEE Transactions on Network and Service Management",
    "IEEE Transactions on Transportation Electrification",
    "IEEE Transactions on Learning Technologies",
    "IEEE transactions on computers",
    "IEEE Journal on Selected Topics in Signal Processing",
    "IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing",
    "IEEE journal of biomedical and health informatics",
    "IEEE Signal Processing Magazine",
    "IEEE wireless communications",
    "IEEE/CAA Journal of Automatica Sinica",
    "IEEE Systems Journal",
    "Knowledge and Information Systems",
    "Data & Knowledge Engineering",
    "Applied intelligence (Boston)",
    "Complex & Intelligent Systems",
    "Automation in Construction",
    "Future generations computer systems",
    "Computers & security",
    "Biomedical Signal Processing and Control",
    "Computer graphics forum (Print)",
    "Image and Vision Computing",
    "Machine Vision and Applications",
    "Neural Processing Letters",
    "J. Am. Medical Informatics Assoc.",
    "Journal of Biomedical Informatics",
    "Artif. Intell. Medicine",
    "Briefings Bioinform.",
    "Bioinform.",
    "Journal of Computational Physics",
    "Comput. Aided Civ. Infrastructure Eng.",
    "International Journal of Machine Learning and Cybernetics",
    "Pattern Recognition Letters",
    "ACM Transactions on Evolutionary Learning and Optimization",
    "ACM Trans. Asian Low Resour. Lang. Inf. Process.",
    "ACM Transactions on Architecture and Code Optimization (TACO)",
    "npj Digital Medicine",
    "Signal, Image and Video Processing",
    "The Visual Computer",
    "Intelligent Data Analysis",
    "Journal of Real-Time Image Processing",
    "Comput. Methods Programs Biomed.",
    "Comput. Medical Imaging Graph.",
    "Comput. Biol. Medicine",
    "Cybernetics and systems",
    "Scientometrics",
    "CAAI Transactions on Intelligence Technology",
    "Journal of Supercomputing",
    "International Journal of Production Research",
    "Ocean Engineering",
    "Chemometrics and Intelligent Laboratory Systems",
    "Artificial Intelligence and Law",
    "Machine Translation",
    "International Journal of Artificial Intelligence in Education",
    "Natural Language Processing Journal",
    "Journal of the American Statistical Association",
    "IET Image Processing",
    "Connection science",
    "Machine Learning and Knowledge Extraction",
}

# Lower-tier / General journals — Score: 0.25
_VENUE_C_JOURNAL = {
    "IEEE Access",
    "Scientific Reports",
    "Applied Sciences",
    "Electronics",
    "PLoS ONE",
    "bioRxiv",
    "medRxiv",
    "Sustainability",
    "Remote Sensing",
    "Mathematics",
    "Drones",
    "Bioengineering",
    "Cancers",
    "Diagnostics",
    "Journal of Imaging",
    "Big Data and Cognitive Computing",
    "PeerJ Computer Science",
    "Algorithms",
    "Entropy",
    "Healthcare",
    "Buildings",
    "Technologies",
    "Smart Cities",
    "Future Internet",
    "Frontiers Artif. Intell.",
    "Frontiers in Environmental Science",
    "F1000Research",
    "JMIR Formative Research",
    "JMIR AI",
    "Journal of Medical Internet Research",
    "BMC Biology",
    "BMC Genomics",
    "BMC Bioinformatics",
    "BMC Cancer",
    "BMC Medical Imaging",
    "BMC Medical Informatics and Decision Making",
    "BMC Medical Research Methodology",
    "Vehicles",
    "Laws",
    "Data in Brief",
    "SN Computer Science",
    "Journal of Big Data",
    "Advances in Intelligent Systems and Computing",
    "Procedia Computer Science",
    "Journal of Physics: Conference Series",
    "ITM Web of Conferences",
    "Inf.",
    "PLoS Comput. Biol.",
    "Health Information Science and Systems",
    "Informatics in Medicine Unlocked",
    "Digital Health",
    "Physiological Measurement",
    "Structural Health Monitoring",
    "Journal of Marine Science and Engineering",
    "Alexandria Engineering Journal",
    "Information and Software Technology",
    "Discover Computing",
    "AI Open",
    "Ai & Society",
    "AI &amp; SOCIETY",
    "Education and Information Technologies : Official Journal of the IFIP technical committee on Education",
    "Social science computer review",
    "Autonomous Intelligent Systems",
    "Journal of Computing and Information Science in Engineering",
    "Applied Computational Intelligence and Soft Computing",
    "Machine Intelligence Research",
    "Applied and Computational Engineering",
    "Secur. Commun. Networks",
    "Service Oriented Computing and Applications",
    "Applied Informatics",
    "Expert Syst. J. Knowl. Eng.",
    "Engineering Reports",
    "Central European Journal of Operations Research",
    "Computer Modeling in Engineering &amp; Sciences",
    "Advances in Production Engineering &amp; Management",
    "Journal of Energy Storage",
    "Ecography",
    "Thin-walled structures",
    "International Journal of Applied Earth Observation and Geoinformation",
    "ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences",
    "Egyptian Journal of Remote Sensing and Space Sciences",
    "Geoscience Frontiers",
    "Science China. Earth Sciences",
    "Ore Geology Reviews",
    "Langenbeck's archives of surgery (Print)",
    "Diagnostic and Interventional Radiology",
    "Diagnostic and Interventional Imaging",
    "Rheumatology Advances in Practice",
    "Microbiology spectrum",
    "Eye",
    "Neurosurgery",
    "Methods",
    "International Journal of Computer Assisted Radiology and Surgery",
    "Journal of Medical Imaging",
    "Journal of Imaging Science and Technology",
    "Philosophical Studies",
    "Police Practice & Research",
    "TechTrends",
    "Aslib Journal of Information Management",
    "Journal of information science",
    "Egyptian Informatics Journal",
    "Virtual Reality & Intelligent Hardware",
}

# Workshop detection patterns
_WORKSHOP_PARENT_PATTERNS = [
    (r"CVPR\s*W", "A*"), (r"ICCV\s*W", "A*"), (r"ECCV\s*W", "A*"),
    (r"NeurIPS.*Workshop", "A*"), (r"ICML.*Workshop", "A*"),
    (r"ACL.*Workshop", "A*"), (r"EMNLP.*Workshop", "A*"),
    (r"MICCAI", "A"), (r"ICASSP\s*W", "A"), (r"WACV\s*W", "A"),
    (r"PerCom\s*Workshop", "A*"),
]

# Italian National Conference on Sensors — frequently appears, it's a C/national conf
_VENUE_NATIONAL_CONF = {
    "Italian National Conference on Sensors",
}


def venue_score(venue_name: str) -> float:
    """
    Return a venue prestige score in [0, 1] based on ICORE 2026 rankings.

    Scoring:
        1.0   — ICORE A* (flagship conferences)
        0.75  — ICORE A conferences + top-tier journals
        0.5   — ICORE B conferences + solid mid-tier journals
        0.25  — ICORE C conferences + lower/general journals + arXiv
        0.125 — arXiv / preprints
        0.0   — Unknown / empty
    """
    if not venue_name or not venue_name.strip():
        return 0.0

    v = venue_name.strip()

    # Exact match: A*
    if v in _VENUE_ASTAR:
        return 1.0

    # Exact match: A conferences
    if v in _VENUE_A:
        return 0.75

    # Exact match: Top journals
    if v in _VENUE_TOP_JOURNAL:
        return 0.75

    # Exact match: B conferences
    if v in _VENUE_B:
        return 0.5

    # Exact match: Mid journals
    if v in _VENUE_MID_JOURNAL:
        return 0.5

    # Workshop at a top conference → 0.5
    for pattern, parent_tier in _WORKSHOP_PARENT_PATTERNS:
        if re.search(pattern, v, re.IGNORECASE):
            return 0.5

    # Workshops in venue name with known parent conferences
    if "Workshop" in v or "WS" in v.split() or "@" in v:
        return 0.375

    # Exact match: C/general journals
    if v in _VENUE_C_JOURNAL:
        return 0.25

    # National conferences
    if v in _VENUE_NATIONAL_CONF:
        return 0.25

    # arXiv / preprints
    if v.lower() in ("arxiv.org", "arxiv", "social science research network", "biorxiv", "medrxiv", "ssrn"):
        return 0.125

    # Heuristic: IEEE conference proceedings (not in lists above)
    if re.match(r"^\d{4}\s+IEEE", v) or "IEEE" in v:
        return 0.25

    # Heuristic: ACM venues not already matched
    if "ACM" in v:
        return 0.375

    # Heuristic: "International Conference" or "International Journal" not matched
    if "International Conference" in v or "International Congress" in v:
        return 0.25
    if "International Journal" in v:
        return 0.25

    # Heuristic: "Findings" (ACL Findings etc.)
    if v == "Findings":
        return 0.625

    # Catch-all for anything with year prefix (usually minor conferences)
    if re.match(r"^\d{4}\s", v):
        return 0.125

    # Unknown venue
    return 0.125


# ═══════════════════════════════════════════════════════════════
# AFFILIATION SCORING
# ═══════════════════════════════════════════════════════════════

# Tier 1: Elite — 4icu.org top-50 + CSRankings top-20 + major industry labs
# Score: 1.0
_AFF_ELITE = [
    # 4icu.org top-50 (world rank)
    "Massachusetts Institute of Technology", "MIT",
    "Harvard University",
    "Stanford University",
    "Cornell University",
    "University of California, Berkeley", "UC Berkeley", "Berkeley",
    "University of Washington",
    "University of Michigan",
    "Columbia University",
    "University of Pennsylvania",
    "University of Oxford", "Oxford",
    "Yale University",
    "University of California, Los Angeles", "UCLA",
    "University of Wisconsin",
    "University of Texas at Austin",
    "University of Minnesota",
    "University of Toronto",
    "Purdue University",
    "University of Cambridge", "Cambridge",
    "University of Chicago",
    "New York University", "NYU",
    "Princeton University",
    "University of California, San Diego", "UCSD",
    "University of Florida",
    "University of Southern California", "USC",
    "University of British Columbia",
    "Carnegie Mellon University", "CMU",
    "Johns Hopkins University",
    "Duke University",
    "University of Illinois Urbana-Champaign", "UIUC", "University of Illinois",
    "University of Maryland",
    "University College London", "UCL",
    "Northwestern University",
    "Georgia Institute of Technology", "Georgia Tech",
    "University of Waterloo",
    "University of Edinburgh",
    "ETH Zurich", "Eidgenössische Technische Hochschule",
    "California Institute of Technology", "Caltech",
    "University of Alberta",
    "McGill University",
    "University of Massachusetts",

    # CSRankings top-20 for CS (2026)
    "Tsinghua University",
    "Shanghai Jiao Tong University",
    "Zhejiang University",
    "Peking University",
    "Nanjing University",
    "National University of Singapore", "NUS",
    "Hong Kong University of Science and Technology", "HKUST",
    "Chinese Academy of Sciences",
    "KAIST", "Korea Advanced Institute",
    "University of Science and Technology of China", "USTC",

    # Major industry research labs
    "Google", "Google Research", "Google Brain", "Google DeepMind", "Google (United States)",
    "DeepMind", "DeepMind (United Kingdom)",
    "Microsoft", "Microsoft Research", "Microsoft (United States)",
    "Meta AI", "Meta", "Facebook AI Research", "FAIR",
    "OpenAI",
    "Apple",
    "Amazon", "Amazon Web Services", "AWS",
    "NVIDIA",
    "IBM Research", "IBM",
    "Anthropic",
]

# Tier 2: Strong — 4icu.org 51-200 + CSRankings 21-50 + known industry
# Score: 0.66
_AFF_STRONG = [
    # 4icu.org 51-200 (selected)
    "University of Pittsburgh",
    "Virginia Tech", "Virginia Polytechnic",
    "University of California, Santa Barbara", "UCSB",
    "University of California, Irvine",
    "University of California, Davis",
    "North Carolina State University",
    "Penn State University", "Pennsylvania State",
    "Boston University",
    "Ohio State University",
    "Arizona State University",
    "Monash University",
    "University of New South Wales",
    "University of Sydney",
    "Brown University",
    "University of Rochester",
    "Simon Fraser University",
    "University of Melbourne",
    "National Taiwan University",
    "Technion",
    "Tel Aviv University",
    "University of Amsterdam",
    "University of Heidelberg",
    "Technical University of Munich", "TU Munich",
    "Ludwig Maximilian University",
    "University of Tokyo",
    "Kyoto University",
    "Seoul National University",
    "University of Manchester",
    "Imperial College London", "Imperial College",
    "King's College London",
    "University of Southampton",
    "University of Glasgow",

    # CSRankings 21-50 for CS
    "Fudan University",
    "Harbin Institute of Technology",
    "Wuhan University",
    "Sun Yat-sen University",
    "Huazhong University of Science and Technology",
    "Beijing University of Posts and Telecommunications",
    "Beihang University",
    "Nanyang Technological University", "NTU",
    "University of Chinese Academy of Sciences",
    "Shandong University",
    "Xi'an Jiaotong University",
    "Southeast University",
    "Northeastern University",
    "Tianjin University",
    "University of Electronic Science and Technology of China",
    "Central South University",
    "Renmin University",
    "Hong Kong Polytechnic University",
    "City University of Hong Kong",
    "Chinese University of Hong Kong",
    "Hong Kong Baptist University",

    # Known industry
    "Huawei", "Huawei Research",
    "Samsung", "Samsung Research",
    "Alibaba", "Alibaba Group", "DAMO Academy",
    "Tencent", "Tencent AI Lab",
    "Baidu", "Baidu Research",
    "ByteDance",
    "JD.com", "JD AI Research",
    "Intel", "Intel Labs",
    "Qualcomm",
    "Adobe", "Adobe Research",
    "Salesforce", "Salesforce Research",
    "Bosch",
    "Siemens",
    "Sony",
    "Toyota Research",
    "Allen Institute for AI", "AI2",
    "Max Planck",
    "INRIA",
]

# Compile into lowercase sets for fuzzy matching
_AFF_ELITE_LOWER = [a.lower() for a in _AFF_ELITE]
_AFF_STRONG_LOWER = [a.lower() for a in _AFF_STRONG]


def _match_affiliation(aff_name: str, reference_list: list) -> bool:
    """Check if an affiliation matches any entry in the reference list (substring)."""
    aff_lower = aff_name.lower().strip()
    if not aff_lower:
        return False
    for ref in reference_list:
        if ref in aff_lower or aff_lower in ref:
            return True
    return False


def affiliation_score_single(aff_name: str) -> float:
    """
    Return an affiliation prestige score in [0, 1] for a single affiliation string.

    Scoring:
        1.0  — Elite (4icu.org top-50, CSRankings top-20, major industry labs)
        0.66 — Strong (4icu.org 51-200, CSRankings 21-50, known industry)
        0.33 — Known (any identifiable institution not in above tiers)
        0.0  — Unknown / empty
    """
    if not aff_name or not aff_name.strip():
        return 0.0

    if _match_affiliation(aff_name, _AFF_ELITE_LOWER):
        return 1.0

    if _match_affiliation(aff_name, _AFF_STRONG_LOWER):
        return 0.66

    # Any non-empty affiliation is at least "known"
    return 0.33


def paper_affiliation_score(paper: dict) -> float:
    """
    Return the max affiliation score across all authors of a paper.

    Uses the max because a paper affiliated with a top institution carries
    that prestige signal regardless of co-authors' affiliations.
    """
    max_score = 0.0
    for author in paper.get("authors", []):
        for aff in author.get("affiliations", []):
            s = affiliation_score_single(aff)
            if s > max_score:
                max_score = s
            if max_score >= 1.0:
                return 1.0
    return max_score


# ═══════════════════════════════════════════════════════════════
# VALIDATION / DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════

def validate_mappings(papers_by_topic: dict):
    """Print coverage statistics for venue and affiliation mappings."""
    from collections import Counter

    venue_tier_counts = Counter()
    aff_tier_counts = Counter()
    unmapped_venues = Counter()

    total_papers = 0
    for topic, papers in papers_by_topic.items():
        for p in papers:
            total_papers += 1
            vs = venue_score(p.get("venue", ""))
            venue_tier_counts[vs] += 1
            if vs <= 0.125:
                v = p.get("venue", "").strip()
                if v and v.lower() != "arxiv.org":
                    unmapped_venues[v] += 1

            a_s = paper_affiliation_score(p)
            aff_tier_counts[a_s] += 1

    print(f"\n{'='*60}")
    print(f"Venue score distribution ({total_papers} papers):")
    for score in sorted(venue_tier_counts.keys(), reverse=True):
        label = {1.0: "A* (flagship)", 0.75: "A / top journal", 0.625: "Findings",
                 0.5: "B / mid journal / top workshop", 0.375: "Other workshop / ACM",
                 0.25: "C / general", 0.125: "arXiv / unknown", 0.0: "Empty"}.get(score, str(score))
        print(f"  {score:.3f} ({label}): {venue_tier_counts[score]}")

    if unmapped_venues:
        print(f"\nUnmapped venues (scored ≤0.125, not arXiv):")
        for v, c in unmapped_venues.most_common(20):
            print(f"  {c:2d}  {v}")

    print(f"\nAffiliation score distribution ({total_papers} papers):")
    for score in sorted(aff_tier_counts.keys(), reverse=True):
        label = {1.0: "Elite", 0.66: "Strong", 0.33: "Known", 0.0: "Unknown"}.get(score, str(score))
        print(f"  {score:.2f} ({label}): {aff_tier_counts[score]}")


if __name__ == "__main__":
    import json
    import os

    papers_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scholar_papers.json")
    with open(papers_file) as f:
        data = json.load(f)
    validate_mappings(data)
