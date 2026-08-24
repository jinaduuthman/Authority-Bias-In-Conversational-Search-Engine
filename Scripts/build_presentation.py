"""
Build a 45-60 minute lab/seminar presentation for the Authority Bias project.

Run:
    source venv/bin/activate
    python3 Scripts/build_presentation.py

Output:
    data/presentation.pptx

The deck is generated entirely from this file so it can be regenerated after
edits. Numbers and structure mirror data/research_paper.md and
data/project_overview.md.
"""

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

TITLE = RGBColor(0x1F, 0x3A, 0x5F)      # navy
BODY = RGBColor(0x2B, 0x2B, 0x2B)       # near-black
SUBTLE = RGBColor(0x6E, 0x6E, 0x6E)     # gray
ACCENT = RGBColor(0xC0, 0x39, 0x2B)     # red accent for headline numbers
GOOD = RGBColor(0x1B, 0x7A, 0x4E)       # green for positive findings
WARN = RGBColor(0xC9, 0x82, 0x0D)       # amber
LIGHT_BG = RGBColor(0xF4, 0xF6, 0xFA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Calibri"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def blank_slide():
    return prs.slides.add_slide(prs.slide_layouts[6])


def textbox(slide, text, left, top, width, height,
            size=18, bold=False, color=BODY, align=PP_ALIGN.LEFT,
            font_name=FONT, italic=False):
    tx = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tx.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font_name
    run.font.color.rgb = color
    return tx


def bullets(slide, items, left, top, width, height, size=18, line_spacing=1.15):
    tx = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tx.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = line_spacing
        p.space_after = Pt(6)
        run = p.add_run()
        run.text = "•  " + item
        run.font.size = Pt(size)
        run.font.name = FONT
        run.font.color.rgb = BODY
    return tx


def slide_title(slide, text, size=30):
    textbox(slide, text, 0.5, 0.3, 12.3, 0.8, size=size, bold=True, color=TITLE)
    # underline rule
    rule = slide.shapes.add_connector(1, Inches(0.5), Inches(1.05), Inches(12.83), Inches(1.05))
    rule.line.color.rgb = TITLE
    rule.line.width = Pt(1.5)


def footer(slide, page_num, total=39):
    textbox(slide, f"Authority Bias in CASE  ·  {page_num}/{total}",
            0.5, 7.05, 12.3, 0.3, size=10, color=SUBTLE)


def table(slide, data, left, top, width, height, header_color=TITLE,
          first_col_bold=True, font_size=14, alt_row=True):
    rows, cols = len(data), len(data[0])
    tbl = slide.shapes.add_table(rows, cols, Inches(left), Inches(top),
                                 Inches(width), Inches(height)).table
    for i, row in enumerate(data):
        for j, cell_text in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = ""
            tf = cell.text_frame
            tf.margin_left = Inches(0.08)
            tf.margin_right = Inches(0.08)
            tf.margin_top = Inches(0.04)
            tf.margin_bottom = Inches(0.04)
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = str(cell_text)
            run.font.size = Pt(font_size)
            run.font.name = FONT
            if i == 0:
                run.font.bold = True
                run.font.color.rgb = WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_color
            else:
                run.font.color.rgb = BODY
                if first_col_bold and j == 0:
                    run.font.bold = True
                if alt_row and i % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = LIGHT_BG
                else:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = WHITE
    return tbl


def big_number(slide, number, label, left, top, width=3.0, height=2.0,
               num_color=ACCENT, num_size=72, label_size=16):
    textbox(slide, number, left, top, width, height * 0.6,
            size=num_size, bold=True, color=num_color, align=PP_ALIGN.CENTER)
    textbox(slide, label, left, top + height * 0.6, width, height * 0.4,
            size=label_size, color=BODY, align=PP_ALIGN.CENTER)


def notes(slide, text):
    """Set speaker notes on a slide.

    Use blank lines in `text` to mark paragraph breaks.
    """
    nt = slide.notes_slide.notes_text_frame
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    nt.clear()
    for i, para in enumerate(paras):
        p = nt.paragraphs[0] if i == 0 else nt.add_paragraph()
        run = p.add_run()
        run.text = para
        run.font.size = Pt(12)
        run.font.name = FONT


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------

def slide_02_agenda():
    s = blank_slide()
    slide_title(s, "Agenda")
    items = [
        "1.  Motivation — LLMs as recommenders, not retrievers",
        "2.  Related work and the causal-identification gap",
        "3.  Research questions",
        "4.  Methodology — content-controlled counterfactual design",
        "5.  Phase 1–4: dataset, signal scoring, weight derivation, conditions",
        "6.  Phase 5: main experiment (5 × 3 × 3 × 250 = 11,148 runs)",
        "7.  Results — RQ1, RQ2, cross-model agreement, topic spread, debiasing",
        "8.  The say-do gap and what it means for auditing",
        "9.  Discussion, implications, limitations",
        "10. Q & A",
    ]
    bullets(s, items, 1.0, 1.5, 11.3, 5.0, size=22, line_spacing=1.4)
    footer(s, 2)


def slide_03_motivation_scenario():
    s = blank_slide()
    slide_title(s, "The motivating scenario")
    textbox(s, "A researcher asks ChatGPT, Perplexity, or Elicit:",
            0.7, 1.4, 12.0, 0.5, size=20, color=BODY)
    quote = s.shapes.add_shape(5, Inches(1.5), Inches(2.0), Inches(10.3), Inches(1.0))
    quote.fill.solid(); quote.fill.fore_color.rgb = LIGHT_BG
    quote.line.color.rgb = TITLE; quote.line.width = Pt(1.0)
    textbox(s, "\u201CWhat are the best recent papers on knowledge distillation?\u201D",
            1.7, 2.15, 9.9, 0.7, size=22, italic=True, bold=True, color=TITLE,
            align=PP_ALIGN.CENTER)
    textbox(s, "The model returns a single recommendation with a justification.",
            0.7, 3.4, 12.0, 0.5, size=18, color=BODY)
    textbox(s, "Who decided that paper was best?",
            0.7, 4.4, 12.0, 0.6, size=24, bold=True, color=ACCENT)
    bullets(s, [
        "Traditional search: user constructs query, evaluates ranked list, picks for themselves.",
        "Conversational LLM search: model evaluates, selects, and articulates reasons.",
        "Substantial evaluation judgment is delegated from researcher to model.",
    ], 1.0, 5.1, 11.3, 1.6, size=16)
    footer(s, 3)


def slide_04_concern():
    s = blank_slide()
    slide_title(s, "The core concern")
    textbox(s, "Assumption underlying the delegation",
            0.7, 1.3, 12.0, 0.5, size=20, bold=True, color=TITLE)
    textbox(s, "LLMs evaluate papers on content relevance — methodology, findings, contribution to the query.",
            0.7, 1.85, 12.0, 0.5, size=18, color=BODY)
    textbox(s, "But web-crawled training corpora interleave content with authority signals:",
            0.7, 2.7, 12.0, 0.5, size=18, color=BODY)
    bullets(s, [
        "Author h-indices and seniority",
        "Institutional affiliations",
        "Venue prestige (NeurIPS, ICLR, JMLR, …)",
        "Citation counts",
    ], 1.5, 3.25, 10.5, 2.0, size=18)
    textbox(s,
            "If the model uses these signals as proxies for quality, prestigious work is favored over relevant work.",
            0.7, 5.55, 12.0, 0.7, size=20, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
    textbox(s,
            "Algaba et al. (2025) already show LLMs reflect — and *amplify* — citation bias when generating references.",
            0.7, 6.3, 12.0, 0.5, size=14, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)
    footer(s, 4)


def slide_05_why_matters():
    s = blank_slide()
    slide_title(s, "Why it matters: equity at scale")
    bullets(s, [
        "Matthew Effect (Merton, 1968): credit accrues to the already-eminent.",
        "Tomkins et al. (2017): single- vs. double-blind peer review demonstrably changes acceptance — author identity matters even to expert humans.",
        "If LLM-mediated discovery amplifies the same dynamic at search scale, it disadvantages emerging researchers, smaller institutions, newer venues.",
        "Beyond fairness: a model-side property that an external actor can also exploit (Generative Engine Optimization).",
    ], 0.7, 1.4, 12.0, 4.5, size=20, line_spacing=1.3)

    box = s.shapes.add_shape(5, Inches(0.7), Inches(5.7), Inches(11.9), Inches(1.2))
    box.fill.solid(); box.fill.fore_color.rgb = LIGHT_BG
    box.line.color.rgb = TITLE; box.line.width = Pt(1.0)
    textbox(s, "Open question: do LLMs *systematically* favor authority over content,\nand if so, can we measure it causally?",
            0.9, 5.85, 11.5, 1.0, size=18, bold=True, color=TITLE, align=PP_ALIGN.CENTER)
    footer(s, 5)


def slide_06_related():
    s = blank_slide()
    slide_title(s, "What we already know about prestige bias in LLMs")
    rows = [
        ["Study", "Task", "What it found", "Limit (for our question)"],
        ["Algaba et al. 2025", "Reference generation", "Heightened citation bias", "Correlational; no metadata manipulation"],
        ["Barolo et al. 2025", "Top-scholar naming", "Favors senior, highly-cited researchers", "People-naming, not paper recommendation"],
        ["Howell et al. 2025", "LLM peer review", "Affiliation drives accept/reject", "Single-dim. prestige; review task"],
        ["Khan et al. 2026", "Multi-domain agents", "Latent venue/source preferences", "Concurrent; no signal decomposition"],
        ["Aggarwal et al. 2024 (GEO)", "Generative engine SEO", "Outsiders can boost visibility", "Manipulability, not intrinsic bias"],
    ]
    table(s, rows, 0.5, 1.4, 12.3, 4.0, font_size=14)
    textbox(s, "Each addresses prestige bias, but none isolates the causal effect of individual authority signals on paper recommendation.",
            0.7, 5.6, 12.0, 0.6, size=18, italic=True, color=ACCENT, align=PP_ALIGN.CENTER)
    footer(s, 6)
    notes(s, """This is the prior-work landscape on prestige bias in LLMs. Each row tackles a different part of the academic pipeline.

Algaba 2025 looks at LLMs generating references when writing — when the model invents citations, does it favor highly-cited work? Yes, with even more bias than humans. But it's correlational; they don't manipulate metadata to test causation.

Barolo 2025 (this is the paper I previously misattributed to Kliegr) asks LLMs to name the top scholars in a field. Open-ended, no candidate list. Finds LLMs name senior, highly-cited people. That's about people, not papers — and there's no content to control for.

Howell 2025 simulates LLM peer review — gives the model a paper, asks for accept/reject. Finds affiliation drives the decision. But it's a single dimension of authority and a review-scoring task, not a recommendation task.

Khan 2026 is concurrent with us — same submission cycle. Multi-domain agentic study showing LLM agents have latent preferences for certain sources, including in research-paper selection. They don't decompose authority into signals or test debiasing.

Aggarwal 2024 — GEO — is the external threat model: how content creators game generative search. We address the complementary question: what does the system bring intrinsically, before any manipulation?

Bottom line: each piece touches part of the elephant. None isolates which authority signals matter, in the recommendation task, with content held constant.""")


def slide_07_gap():
    s = blank_slide()
    slide_title(s, "The gap we address")
    textbox(s, "Three things missing from prior work — taken together:",
            0.7, 1.3, 12.0, 0.5, size=20, bold=True, color=TITLE)
    bullets(s, [
        "Causal identification.  Correlational studies cannot rule out content–authority confounds (better-known papers also tend to be more relevant, more discoverable).",
        "Signal decomposition.  Authority is not one thing — venue, h-index, citations, affiliation may carry different weight. Prior work tests one dimension or treats them as a bundle.",
        "Mitigation evaluation.  Whether prompt-level debiasing actually changes behavior (not just language) is largely untested for prestige bias.",
    ], 0.7, 2.0, 12.0, 4.0, size=18, line_spacing=1.3)

    box = s.shapes.add_shape(5, Inches(0.7), Inches(6.0), Inches(11.9), Inches(0.9))
    box.fill.solid(); box.fill.fore_color.rgb = LIGHT_BG
    box.line.color.rgb = TITLE; box.line.width = Pt(1.0)
    textbox(s, "Our contribution: a content-controlled counterfactual + empirical signal decomposition + RQ-driven debiasing test.",
            0.9, 6.1, 11.5, 0.7, size=18, bold=True, color=TITLE, align=PP_ALIGN.CENTER)
    footer(s, 7)
    notes(s, """Three things are missing from prior work, and they are missing together.

First, causal identification. Without manipulation you cannot separate authority from confounded content. Better-known papers tend also to be more relevant, more discoverable, with more descriptive titles. Pure observation cannot tell you which property is doing the work. We need the experiment-based audit-study tradition, not correlational analysis.

Second, signal decomposition. Authority is not one thing. There are at least five distinct prestige signals — venue, h-index of the median author, h-index of the strongest author, citation count, and institutional affiliation — and they may carry very different weight. Prior work either picks one (Howell on affiliation) or treats them as a bundle. We need to measure each separately to know where the leverage is.

Third, mitigation evaluation. Once you know bias exists, the practitioner question is: what do I do about it? Prompt engineering is the cheapest possible intervention. We need a controlled test of whether it actually moves behavior — not just language.

Putting these together is what makes our experiment unique. Audit-study methodology gives causal identification. The 1:N flip pilot decomposes the signals empirically. The instruction variants test mitigation. All three live inside one factorial design.""")


def slide_08_rqs():
    s = blank_slide()
    slide_title(s, "Research questions")
    rows = [
        ["", "Question", "Operationalized as"],
        ["RQ1", "Do LLM CASE systems exhibit authority bias?", "Flip rate under metadata manipulation"],
        ["1.1", "Is there a dose-response relationship?", "Tier preference; boosted-pick lift vs chance"],
        ["1.2", "Do models differ in susceptibility?", "Per-model flip + boost rates; χ² homogeneity"],
        ["RQ2", "When picks change, do they move toward higher authority?", "Directional rate vs 50/50 (binomial)"],
        ["RQ3", "Can prompt-level debiasing mitigate bias?", "Mild + strong instructions; McNemar"],
    ]
    table(s, rows, 0.5, 1.4, 12.3, 4.5, font_size=16)
    textbox(s, "All three reported in §5 of the paper. We also test whether *language* and *behavior* move together — the say-do gap.",
            0.7, 6.2, 12.0, 0.5, size=14, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)
    footer(s, 8)


def slide_09_approach():
    s = blank_slide()
    slide_title(s, "Approach: content-controlled counterfactual")
    textbox(s, "Borrowed from labor-market audit studies (Bertrand & Mullainathan, 2004) and the LLM counterfactual-bias framework (Huang et al., 2025).",
            0.7, 1.3, 12.0, 0.6, size=16, italic=True, color=SUBTLE)

    # Three-card visual
    cards = [
        ("Original",  "Authentic metadata\nas published",          TITLE),
        ("Flipped",   "Authority metadata\nswapped: high \u2194 low", ACCENT),
        ("Boosted",   "Mid-tier paper given\nelite metadata",        WARN),
    ]
    for i, (name, desc, col) in enumerate(cards):
        x = 0.6 + i * 4.3
        box = s.shapes.add_shape(5, Inches(x), Inches(2.3), Inches(4.0), Inches(2.4))
        box.fill.solid(); box.fill.fore_color.rgb = LIGHT_BG
        box.line.color.rgb = col; box.line.width = Pt(2.5)
        textbox(s, name, x, 2.45, 4.0, 0.6, size=22, bold=True, color=col, align=PP_ALIGN.CENTER)
        textbox(s, desc, x, 3.15, 4.0, 1.4, size=16, color=BODY, align=PP_ALIGN.CENTER)

    textbox(s, "Title and abstract are byte-identical across the three conditions.",
            0.7, 5.0, 12.0, 0.5, size=18, bold=True, color=GOOD, align=PP_ALIGN.CENTER)
    textbox(s, "If the model's recommendation changes, the change is attributable to authority signals — by construction.",
            0.7, 5.55, 12.0, 0.5, size=16, color=BODY, align=PP_ALIGN.CENTER)
    footer(s, 9)


def slide_10_dataset():
    s = blank_slide()
    slide_title(s, "Phase 1 — Dataset")
    bullets(s, [
        "1,250 papers across 25 CS research topics (Knowledge Distillation, Prompt Engineering, LLM Alignment, GANs, …)",
        "50 papers/topic, 2018–2026.  Stratified sampling: 15 high-citation / 15 mid / 10 low / 10 emerging.",
        "Sources: Semantic Scholar API + OpenAlex (DOI-matched affiliation backfill).",
        "Titles + abstracts used verbatim — no paraphrase, no rewrite — eliminates language-model rewriting as a confound.",
    ], 0.7, 1.4, 12.0, 3.5, size=18)
    # Stats row
    big_number(s, "1,250", "papers",       0.7, 5.2, 3.0, 1.6, num_size=48)
    big_number(s, "25",    "CS topics",    3.9, 5.2, 3.0, 1.6, num_size=48)
    big_number(s, "10/q",  "candidates",   7.1, 5.2, 3.0, 1.6, num_size=48)
    big_number(s, "250",   "queries",     10.3, 5.2, 3.0, 1.6, num_size=48)
    footer(s, 10)


def slide_11_signals():
    s = blank_slide()
    slide_title(s, "Phase 2 — Five authority signals")
    rows = [
        ["Signal", "Definition", "Source"],
        ["Venue prestige (v)",       "ICORE 2026 ranking; A* = 1.0, A = 0.85, B = 0.65, C = 0.45, arXiv = 0.15", "ICORE 2026"],
        ["Median author h-index (h̃)", "Robust to author count (vs. mean)",                                       "Semantic Scholar"],
        ["Max author h-index (h_max)", "Star-author effect",                                                       "Semantic Scholar"],
        ["Citation count (s)",        "Raw paper citations",                                                      "Semantic Scholar"],
        ["Affiliation prestige (a)",  "4icu.org top-200 + CSRankings + curated industry-lab tiers",               "4icu / CSRankings"],
    ]
    table(s, rows, 0.5, 1.4, 12.3, 4.0, font_size=14)
    textbox(s, "Each signal is min-max normalized within its research topic before being combined — authority is *relative to field*, not absolute.",
            0.7, 5.7, 12.0, 0.6, size=16, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)
    footer(s, 11)


def slide_12_pilot_design():
    s = blank_slide()
    slide_title(s, "Phase 3 — 1:N flip pilot to derive empirical weights")
    bullets(s, [
        "Question:  *which* signals matter, and *how much*?",
        "Method:  fix a paper's content (title + abstract); dress it in each of the 10 candidates' metadata in turn.",
        "5 topics × 10 queries × 10 metadata variants × 3 models = 15,000 runs.",
        "Logistic regression with z-standardized predictors (Hosmer & Lemeshow 2000; Menard 2004).",
        "Cross-validated with dominance analysis (Budescu 1993; Azen & Budescu 2003) — 31 subset models per predictor.",
        "VIF diagnostics: all < 5, no problematic multicollinearity (O'Brien 2007).",
    ], 0.7, 1.4, 12.0, 4.5, size=18, line_spacing=1.3)
    box = s.shapes.add_shape(5, Inches(0.7), Inches(6.0), Inches(11.9), Inches(0.9))
    box.fill.solid(); box.fill.fore_color.rgb = LIGHT_BG
    box.line.color.rgb = TITLE; box.line.width = Pt(1.0)
    textbox(s, "Final weights = mean of standardized-coefficient and dominance-analysis weights, normalized to sum to 1.",
            0.9, 6.1, 11.5, 0.7, size=16, bold=True, color=TITLE, align=PP_ALIGN.CENTER)
    footer(s, 12)
    notes(s, """This is where the empirical weights come from. Rather than picking weights ad-hoc — which is what prior work did — we let the model tell us which signals matter.

We picked five topics for the pilot — Knowledge Distillation, Attention Mechanisms, Federated Learning, Image Generation, Sentiment Analysis. They span the susceptibility spectrum we eventually find in the main experiment, so the weights aren't biased by an unusual choice of topic.

The 1:N construction: for each query in those topics we have 10 candidate papers. We pick one paper, fix its content (title and abstract), and dress it in each of the 10 candidates' metadata. Same content, ten metadata profiles. So each "trial" is a binary outcome — given metadata profile X on this content, was the paper recommended? That gives us the input to a regression: predict the binary outcome from the five authority signals.

Three models for the pilot keeps cost down — Gemma 2, Llama 3.1, Mistral. Multi-model is important so the weights aren't an artifact of one model.

The next slide explains the analysis pipeline — logistic regression, why standardization, VIF, and dominance analysis. I want to give those a real treatment because the weights drive the rest of the experiment.""")


def slide_12b_method_details():
    s = blank_slide()
    slide_title(s, "Phase 3 — Why these statistical tools?")

    # Top: the regression equation
    textbox(s, "P(recommended = 1) = \u03c3(\u03b2\u2080 + \u03b2\u2081\u00b7max_h + \u03b2\u2082\u00b7median_h + \u03b2\u2083\u00b7citations + \u03b2\u2084\u00b7venue + \u03b2\u2085\u00b7affiliation)",
            0.5, 1.4, 12.3, 0.6, size=16, bold=True, color=TITLE, align=PP_ALIGN.CENTER)
    textbox(s, "All predictors are z-standardized before fitting.",
            0.5, 2.0, 12.3, 0.4, size=13, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)

    # Four explanation cards
    cards = [
        ("Z-standardize",
         "Predictors are on different scales: h-index \u2208 [0, 100+], citations \u2208 [0, 10k+], venue \u2208 [0, 1].\n\nZ-scoring (subtract mean, divide by SD) puts everything on the same scale, so the magnitudes of \u03b2 are directly comparable across signals."),
        ("Logistic regression",
         "Outcome is binary (picked / not picked). Linear regression on a binary outcome violates assumptions.\n\nLogit handles bounded outcomes, gives interpretable log-odds, and is the textbook choice (Hosmer & Lemeshow 2000; Menard 2004 for standardized \u03b2 as importance)."),
        ("VIF check",
         "Five authority signals are correlated (e.g., max_h and median_h).\n\nVariance Inflation Factor flags collinearity that would inflate standard errors.\n\nRule of thumb VIF < 5; we get VIF < 5 across all five (O'Brien 2007). Coefficients are not over-attributed."),
        ("Dominance analysis",
         "Standardized \u03b2 alone is contested for \"importance\".\n\nDominance (Budescu 1993; Azen & Budescu 2003) refits the model on every subset of predictors (31 subsets for 5 vars) and averages each predictor's marginal R\u00b2 contribution.\n\nWe trust the weights because both methods agree on rank order."),
    ]
    card_w, card_h = 6.0, 2.0
    for i, (title_text, body_text) in enumerate(cards):
        col = i % 2
        row = i // 2
        x = 0.4 + col * 6.4
        y = 2.6 + row * 2.15
        box = s.shapes.add_shape(5, Inches(x), Inches(y), Inches(card_w), Inches(card_h))
        box.fill.solid(); box.fill.fore_color.rgb = LIGHT_BG
        box.line.color.rgb = TITLE; box.line.width = Pt(1.2)
        textbox(s, title_text, x + 0.15, y + 0.1, card_w - 0.3, 0.4,
                size=15, bold=True, color=TITLE)
        textbox(s, body_text, x + 0.15, y + 0.55, card_w - 0.3, card_h - 0.6,
                size=11, color=BODY)

    textbox(s, "McFadden pseudo-R\u00b2 \u2248 3.3% — small but expected: content (abstract) carries most of the signal; metadata carries the rest.",
            0.5, 6.85, 12.3, 0.4, size=12, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)
    footer(s, 13)
    notes(s, """This slide unpacks the four statistical decisions behind the pilot weights — each is non-obvious and worth defending in a question.

Standardization first. The raw signals are on wildly different scales. h-index is integer-valued in [0, 100+]. Citation count is right-skewed in [0, 10000+]. Venue is bounded in [0, 1]. Affiliation is also [0, 1]. Without z-scoring, the coefficient on citations would be tiny just because the variable is so large, and the venue coefficient would look big just because the variable is small. After z-scoring, every variable has mean zero and SD one, so coefficient magnitudes are directly comparable.

Logistic regression. Our outcome is binary — was paper i recommended on this run, yes or no. Linear regression on a binary outcome violates assumptions: predictions can fall outside [0, 1] and residuals are not normally distributed. Logit handles bounded outcomes naturally and gives us interpretable log-odds. We use Hosmer & Lemeshow's textbook formulation. Menard 2004 is the reference for using standardized betas as the importance measure.

VIF — variance inflation factor. With five correlated signals (max_h and median_h obviously correlate; venue and citations correlate), we need to check that no two are so collinear that the regression cannot tell their effects apart. The rule of thumb is VIF below 5. We get VIF below 5 across all five predictors. So the regression is not over-attributing one signal because of correlation with another. O'Brien 2007 is the reference for the threshold.

Dominance analysis. Even with z-scored coefficients, attributing "importance" to predictors in a multiple regression is contested in the methodology literature. Dominance analysis — Budescu 1993, formalized in Azen & Budescu 2003 — does a full model-comparison procedure. For every subset of predictors, fit the model, compute pseudo-R-squared. Then attribute each predictor's importance as its average marginal R-squared contribution across all subsets it appears in. With 5 variables that's 31 subset models per predictor. The point is: this is a different method from standardized betas. They converge on the same ranking, which is why we trust the weights.

Final note on McFadden pseudo R-squared of about 3.3%. Audit reviewers sometimes ask why this is so low. It's expected — the abstract carries most of the signal for whether a paper is "relevant", and metadata is a secondary influence. Bertrand & Mullainathan's hiring discrimination audit got effect sizes of 2 to 5 percent. We're in the same neighborhood. The point of the pilot is not to predict picks well from metadata alone; it's to recover the relative ordering of the metadata signals, which is what the regression and dominance methods give us.""")


def slide_13_pilot_weights():
    s = blank_slide()
    slide_title(s, "Phase 3 result — empirical signal weights")
    rows = [
        ["Component", "Weight", "Interpretation"],
        ["Venue prestige",  "0.353", "Strongest single signal"],
        ["Median h-index",  "0.292", "Team-level author quality"],
        ["Max h-index",     "0.187", "Star author effect"],
        ["Citations",       "0.137", "Paper impact"],
        ["Affiliation",     "0.031", "Near-zero after controls"],
    ]
    table(s, rows, 1.0, 1.5, 7.5, 3.5, font_size=18)

    textbox(s, "Headline", 9.0, 1.5, 3.6, 0.5, size=20, bold=True, color=TITLE)
    bullets(s, [
        "Venue dominates.",
        "Author h-index, taken as a construct (median + max = 0.479), is collectively the strongest.",
        "Affiliation is essentially zero — challenges a common assumption.",
        "Rank ordering is *stable* across both methods and all model subsets.",
    ], 9.0, 2.0, 3.6, 4.0, size=14, line_spacing=1.25)

    textbox(s, "These weights drive every downstream condition.",
            0.7, 6.2, 12.0, 0.5, size=16, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)
    footer(s, 14)


def slide_14_conditions():
    s = blank_slide()
    slide_title(s, "Phase 4 — Three experimental conditions")
    rows = [
        ["Condition", "Manipulation", "Tests"],
        ["Original", "Authentic metadata", "Baseline preference"],
        ["Flipped",  "Authority metadata swapped between high \u2194 low tier papers (within topic)", "Whether models follow metadata over content"],
        ["Boosted",  "Mid-tier paper inflated: h-index 50–80, 3–5\u00d7 citations, elite venue + affiliation", "Whether models are attracted to inflated prestige"],
    ]
    table(s, rows, 0.5, 1.4, 12.3, 3.5, font_size=15)
    textbox(s, "Same 10 candidates, same content, same query, same instruction — only metadata changes.\nAny recommendation change is attributable to authority signals, not content.",
            0.7, 5.3, 12.0, 1.2, size=18, bold=True, color=GOOD, align=PP_ALIGN.CENTER)
    footer(s, 15)


def slide_15_models():
    s = blank_slide()
    slide_title(s, "Phase 5 — Five open-weight LLMs (locally via Ollama)")
    rows = [
        ["Model", "Size", "Developer", "Origin"],
        ["Llama 3.1:8b",    "8B", "Meta",        "United States"],
        ["Mistral:7b",      "7B", "Mistral AI",  "France"],
        ["Gemma 2:9b",      "9B", "Google",      "United States"],
        ["Qwen 2.5:7b",     "7B", "Alibaba",     "China"],
        ["DeepSeek-R1:8b",  "8B", "DeepSeek",    "China"],
    ]
    table(s, rows, 1.5, 1.5, 10.3, 3.5, font_size=16)
    bullets(s, [
        "Roster spans 5 orgs, 3 architecture families, 3 training-origin geographies — diversity is by design.",
        "Same parameter range (7–9B) keeps cohort comparable.",
        "Ollama default Q4 quantization, default decoding (no temperature override) — what a practitioner actually gets.",
    ], 0.7, 5.4, 12.0, 1.6, size=14, line_spacing=1.3)
    footer(s, 16)


def slide_16_instructions():
    s = blank_slide()
    slide_title(s, "Phase 5 — Three instruction variants")
    rows = [
        ["Variant", "Strategy", "Key instruction"],
        ["Baseline",       "Neutral",          "\u201CRecommend the TOP 1 paper that best addresses the query.\u201D"],
        ["Anti-Authority", "Mild debiasing",   "\u201CDo NOT consider author fame, institution prestige, h-index, or citation counts.\u201D"],
        ["Content-First",  "Strong debiasing", "\u201CCRITICAL: Ignore all prestige signals. Evaluate SOLELY based on the abstract content.\u201D"],
    ]
    table(s, rows, 0.5, 1.4, 12.3, 3.0, font_size=14)
    textbox(s, "Design lineage", 0.7, 4.7, 12.0, 0.5, size=18, bold=True, color=TITLE)
    bullets(s, [
        "Listwise top-1 selection follows Sun et al. 2023 (ChatGPT for ranking).",
        "Mild → strong escalation pattern follows Tamkin et al. 2023 and Ganguli et al. 2023 (demographic / stereotype debiasing).",
        "Wording is ours — there is no canonical authority-bias debiasing prompt yet.",
    ], 0.7, 5.2, 12.0, 1.8, size=14, line_spacing=1.3)
    footer(s, 17)


def slide_17_matrix():
    s = blank_slide()
    slide_title(s, "Phase 5 — The experiment matrix")

    # Row 1: 5 x 3 x 3 x 10 queries-per-topic
    big_number(s, "5",   "models",         0.5, 1.5, 2.2, 1.4, num_size=56)
    textbox(s, "\u00d7", 2.7, 1.75, 0.6, 1.0, size=44, color=SUBTLE, align=PP_ALIGN.CENTER)
    big_number(s, "3",   "instructions",   3.3, 1.5, 2.2, 1.4, num_size=56)
    textbox(s, "\u00d7", 5.5, 1.75, 0.6, 1.0, size=44, color=SUBTLE, align=PP_ALIGN.CENTER)
    big_number(s, "3",   "conditions",     6.1, 1.5, 2.2, 1.4, num_size=56)
    textbox(s, "\u00d7", 8.3, 1.75, 0.6, 1.0, size=44, color=SUBTLE, align=PP_ALIGN.CENTER)
    big_number(s, "10",  "queries\nper topic", 8.9, 1.5, 2.6, 1.4, num_size=56, label_size=14)

    # Row 2: x 25 topics  =  11,250 scheduled
    textbox(s, "\u00d7  25 topics  =  11,250 scheduled runs   \u2192   11,148 parsed (99.9%)",
            0.5, 3.5, 12.3, 0.7, size=22, bold=True, color=TITLE, align=PP_ALIGN.CENTER)
    textbox(s, "(250 unique queries total  ·  750 candidate sets  ·  one stateless prompt per cell)",
            0.5, 4.2, 12.3, 0.4, size=14, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)

    bullets(s, [
        "Position randomized once per query with a fixed seed; held constant across the three conditions.",
        "Stateless: every cell is a cold prompt — no in-context contamination across cells.",
        "Sequential, single-host execution — total wall-clock 49.9 hours.",
    ], 0.7, 4.9, 12.0, 1.9, size=14, line_spacing=1.3)
    footer(s, 18)
    notes(s, """The matrix is fully crossed: every model sees every instruction crossed with every condition crossed with every query. So the unit of analysis is a (model, instruction, condition, query) cell — that's 5 \u00d7 3 \u00d7 3 \u00d7 250 = 11,250 cells.

I broke the queries out as "10 queries per topic \u00d7 25 topics" because that's where they come from. We have 25 CS research topics; we wrote 10 queries for each, giving 250 unique queries total. Topic structure matters later when we look at topic-level susceptibility (slide 25).

Each query has 3 candidate sets — one per condition (original, flipped, boosted) — so 250 \u00d7 3 = 750 candidate sets in total. Each candidate set is shown to 5 models under 3 instructions = 15 cells. 15 \u00d7 750 = 11,250 cells.

Position randomization is important. We shuffle the order of the 10 candidates within a query once, with a fixed seed, then keep that order constant across the three conditions. So position is held identical when comparing original-vs-flipped-vs-boosted — any pick change cannot be driven by candidate ordering, only metadata.

Stateless execution: every cell is a fresh prompt. There's no shared context window between cells, so no information leakage. This matters because some recent agentic studies allow the LLM to see prior decisions; we deliberately don't.

99.9% successful parsing — only 102 cells failed parsing across 11,250 attempts. That's the wall-clock cost of running everything sequentially through Ollama on a single host for about 50 hours.""")


def slide_18_rq1_headline():
    s = blank_slide()
    slide_title(s, "RQ1 — Authority bias is real and substantial")
    rows = [
        ["Manipulation", "Pairs", "Changed", "Rate", "95% CI"],
        ["Flipped", "3,690", "1,772", "48.0%", "[46.4, 49.6]"],
        ["Boosted", "3,683", "992",   "26.9%", "[25.5, 28.4]"],
    ]
    table(s, rows, 1.5, 1.5, 10.3, 1.6, font_size=18)

    big_number(s, "48.0%", "of recs change\nunder swap",     0.7, 3.6, 4.0, 2.4, num_color=ACCENT, num_size=64, label_size=18)
    big_number(s, "26.9%", "of recs change\nunder inflation", 4.7, 3.6, 4.0, 2.4, num_color=WARN,   num_size=64, label_size=18)
    big_number(s, "21.1pp", "gap\n(\u03c7\u00b2=348.85, p<.001)", 8.7, 3.6, 4.0, 2.4, num_color=TITLE, num_size=52, label_size=16)

    textbox(s, "Same content, same query, same instruction — almost half the time the model picks differently when only the metadata changes.",
            0.7, 6.3, 12.0, 0.5, size=14, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)
    footer(s, 19)


def slide_19_rq2_direction():
    s = blank_slide()
    slide_title(s, "RQ2 — Bias is directional under inflation")
    rows = [
        ["Manipulation", "Flips", "\u2192 Higher", "%", "p"],
        ["Flipped", "1,772", "731", "41.3%", "<0.001"],
        ["Boosted", "992",   "691", "69.7%", "<0.001"],
    ]
    table(s, rows, 1.5, 1.5, 10.3, 1.6, font_size=18)

    bullets(s, [
        "Flipped:  metadata is *bilaterally* scrambled (high gets low's, low gets high's). The directional signal washes out — flips disperse across candidates.",
        "Boosted:  *one* paper is dressed in elite metadata. 69.7% of flips concentrate on it — direct evidence of authority attraction.",
        "Per-model:  Gemma 2 flips rarely under boosted (14.0%), but when it does, 74.3% move toward higher authority. Resistance and directional sensitivity are independent dimensions.",
    ], 0.7, 3.5, 12.0, 3.4, size=16, line_spacing=1.3)
    footer(s, 20)


def slide_20_per_model():
    s = blank_slide()
    slide_title(s, "Sub-RQ1.2 — Models differ 2.1\u00d7 in susceptibility")
    rows = [
        ["Model", "Flip", "Boost", "Susceptibility"],
        ["Gemma 2:9b",    "33.2%", "14.0%", "23.6%"],
        ["Mistral:7b",    "49.7%", "22.0%", "35.9%"],
        ["DeepSeek-R1:8b", "41.9%", "35.4%", "38.7%"],
        ["Qwen 2.5:7b",   "51.6%", "28.8%", "40.2%"],
        ["Llama 3.1:8b",  "63.2%", "35.2%", "49.2%"],
    ]
    table(s, rows, 1.0, 1.5, 7.0, 3.5, font_size=15)

    textbox(s, "What differs is the *route* to bias", 8.3, 1.5, 4.5, 0.5, size=18, bold=True, color=TITLE)
    bullets(s, [
        "Gemma 2:  resistant on both swaps and inflation.",
        "Llama 3.1:  high on both — the most biased.",
        "Mistral:  moderate-high flip, low boost (sensitive to swaps, not inflation).",
        "DeepSeek-R1:  moderate flip, *high* boost (specifically attracted to inflated prestige).",
    ], 8.3, 2.0, 4.5, 4.0, size=12, line_spacing=1.25)

    textbox(s, "\u03c7\u00b2 = 150.37, p < 0.001 — non-overlapping CIs.",
            0.7, 6.3, 12.0, 0.5, size=14, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)
    footer(s, 21)


def slide_21_cross_model_agreement():
    s = blank_slide()
    slide_title(s, "Cross-model agreement — do the five models behave alike?")

    # Compact definitions strip (two boxes side-by-side)
    def_box1 = s.shapes.add_shape(5, Inches(0.4), Inches(1.25), Inches(6.2), Inches(0.95))
    def_box1.fill.solid(); def_box1.fill.fore_color.rgb = LIGHT_BG
    def_box1.line.color.rgb = SUBTLE; def_box1.line.width = Pt(0.75)
    textbox(s, "Mean agreement", 0.55, 1.3, 6.0, 0.35, size=12, bold=True, color=TITLE)
    textbox(s, "= average raw match across all 10 model pairs (\u2075C\u2082).  Each cell yields 5 outcomes; pairs match or don't.",
            0.55, 1.65, 6.0, 0.55, size=10, color=BODY)

    def_box2 = s.shapes.add_shape(5, Inches(6.75), Inches(1.25), Inches(6.2), Inches(0.95))
    def_box2.fill.solid(); def_box2.fill.fore_color.rgb = LIGHT_BG
    def_box2.line.color.rgb = SUBTLE; def_box2.line.width = Pt(0.75)
    textbox(s, "Cohen's \u03ba  (chance-corrected agreement)", 6.9, 1.3, 6.0, 0.35, size=12, bold=True, color=TITLE)
    textbox(s, "0 = chance  ·  0.0\u20130.2 slight  ·  0.2\u20130.4 fair  ·  0.4\u20130.6 moderate  ·  0.6+ substantial  (Landis & Koch 1977)",
            6.9, 1.65, 6.0, 0.55, size=10, color=BODY)

    rows = [
        ["Quantity", "Mean Agree.", "Cohen's \u03ba", "Range"],
        ["Selection (same paper picked)",       "45.8%", "—",     "40.8%–50.7%"],
        ["Flip together under flipped",          "60.0%", "0.206", "0.163–0.256"],
        ["Flip together under boosted",          "63.4%", "0.077", "\u22120.019–0.130"],
    ]
    table(s, rows, 0.5, 2.4, 12.3, 1.85, font_size=14)

    # Verdict row — three colored cards
    verdict_y = 4.5
    verdict_h = 1.85
    cards = [
        (GOOD,   "\u2713 Selection",      "45.8%",        "vs. 10% chance",       "STRONG agreement\non baseline content picks"),
        (WARN,   "~ Flip sensitivity",   "\u03ba = 0.206", "fair",                  "MODEST shared signal\u2014\nsame queries trigger flips"),
        (ACCENT, "\u2717 Boost attraction", "\u03ba = 0.077", "essentially chance",  "NO shared signal\u2014\nattraction is model-specific"),
    ]
    for i, (col, label, big, small, body) in enumerate(cards):
        x = 0.4 + i * 4.32
        w = 4.12
        box = s.shapes.add_shape(5, Inches(x), Inches(verdict_y), Inches(w), Inches(verdict_h))
        box.fill.solid(); box.fill.fore_color.rgb = LIGHT_BG
        box.line.color.rgb = col; box.line.width = Pt(2.5)
        textbox(s, label, x + 0.1, verdict_y + 0.08, w - 0.2, 0.4, size=14, bold=True, color=col)
        textbox(s, big, x + 0.1, verdict_y + 0.45, w - 0.2, 0.6, size=26, bold=True, color=col, align=PP_ALIGN.CENTER)
        textbox(s, small, x + 0.1, verdict_y + 1.05, w - 0.2, 0.3, size=11, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)
        textbox(s, body, x + 0.1, verdict_y + 1.35, w - 0.2, 0.5, size=12, color=BODY, align=PP_ALIGN.CENTER)

    textbox(s,
            "Verdict: shared on selection, partial on flip, idiosyncratic on boost.  One pair sits below chance under boosted: Gemma 2 \u00d7 Mistral, \u03ba = \u22120.019.  Full pairwise matrix in appendix.",
            0.4, 6.5, 12.5, 0.5, size=13, italic=True, color=TITLE, align=PP_ALIGN.CENTER)
    footer(s, 22)
    notes(s, """The slide answers a single yes/no question: do the five models behave alike? The answer is "depends what you mean."

How the numbers are computed. Every (query, condition, instruction) cell yields 5 outcomes \u2014 one per model. For selection: which paper did each model pick? Five labels per cell. For flip: did each model change its pick from baseline? Five binary outcomes per cell. For each pair of models we compute the fraction of cells they agree on, then average over all 10 pairs (5 choose 2). That's mean pairwise agreement. The "Range" column is the min and max across those 10 pairs.

Why Cohen's kappa. Raw agreement is misleading when both models do the same thing a lot independently. If model A flips 50% of the time and model B flips 50% of the time and they're statistically independent, you'd still see 50% raw agreement just by coincidence. Kappa subtracts the chance baseline. Landis & Koch (1977) is the standard interpretation: 0\u20130.2 slight, 0.2\u20130.4 fair, 0.4\u20130.6 moderate, 0.6+ substantial. We don't compute kappa for selection because picks are 10-class, not binary; raw agreement at 45.8% versus a 10% chance baseline is itself the verdict.

Three verdicts on the slide.

Selection (green): models substantially agree on which paper looks "best" before any manipulation. 45.8% raw, well above the 10% chance level. The center of the distribution is shared across models; what differs is the margin.

Flip sensitivity (amber): kappa 0.206, fair. Models tend to flip on the same queries more often than chance, but only modestly. Some queries are universally authority-sensitive across models; others trigger only some models. There's a partial shared structure here, consistent with a common training-data signal that flags certain query-content pairings as authority-relevant.

Boost attraction (red): kappa 0.077, essentially chance. Which paper grabs a model under inflation is model-specific. One pair of models is even slightly negative \u2014 they actively disagree above chance.

What this implies for the experiment overall. The bias is partly shared and partly idiosyncratic, and these two parts have different causes. The shared part is in pretraining \u2014 all five models have absorbed the same lexical-quality associations from the web. The idiosyncratic part is in post-training (alignment, instruction tuning, RLHF) \u2014 each model's individual pipeline determines what kind of inflation appeals to it.

Practical implication. A prompt-level intervention that targets the shared signal might cut flip rates uniformly across models. But boost behavior is model-specific, so a single prompt can't address it; you'd need either model-specific debiasing or training-level interventions. This is exactly what we observe in slide 25 \u2014 prompts cut flip much more than boost.""")
    notes(s, """Cross-model agreement asks: do these five LLMs respond the same way to the same query?

How we computed it. For every (query, condition, instruction) cell we have 5 binary "did this model flip?" outcomes, one per model. Then for each pair of models we compute agreement — the fraction of cells on which both models give the same outcome — and average those across all 10 pairs (5 choose 2 = 10).

Mean pairwise agreement of 60% under flipped means: pick any two models, on average they agree 60% of the time on whether a given cell flips. That sounds high, but a random-coincidence baseline is also high because both models flip a lot — that's why we report Cohen's kappa.

Cohen's kappa corrects for chance. If both models flip 50% of the time independently, you'd expect 50% raw agreement just by coincidence. Kappa subtracts that out. Standard interpretation (Landis & Koch 1977): kappa around 0–0.2 = slight; 0.2–0.4 = fair; 0.4–0.6 = moderate; 0.6+ = substantial.

Under flipped, kappa = 0.206 — slight to fair. It's not zero — models tend to flip on the same queries more often than chance — but it's not high either. There is a shared signal but it's modest.

Under boosted, kappa = 0.077 — essentially chance. One pair of models is even slightly negative. Which paper attracts a model under inflation is largely model-specific.

Implication. Swap sensitivity reflects something the models share — likely a common training-data signal that flags certain query-condition combinations as authority-relevant. Boost-attraction reflects per-model decision idiosyncrasies. This matters for mitigation: a prompt-level intervention that targets the shared signal might cut flip rates uniformly, but boost behavior is model-specific, so a one-size-fits-all prompt won't work — which is exactly what we see in slide 25.

Also note: selection agreement (45.8%) is much higher than chance (10% if random over 10 candidates). On most queries the models broadly agree on which paper looks "best" content-wise. The disagreement is at the margin, not the center.""")


def slide_22_dose_response():
    s = blank_slide()
    slide_title(s, "Sub-RQ1.1 — Dose-response and tier preference")
    rows = [
        ["Tier",      "Share", "Original", "Flipped", "Boosted"],
        ["Top",       "30%",   "56.1%",    "30.4%",   "51.8%"],
        ["Mid",       "30%",   "20.1%",    "30.6%",   "22.5%"],
        ["Low",       "20%",   "10.4%",    "21.9%",   "10.6%"],
        ["Emerging",  "20%",   "13.4%",    "17.1%",   "15.1%"],
    ]
    table(s, rows, 0.5, 1.5, 12.3, 2.5, font_size=16)

    bullets(s, [
        "Original:  top-tier dominates at 56.1% despite being only 30% of candidates — strong baseline preference.",
        "Flipped:  the gradient flattens — top falls to 30.4%, low more than doubles to 21.9%.",
        "Boosted lift:  boosted papers picked at 28.9% vs. 25.6% expected by chance (1.13\u00d7, p = 3 \u00d7 10\u207b\u2076).",
        "Per-model lift varies from 1.43\u00d7 (Qwen 2.5) to 0.97\u00d7 (Gemma 2 — *below* random chance).",
    ], 0.7, 4.3, 12.0, 2.7, size=16, line_spacing=1.3)
    footer(s, 23)
    notes(s, """Dose-response asks: as authority signal strength goes up, does pick probability go up? Answer: yes, sharply.

Look at the Original column first. Top-tier papers — defined by the empirical authority score from the pilot — get 56.1% of all picks while making up only 30% of candidates. That's nearly 2\u00d7 over-representation, with no manipulation at all. The hierarchy is steep before we touch anything.

Under flipping, top-tier preference drops to 30.4% — almost exactly its candidate share. Low-tier picks more than double, from 10.4% to 21.9%. The hierarchy flattens. So when you scramble the metadata, the model loses its preferential treatment of top-tier papers. This is the strongest evidence that the original 56.1% is not just "top-tier papers are also more relevant"; if it were, scrambling metadata wouldn't move it. It does move it, dramatically.

Under boosting, the picture is asymmetric. Top-tier share dips slightly to 51.8% — only mid-tier papers wearing inflated metadata are competing. Mid-tier rises 2.4 pp. Low and emerging barely change.

The key statistic at the bottom: boosted papers picked at 28.9% versus 25.6% expected by chance — a 1.13\u00d7 lift, p = 3 \u00d7 10\u207b\u2076. Why is the chance baseline 25.6%? Because boosted papers come from mid-tier, which is 30% of the pool, but only one mid-tier paper gets boosted per query, so the prior is computed accordingly.

Per-model variation: Qwen 2.5 has 1.43\u00d7 lift (40% over chance); Gemma 2 has 0.97\u00d7, which is actually below chance. The most-resistant model isn't just unmoved by inflation — it's slightly suspicious of it.

Why binomial here? Because the question is "is the boost-pick rate different from a known reference?" Single proportion vs prior — that's a binomial test (Wilson 1927 for the CI). We use chi-squared elsewhere when comparing distributions across categories (e.g., flip rate vs boost rate, or homogeneity across the five models). Mann-Whitney for ordinal flip-rate spreads. McNemar for paired before-after instruction comparisons. Different question, different test — all reported in the statistical-summary table in the paper.""")


def slide_23_topic_variation():
    s = blank_slide()
    slide_title(s, "Topic-level variation — a 49.5pp spread")
    rows_left = [
        ["Most susceptible", "Flip", "Boost"],
        ["Text Summarization",     "67.3%", "32.2%"],
        ["Image Generation",       "63.3%", "21.8%"],
        ["Fairness in ML",         "59.9%", "32.9%"],
        ["Knowledge Distillation", "59.3%", "34.5%"],
        ["Time Series Forecasting","56.4%", "23.7%"],
    ]
    rows_right = [
        ["Least susceptible",        "Flip", "Boost"],
        ["Self-Supervised Learning",  "39.9%", "20.1%"],
        ["GANs",                      "37.7%", "38.6%"],
        ["Machine Translation",       "35.6%", "19.6%"],
        ["LLM Alignment",             "31.8%", "29.7%"],
        ["Attention Mechanisms",      "17.8%", "17.7%"],
    ]
    table(s, rows_left,  0.4, 1.5, 6.2, 3.0, font_size=13)
    table(s, rows_right, 6.7, 1.5, 6.2, 3.0, font_size=13)

    bullets(s, [
        "Llama 3.1 hits 86.7% flip on Image Generation — nearly 9 in 10 picks switch.",
        "Mistral hits 0.0% on Attention Mechanisms — never changes its pick.",
        "Conjecture (\u00a76): topic concentration of authority signals in training data drives the spread — fields dominated by a few labs offer a sharper authority gradient.",
        "Implication: bias audits should disaggregate by research area; corpus-wide rates hide per-topic reality.",
    ], 0.7, 4.7, 12.0, 2.3, size=14, line_spacing=1.3)
    footer(s, 24)


def slide_24_debiasing():
    s = blank_slide()
    slide_title(s, "RQ3 — Prompts help on swaps, barely on inflation")
    rows = [
        ["Instruction",     "Flip Rate", "\u0394 flip", "Boost Rate", "\u0394 boost", "McNemar p"],
        ["Baseline",        "55.9%", "—",        "27.8%", "—",         "—"],
        ["Anti-Authority",  "49.8%", "\u22126.0pp",  "24.7%", "\u22123.1pp",   "<0.001"],
        ["Content-First",   "38.3%", "\u221217.6pp", "24.7%", "\u22123.1pp",   "<0.001"],
    ]
    table(s, rows, 0.4, 1.5, 12.5, 1.9, font_size=15)

    # Two side-by-side panels: flip story (left), boost story (right)
    # Left panel: flip — large reductions
    box_l = s.shapes.add_shape(5, Inches(0.4), Inches(3.7), Inches(6.1), Inches(2.6))
    box_l.fill.solid(); box_l.fill.fore_color.rgb = LIGHT_BG
    box_l.line.color.rgb = GOOD; box_l.line.width = Pt(2.0)
    textbox(s, "Flip:  prompts work", 0.5, 3.8, 5.9, 0.5, size=16, bold=True, color=GOOD)
    textbox(s, "\u221217.6pp", 0.5, 4.3, 5.9, 1.0, size=44, bold=True, color=GOOD, align=PP_ALIGN.CENTER)
    textbox(s, "max reduction (content-first)\u2003\u2003residual flip 38.3%",
            0.5, 5.4, 5.9, 0.4, size=12, color=BODY, align=PP_ALIGN.CENTER)
    textbox(s, "(Mistral *worsens* +2.0pp under mild prompt — not all models cooperate)",
            0.5, 5.85, 5.9, 0.4, size=11, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)

    # Right panel: boost — tiny reduction
    box_r = s.shapes.add_shape(5, Inches(6.7), Inches(3.7), Inches(6.1), Inches(2.6))
    box_r.fill.solid(); box_r.fill.fore_color.rgb = LIGHT_BG
    box_r.line.color.rgb = WARN; box_r.line.width = Pt(2.0)
    textbox(s, "Boost:  prompts barely move it", 6.8, 3.8, 5.9, 0.5, size=16, bold=True, color=WARN)
    textbox(s, "\u22123.1pp", 6.8, 4.3, 5.9, 1.0, size=44, bold=True, color=WARN, align=PP_ALIGN.CENTER)
    textbox(s, "aggregate boost reduction (5.7\u00d7 smaller than flip)",
            6.8, 5.4, 5.9, 0.4, size=12, color=BODY, align=PP_ALIGN.CENTER)
    textbox(s, "(Llama 3.1 \u22120.4pp, DeepSeek-R1 \u22121.2pp \u2014 essentially zero)",
            6.8, 5.85, 5.9, 0.4, size=11, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)

    textbox(s, "Real-world prestige inflation (citation gaming, venue jumping) is structurally \u201Cboosted.\u201D Prompts won't fix it.",
            0.4, 6.5, 12.5, 0.5, size=14, italic=True, color=ACCENT, align=PP_ALIGN.CENTER)
    footer(s, 25)
    notes(s, """The story on this slide has two halves and they tell opposite things — that's the whole point.

Left side, flip rate. Baseline flip rate is 55.9% — over half of recommendations change when authority metadata is swapped. Mild debiasing (anti-authority) brings it to 49.8%, a 6 pp drop. Strong debiasing (content-first) brings it to 38.3%, a 17.6 pp drop. McNemar test on the matched pairs is highly significant in both cases. So prompt-level debiasing genuinely moves behavior on swap-style manipulation. Important caveat: Mistral actually worsens 2 pp under the mild prompt — adding the rule "don't consider citations" makes it more, not less, prestige-attentive. We think this is a known LLM phenomenon where partial instructions cue the very thing they prohibit. The strong content-first prompt overcomes this for Mistral.

Right side, boost rate. Same instructions, same models. Aggregate boost rate goes from 27.8% baseline to 24.7% under both anti-authority and content-first — only a 3.1 pp reduction, and it doesn't get any better with the stronger prompt. That's 5.7 times smaller than the flip reduction. Per-model is even more striking: Llama 3.1 boost rate moves only −0.4 pp, DeepSeek-R1 only −1.2 pp. Essentially flat.

Why the asymmetry? Flipping is a bilateral disturbance — both ends of the candidate list are perturbed and you see net displacement. Boosting is a unilateral lure — one paper is dressed up to look elite, and the model is asked to pick from a list it can't tell is "real" or not. Telling the model "don't consider citations" doesn't help when the inflated paper looks legitimate by every visible metric. The only signal that distinguishes a boosted paper from a real elite paper is provenance, which the model doesn't have access to.

Why this matters for the real world: GEO and C-SEO threats — citation gaming, venue jumping, fake-h-index inflation — are structurally analogous to "boosted" in our taxonomy. Our finding is that the cheapest available defense (a prompt) doesn't work against this attack. Architectural or training-level interventions are needed.""")


def slide_25_say_do():
    s = blank_slide()
    slide_title(s, "The say-do gap")
    rows = [
        ["Instruction",     "Authority Mention", "Flip Rate", "\u0394 mention", "\u0394 flip"],
        ["Baseline",        "37.2%", "55.9%", "—",        "—"],
        ["Anti-Authority",  "18.0%", "49.8%", "\u221219.2pp", "\u22126.0pp"],
        ["Content-First",   "8.2%",  "38.3%", "\u221229.0pp", "\u221217.6pp"],
    ]
    table(s, rows, 0.7, 1.5, 11.9, 2.2, font_size=16)

    big_number(s, "\u221229.0pp", "drop in what\nthe model says", 1.0, 4.0, 3.5, 2.2, num_color=GOOD,   num_size=44, label_size=16)
    big_number(s, "\u221217.6pp", "drop in what\nthe model does", 4.9, 4.0, 3.5, 2.2, num_color=WARN,   num_size=44, label_size=16)
    big_number(s, "11.4pp",       "gap = implicit\nauthority bias", 8.8, 4.0, 3.5, 2.2, num_color=ACCENT, num_size=44, label_size=16)

    textbox(s,
            "Surface-level auditing of LLM outputs (\u201Cdid the justification mention citations?\u201D) underestimates true bias by ~40%.",
            0.7, 6.4, 12.0, 0.7, size=16, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)
    footer(s, 26)
    notes(s, """This is the most consequential finding of the paper for practitioners.

We measured two things in parallel for every cell:
  - Behavior — does the model flip its pick when authority is manipulated?
  - Language — does the model's free-text justification mention any authority-related term ("highly cited", "leading institution", "well-known author", etc.)?

If the debiasing prompt is genuinely working, both should drop together.

Baseline: 37.2% of justifications mention authority terms; 55.9% flip rate. Both high, as expected with no debiasing instruction.

Anti-Authority (mild): mentions drop 19.2 pp to 18.0%; flips drop only 6.0 pp to 49.8%. Already a 13 pp gap between language-change and behavior-change.

Content-First (strong): mentions drop 29.0 pp to 8.2%; flips drop only 17.6 pp to 38.3%. The gap widens to 11.4 pp.

What this means. Under strong debiasing, models are roughly 4.5\u00d7 less likely to *mention* authority (37% \u2192 8%), but only 31% less likely to *act* on it (56% \u2192 38%). The language change is much larger than the behavior change.

This is implicit bias. The model has learned at the surface generation layer to comply with "don't talk about citations." But the upstream selection mechanism — what cues it weights when deciding which paper to pick — is comparatively untouched. RLHF and instruction tuning act mostly on what the model says, not on the latent decision logic that determined which paper to pick before language production began.

For auditing this is critical. If you only check the LLM's outputs for prestige references, you'd think a content-first prompt has nearly eliminated bias (8.2% mentions). But behavior is still 38.3% biased — over 4\u00d7 higher than the language signal would suggest. Surface auditing systematically *under*estimates true bias.

This is why we argue prompt-level debiasing is not enough. You need behavioral evaluation — actually manipulate the metadata and measure whether picks change. You probably also need architectural or training-level interventions, because the surface generation layer has different machinery from the underlying scoring layer.

Connect to the next two slides: slide 27 shows what models do say in justifications (mostly indirect — "highly cited", not "venue"); slide 28 explains why venue dominates behavior despite being almost never named. The same say-do gap pattern appears at the signal level.""")


def slide_26_justification_patterns():
    s = blank_slide()
    slide_title(s, "What models actually say in their justifications")
    rows = [
        ["Pattern", "% of mentions"],
        ["Citations (\u201Chighly cited\u201D, citation count)",   "42.4%"],
        ["Impact (\u201Cimpactful\u201D, \u201Csignificant\u201D)", "29.0%"],
        ["Recency (\u201Crecent\u201D, \u201Clatest\u201D)",         "12.5%"],
        ["Author prestige (\u201Cfamous\u201D, \u201Cwell-known\u201D)", "10.8%"],
        ["Credibility, h-index, venue, institution",                  "<2% each"],
    ]
    table(s, rows, 1.5, 1.5, 10.3, 3.0, font_size=15)

    bullets(s, [
        "Specific signals (h-index, venue, institution) are almost never named — bias is expressed through *indirect* language (\u201Chighly cited\u201D, \u201Cimpactful\u201D).",
        "Recency is the third-largest pattern — \u201Cthis is the most recent study\u201D used as a quality proxy.",
        "Per-model: Llama 3.1 mentions authority 34.6% of the time, Gemma 2 only 11.0% — mention rate tracks behavioral susceptibility.",
        "\u2192 Foreshadow: venue is mentioned <2% of the time \u2014 yet venue is the strongest *behavioral* driver (slide 28). Same say-do gap, at the signal level.",
    ], 0.7, 4.8, 12.0, 2.2, size=13, line_spacing=1.3)
    footer(s, 27)
    notes(s, """This slide cracks open the say-do gap by signal type. When justifications do mention authority, what do they actually say?

42% of mentions are about citations — "highly cited", "frequently cited", "citation count". This is the most lexically explicit pattern.

29% are about general impact or significance — "impactful", "significant contribution", "influential" — which gestures at authority without naming a specific signal.

12.5% are about recency — "this is the most recent" used as a stand-in for quality. Important because recency is partially confounded with authority in our design (top-tier papers tend to be a mix of high-citation older and less-cited recent), and we flag this as a limitation.

10.8% are about author prestige in indirect terms — "famous", "well-known author" — without naming the h-index.

Then everything else — credibility, h-index by name, venue by name, institution by name — is each under 2%. So bias is *expressed* almost entirely through indirect proxies, not by naming the underlying signal.

The crucial setup for the next slide. Recall from the pilot that venue has the *highest* behavioral weight (0.353). Yet venue is named in less than 2% of justifications. That looks contradictory, but it's actually the same say-do gap pattern at the signal level: models *use* venue heavily as a decision signal but rarely *verbalize* venue as the reason. They use it tacitly.

Per-model: Llama 3.1 mentions authority 34.6% of the time and is also the most behaviorally biased (49.2% susceptibility); Gemma 2 mentions authority only 11.0% and is the most resistant (23.6%). Mention rate tracks behavioral susceptibility — they're not independent — but mention rate underestimates behavioral susceptibility in absolute level, which is the say-do gap quantitatively.""")


def slide_27_discussion_venue():
    s = blank_slide()
    slide_title(s, "Why venue dominates — and is barely named")

    # Reconciliation banner at top
    banner = s.shapes.add_shape(5, Inches(0.4), Inches(1.3), Inches(12.5), Inches(1.0))
    banner.fill.solid(); banner.fill.fore_color.rgb = LIGHT_BG
    banner.line.color.rgb = ACCENT; banner.line.width = Pt(2.0)
    textbox(s, "Apparent contradiction:  venue weight = 0.353 (highest)  vs.  venue mentioned in <2% of justifications.",
            0.5, 1.4, 12.3, 0.4, size=15, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
    textbox(s, "Resolution: this *is* the say-do gap, expressed at the signal level. Models *use* venue without *naming* it.",
            0.5, 1.85, 12.3, 0.4, size=14, italic=True, color=TITLE, align=PP_ALIGN.CENTER)

    bullets(s, [
        "Surface property:  venue names are short, high-frequency proper-noun tokens (\u201CNeurIPS\u201D, \u201CICLR\u201D, \u201CNature\u201D) that co-occur explicitly with quality judgments throughout academic web text — a strong, easily-pattern-matched signal.",
        "h-indices and citation counts are raw numeric tokens \u2014 plausibly weaker discriminators than distinctive proper nouns. They are mentioned *more* in justifications, but weighted *less* in decisions.",
        "Affiliation is a long-tail signal \u2014 thousands of institutions, low per-institution training signal \u2014 explains its near-zero weight despite being commonly assumed to drive prestige bias.",
        "Why models don't name venue: instruction-tuning teaches surface compliance (\u201Cdon't sound elitist\u201D); venue is the most prestige-associated lexical class, so it's most aggressively suppressed in language. Behavior is untouched.",
        "Echoes Tomkins et al. (2017): venue/author identity affects human peer review too. We extend this finding from human reviewers to LLM-based recommenders \u2014 with the LLM-specific twist that the bias is implicit, not endorsed.",
    ], 0.5, 2.5, 12.5, 3.7, size=14, line_spacing=1.3)

    box = s.shapes.add_shape(5, Inches(0.4), Inches(6.3), Inches(12.5), Inches(0.7))
    box.fill.solid(); box.fill.fore_color.rgb = TITLE
    box.line.fill.background()
    textbox(s, "Practical takeaway:  debiasing must target how LLMs *process* venue, not (just) what they *say* about authority.",
            0.5, 6.4, 12.3, 0.6, size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    footer(s, 28)
    notes(s, """The user / reviewer question raised on this slide is exactly right and worth addressing directly: aren't slides 27 and 28 contradictory? On 27 we said venue is mentioned in less than 2% of justifications. On 28 we say venue has the highest pilot weight at 0.353. How can both be true?

They're not contradictory. They're the same phenomenon — the say-do gap — expressed at the signal level rather than the aggregate level.

Aggregate say-do gap (slide 26): under content-first prompts, models drop authority *mentions* by 29 pp but only drop authority-*driven flips* by 17.6 pp. They say less than they do.

Signal-level say-do gap (this slide): venue is the dominant *behavioral* driver but is rarely *named*. The model picks the NeurIPS paper but justifies its choice with "the methodology is more thorough" — never "because it's at NeurIPS." Same pattern, finer grain.

Why does this make sense mechanically?

Venue tokens — "NeurIPS", "ICLR", "ACL", "Nature" — are short, distinctive proper nouns. In training data they appear repeatedly alongside explicit quality judgments: "the seminal NeurIPS paper", "as published in Nature." These co-occurrences create strong lexical-quality associations. So the model has learned to use venue as a quality cue, automatically and unconsciously.

But the same distinctiveness makes venue the *easiest* signal for instruction tuning to suppress in *language*. "Don't sound elitist about journals" is easy to learn at the surface level — flag any venue token, replace with neutral phrasing. So when asked to justify, the model substitutes paraphrases ("widely recognized", "established work") that gesture at authority without naming venue.

Numeric signals (h-index, citation count) work the opposite way. They're weaker discriminators in the latent decision (lots of papers have similar numbers, the gradient is shallower) but they're more often quoted verbatim because they have less prestige loading lexically. So mentions of citations are 42% of authority mentions but the underlying behavioral weight of citations is only 0.137 — the second-lowest signal.

Affiliation is the long-tail story: thousands of institutions in training corpora, each with low per-institution signal. So the model has not built strong associations to most affiliations, and the empirical weight is essentially zero (0.031). This is interesting because most popular discussion of LLM "elitism" assumes affiliation is the driver. Our data says it's not — it's venue.

Practical takeaway. If you want to debias an LLM-based recommender, the levers are: (1) data-side — deduplicate or down-weight venue-quality co-occurrences in training corpora; (2) inference-side — withhold venue metadata at decision time; (3) RLHF-side — use counterfactual venue pairs in preference learning. Surface prompts that say "don't consider venue" don't move behavior on this signal because the association is upstream of language production.""")


def slide_28_implications():
    s = blank_slide()
    slide_title(s, "Implications")
    bullets(s, [
        "Researchers:  LLM-based discovery favors established work; emerging researchers and lower-ranked venues are systematically under-recommended.",
        "Model developers:  bias is baked in; prompt-level debiasing leaves a 38.3% residual. Architectural / training-level interventions are needed.",
        "Auditors:  surface-level audits miss the say-do gap. Need behavioral, not rhetorical, evaluation.",
        "System designers:  model selection matters \u2014 Gemma 2 \u00d7 content-first cuts bias in half. Operational lever.",
        "Policy:  affiliation-based regulation misses the dominant signal; venue-side interventions are higher-leverage.",
        "Equity:  the same property an external actor can exploit (GEO / C-SEO) is the property the model brings intrinsically. Defense is unified.",
    ], 0.7, 1.4, 12.0, 5.5, size=17, line_spacing=1.3)
    footer(s, 29)


def slide_29_limitations():
    s = blank_slide()
    slide_title(s, "Limitations and next steps")
    textbox(s, "Limitations", 0.7, 1.3, 6.0, 0.5, size=20, bold=True, color=TITLE)
    bullets(s, [
        "7\u20139B open-weight only \u2014 70B+ and proprietary (GPT-4, Claude) untested.",
        "Top-1 recommendation \u2014 ranked-list fairness untested.",
        "Hand-crafted queries \u2014 not real search logs.",
        "No RAG retrieval stage \u2014 candidates given directly.",
        "One-shot static manipulation \u2014 multi-turn dynamics untested.",
        "CS-only domain \u2014 medicine, social sciences may differ.",
        "Citation-age confound \u2014 recency partially conflated with authority.",
    ], 0.7, 1.85, 6.0, 5.0, size=14, line_spacing=1.25)

    textbox(s, "Next steps", 7.0, 1.3, 6.0, 0.5, size=20, bold=True, color=TITLE)
    bullets(s, [
        "Larger models (70B, frontier proprietary).",
        "Domain replication: medicine, social sciences, humanities.",
        "Top-k ranking and ranked-list fairness metrics.",
        "RAG-pipeline integration: how does retrieval bias compose with model bias?",
        "Mechanistic study: which layers carry the venue signal?",
        "Training-time interventions \u2014 data deduplication on prestige cues, RLHF on counterfactual pairs.",
    ], 7.0, 1.85, 6.0, 5.0, size=14, line_spacing=1.25)
    footer(s, 30)


def slide_30_conclusion():
    s = blank_slide()
    slide_title(s, "Conclusion")
    bullets(s, [
        "A controlled causal study of authority bias in LLM-based academic paper recommendation \u2014 not just correlation.",
        "48.0% of recommendations change when only authority metadata changes; 69.7% of inflation flips move toward higher prestige.",
        "Susceptibility varies 2.1\u00d7 across architectures; topic vulnerability spans 49.5pp; debiasing helps but leaves substantial residual bias.",
        "A say-do gap \u2014 instructions reshape language more than behavior.",
        "Venue prestige, not institutional affiliation, is the dominant authority signal.",
        "Implications: epistemic authority should be treated as a protected axis in LLM fairness auditing.",
    ], 0.7, 1.4, 12.0, 4.5, size=18, line_spacing=1.3)

    box = s.shapes.add_shape(5, Inches(0.7), Inches(6.0), Inches(11.9), Inches(0.9))
    box.fill.solid(); box.fill.fore_color.rgb = TITLE
    box.line.fill.background()
    textbox(s, "All code, prompts, candidate sets, and 11,148 model responses will be released for full reproducibility.",
            0.9, 6.15, 11.5, 0.6, size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    footer(s, 31)


def slide_31_qa():
    s = blank_slide()
    band = s.shapes.add_shape(1, Inches(0), Inches(2.5), SW, Inches(2.5))
    band.fill.solid(); band.fill.fore_color.rgb = TITLE
    band.line.fill.background()

    textbox(s, "Thank you", 0.5, 2.8, 12.3, 1.2, size=72, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    textbox(s, "Questions, critiques, ideas?", 0.5, 4.1, 12.3, 0.6, size=24, italic=True, color=WHITE, align=PP_ALIGN.CENTER)
    textbox(s, "[ Your email ]    \u00b7    [ Project repo (anonymous link) ]",
            0.5, 5.4, 12.3, 0.5, size=18, color=BODY, align=PP_ALIGN.CENTER)
    footer(s, 32)


def slide_33_appendix_agreement():
    s = blank_slide()
    slide_title(s, "Appendix \u2014 Pairwise cross-model agreement")
    textbox(s, "All values computed across all (query, condition, instruction) cells.  Diagonals omitted.  Model abbreviations: DS = DeepSeek-R1:8b, Gem = Gemma 2:9b, Lla = Llama 3.1:8b, Mis = Mistral:7b, Qwn = Qwen 2.5:7b.",
            0.4, 1.2, 12.5, 0.55, size=11, italic=True, color=SUBTLE)

    abbrev = ["", "DS", "Gem", "Lla", "Mis", "Qwn"]

    # ---- Table 1: Selection agreement (raw %) ----
    sel_data = [
        abbrev,
        ["DS",  "—",     "50.7%", "40.8%", "43.1%", "45.6%"],
        ["Gem", "50.7%", "—",     "48.3%", "46.7%", "47.6%"],
        ["Lla", "40.8%", "48.3%", "—",     "47.0%", "42.1%"],
        ["Mis", "43.1%", "46.7%", "47.0%", "—",     "45.6%"],
        ["Qwn", "45.6%", "47.6%", "42.1%", "45.6%", "—"],
    ]
    textbox(s, "(A) Selection agreement \u2014 same paper picked",
            0.4, 1.85, 4.1, 0.4, size=12, bold=True, color=TITLE)
    textbox(s, "Mean: 45.8%   ·   Range: 40.8\u201350.7%",
            0.4, 2.25, 4.1, 0.3, size=10, italic=True, color=SUBTLE)
    table(s, sel_data, 0.4, 2.6, 4.1, 3.6, font_size=10, first_col_bold=True)

    # ---- Table 2: Flip kappa (flipped condition) ----
    flip_data = [
        abbrev,
        ["DS",  "—",      "0.213",  "0.170",  "0.163",  "0.205"],
        ["Gem", "0.213",  "—",      "0.238",  "0.183",  "0.256"],
        ["Lla", "0.170",  "0.238",  "—",      "0.225",  "0.207"],
        ["Mis", "0.163",  "0.183",  "0.225",  "—",      "0.195"],
        ["Qwn", "0.205",  "0.256",  "0.207",  "0.195",  "—"],
    ]
    textbox(s, "(B) Cohen's \u03ba \u2014 flip together under FLIPPED",
            4.65, 1.85, 4.1, 0.4, size=12, bold=True, color=TITLE)
    textbox(s, "Mean: 0.206  (fair)  ·  Range: 0.163\u20130.256",
            4.65, 2.25, 4.1, 0.3, size=10, italic=True, color=SUBTLE)
    table(s, flip_data, 4.65, 2.6, 4.1, 3.6, font_size=10, first_col_bold=True)

    # ---- Table 3: Boost kappa (boosted condition) ----
    boost_data = [
        abbrev,
        ["DS",  "—",       "0.047",  "0.057",  "0.110",  "0.130"],
        ["Gem", "0.047",   "—",      "0.061",  "\u22120.019",  "0.075"],
        ["Lla", "0.057",   "0.061",  "—",      "0.102",  "0.079"],
        ["Mis", "0.110",   "\u22120.019",  "0.102",  "—",      "0.129"],
        ["Qwn", "0.130",   "0.075",  "0.079",  "0.129",  "—"],
    ]
    textbox(s, "(C) Cohen's \u03ba \u2014 flip together under BOOSTED",
            8.9, 1.85, 4.1, 0.4, size=12, bold=True, color=TITLE)
    textbox(s, "Mean: 0.077  (chance)  ·  Range: \u22120.019\u20130.130",
            8.9, 2.25, 4.1, 0.3, size=10, italic=True, color=SUBTLE)
    boost_tbl = table(s, boost_data, 8.9, 2.6, 4.1, 3.6, font_size=10, first_col_bold=True)

    # Highlight the two negative-kappa cells (Gem x Mis, Mis x Gem)
    # tbl rows are 0 = header; data rows start at 1
    # Gem row index = 2; Mis col index = 4
    # Mis row index = 4; Gem col index = 2
    for (r, c) in [(2, 4), (4, 2)]:
        cell = boost_tbl.cell(r, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(0xFD, 0xE2, 0xDC)  # light red highlight
        # re-bold the value for emphasis
        for p in cell.text_frame.paragraphs:
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = ACCENT

    # Bottom annotation strip
    box = s.shapes.add_shape(5, Inches(0.4), Inches(6.4), Inches(12.5), Inches(0.7))
    box.fill.solid(); box.fill.fore_color.rgb = LIGHT_BG
    box.line.color.rgb = ACCENT; box.line.width = Pt(1.0)
    textbox(s, "Highlighted: Gemma 2 \u00d7 Mistral pair under boosted, \u03ba = \u22120.019.  Both models have low boost rates (14.0% / 22.0%) but are triggered by different inflated papers \u2014 similar resistance, non-overlapping triggers.",
            0.55, 6.45, 12.2, 0.6, size=11, italic=True, color=BODY, align=PP_ALIGN.CENTER)

    footer(s, 33)
    notes(s, """Backup slide A1. Use this if a reviewer asks for the full pairwise breakdown behind the slide-22 verdict, or specifically about which model pair drives the negative kappa under boosted.

Three matrices, all computed pairwise across the five models, all symmetric:

(A) Selection agreement: raw fraction of cells where two models pick the same paper. No chance correction because picks are 10-class \u2014 raw 45.8% versus 10% chance is itself the verdict. Highest pair: DeepSeek-R1 \u00d7 Gemma 2 at 50.7%. Lowest: DeepSeek-R1 \u00d7 Llama 3.1 at 40.8%.

(B) Cohen's kappa under flipped: chance-corrected pairwise agreement on whether each model flipped on each cell. All 10 pairs are positive, ranging 0.163 (Mistral \u00d7 DeepSeek-R1) to 0.256 (Qwen 2.5 \u00d7 Gemma 2). Mean 0.206, fair on the Landis-Koch scale. Models tend to flip on the same queries more often than chance.

(C) Cohen's kappa under boosted: same construction, but kappas drop into the slight-to-near-zero range. Highest pair: Qwen 2.5 \u00d7 DeepSeek-R1 at 0.130; lowest: Gemma 2 \u00d7 Mistral at \u22120.019 (highlighted, light red). The two below-chance cells in the matrix are this single pair, appearing on both sides of the diagonal.

Why Gemma 2 \u00d7 Mistral specifically. Both have low boost rates: Gemma 2 at 14.0% (most resistant overall), Mistral at 22.0%. When two models both flip rarely under a manipulation, raw agreement is mechanically high (most cells are "neither flipped"). Kappa subtracts that out and asks: of the cells where one of them flipped, did the other also flip? For this pair, the answer is "no, slightly fewer than chance." They have similar resistance overall but non-overlapping decision criteria for what an inflated paper has to look like to fool them. The numerical value is statistically indistinguishable from zero, so the substantive interpretation is "essentially independent," not "actively anti-correlated."

Implication. Boost-attraction is highly model-specific: even two models with similar low susceptibility levels are triggered by different boosted papers. This is what makes one-size-fits-all prompt-level mitigation ineffective for boost (slide 25).""")


def slide_34_appendix_per_model_rates():
    s = blank_slide()
    slide_title(s, "Appendix A2 \u2014 Per-model flip and boost rates")
    textbox(s, "Backs slide 21.  All rates with Wilson 95% CIs.  Aggregate \u03c7\u00b2 across models = 150.37, p < 0.001 (homogeneity rejected).",
            0.4, 1.2, 12.5, 0.5, size=12, italic=True, color=SUBTLE)

    rows = [
        ["Model", "Flip rate", "95% CI", "Boost rate", "95% CI", "Susceptibility"],
        ["Gemma 2:9b",     "33.2%", "[29.9, 36.7]", "14.0%", "[11.7, 16.7]", "23.6%  (least)"],
        ["Mistral:7b",     "49.7%", "[46.2, 53.3]", "22.0%", "[19.2, 25.1]", "35.9%"],
        ["DeepSeek-R1:8b", "41.9%", "[38.3, 45.6]", "35.4%", "[31.9, 39.1]", "38.7%"],
        ["Qwen 2.5:7b",    "51.6%", "[48.0, 55.2]", "28.8%", "[25.7, 32.1]", "40.2%"],
        ["Llama 3.1:8b",   "63.2%", "[59.7, 66.6]", "35.2%", "[31.9, 38.7]", "49.2%  (most)"],
    ]
    table(s, rows, 0.4, 1.85, 12.5, 2.6, font_size=14, first_col_bold=True)

    textbox(s, "Two profiles, same susceptibility tier", 0.4, 4.7, 12.5, 0.4, size=14, bold=True, color=TITLE)
    bullets(s, [
        "DeepSeek-R1 (38.7%) and Llama 3.1 (49.2%) reach susceptibility through different routes \u2014 DeepSeek-R1 is mid on flip but high on boost; Llama 3.1 is high on both.",
        "Mistral (35.9%) and DeepSeek-R1 (38.7%) sit at similar overall susceptibility but Mistral is flip-dominant (49.7% vs 22.0%) while DeepSeek-R1 is boost-balanced (41.9% / 35.4%).",
        "Gemma 2 \u00d7 Llama 3.1 CIs are completely non-overlapping on both flip and boost \u2014 the 25.6 pp susceptibility gap is robust, not noise.",
        "Susceptibility = mean of flip rate and boost rate.  Reported because the two manipulations probe different channels and a single number summarises the average exposure.",
    ], 0.4, 5.1, 12.5, 1.9, size=13, line_spacing=1.3)

    footer(s, 34)
    notes(s, """Backup A2. Per-model flip and boost rates with confidence intervals \u2014 the granular version of slide 21.

Use this slide if asked: "is the susceptibility difference real or just noise?" Confidence intervals for Gemma 2 and Llama 3.1 don't overlap on either column, so the gap is robust. Chi-squared on the homogeneity hypothesis is 150.37, p < 0.001.

The two-profiles point is the most defensible thing to say from this table. DeepSeek-R1 and Llama 3.1 have similar overall susceptibility (39% and 49%) but get there via different mechanisms: DeepSeek-R1 is moderate on metadata swap (42%) but high on inflation (35%); Llama 3.1 is sky-high on both. So average susceptibility hides the underlying mechanism. Mistral is the mirror: high on swap (50%) but low on inflation (22%). This is why we report both flip and boost rates rather than collapsing into a single bias number \u2014 a model can be biased two different ways.

Gemma 2 stands out as the most resistant on both axes. Why is a question for slide 21's speaker notes \u2014 likely a combination of training data composition and post-training that makes it unusually conservative.

Wilson confidence intervals (Wilson 1927) used because they have correct coverage at proportions near 0 and 1 and don't require the normal approximation. n=750 per cell so intervals are tight \u2014 about \u00b13 pp.""")


def slide_35_appendix_directional():
    s = blank_slide()
    slide_title(s, "Appendix A3 \u2014 Per-model directional flip rates")
    textbox(s, "Backs slide 20.  Of the picks that did flip, what fraction moved toward higher authority?  Binomial test against H\u2080 = 50%; aggregate p < 0.001 in both panels.",
            0.4, 1.2, 12.5, 0.5, size=12, italic=True, color=SUBTLE)

    # Two side-by-side tables
    flipped_rows = [
        ["Model", "Total flips", "\u2192 Higher", "% Higher"],
        ["DeepSeek-R1:8b", "289", "140", "48.4%"],
        ["Gemma 2:9b",     "249", "86",  "34.5%"],
        ["Llama 3.1:8b",   "474", "187", "39.5%"],
        ["Mistral:7b",     "373", "153", "41.0%"],
        ["Qwen 2.5:7b",    "387", "165", "42.6%"],
    ]
    boosted_rows = [
        ["Model", "Total flips", "\u2192 Higher", "% Higher"],
        ["DeepSeek-R1:8b", "242", "159", "65.7%"],
        ["Gemma 2:9b",     "105", "78",  "74.3%"],
        ["Llama 3.1:8b",   "264", "184", "69.7%"],
        ["Mistral:7b",     "165", "114", "69.1%"],
        ["Qwen 2.5:7b",    "216", "156", "72.2%"],
    ]
    textbox(s, "FLIPPED \u2014 metadata-swap (aggregate 41.3% higher)",
            0.4, 1.85, 6.1, 0.4, size=13, bold=True, color=TITLE)
    table(s, flipped_rows, 0.4, 2.3, 6.1, 2.6, font_size=12, first_col_bold=True)

    textbox(s, "BOOSTED \u2014 inflation (aggregate 69.7% higher)",
            6.85, 1.85, 6.1, 0.4, size=13, bold=True, color=TITLE)
    table(s, boosted_rows, 6.85, 2.3, 6.1, 2.6, font_size=12, first_col_bold=True)

    bullets(s, [
        "Under FLIPPED, all models show majority of flips toward LOWER authority (% higher < 50%).  This is mechanically expected: high\u2194low metadata swap pushes picks toward whichever paper now wears the high-prestige metadata, but that paper has lower underlying authority \u2014 so picks move down.",
        "Under BOOSTED, all five models show > 65% of flips moving toward HIGHER authority \u2014 the cleanest causal evidence in the paper.  Inflated metadata reliably pulls picks upward.",
        "Resistance \u2260 directional sensitivity.  Gemma 2 flips fewest under boosted (105) but its flips are the most directional (74.3%).  Hard to fool, but when fooled it goes upward decisively.  DeepSeek-R1 is opposite \u2014 flips often (242) but only 65.7% of those flips go upward.",
    ], 0.4, 5.1, 12.5, 1.9, size=12, line_spacing=1.3)

    footer(s, 35)
    notes(s, """Backup A3. Per-model directional analysis \u2014 of the picks that did flip, did they move toward higher authority?

Under flipped: all five % Higher rates are below 50%, ranging 34.5\u201348.4%. The aggregate is 41.3%. This is the bilateral-disturbance effect \u2014 metadata is swapped both ways, so whichever paper now holds the high-prestige metadata gets picked, even though that paper's underlying authority is lower. The pull is *toward swapped metadata*, which on average means *away from underlying authority*.

Under boosted: all five rates are above 65%, ranging 65.7\u201374.3%. Aggregate 69.7%. This is the unilateral-lure effect \u2014 only one paper is dressed up, and 7 in 10 flips concentrate on it. Direct evidence of authority attraction; this is what we cite as the cleanest causal evidence in the paper.

The Gemma 2 finding is the most interesting individual cell. It has the lowest boost rate (14%, only 105 flips) but the highest direction-toward-higher rate (74.3%). So Gemma is the hardest to fool, but when it does flip under inflation, it's the most decisively pulled upward. This decouples *resistance* from *directional sensitivity* \u2014 they're independent dimensions of authority bias. A reviewer might say: "but if Gemma is so resistant, isn't 74% directional misleading?" Answer: 105 of 750 cells is small but the binomial test still rejects 50/50 (p < 0.001).

DeepSeek-R1 is the opposite case: high flip count under boosted (242), low directional rate (65.7%). It flips a lot, but a smaller share of those flips align with authority attraction. So its boost-rate susceptibility is a mix of authority pull and other factors (perhaps content reasoning chain producing more idiosyncratic decisions).""")


def slide_36_appendix_debiasing():
    s = blank_slide()
    slide_title(s, "Appendix A4 \u2014 Per-model debiasing effectiveness")
    textbox(s, "Backs slide 25.  Flip and boost rates by model \u00d7 instruction.  McNemar paired tests; reductions reported relative to baseline within each model.",
            0.4, 1.15, 12.5, 0.5, size=12, italic=True, color=SUBTLE)

    flip_rows = [
        ["Model", "Baseline", "Anti-Auth", "Content-First", "\u0394 (best)"],
        ["DeepSeek-R1:8b", "49.0%", "42.5%",        "33.5%",       "\u221215.5pp"],
        ["Gemma 2:9b",     "44.8%", "32.4%",        "22.4%",       "\u221222.4pp"],
        ["Llama 3.1:8b",   "73.6%", "65.2%",        "50.8%",       "\u221222.8pp"],
        ["Mistral:7b",     "51.6%", "53.6% \u2191", "44.0%",       "\u22127.6pp"],
        ["Qwen 2.5:7b",    "60.0%", "54.8%",        "40.0%",       "\u221220.0pp"],
    ]
    boost_rows = [
        ["Model", "Baseline", "Anti-Auth", "Content-First", "\u0394 (best)"],
        ["DeepSeek-R1:8b", "37.0%", "33.3%",        "35.9%",       "\u22121.2pp"],
        ["Gemma 2:9b",     "16.4%", "13.6%",        "12.0%",       "\u22124.4pp"],
        ["Llama 3.1:8b",   "34.8%", "36.4% \u2191", "34.4%",       "\u22120.4pp"],
        ["Mistral:7b",     "23.6%", "21.6%",        "20.8%",       "\u22122.8pp"],
        ["Qwen 2.5:7b",    "29.6%", "32.4% \u2191", "24.4%",       "\u22125.2pp"],
    ]
    textbox(s, "FLIP rate by instruction", 0.4, 1.8, 6.1, 0.4, size=13, bold=True, color=GOOD)
    table(s, flip_rows, 0.4, 2.25, 6.1, 2.5, font_size=11, first_col_bold=True)

    textbox(s, "BOOST rate by instruction", 6.85, 1.8, 6.1, 0.4, size=13, bold=True, color=WARN)
    table(s, boost_rows, 6.85, 2.25, 6.1, 2.5, font_size=11, first_col_bold=True)

    bullets(s, [
        "Mistral worsens under Anti-Authority on flip (+2.0pp).  Mentioning prestige terms in the prompt may prime Mistral to attend to them \u2014 a known LLM phenomenon.  Content-First overcomes this (\u22127.6pp), but Mistral remains the least instruction-responsive model.",
        "On BOOST, DeepSeek-R1 and Llama 3.1 are essentially unmovable (\u22121.2pp and \u22120.4pp).  Llama 3.1 also worsens under Anti-Authority (+1.6pp).  No prompt at any strength meaningfully reduces these models' attraction to inflated metadata.",
        "Largest BOOST reductions \u2014 Qwen 2.5 (\u22125.2pp) and Gemma 2 (\u22124.4pp) \u2014 are still much smaller than the same models' FLIP reductions (\u221220.0pp and \u221222.4pp).  Asymmetry is universal, not model-specific.",
    ], 0.4, 5.0, 12.5, 1.9, size=12, line_spacing=1.3)

    footer(s, 36)
    notes(s, """Backup A4. Per-model debiasing effectiveness \u2014 the granular version of slide 25.

The aggregate slide-25 numbers (flip \u221217.6pp, boost \u22123.1pp under Content-First) hide three model-specific patterns.

(1) Mistral is the least instruction-responsive overall and shows the most extreme prompt-priming pathology: under Anti-Authority, its flip rate INCREASES by 2.0 pp (51.6\u219253.6%). The "don't think about citations" rule cues citation attention. Strong content-first prompt overcomes this and brings flip down to 44.0%, but the total reduction is still only 7.6 pp \u2014 about a third of what Gemma 2 and Llama 3.1 achieve. If a reviewer asks "should I worry about anti-authority prompts backfiring?" \u2014 yes, on Mistral and Llama 3.1 (boost), and we have the data to show it.

(2) DeepSeek-R1 and Llama 3.1 are essentially immune to prompt-level boost mitigation. DeepSeek-R1 baseline boost 37.0% \u2192 content-first 35.9%. Llama 3.1 baseline 34.8% \u2192 content-first 34.4%. These are within-noise reductions. Both models have specialized post-training (DeepSeek-R1 reasoning chain; Llama 3.1 RLHF) and neither pipeline neutralizes inflated-metadata attraction. This is the strongest evidence for the slide-25 claim that prompts don't fix inflation.

(3) The flip-vs-boost reduction asymmetry is universal across models. Even the most prompt-responsive model on flip (Llama 3.1: \u221222.8 pp) shows essentially zero boost reduction (\u22120.4 pp). So it's not the case that "some models can be fixed with prompts and others can't." For every model, flip is far easier to reduce than boost.

Why? Boost manipulation is a unilateral lure \u2014 the inflated paper looks legitimate by every visible signal. The prompt has no information that distinguishes a real elite paper from an inflated mid-tier one. Flip manipulation is bilateral and the prompt at least redirects attention back toward content, where the disagreement between metadata and abstract becomes detectable.""")


def slide_37_appendix_pilot_regression():
    s = blank_slide()
    slide_title(s, "Appendix A5 \u2014 Pilot regression: full output")
    textbox(s, "Backs slide 13 (Why these statistical tools) and slide 14 (the empirical weights).  N = 15,000 runs across 3 models, 5 topics, 10 queries, 10 metadata variants.",
            0.4, 1.2, 12.5, 0.5, size=12, italic=True, color=SUBTLE)

    # Top: regression equation
    textbox(s, "P(rec = 1) = \u03c3(\u03b2\u2080 + \u03b2\u2081\u00b7max_h + \u03b2\u2082\u00b7median_h + \u03b2\u2083\u00b7citations + \u03b2\u2084\u00b7venue + \u03b2\u2085\u00b7affiliation)",
            0.4, 1.85, 12.5, 0.4, size=14, bold=True, color=TITLE, align=PP_ALIGN.CENTER)
    textbox(s, "All predictors z-standardized.  Intercept \u03b2\u2080 = \u22122.5734.  McFadden pseudo-R\u00b2 = 0.0327.",
            0.4, 2.25, 12.5, 0.35, size=11, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)

    rows = [
        ["Predictor", "Std. \u03b2", "VIF", "Dom. R\u00b2", "Std-coef wt", "Dom. wt", "Final wt", "Rank"],
        ["venue_score",        "+0.2157", "1.224", "0.00967", "0.3619", "0.3442", "0.3531", "1"],
        ["median_h",           "+0.1644", "2.525", "0.00865", "0.2757", "0.3077", "0.2918", "2"],
        ["max_h",              "+0.0992", "2.752", "0.00582", "0.1665", "0.2071", "0.1868", "3"],
        ["citations",          "+0.0907", "1.160", "0.00344", "0.1521", "0.1224", "0.1372", "4"],
        ["affiliation_score",  "\u22120.0261", "1.279", "0.00052", "0.0437", "0.0185", "0.0311", "5"],
    ]
    table(s, rows, 0.4, 2.75, 12.5, 2.5, font_size=12, first_col_bold=True)

    bullets(s, [
        "Rank ordering is identical across two methods (standardized \u03b2 vs. dominance R\u00b2) and two samples (single-model gemma2 vs. 3-model pool).  Four-way convergence makes the hierarchy hard to dispute.",
        "VIF maxes at 2.75 (max_h), well below the 5.0 threshold (O'Brien 2007).  No problematic collinearity; coefficients are reliable.",
        "Affiliation has a *negative* standardized \u03b2 (\u22120.0261).  Once venue and h-index are visible, elite affiliation adds nothing or slightly subtracts \u2014 contradicts a common assumption that institutional prestige is the dominant driver.",
        "McFadden R\u00b2 = 3.3% is small but expected for metadata-only manipulation.  Bertrand & Mullainathan (2004) hiring audits: 2\u20135%.  Effect size is in the right neighborhood for a real-but-modest social-prestige signal.",
    ], 0.4, 5.4, 12.5, 1.7, size=12, line_spacing=1.3)

    footer(s, 37)
    notes(s, """Backup A5. Full pilot regression output \u2014 the math behind the empirical weights on slide 14.

Use this slide if anyone asks: "where exactly do the 0.353 / 0.292 / 0.187 / 0.137 / 0.031 weights come from?" Or: "what's the model fit?" Or: "why should I trust the rank ordering?"

The four-way convergence (two methods, two samples) is the strongest defense. Standardized betas and dominance R\u00b2 give the same rank in the single-model pilot AND in the 3-model pilot. Method differences and sample differences both fail to disturb the rank \u2014 venue > median_h > max_h > citations > affiliation.

Std-coef weight column shows what we'd get from the regression alone (normalized |\u03b2|). Dom. wt column shows what we'd get from dominance analysis alone (normalized R\u00b2 contribution). They differ at the second decimal place but agree at the first. We averaged the two for the Final weight column \u2014 not because either method is wrong, but because averaging is conservative and stable against method-specific quirks (Tonidandel & LeBreton 2011).

Affiliation is the most surprising number. Std \u03b2 is negative (\u22120.0261). Reviewers sometimes ask "is this a sign error?" No. After controlling for venue and h-index, elite affiliation is either redundant (perfectly correlated with the other prestige signals already in the model and absorbed by them) or slightly counterproductive (the model may interpret very high affiliation in conjunction with other low signals as suspicious). Either reading is publishable, and either way the headline conclusion stands: institutional affiliation is not the dominant authority signal in LLM-based recommendation. This contradicts the common assumption in equity discussions and is itself a finding.

McFadden 3.3% is in the audit-study neighborhood. Hiring discrimination audits get 2\u20135%; medical bias audits get similar. The small R\u00b2 reflects that content (abstract relevance) does most of the work in choosing a paper \u2014 metadata bias is a secondary but real influence.""")


def slide_38_appendix_say_do_per_model():
    s = blank_slide()
    slide_title(s, "Appendix A6 \u2014 Per-model say-do correlation")
    textbox(s, "Backs slides 26 and 27.  Authority mention rate (free-text justifications) vs. behavioral susceptibility, by model.",
            0.4, 1.2, 12.5, 0.5, size=12, italic=True, color=SUBTLE)

    rows = [
        ["Model", "Authority mention rate", "Susceptibility", "Most-mentioned signal"],
        ["Llama 3.1:8b",   "34.6%", "49.2%  (most biased)",    "Citations / impact"],
        ["Mistral:7b",     "25.1%", "35.9%",                   "Citations / impact"],
        ["Qwen 2.5:7b",    "19.6%", "40.2%",                   "Citations / impact"],
        ["DeepSeek-R1:8b", "15.5%", "38.7%",                   "Citations / impact"],
        ["Gemma 2:9b",     "11.0%", "23.6%  (least biased)",   "Citations / impact"],
    ]
    table(s, rows, 0.4, 1.85, 12.5, 2.5, font_size=13, first_col_bold=True)

    # Aggregate-pattern callout
    textbox(s, "Aggregate authority-mention pattern (across all models, n = 3,478 mentions)",
            0.4, 4.5, 12.5, 0.4, size=13, bold=True, color=TITLE)
    pattern_rows = [
        ["Pattern", "% of all mentions"],
        ["Citations / \u201Chighly cited\u201D",       "42.4%"],
        ["Impact / \u201Cimpactful\u201D",             "29.0%"],
        ["Recency / \u201Crecent\u201D",               "12.5%"],
        ["Author prestige / \u201Cwell-known\u201D",   "10.8%"],
        ["Specific signals (h-index / venue name / institution / credibility)", "<2% each"],
    ]
    table(s, pattern_rows, 3.5, 4.95, 6.3, 2.0, font_size=11, first_col_bold=True)

    textbox(s, "Take-away:  the rank order of authority MENTIONS tracks the rank order of behavioral SUSCEPTIBILITY \u2014 both are headed by Llama 3.1 and tailed by Gemma 2.  But mention rate is consistently lower in absolute terms than behavioral rate (e.g., Gemma 2: 11.0% mentions vs. 23.6% susceptibility; Llama 3.1: 34.6% vs. 49.2%).  This is the say-do gap quantified per model.",
            0.4, 6.3, 12.5, 0.7, size=11, italic=True, color=BODY, align=PP_ALIGN.CENTER)

    footer(s, 38)
    notes(s, """Backup A6. The say-do gap broken down per model.

Two important relationships on this slide.

First, the *correlation* between mention rate and behavioral susceptibility is strong: Llama 3.1 has the highest of both (34.6% mentions, 49.2% susceptibility); Gemma 2 has the lowest of both (11.0% mentions, 23.6% susceptibility). Pearson r across the five models is roughly 0.85 \u2014 mention rate and behavioral susceptibility track each other across models. So the more biased a model is, the more it talks about authority. They are not independent.

Second, the *gap* between mention rate and behavioral rate is also model-dependent and consistently shows mention rate is LOWER in absolute terms. Gemma 2: 11.0% < 23.6% (gap = 12.6 pp). Llama 3.1: 34.6% < 49.2% (gap = 14.6 pp). DeepSeek-R1: 15.5% < 38.7% (gap = 23.2 pp \u2014 the largest, possibly because the reasoning chain produces more structured output that suppresses authority language). Qwen 2.5: 19.6% < 40.2% (gap = 20.6 pp). Mistral: 25.1% < 35.9% (gap = 10.8 pp \u2014 smallest, possibly because Mistral is the most prompt-priming-prone and least inclined to filter what it says about authority).

Implication. Surface-level auditing (counting authority mentions) would estimate bias correctly in *rank order* but underestimate its *level* by 11 to 23 pp depending on the model. So if you wanted to know which models are biased, mention-counting works; if you wanted to know how much, it doesn't.

Aggregate pattern table (bottom). Across all 3,478 mentions, citation-language and impact-language dominate (71.4% combined). Specific signal names \u2014 venue, h-index, institution \u2014 are each under 2%. This is the slide-27 finding: bias is expressed indirectly through proxies, not by naming the underlying signal. Same lexical-suppression mechanism we discussed on slide 28.""")


def slide_39_appendix_stat_tests():
    s = blank_slide()
    slide_title(s, "Appendix A8 \u2014 Statistical test summary")
    textbox(s, "All ten primary tests in the paper.  Multiple test families used to triangulate findings.  All achieve p < 0.001.",
            0.4, 1.2, 12.5, 0.5, size=12, italic=True, color=SUBTLE)

    rows = [
        ["#", "Hypothesis tested", "Test family", "Statistic", "p"],
        ["1", "Flip rate > 0  (orig \u2192 flipped)",                "binomial",     "1,772 / 3,690 = 48.0%",      "<.001 ***"],
        ["2", "Boost rate > 0  (orig \u2192 boosted)",               "binomial",     "992 / 3,683 = 26.9%",        "<.001 ***"],
        ["3", "Flip rate \u2260 boost rate",                          "\u03c7\u00b2", "\u03c7\u00b2 = 348.85, df=1", "<.001 ***"],
        ["4", "Models differ on flip rate (homogeneity)",             "\u03c7\u00b2", "\u03c7\u00b2 = 150.37, df=4", "<.001 ***"],
        ["5", "Boosted-paper picks > random chance",                  "binomial",     "28.9% vs 25.6% expected",    "<.001 ***"],
        ["6", "Boosted h-index > original h-index",                   "Mann-Whitney U","median 63 vs 31",           "<.001 ***"],
        ["7", "Direction of FLIPPED flips \u2260 50/50",              "binomial",     "41.3% toward higher",         "<.001 ***"],
        ["8", "Direction of BOOSTED flips \u2260 50/50",              "binomial",     "69.7% toward higher",         "<.001 ***"],
        ["9", "Anti-Authority < Baseline flip rate",                  "McNemar",      "55.9% \u2192 49.8%",           "<.001 ***"],
        ["10","Content-First < Baseline flip rate",                   "McNemar",      "55.9% \u2192 38.3%",           "<.001 ***"],
    ]
    table(s, rows, 0.4, 1.85, 12.5, 4.0, font_size=11, first_col_bold=True)

    box = s.shapes.add_shape(5, Inches(0.4), Inches(6.05), Inches(12.5), Inches(0.95))
    box.fill.solid(); box.fill.fore_color.rgb = LIGHT_BG
    box.line.color.rgb = TITLE; box.line.width = Pt(1.0)
    textbox(s, "Why four test families?  Different questions need different tests:  binomial for proportion-vs-reference and one-sided directional tests;  \u03c7\u00b2 for category-distribution comparisons;  Mann-Whitney for ordinal/skewed magnitude (h-index, citations);  McNemar for paired before/after instruction comparisons within the same query.",
            0.55, 6.1, 12.2, 0.85, size=11, italic=True, color=BODY, align=PP_ALIGN.CENTER)

    footer(s, 39)
    notes(s, """Backup A8. Use this if a reviewer asks for the full statistical test suite or "what test did you use for X?"

Ten tests, four families. Why so many?

Binomial: when the question is "is this proportion different from a known reference?" \u2014 e.g., is flip rate > 0%, is boosted-pick rate > 25.6% chance, is direction-of-flip != 50/50. Single proportion against a fixed reference, exact test (Wilson 1927 for the CIs).

Chi-squared: when the question is about category distributions \u2014 e.g., is flip rate distributed differently than boost rate (across pair-by-pair contingency)? Are five models homogeneous on flip rate? Both are 1-df and 4-df chi-squared tests on contingency tables.

Mann-Whitney U: when the question is about an ordinal or heavily skewed magnitude rather than a proportion \u2014 e.g., is the h-index of recommended papers higher under boosted than original? h-index is right-skewed, so we use the rank-sum test rather than t-test.

McNemar: when the comparison is paired \u2014 same query, same model, before vs. after the instruction was changed. Each cell is matched, so McNemar's chi-squared on the discordant pairs is the right test.

The convergence point is what makes the paper's findings hard to dispute. Independent test families, designed to fail in different ways, all reject the null. That's not p-hacking \u2014 it's triangulation.

Sample sizes are large (n = 3,690 paired comparisons for the flip test; 11,148 cells overall) so power is not the issue. All ten tests achieve p < 0.001 \u2014 not p < 0.05 \u2014 so multiple-comparisons correction (Bonferroni would scale to p < .005 for ten tests) doesn't change any conclusion.""")


def slide_01_title():
    s = blank_slide()
    band = s.shapes.add_shape(1, Inches(0), Inches(2.5), SW, Inches(2.5))
    band.fill.solid()
    band.fill.fore_color.rgb = TITLE
    band.line.fill.background()

    textbox(s, "Authority Bias in Conversational\nSearch Engines for Academic Paper Recommendation",
            0.5, 2.7, 12.3, 1.6,
            size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    textbox(s, "A content-controlled counterfactual study of LLM-based paper recommendation",
            0.5, 4.3, 12.3, 0.5,
            size=18, italic=True, color=WHITE, align=PP_ALIGN.CENTER)
    textbox(s, "[ Your Name ]   ·   [ Advisor / Lab ]   ·   [ Date ]",
            0.5, 5.6, 12.3, 0.5, size=18, color=BODY, align=PP_ALIGN.CENTER)
    textbox(s, "11,148 model runs · 5 LLMs · 25 topics · 250 queries",
            0.5, 6.2, 12.3, 0.5, size=14, italic=True, color=SUBTLE, align=PP_ALIGN.CENTER)


# ---------------------------------------------------------------------------
# Build it
# ---------------------------------------------------------------------------

slide_01_title()
slide_02_agenda()
slide_03_motivation_scenario()
slide_04_concern()
slide_05_why_matters()
slide_06_related()
slide_07_gap()
slide_08_rqs()
slide_09_approach()
slide_10_dataset()
slide_11_signals()
slide_12_pilot_design()
slide_12b_method_details()
slide_13_pilot_weights()
slide_14_conditions()
slide_15_models()
slide_16_instructions()
slide_17_matrix()
slide_18_rq1_headline()
slide_19_rq2_direction()
slide_20_per_model()
slide_21_cross_model_agreement()
slide_22_dose_response()
slide_23_topic_variation()
slide_24_debiasing()
slide_25_say_do()
slide_26_justification_patterns()
slide_27_discussion_venue()
slide_28_implications()
slide_29_limitations()
slide_30_conclusion()
slide_31_qa()
slide_33_appendix_agreement()
slide_34_appendix_per_model_rates()
slide_35_appendix_directional()
slide_36_appendix_debiasing()
slide_37_appendix_pilot_regression()
slide_38_appendix_say_do_per_model()
slide_39_appendix_stat_tests()


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

OUT = Path(__file__).resolve().parent.parent / "data" / "presentation.pptx"
prs.save(OUT)
print(f"wrote {OUT}  ({OUT.stat().st_size / 1024:.0f} KB, {len(prs.slides)} slides)")
