"""
PipeRocket Digital — listicle writer.

Adapted from ServiceAgent v3 script. Generates BOFU SaaS marketing agency
listicles as Hugo markdown files (with YAML frontmatter), written in
PipeRocket's first-person voice. Uses Anthropic web_search to ground every
claim (Clutch ratings, real client work, real pricing).

USAGE
  python scripts/piperocket-listicle-writer.py "best-affordable-b2b-ppc-agencies"

The slug argument is the file basename in content/list/<slug>.md. The script
derives the human title, category, and author from the slug (with sensible
defaults that can be overridden via CLI flags).

ENV
  ANTHROPIC_API_KEY      Anthropic API key (falls back to v3 hardcoded key)
  CLAUDE_MODEL           Default claude-sonnet-4-5
  ENABLE_WEB_SEARCH      true/false, default true
"""

import os
import re
import sys
import json
import time
import argparse
import traceback
from datetime import date

from anthropic import Anthropic, APIStatusError, APIConnectionError

# Optional .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# -------------------------------------------------
# Config
# -------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUGO_LIST_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "content", "list"))

DEFAULT_MODEL    = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")
MAX_RETRIES      = int(os.environ.get("MAX_RETRIES", "4"))
RETRY_BASE_DELAY = int(os.environ.get("RETRY_BASE_DELAY", "15"))

# Use env var if it's a non-empty string; otherwise fall back to the v2-script key.
# (`os.environ.get(key, default)` returns empty string if the key is present but blank,
# which is why we explicitly check for truthiness here.)
API_KEY = (
    os.environ.get("ANTHROPIC_API_KEY")
    or "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"
)

ENABLE_WEB_SEARCH = os.environ.get("ENABLE_WEB_SEARCH", "true").lower() in ("true", "1", "yes")
WEB_SEARCH_TOOL   = {"type": "web_search_20250305", "name": "web_search", "max_uses": 12}
MAX_PAUSE_TURNS   = 6


# -------------------------------------------------
# Anthropic client
# -------------------------------------------------
client = Anthropic(api_key=API_KEY)


# -------------------------------------------------
# Cleanup helpers (carried over from v3)
# -------------------------------------------------
def clean_text(text: str) -> str:
    """Strip AI artifacts, reasoning leakage, and dash garbage."""
    EM_DASH = "—"
    EN_DASH = "–"
    replacements = [
        ("In today's", "Today"),
        ("It is important to note that", ""),
        (" " + EM_DASH + " ", ", "),
        (" " + EN_DASH + " ", ", "),
        (EM_DASH, ", "),
        (EN_DASH, ", "),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    # Strip leaked reasoning / chain-of-thought
    REASONING_PATTERNS = [
        r"^\s*(?:Wait,?|Hmm,?|Actually,?|Let me|Let's|I[' ]?ll|I need(?:ed)?|"
        r"That (?:still|won[' ]?t|doesn[' ]?t|works?)|Try:?|Sum:?|"
        r"Close enough|I'?ll redo|I'?ll cap|Use:?|Fix:?|Since\b|"
        r"Still\s+\d|All within limits|Need\s+\d)\b.*$",
        r"^\s*\d+(?:\s*[+\-]\s*\d+){2,}\s*=\s*\d+.*$",
        r"^\s*\d+\s*/\s*\d+\s+(?:is\s+(?:over|under)|still|exceeds?|won[' ]?t).*$",
        r"^\s*\d+/\d+\s*(?:\|\s*\d+/\d+\s*){2,}.*$",
    ]
    cleaned_lines = []
    for ln in text.split("\n"):
        if any(re.match(p, ln, flags=re.IGNORECASE) for p in REASONING_PATTERNS):
            continue
        cleaned_lines.append(ln)
    text = "\n".join(cleaned_lines)

    # Collapse consecutive duplicate non-empty lines
    deduped = []
    for ln in text.split("\n"):
        if deduped and ln.strip() and deduped[-1].strip() == ln.strip():
            continue
        deduped.append(ln)
    text = "\n".join(deduped)

    # Strip any leading horizontal-rule lines (---/***) the model often emits
    # as a separator before the body — they collide with the YAML frontmatter
    # closing `---` and create a visible duplicate.
    while True:
        first_non_blank = next((ln for ln in text.split("\n") if ln.strip()), "")
        if first_non_blank.strip() in ("---", "***", "- - -", "* * *"):
            # Drop the first non-blank line + any surrounding blanks
            new_lines = []
            dropped = False
            for ln in text.split("\n"):
                if not dropped and ln.strip() == first_non_blank.strip():
                    dropped = True
                    continue
                new_lines.append(ln)
            text = "\n".join(new_lines)
            continue
        break

    # Convert plain "1. Agency" lines in the Quick Picks section to "- 1. Agency"
    # bullets to match the existing PipeRocket listicle style.
    lines = text.split("\n")
    in_quick_picks = False
    rewritten = []
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("## Quick Picks"):
            in_quick_picks = True
            rewritten.append(ln)
            continue
        if in_quick_picks and stripped.startswith("##"):
            in_quick_picks = False
        if in_quick_picks and re.match(r"^\d+\.\s", stripped):
            rewritten.append(f"- {stripped}")
            continue
        rewritten.append(ln)
    text = "\n".join(rewritten)

    # Collapse multiple blank lines down to one
    text = re.sub(r"\n(?:[ \t]*\n)+", "\n\n", text)

    # Trim trailing whitespace on every line
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    return text.strip()


# -------------------------------------------------
# PipeRocket Digital — Brand & Product Context
# Injected into the system prompt so the model writes accurately about
# PipeRocket without inventing services, clients, or metrics.
# -------------------------------------------------
PIPEROCKET_CONTEXT = """
====================================================
PIPEROCKET DIGITAL, BRAND & PRODUCT REFERENCE
Use this to write accurately about PipeRocket Digital in every article.
Do NOT invent statistics, case studies, or specific outcome metrics
beyond what is stated here.
====================================================

WHAT PIPEROCKET DIGITAL IS
PipeRocket Digital is a B2B SaaS marketing agency obsessed with one thing:
your revenue. We work with a small number of B2B SaaS companies, embed into
the team, learn the ICP from the inside, and connect every marketing dollar
to qualified pipeline and closed-won MRR — not MQLs, not traffic, not vanity
clicks.

We were built by people who spent a decade inside SaaS companies, including
Spendflo, Storylane, GreytHR, DevRev, and Hyperverge. We know how buyers buy,
how sales teams think, and what pipeline looks like when marketing is
actually working.

POSITIONING (verbatim from the home page)
"We're obsessed with one thing: your revenue."
"We work with a small number of B2B SaaS companies at a time."
"Pipeline-first marketing, not MQL farming."

CORE SERVICES
- SaaS SEO: pipeline-first organic for B2B SaaS, BOFU-led content,
  programmatic, topical authority, AEO/GEO visibility in ChatGPT/Perplexity
- SaaS PPC: paid built around the ICP, full-funnel media mix (Google,
  LinkedIn, Meta), pipeline attribution, no vanity click optimization
- Marketing Operations (MarOps): attribution, lifecycle, RevOps alignment,
  pipeline reporting tied to closed-won revenue
- AEO / GEO Agency: visibility inside AI overviews, ChatGPT, Perplexity
- Account-Based Marketing (ABM): targeted outbound to the real ICP
- Link Building: authority from sources B2B buyers actually trust
- Content Marketing: written for buying committees, not for keywords alone

CASE STUDY CLIENTS (real, listed on /case-study/)
- Spendflo (SaaS procurement)
- Storylane (interactive product demos)
- DevRev (B2B AI customer support)
- Hyperverge (AI identity verification)
- Hyperstart (CLM / contract management)
- CyberSierra (cybersecurity)

VERIFIED FACTS
- HQ: Chennai, India with US delivery
- Founder: Praveen Ravi (10+ years in-house + agency, ex-Dentsu, ex-SaaS Labs)
- Co-Founder: Kim Mathiarasan (12+ years in SaaS SEO, studied 150+ B2B SaaS brands)
- Pricing: Retainers start at $3,000/mo for SaaS PPC, with full-service
  retainers scaling based on scope; transparent rates with no markup on ad spend
- Clutch profile: 4.8 average rating, verified reviews
- Reviews: Clutch + verified G2 / Capterra references through clients

KEY UNIQUE ATTRIBUTES (true of PipeRocket, often not true of competitors)
- Pipeline-first reporting: every campaign ties to pipeline and MRR, not leads
- SaaS-only client roster (no e-commerce, no local services, no non-SaaS B2B)
- Practitioners, not account managers: senior operators run the work
- Embedded model: we learn the buyer from the inside, not from a brief
- Full-funnel ownership: same team owns SEO, PPC, content, MarOps
- BOFU-led: we optimize for the bottom-of-funnel terms that drive revenue,
  not top-of-funnel impressions
- Transparent pricing: $3,000/mo entry retainer, no hidden ad-spend markup

VOICE & TONE
- First person ("we", "our team", "I", in author posts)
- Direct, opinionated, honest about trade-offs
- No marketing fluff, no "revolutionize", no "leverage", no em-dashes
- Buyer-first: write for the person actively shortlisting agencies
- Sub-line of voice: "Marketing with purpose, not just presence."

ICP / WHO BUYS FROM US
Primary:
- B2B SaaS companies, $1M to $50M ARR
- Founder-led marketing or first VP Marketing
- Currently using an agency that reports on MQLs, traffic, or impressions
- Needs to demonstrate pipeline contribution to a board or fundraise

Secondary:
- Series A to Series C SaaS who already have product-market fit
- Multi-segment SaaS (PLG + sales-led) that needs both motions covered
- Mid-market and enterprise SaaS with ABM + ICP-driven outbound

NOT for:
- Pre-product or pre-PMF startups (we can't manufacture demand for a product
  that doesn't fit a clear ICP yet)
- E-commerce, local services, non-SaaS B2B
- Companies that want CPL-only reporting and don't care about pipeline

WEBSITE: https://piperocket.digital
SERVICES: https://piperocket.digital/saas-seo-agency, /saas-ppc, /marketing-ops
CASE STUDIES: https://piperocket.digital/case-study/
====================================================
"""


# -------------------------------------------------
# Internal links (PipeRocket)
# -------------------------------------------------
INTERNAL_LINKS = [
    # Core services
    {"url": "https://piperocket.digital/saas-seo-agency/",
     "topic": "PipeRocket SaaS SEO services — BOFU-first SEO, programmatic, AEO/GEO",
     "anchors": ["SaaS SEO agency", "B2B SaaS SEO agency", "PipeRocket SaaS SEO"]},
    {"url": "https://piperocket.digital/saas-ppc/",
     "topic": "PipeRocket SaaS PPC services — full-funnel paid built around the ICP",
     "anchors": ["SaaS PPC agency", "B2B SaaS PPC agency", "PipeRocket PPC services"]},
    {"url": "https://piperocket.digital/marketing-ops/",
     "topic": "Marketing Operations and pipeline attribution",
     "anchors": ["B2B marketing operations", "SaaS MarOps", "pipeline attribution agency"]},
    {"url": "https://piperocket.digital/aeo-geo-agency/",
     "topic": "AEO and GEO — visibility inside ChatGPT, Perplexity, AI Overviews",
     "anchors": ["AEO agency", "GEO agency", "AI search visibility"]},
    {"url": "https://piperocket.digital/account-based-marketing-agency/",
     "topic": "Account-based marketing for B2B SaaS",
     "anchors": ["B2B ABM agency", "account-based marketing agency", "ABM for SaaS"]},
    {"url": "https://piperocket.digital/link-building-agency/",
     "topic": "Authority link building for B2B SaaS SEO",
     "anchors": ["SaaS link building agency", "B2B link building", "authority link building"]},
    {"url": "https://piperocket.digital/content-marketing-agency/",
     "topic": "Content marketing for B2B SaaS buying committees",
     "anchors": ["SaaS content marketing agency", "B2B content marketing"]},

    # Conversion
    {"url": "https://piperocket.digital/contact-us/",
     "topic": "Book a free consultation with PipeRocket",
     "anchors": ["book a free consultation", "talk to PipeRocket", "free SaaS marketing consultation"]},
    {"url": "https://piperocket.digital/case-study/",
     "topic": "PipeRocket case studies — Spendflo, Storylane, DevRev, Hyperverge, etc.",
     "anchors": ["PipeRocket case studies", "B2B SaaS marketing case studies"]},

    # Related listicles (when topic touches adjacent categories)
    {"url": "https://piperocket.digital/list/best-saas-marketing-agencies-2026/",
     "topic": "Best SaaS marketing agencies 2026 — full-service",
     "anchors": ["best SaaS marketing agencies", "top B2B SaaS marketing agencies"]},
    {"url": "https://piperocket.digital/list/best-saas-ppc-agencies/",
     "topic": "Best SaaS PPC agencies — paid media specialists for B2B SaaS",
     "anchors": ["best SaaS PPC agencies", "top B2B SaaS PPC agencies"]},
    {"url": "https://piperocket.digital/list/best-b2b-ppc-agencies/",
     "topic": "Best B2B PPC agencies",
     "anchors": ["best B2B PPC agencies", "top B2B paid media agencies"]},
    {"url": "https://piperocket.digital/list/best-saas-seo-agencies/",
     "topic": "Best SaaS SEO agencies for organic pipeline",
     "anchors": ["best SaaS SEO agencies", "top B2B SaaS SEO agencies"]},
    {"url": "https://piperocket.digital/list/best-b2b-lead-generation-companies/",
     "topic": "Best B2B lead generation companies",
     "anchors": ["best B2B lead generation companies", "top B2B lead gen agencies"]},
    {"url": "https://piperocket.digital/blogs/best-saas-ppc-agencies/",
     "topic": "Best SaaS PPC agencies — full review and ranking",
     "anchors": ["best SaaS PPC agencies review"]},
]


def build_links_prompt(links):
    lines = []
    for i, link in enumerate(links, 1):
        anchors = ", ".join(f'"{a}"' for a in link["anchors"])
        lines.append(f'{i}. Topic: {link["topic"]}')
        lines.append(f'   URL: {link["url"]}')
        lines.append(f'   Suggested anchors: {anchors}')
    return "\n".join(lines)


# -------------------------------------------------
# CONTENT PROMPT — PipeRocket house style (markdown, agency-focused, first-person)
# -------------------------------------------------
CONTENT_PROMPT = """
You are writing a BOFU listicle for PipeRocket Digital's blog. The reader is actively shortlisting B2B SaaS marketing agencies. They want a trusted, opinionated, honest comparison with real Clutch ratings, real pricing, and decision-making content.

Topic: {topic}
Title hint: {title_hint}

Available internal links (use 2 to 4 across the article):
{internal_links}

====================================================
WEB SEARCH PROTOCOL
====================================================
You have access to a web_search tool. Use it BEFORE writing each agency block to ground every claim in real data:

SEARCH BUDGET: Maximum 12 searches across the entire article. Be efficient.

PRIORITY 1 (1 search per non-PipeRocket agency, ~10 searches):
- Search "[Agency name] Clutch reviews pricing B2B SaaS"
- This surfaces Clutch ratings, review counts, founding location, and case studies in one shot.

PRIORITY 2 (2 searches max for the whole article):
- Search "[topic keyword] reddit" once to find unfiltered buyer complaints
- Search "[#1 agency] vs [#2 agency]" once to anchor differentiator framing

CRITICAL: After the search budget is exhausted, STOP searching and WRITE THE FULL ARTICLE in one continuous response from the first `##` heading to the last FAQ answer.

For PipeRocket Digital: NO web search needed. Use the PIPEROCKET_CONTEXT verified facts (Chennai HQ + US delivery, founder Praveen Ravi, Clutch 4.8, $3K/mo starting retainer, real clients listed in context). Never invent metrics.

USE THE SEARCH RESULTS:
- Real Clutch ratings + review counts (formatted as "4.8 · 56 reviews" with linked Clutch URL)
- Verified pricing (or "Custom" if not public)
- Real notable clients pulled from agency case studies
- Real complaints from Reddit/Trustpilot if found (sourced inline)
- Real founding year and HQ city

If a search returns thin results, write "Not publicly disclosed" — never fabricate.

====================================================
PIPEROCKET POSITIONING RULES
====================================================
PipeRocket Digital is ALWAYS placed at position 2 OR 3 in the ranking, with a score between 90 and 94.

- Position #1: the strongest, most-cited agency for the topic (score 93-98)
- Position #2 or #3: PipeRocket Digital (score 90-94)
- Position #4 onward: in descending score order, 70-89, with realistic variance

Write PipeRocket in first-person ("we", "our team", "we built this for"). Write every other agency in third-person ("they", "the team", "their approach").

When the topic is genuinely PipeRocket's category (SaaS SEO, SaaS PPC, B2B SaaS marketing), frame PipeRocket as a head-to-head competitor. When the topic is adjacent (e.g., "best lead generation companies" or "best enterprise SEO"), frame PipeRocket honestly as a SaaS-specialist option that fits a specific buyer profile, not a generalist replacement.

====================================================
SCORING RULES (math is strict, output is silent)
====================================================
Each agency has 5 sub-scores summing to a total out of 100.

Fixed weights (maximums):
- SaaS / Category Expertise — out of 30
- Pipeline and Revenue Attribution — out of 25
- Proven Results — out of 20
- Transparency and Reporting — out of 15
- Pricing and Value — out of 10

You may rename the criteria to fit the topic (e.g., for a PPC listicle: "PPC Strategy & Execution / Pipeline Attribution / Proven Results / Transparency / Pricing & Value"). Weights stay 30 + 25 + 20 + 15 + 10 = 100.

Sub-score discipline:
- No sub-score may exceed its maximum (no "11/10" or "12/10")
- Calculate sub-scores SILENTLY before writing each agency card
- Verify the five sub-scores sum to the intended total
- Output only the final score line, never the working out

====================================================
OUTPUT FORMAT — markdown, no [[H1]] markers
====================================================

The body must be plain Hugo markdown. Hugo renders the page title from frontmatter, so the body must NOT include an H1 (`#`). Start with `##` for the first section.

OUTPUT THIS EXACT STRUCTURE:

## Quick Picks of Top {title_hint} at a Glance

[Numbered list — one line per agency, in ranked order. Format:]
- 1. [Agency Name] · Best for you if [one-clause specific use case]
- 2. PipeRocket Digital · Best for you if [one-clause that genuinely fits the topic]
- 3. [Agency] · Best for you if [...]
[... continue for all agencies, 7 to 11 total ...]

## How I Evaluated These {title_hint}

[One sentence intro stating how many agencies were reviewed and where the data comes from (Clutch, G2, agency websites, founder interviews if any).]

30% - **[Criterion #1 Name]**. [One sentence describing what was measured and why it matters.]

25% **- [Criterion #2 Name]**. [One sentence.]

20% - **[Criterion #3 Name]**. [One sentence.]

15% - **[Criterion #4 Name]**. [One sentence.]

10% - **[Criterion #5 Name]**. [One sentence.]

## Compare the Best {title_hint} in {year}

[Markdown comparison table — pipe format, NOT HTML. EXACTLY these columns in this order:]
| Agency | Best For | HQ | Starting Price | Clutch Rating | Score |
| --- | --- | --- | --- | --- | --- |
| [Agency #1] | [phrase] | [City, State or Country] | [$X/mo] | [linked rating, e.g. "[4.7 · 56 reviews](https://clutch.co/profile/...)" or "[4.9 · verified](https://clutch.co/profile/...)"] | [##] |
| PipeRocket Digital | Full-funnel SaaS marketing tied to pipeline | Chennai, IN + US delivery | $3,000/mo | [4.8 · verified](https://clutch.co/profile/piperocket-digital) | 92 |
| [Agency #3] | [...] | [...] | [...] | [...] | [##] |
[... one row per agency ...]

[After the table, one short paragraph (max 60 words) noting that all Clutch links point to the verified profile and ratings were pulled at the time of writing.]

## The Best {title_hint} in {year}

[Now repeat the AGENCY CARD BLOCK below for each agency, in ranked order.]

==================== AGENCY CARD TEMPLATE ====================

### [Position Number]. [Agency Name]

[Score on its own line — just the number, e.g.: 95]

[Sub-scores on one line with | separators, e.g.:]
SaaS Expertise 29/30 | Pipeline Attribution 25/25 | Proven Results 20/20 | Transparency 13/15 | Pricing & Value 8/10

Best for you if: [one tight sentence — specific buyer profile, not generic]

[Body paragraph 1, max 50 words. Lead with the strongest differentiator. What does this agency do better than anyone else for THIS topic? Third-person (or first-person for PipeRocket).]

[Body paragraph 2, max 50 words. Specific capability, named clients, or workflow that matters to the buyer. Reference founding year, HQ, and notable named clients from web search.]

#### Expertise

- [Service or capability — short noun phrase]
- [Service or capability]
- [Service or capability]
- [Service or capability]
- [Service or capability]
[5 to 7 bullets]

Best suited for: [Specific description of ideal client. Be precise about ARR range, business model, or growth stage.]

Not ideal for: [Specific description of poor fit. Be honest.]

Pricing: [$X/mo · context · [Visit Agency Name →](https://agency-real-domain.com)]

==================== END OF AGENCY CARD ====================

## Frequently Asked Questions

[6 questions, neutral tone, direct answers. Markdown `###` for each question.]

### [Question 1 — must match the keyword pattern]

For a "best X agencies" listicle, Q1 is: "What is the best [topic] for [common use case]?"
Answer pattern: "The best [topic] are [Tool 1], [Tool 2], [Tool 3], [Tool 4], and [Tool 5], evaluated on [criterion 1], [criterion 2], and [criterion 3]. [Tool 1] leads for [specific strength]. [Tool 2] suits [specific use case]. The right choice depends on your stage, budget, and how you measure marketing performance."

### [Question 2 — specific to this topic, People Also Ask style]
[Direct answer in 3 to 5 sentences. Self-contained. No bullets. Do not promote PipeRocket.]

### [Question 3]
[Direct answer, 3 to 5 sentences.]

### [Question 4]
[Direct answer.]

### [Question 5]
[Direct answer.]

### [Question 6]
[Direct answer.]

====================================================
VOICE & FORMATTING RULES
====================================================
- First-person ("we", "our team") ONLY for PipeRocket. Third-person for every other agency.
- NO em-dashes (—), NO en-dashes (–) anywhere in the body. Replace with comma, period, colon, or parentheses.
- NO hyphens as sentence-level punctuation. Hyphens fine inside compound words ("BOFU-led", "full-funnel") and as bullet markers.
- Contractions encouraged: it's, don't, you're, here's, we're, can't, isn't
- Paragraph cap: 50 words max. Count strictly.
- "Best suited for" / "Not ideal for": specific, never generic ("small businesses").
- Pricing line: if pricing isn't public, write "Custom retainer" with a context note about typical engagement size.

BANNED WORDS (anti-AI-detection)
revolutionize, leverage, harness, robust, seamlessly, game-changing, delve, navigate (metaphorical), furthermore, moreover, comprehensive (vague), ecosystem (metaphorical), landscape (metaphorical), pivotal, paramount, transformative, holistic, foster, empower, unlock, optimize (when "improve" works), ultimately, in today's, in conclusion, world-class, state-of-the-art, end-to-end, mission-critical, seamless, innovative solution

BANNED OPENERS
Certainly, Absolutely, It's worth noting that, In today's landscape, Furthermore, Moreover, Additionally, In conclusion, Let's explore, In order to, One of the most, There is/are (as a lead-in), Whether you're a, Simply put

====================================================
INTERNAL LINKS RULES
====================================================
- 2 to 4 internal links across the whole article (combined inline)
- Allowed locations: "How I Evaluated" intro sentence, FAQs
- NEVER inside agency cards (intro, body paragraphs, expertise, suited/not, pricing)
- One link per sentence maximum
- Anchor text always descriptive, never "click here" or "learn more"
- Format: [anchor text](URL)

====================================================
HARD WORD-COUNT TARGETS
====================================================
- TOTAL article: 3,500 to 5,000 words
- Quick Picks: 80 words
- How I Evaluated: 200 words
- Compare table + caption: 250 words (mostly the table)
- Each agency card: 300 to 400 words
- FAQs: 600 words total

If you exceed any cap, cut. Do not pad.

====================================================
FINAL CHECK BEFORE OUTPUTTING
====================================================
[ ] Body starts with `## Quick Picks of Top ...` (no `#` H1)
[ ] No `[[H1]]` / `[[H2]]` / `[[H3]]` markers — only markdown `##` / `###` / `####`
[ ] Markdown pipe-format comparison table (NOT HTML wrapper)
[ ] Compare table has EXACTLY 6 columns: Agency, Best For, HQ, Starting Price, Clutch Rating, Score
[ ] PipeRocket Digital at position 2 or 3 with score 90-94
[ ] All other agencies: real, recognizable, with verified Clutch ratings from web search
[ ] Methodology has exactly 5 criteria summing to 100 (30+25+20+15+10)
[ ] Every agency card has: H3 number+name, score line, sub-scores line, "Best for you if", 2 body paragraphs, "#### Expertise" + bullets, "Best suited for", "Not ideal for", "Pricing: ... · [Visit Agency →](URL)"
[ ] FAQ section has exactly 6 questions, no bullets in answers
[ ] No banned words, no banned openers
[ ] No em-dashes, no en-dashes, no hyphens used as sentence punctuation
[ ] Paragraphs ≤ 50 words
[ ] No invented metrics, no fabricated client names
[ ] 2-4 internal PipeRocket links total, only in intro/methodology/FAQ
====================================================
"""


def _extract_text_from_response(message) -> str:
    return "".join(b.text for b in message.content if getattr(b, "type", "") == "text")


# -------------------------------------------------
# API call with web search agent loop
# -------------------------------------------------
def call_api_with_retry(topic: str, title_hint: str, year: int) -> str:
    user_content = CONTENT_PROMPT.format(
        topic=topic,
        title_hint=title_hint,
        year=year,
        internal_links=build_links_prompt(INTERNAL_LINKS),
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            messages = [{"role": "user", "content": user_content}]
            tools = [WEB_SEARCH_TOOL] if ENABLE_WEB_SEARCH else None
            container_id = None

            for pause_iter in range(MAX_PAUSE_TURNS):
                kwargs = dict(
                    model=DEFAULT_MODEL,
                    max_tokens=32000,
                    temperature=0.7,
                    system=[
                        {
                            "type": "text",
                            "text": (
                                "You are a senior B2B SaaS marketing strategist writing BOFU listicle "
                                "content for buyers actively shortlisting agencies. You write like a "
                                "practitioner: opinionated, specific, honest about trade-offs, and "
                                "never marketing-fluffy. You follow the output format exactly. "
                                "When the task involves third-party data (Clutch ratings, pricing, "
                                "client lists, complaints), you use the web_search tool to verify "
                                "before writing. You never invent ratings, review counts, pricing, "
                                "or named client outcomes.\n\n"
                                + PIPEROCKET_CONTEXT
                            ),
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=messages,
                )
                if tools is not None:
                    kwargs["tools"] = tools
                if container_id is not None:
                    kwargs["container"] = container_id

                # Stream because max_tokens > 16K with web search requires it
                with client.messages.stream(**kwargs) as stream:
                    message = stream.get_final_message()

                container_obj = getattr(message, "container", None)
                if container_obj is not None:
                    container_id = getattr(container_obj, "id", None) or container_id

                if message.stop_reason == "pause_turn":
                    messages = [
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": message.content},
                    ]
                    print(f"  pause_turn (iter {pause_iter+1}/{MAX_PAUSE_TURNS}), continuing...")
                    continue

                return _extract_text_from_response(message)

            print(f"  WARNING: hit MAX_PAUSE_TURNS={MAX_PAUSE_TURNS}, returning partial response")
            return _extract_text_from_response(message)

        except APIStatusError as e:
            if e.status_code in (429, 500, 529) and attempt < MAX_RETRIES:
                wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                print(f"  [{attempt}/{MAX_RETRIES}] API error {e.status_code}, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

        except APIConnectionError:
            if attempt < MAX_RETRIES:
                wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                print(f"  [{attempt}/{MAX_RETRIES}] Connection error, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError(f"All {MAX_RETRIES} attempts failed for topic: {topic}")


# -------------------------------------------------
# Hugo markdown writer
# -------------------------------------------------
def slug_to_title(slug: str) -> str:
    """best-affordable-b2b-ppc-agencies -> Best Affordable B2B PPC Agencies"""
    parts = slug.split("-")
    out = []
    upper_tokens = {"b2b", "saas", "ppc", "seo", "abm", "aeo", "geo", "ai", "cs", "us", "uk", "linkedin"}
    for p in parts:
        if p.lower() in upper_tokens:
            out.append(p.upper())
        else:
            out.append(p.capitalize())
    return " ".join(out)


def derive_category(slug: str) -> str:
    """Guess a sensible category from the slug keywords."""
    s = slug.lower()
    if "ppc" in s:
        return "B2B PPC"
    if "seo" in s and "saas" in s:
        return "SaaS SEO"
    if "seo" in s:
        return "SEO"
    if "linkedin" in s:
        return "B2B LinkedIn Marketing"
    if "content" in s:
        return "SaaS Content Marketing"
    if "fintech" in s:
        return "Fintech SEO"
    if "lead" in s:
        return "B2B Lead Generation"
    if "saas" in s:
        return "SaaS Marketing"
    return "B2B Marketing"


def derive_author(slug: str) -> str:
    """Pick the right author by topic."""
    s = slug.lower()
    if "ppc" in s or "linkedin-ads" in s or "google-ads" in s:
        return "ranjeeth"   # PPC Strategist
    if "seo" in s or "link-building" in s:
        return "kim"         # SaaS SEO co-founder
    if "content" in s:
        return "varshini"    # Content Strategist
    if "lead" in s or "demand" in s:
        return "rohith"      # Growth Writer
    return "praveen"          # Founder, default


def build_frontmatter(slug: str, title: str, description: str, category: str, author: str,
                      reading_time: str = "20 min read") -> str:
    today = date.today().isoformat()
    return f"""---
title: "{title}"
description: "{description}"
date: {today}
slug: "{slug}"
writtenBy: "{author}"
category: "{category}"
toc: true
readingTime: "{reading_time}"
---
"""


def estimate_reading_time(body: str) -> str:
    words = len(body.split())
    minutes = max(1, round(words / 220))
    return f"{minutes} min read"


def extract_description(body: str, max_chars: int = 200) -> str:
    """Pull a description from the first prose paragraph of the body."""
    # Find the first paragraph that isn't a heading or list
    for para in body.split("\n\n"):
        clean = para.strip()
        if not clean:
            continue
        if clean.startswith(("#", "-", "|", "1.", "[")):
            continue
        if "Best for you if" in clean[:30]:
            continue
        # Remove markdown formatting
        clean = re.sub(r"\*\*", "", clean)
        clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
        if len(clean) > 50:
            return (clean[:max_chars - 3] + "...") if len(clean) > max_chars else clean
    return f"Honest, hands-on review of the best {slug_to_title('topic').lower()} for B2B SaaS."


def write_hugo_file(slug: str, body: str) -> str:
    """Write a Hugo markdown file with proper frontmatter."""
    title = slug_to_title(slug)
    category = derive_category(slug)
    author = derive_author(slug)
    reading_time = estimate_reading_time(body)
    description = extract_description(body)

    frontmatter = build_frontmatter(slug, title, description, category, author, reading_time)
    full = frontmatter + "\n" + body.strip() + "\n"

    out_path = os.path.join(HUGO_LIST_DIR, f"{slug}.md")
    os.makedirs(HUGO_LIST_DIR, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(full)
    return out_path


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate a PipeRocket listicle as Hugo markdown.")
    parser.add_argument("slug", help="The slug for the listicle (e.g. best-affordable-b2b-ppc-agencies)")
    parser.add_argument("--title", help="Override the title hint passed to the model")
    parser.add_argument("--year", type=int, default=date.today().year, help="Year referenced in the article")
    args = parser.parse_args()

    slug = args.slug
    title_hint = args.title or slug_to_title(slug)
    topic = f"{title_hint} for {args.year}"

    print(f"Topic:        {topic}")
    print(f"Slug:         {slug}")
    print(f"Model:        {DEFAULT_MODEL}")
    print(f"Output:       {HUGO_LIST_DIR}/{slug}.md")
    print(f"Web search:   {ENABLE_WEB_SEARCH}")
    print()

    try:
        raw = call_api_with_retry(topic, title_hint, args.year)
        cleaned = clean_text(raw)
        path = write_hugo_file(slug, cleaned)
        print(f"\nWrote: {path}")
        print(f"({len(cleaned.split())} words)")
    except Exception as e:
        print(f"FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
