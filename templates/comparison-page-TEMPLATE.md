# =============================================================================
# COMPARISON PAGE TEMPLATE  —  "PipeRocket vs [Competitor]"
# -----------------------------------------------------------------------------
# Save as:   content/compare/piperocket-digital-vs-[competitor].md
# Becomes:   /compare/piperocket-digital-vs-[competitor]/
# Rendered by: layouts/compare/single.html
#
# HOW THIS PAGE WORKS:
# Almost the whole page is built from the FIELDS below (between the --- lines).
# Each block of fields (short_answer, at_a_glance, services, team, etc.) becomes
# one section on the page. You are filling in DATA, not writing prose.
# The only free-writing is the 3 markdown tables AFTER the closing --- at the bottom.
#
# Fill in every [PLACEHOLDER]. Delete these comment lines (the ones starting with #).
# "a" always = PipeRocket. "b" always = the competitor.
# =============================================================================
---
title: "PipeRocket Digital vs [Competitor]"          # H1 + browser tab
description: "[One sentence summary shown under the title and in link previews.]"
metaTitle: "PipeRocket vs [Competitor]: [hook] Compared"   # <title> tag for Google
metaDescription: "[~150-char summary for Google search results.]"
date: 2026-MM-DD                                     # publish date (shown as "Updated ...")
category: "Agency comparison"                        # red eyebrow label above the title
readingTime: "7 min read"
sources_count: 7                                     # how many entries in `sources:` below
writtenBy: "kim"                                     # author key from data/authors.toml
reviewedBy: "praveen"                                # reviewer key from data/authors.toml

# --- The two products being compared. "a" = PipeRocket everywhere on the page. ---
product_a:
  name: "PipeRocket"
product_b:
  name: "[Competitor]"

# --- Sidebar table of contents. One line per section. anchor must match the ids below. ---
toc:
  - { label: "The short answer",      anchor: "short-answer" }
  - { label: "At a glance",           anchor: "at-a-glance" }
  - { label: "Company profile",       anchor: "backgrounds" }
  - { label: "Decision matrix",       anchor: "decision-matrix" }
  - { label: "Capability comparison", anchor: "services" }
  - { label: "Team structure",        anchor: "team" }
  - { label: "Reporting",             anchor: "reporting" }
  - { label: "Pricing",               anchor: "pricing" }
  - { label: "Strengths & tradeoffs", anchor: "tradeoffs" }
  - { label: "Social proof",          anchor: "social-proof" }
  - { label: "FAQ",                   anchor: "faqs" }

# --- "The short answer": intro line + two side-by-side "who should pick which" cards. ---
short_answer:
  heading: "The short answer"
  intro: >-
    [2-3 sentences: the honest answer depends on stage / whether they need
    a SaaS specialist or full-service breadth.]
  callouts:
    - label: "PipeRocket fit"
      title: "[e.g. B2B SaaS specialist]"
      body: >-
        [Who PipeRocket is the better pick for, and why. **Bold** the verdict.]
    - label: "[Competitor] fit"
      title: "[e.g. Full-service digital marketing]"
      body: >-
        [Who the competitor is the better pick for, and why.]

# --- "Company profile": one paragraph about each company. ---
backgrounds:
  heading: "Company profile"
  companies:
    - name: "PipeRocket"
      meta: "Founded 2023 · Boutique pod · 50+ B2B SaaS clients"   # the small grey line
      body: >-
        [2-3 sentences on PipeRocket.]
    - name: "[Competitor]"
      meta: "Founded [YYYY] · [HQ] · [team size]"
      body: >-
        [2-3 sentences on the competitor: founders, focus, notable clients, ratings.]

# --- "At a glance": quick comparison table. Add/remove rows freely. a=PipeRocket, b=competitor. ---
at_a_glance:
  - { label: "Founded",        a: "2023",          b: "[YYYY]" }
  - { label: "Specialization", a: "B2B SaaS only", b: "[competitor focus]" }
  - { label: "Core motion",    a: "SEO-led",       b: "[competitor motion]" }
  - { label: "Starting price", a: "$3,000 / mo",   b: "[$ / mo or 'Custom']" }
  - { label: "Min contract",   a: "3 months",      b: "[term or 'Not publicly listed']" }
  - { label: "Public rating",  a: "4.9 — Clutch",  b: "[rating — source]" }

# --- "Capability comparison": feature-by-feature table. Use ✓ / ✕ or short text. ---
services:
  heading: "Capability comparison"
  table:
    - { label: "B2B SaaS focus",                a: "✓ Exclusive",          b: "[e.g. One of 150+ verticals]" }
    - { label: "SEO + PPC in one retainer",     a: "✓ Unified attribution", b: "[...]" }
    - { label: "Web design & development",      a: "✕ Not offered",        b: "[...]" }
    - { label: "Starting price",                a: "$3K / mo",             b: "[...]" }
    # ...add as many capability rows as you need

# --- "Team structure": intro + two columns describing each team. ---
team:
  heading: "Team structure"
  intro: >-
    [1-2 sentences on PipeRocket's pod model vs the competitor's structure.]
  columns:
    - heading: "PipeRocket pod"
      subheading: "4 senior practitioners, dedicated to your account"
      members:
        - { role: "Account strategist", seniority: "8 yrs" }
        - { role: "SEO lead",           seniority: "7 yrs" }
        - { role: "Paid media lead",    seniority: "6 yrs" }
        - { role: "Content strategist", seniority: "5 yrs" }
    - heading: "[Competitor] team"
      subheading: "[one-line description of their staffing model]"
      members:
        - { role: "[role]", seniority: "[level]" }
        - { role: "[role]", seniority: "[level]" }

# --- "Reporting": two columns of metrics. Left = typical agency, right = PipeRocket (highlighted). ---
reporting:
  heading: "What we actually report on"
  columns:
    - heading: "Most agency reports"
      metrics:
        - "Impressions — [#]"
        - "Clicks — [#]"
        - "Avg. position — [#]"
        - "CTR — [#]"
    - heading: "PipeRocket report"
      highlight: true                 # this makes the column visually stand out — keep it on PipeRocket
      metrics:
        - "MQLs — [# (+/- vs prior mo)]"
        - "SQLs — [#]"
        - "Pipeline ($) — [$]"
        - "Blended CAC — [$]"
  note: >-
    [1-2 sentences on why outcome metrics beat activity metrics.]

# --- "Pricing": intro + table of what each side actually charges. ---
pricing:
  heading: "Pricing — what you'll actually pay"
  intro: >-
    [1-2 sentences framing the price comparison.]
  table:
    - { label: "Starting price",          a: "$3K / mo",             b: "[...]" }
    - { label: "Typical operating range", a: "$4K – $8K / mo",       b: "[...]" }
    - { label: "Minimum contract",        a: "3 months",             b: "[...]" }
    - { label: "Cancellation terms",      a: "Rolling after month 3", b: "[...]" }

# --- FAQ: question + answer pairs. 5-7 is typical. Neutral tone, no hard selling. ---
faqs:
  - q: "[Question 1?]"
    a: >-
      [Answer.]
  - q: "[Question 2?]"
    a: >-
      [Answer.]
  - q: "When should I choose [Competitor] over PipeRocket?"
    a: >-
      [Honest answer naming who the competitor genuinely suits better.]

# --- Sources: numbered list backing up your claims. sources_count above must match the total. ---
sources:
  - { id: 1, title: "PipeRocket Digital — pricing, services, agency profile", url: "/", accessed: "[Month YYYY]" }
  - { id: 2, title: "Clutch — PipeRocket Digital — rating and verified reviews", url: "https://clutch.co/profile/piperocket-digital", accessed: "[Month YYYY]" }
  - { id: 3, title: "[Competitor] — website, services, positioning", url: "[https://...]", accessed: "[Month YYYY]" }
  - { id: 4, title: "Clutch — [Competitor] profile and verified reviews", url: "[https://clutch.co/profile/...]", accessed: "[Month YYYY]" }
  # ...one entry per source; keep adding until you reach sources_count

featuredImage: "/images/compare-covers/piperocket-digital-vs-[competitor].webp"
---

<!-- =========================================================================
     BODY (markdown). Only THREE tables go here. Everything above the --- line
     built the rest of the page automatically. Keep the ## headings + their text
     exactly as named — the sidebar anchors point to them.
     ========================================================================= -->

## Decision matrix — who fits which side

| Criterion | PipeRocket | [Competitor] |
|---|:---:|:---:|
| [B2B SaaS at Seed to Series B — specialist needed] | ✓ | ✕ |
| [Multi-vertical or non-SaaS business] | ✕ | ✓ |
| [Pipeline-level reporting: MQL, CAC, revenue] | ✓ | ✕ |
| [Budget $3K–$10K / mo] | ✓ | ✓ |

*Check = natural fit. Dash = possible but not the better pick. Cross = outside the model.*

## Strengths & tradeoffs

| Axis | PipeRocket | [Competitor] |
|---|---|---|
| **Vertical depth** | [PipeRocket strength] | [competitor's position] |
| **Team size** | [...] | [...] |
| **Service breadth** | [...] | [...] |
| **Reporting** | [...] | [...] |
| **Entry price** | [...] | [...] |
| **Track record** | [...] | [...] |

## Social proof

| Metric | PipeRocket | [Competitor] |
|---|---|---|
| Clutch rating | 4.9 / 5 | [x / 5] |
| G2 rating | 4.8 / 5 | [x / 5] |
| Verified reviews | 11+ | [#] |
| Lifetime clients | 50+ B2B SaaS | [#] |

> "[A real client quote — pull a verified one, don't invent.]"
>
> — **[Name]**, [Title], [Company]

---

*Competitor data sourced from publicly available information as of [Month YYYY]. Pricing and team sizes may change — verify directly with each agency.*
