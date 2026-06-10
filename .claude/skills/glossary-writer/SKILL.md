---
name: glossary-writer
description: Write a new PipeRocket glossary entry as a complete Hugo markdown file, ready to drop into content/glossary/. Use this skill whenever the user asks to write, create, or generate a glossary entry, glossary page, or "what is X" article for the PipeRocket site. Also use it when the user provides a keyword or term and asks for a glossary-format piece. The skill produces the full .md file with frontmatter, body content, internal links, Fast Facts, Also read links, FAQs, and The Bottom Line — matching the exact format of existing entries like what-is-seo.md and what-is-keyword-research.md.
model: sonnet
effort: medium
---

## What this skill does

Writes a complete PipeRocket glossary entry as a Hugo markdown file (`.md`) ready to save into `content/glossary/` on the piperocket-site project. The output matches the exact format and voice of existing entries — native Hugo markdown, no special markers.

## How to use

The user provides a keyword (the glossary term). You write the full article and either:
- Print it in the conversation for the user to copy, or
- Save it directly to `content/glossary/{slug}.md` if asked

If the user doesn't specify, ask: "Should I save it straight to content/glossary/ or paste it here first?"

---

## Output format (Hugo markdown — match this exactly)

Study these two reference files before writing:
- `/Users/omarsheriff/Desktop/piperocket-site/content/glossary/what-is-seo.md`
- `/Users/omarsheriff/Desktop/piperocket-site/content/glossary/what-is-keyword-research.md`

The format is:

```
---
title: "What Is [Keyword]? [Short angle — e.g. 'Honest Guide for SaaS Teams']"
description: "[2-3 sentence summary of the article, matches opening paragraph]"
metaTitle: "What Is [Keyword]? [Short angle]"
metaDescription: "[Max 155 chars. Answer the query, include keyword, mild CTA]"
date: [today's date YYYY-MM-DD]
slug: "what-is-[keyword-slug]"
categorySlug: "[seo or content-marketing or b2b-marketing]"
writtenBy: "kim"
glossaryCategory: "[SEO or Content Marketing or B2B Marketing]"
toc: true
readingTime: "10 min read"
---

[Opening paragraph — 2-3 sentences. No heading. Plain prose. Defines the concept.
Direct, extractable as a featured snippet. This is the Quick Answer equivalent.]

## TL;DR

- [4-5 plain declarative sentences, 15-30 words each. No bold labels. No stats/numbers unless PipeRocket-sourced.]

## What Is [Keyword]?

[Main definition section — 300-420 words. Bold-label bullets. Micro-example. Contrarian POV surfaces here.]

## [Second H2 — a question]

[250-350 words. Direct answer in first 1-2 sentences. Bold-label bullets. Fast Fact here.]

## [Third H2 — a question]

[250-350 words.]

## [Fourth H2 — a question]

[250-350 words. Fast Fact here (different section from first one).]

## [Fifth H2 — a question]

[250-350 words.]

## Frequently Asked Questions

### 1. [Question?]

[3-5 sentences. Self-contained. No bullets.]

### 2. [Question?]

[3-5 sentences. Self-contained. No bullets.]

### 3. [Question?]

[3-5 sentences. Self-contained. No bullets.]

## The Bottom Line

[2-3 sentences wrapping up. Then closing links inline.]
```

**Key formatting rules:**
- Native markdown only: `##`, `###`, `**bold**`, `> blockquote`
- Fast Facts use blockquote format: `> **Fast Fact:** [text]`
- Also read links: `**Also read:** [anchor](URL)` — placed as last line of a section
- Bullet format: `- **Label:** explanation` (bold label, never plain fragments)
- TL;DR bullets: plain sentences only, no bold labels
- FAQ headings: `### 1. Question?` (numbered)
- No horizontal rules (---), no [[markers]], no numbered lists in body

---

## Writing instructions

Use the following prompt to write the article. Replace `{keyword}` with the glossary term provided.

---

You are a SaaS expert and content writer with deep experience across product, growth, and strategy. You've worked with early-stage startups and scaling SaaS teams. You explain things the way a smart colleague would — clearly, directly, and without padding. Write like you're talking directly to the reader, not publishing for an audience. Use a conversational author-to-reader voice throughout — but keep direct answers direct.

---

STYLE ANCHOR (MANDATORY — read before writing a single sentence):
Read `/Users/omarsheriff/Desktop/piperocket-site/reference/style-anchor.md`. It contains PipeRocket's real human voice signature plus paired generic-AI → PipeRocket examples. The PIPEROCKET versions are the target. As you write, condition every sentence on that voice, not on generic-blog phrasing. Before committing any sentence, ask: "does this read like the PIPEROCKET examples, or like the GENERIC ones?" — and if it drifts generic (the reframe shape, rule-of-three serial lists, em-dashes, polished-flat cadence), rewrite it toward the human pattern. The voice signature there overrides the default fluent phrasing your instinct reaches for. Absorb the cadence; keep spelling and grammar clean.

---

BANNED TRANSITIONS:
Furthermore, Moreover, Additionally, In conclusion, To summarize, In today's world, It is important to note, This is where X comes in, X is more than just Y — it's Z, And that's not all

BANNED PUNCTUATION / FRAMINGS (hard rules):
- **No em-dashes (—) or en-dashes (–) in your prose.** Rewrite with a comma, a period, parentheses, or a colon. (e.g. "BOFU pages don't rank alone — you need authority" → "BOFU pages don't rank alone. You need authority.") The ONLY exception is the pre-approved Fast Fact boilerplate below, which you paste verbatim and may contain an em-dash — the checker exempts `> **Fast Fact:**` lines for this reason. Never introduce a dash anywhere else.
- **No "not just X but also Y" / "not only X but also Y"** framing. State the point directly.
- **No rule-of-three "X, Y, and Z" serial lists inside a sentence.** If three or more items belong together, break them into bullets, or name the two that matter and cut the third.

STRUCTURAL TELLS — BANNED MOVES (the deep AI grooves that survive a word-list; kill these explicitly):

1. **The setup-reframe.** Banned in ALL forms, including the period-chopped version:
   - "The gap isn't the keywords — it's the pages."
   - "X isn't about A, it's about B." / "It's not the page. It's the site around it."
   Just **state the point directly**. A natural end-loaded correction in flowing speech is fine *occasionally* — but never as a section's opening or punchline, and not more than once in a piece.

2. **The crafted aphoristic closer.** A short, polished fragment whose job is to sound profound at the end of a paragraph/section: "The skill is in what you cut." / "The math is unforgiving." Banned. End on a **real, plain takeaway or instruction** instead. NOTE: genuine emphasis/reaction is fine ("Period.", "fix it NOW.") — the ban is on the manufactured insight-fragment, not on short punchy reactions.

3. **Parallel-clause triads.** Not just noun lists — three parallel verb/clause beats for rhythm. Cut to two, or restructure.

4. **Invented specificity.** No fabricated numbers, names, timeframes, or details for "texture." If the number isn't from a real source, don't write it.

The style anchor (reference/style-anchor.md) shows the voice to move toward; these four rules name what to move away from. Apply both.

---

Keyword: {keyword}

Use these internal links naturally across the article where contextually relevant:

1. Topic: best SaaS SEO agencies list
   URL: https://piperocket.digital/list/best-saas-seo-agencies/
   Anchors: "best SaaS SEO agencies", "top SaaS SEO agencies"

2. Topic: best B2B marketing agencies
   URL: https://piperocket.digital/list/best-b2b-marketing-agencies-2026/
   Anchors: "best B2B marketing agencies", "B2B marketing agency"

3. Topic: best B2B SEO agencies
   URL: https://piperocket.digital/list/best-b2b-seo-agencies/
   Anchors: "best B2B SEO agencies", "B2B SEO agency"

4. Topic: best SaaS marketing agencies
   URL: https://piperocket.digital/list/best-saas-marketing-agencies-2026/
   Anchors: "best SaaS marketing agencies", "SaaS marketing agency"

5. Topic: best SaaS PPC agencies
   URL: https://piperocket.digital/list/best-saas-ppc-agencies/
   Anchors: "best SaaS PPC agencies", "SaaS PPC agency"

6. Topic: best enterprise SEO agencies
   URL: https://piperocket.digital/list/best-enterprise-seo-agencies/
   Anchors: "best enterprise SEO agencies", "enterprise SEO agency"

7. Topic: SaaS SEO agency service page
   URL: https://piperocket.digital/saas-seo-agency/
   Anchors: "SaaS SEO agency", "SaaS SEO services"

8. Topic: SaaS PPC service page
   URL: https://piperocket.digital/saas-ppc/
   Anchors: "SaaS PPC", "SaaS paid ads"

9. Topic: PipeRocket contact page
   URL: https://www.piperocket.co/contact
   Anchors: "contact us", "reach out", "get in touch"

10. Topic: PipeRocket SaaS SEO service
    URL: https://www.piperocket.co/saas-seo
    Anchors: "SaaS SEO service", "how we approach SaaS SEO"

11. Topic: PipeRocket SaaS PPC service
    URL: https://www.piperocket.co/saas-ppc
    Anchors: "SaaS PPC service", "paid search for SaaS"

Also use inline glossary links to related terms that already exist on the site (e.g. `[technical SEO](/glossary/what-is-technical-seo/)`, `[domain authority](/glossary/what-is-domain-authority/)`, `[keyword research](/glossary/what-is-keyword-research/)`) where they appear naturally in the body.

====================================================
STEP 0 — ANALYSE THE SERP BEFORE WRITING (MANDATORY)

Before writing a single word, think about what Google actually ranks for this keyword.

Ask yourself:
- What content format does Google prefer for this keyword?
- What length and depth do top-ranking pages likely have?
- What user need is the top result solving?
- Is this informational, navigational, or transactional?
- Would Google show a featured snippet? If yes, what format — paragraph, list, or table?

**SERP GAP (mandatory):**
What are the top 3 ranking pages NOT covering about this keyword?
Look for: missing angles, skipped trade-offs, ignored edge cases, surface-level treatment of a specific sub-topic.
That gap is your differentiation signal — at least one section must say something those pages don't.
Decide which section will carry this differentiated angle before you start writing.

Use these answers silently to shape the article. Do NOT write your SERP analysis in the output.

====================================================
STEP 1 — UNDERSTAND THE KEYWORD BEFORE WRITING

What does someone typing this keyword actually want? Classify intent:
- Informational → Strategist tone (depth, insight, real perspective)
- Practical → Operator tone (step-by-step, clear, no fluff)
- Comparison → Founder tone (honest trade-offs, real-world decisions)
- Decision → Founder tone (outcomes, ROI, confidence-building)

Do NOT mention intent or tone in the output.

====================================================
STEP 2 — BUILD A SHARP POINT OF VIEW (MANDATORY)

Generic content explains what something is. Sharp content argues why most people are doing it wrong.

Before writing, answer internally:

1. CONTRARIAN ANGLE — what common belief about this keyword is wrong or incomplete? This tension runs through the article and must surface in the first main H2 section.

2. DIFFERENTIATION SIGNAL — which section will say something the top 3 results don't? (This comes from your SERP gap analysis above.)

3. THREE OPINION STATEMENTS — identify 3 moments to state a clear, defensible, practitioner-level opinion. Pattern: "Most [teams] [do X]. That's [wrong] because [specific reason]."

4. PATTERN INTERRUPT — one assumption the reader brings that you'll challenge in the first main section.

Rules:
- Contrarian angle in the first main H2 — never buried in FAQs
- At least 2 opinion statements as full committed sentences in the body
- Take positions first, add nuance after — don't hedge everything with "it depends"
- POV must be specific to THIS keyword

====================================================
STEP 3 — SOLVE INTENT ACROSS THE FULL JOURNEY

Address all three stages naturally (don't label them):
1. Discovery: what is this and why does it matter?
2. Decision: how do I evaluate or apply this correctly?
3. Loyalty: what helps beyond the first read — a habit, a check, a warning?

====================================================
STEP 4 — WRITE THE ARTICLE

TOTAL LENGTH: 1,500 to 2,500 words. Do not cut sections short. If under 1,500, you've skipped something.

OUTPUT STRUCTURE:

Opening paragraph (no heading) — 2-3 sentences. Defines the concept directly. Extractable as featured snippet. Your Quick Answer.

## TL;DR
4-5 bullets. Each: single declarative sentence, 15-30 words, no bold labels, no fragments. PipeRocket-sourced stats allowed; invented stats forbidden.

## What Is [keyword]? (first H2 — direct definition)
Structure:
- Paragraph 1 (3-4 lines): define plainly, explain mechanics, state business implication. Contrarian POV surfaces here.
- Bullet list: 4-5 points in bold-label format: `- **Label:** explanation`
- Paragraph 2 (3-4 lines): micro-example (see EXAMPLE RULES)
- Paragraph 3 optional (2-3 lines): "what this means in practice"
Word count: 300-420 words

Then 4-5 more H2 sections. Each:
- Heading = a question a real user types into Google
- Paragraph 1: direct answer in 1-2 sentences, then 2-3 lines context
- Bullet list (3-5 bullets, bold-label format) — not every section needs one
- Paragraph 2: closing insight or micro-example (2-3 lines)
- Word count: 250-350 words

PRACTICAL KEYWORDS: after first H2 bullet list, add an H3 "How to [Action] Step by Step" with 5-7 bold-label bullets explaining action AND reason.

COMPARISON KEYWORDS: at least one H2 section with a pipe-format comparison table.

GLOSSARY DEPTH RULE: if a section touches on tactics or implementation, introduce the concept in 2-3 sentences and link to the relevant deeper blog post. Don't fully resolve the tactical question — leave it slightly open so the link feels like a natural next step.

## Frequently Asked Questions

Exactly 3 FAQs. Format: `### 1. [Question?]`

Each: 3-5 sentences, specific, self-contained, no bullets. Include a number/timeframe/comparison where possible. FAQ answers are the one place the 50-word paragraph cap does NOT apply (a 3-5 sentence answer naturally runs 60-90 words); the checker exempts the FAQ section accordingly. Keep them tight, but don't chop a complete answer to hit a word count.

**FAQ SELECTION RULE (mandatory):** FAQs must answer questions a reader has AFTER reading the article — about application, edge cases, or next steps. Do NOT write FAQs that answer questions already covered in the body.

Good FAQ questions:
- "What's the difference between X and Y in a real scenario?" (edge case)
- "When does this approach break down?" (failure condition)
- "How do I know if X is working?" (measurement/next step)
- "Should I prioritise X or Y first?" (decision trigger)

Bad FAQ questions (already in the article):
- "What is [keyword]?" — answered in the first H2
- "Why does [keyword] matter?" — answered in the body
- "What are the types of [keyword]?" — covered in a section

## The Bottom Line

2-3 sentences. Say something new — don't recap. Tell the reader what to do differently. Then one sentence with closing links.

====================================================
H3 RULES

Only use H3 when there are 2+ genuinely distinct sub-topics in a section. Each H3:
- Short noun phrase (2-4 words), never a question
- Opens with a direct answer or clear label
- Contains 1-2 paragraphs OR 1 paragraph + bullets
- 120-200 words minimum — never a stub

====================================================
EXAMPLE RULES (MANDATORY)

Include exactly 2-3 micro-examples across the full article.

Each must:
- Use a specific fictional SaaS with a clear niche (e.g. "a procurement SaaS for fintech teams")
- Describe the situation or pattern in concrete terms
- Be 2-4 lines, embedded naturally — never introduced as "Example:"
- NO invented outcome metrics on fictional companies (no "churn dropped 28%", no "doubled revenue")

Good framing: "Consider a SaaS that..." / "A compliance tool for..." / "Imagine a project management tool for..."

If you have a real verifiable case study (Spendflo, CyberSierra) you may use it with real numbers.

====================================================
FAST FACT CALLOUTS — MANDATORY

Include exactly 2 Fast Facts in different H2 sections (never in TL;DR).

Format — blockquote on its own line:
`> **Fast Fact:** [one sentence, directly relevant to the section]`

If keyword is SEO/search/content-related, use 2 from:
- `> **Fast Fact:** Organic search drives 91.3% of SaaS traffic — AI-referred visits account for less than 9%.`
- `> **Fast Fact:** Organic search converts SaaS visitors at 0.92% — more than 3x the rate of AI-driven traffic at 0.26%.`
- `> **Fast Fact:** Users from organic search spend an average of 4 minutes 40 seconds on SaaS pages, nearly a full minute longer than AI-referred visitors.`
- `> **Fast Fact:** Organic search drives 37x more SaaS leads than AI search tools, yet most teams treat them as equal channels.`

If NOT SEO-related: write 2 Fast Facts as observed industry patterns — no invented stats or percentages.

====================================================
ALSO READ LINKS

Place `**Also read:** [anchor text](URL)` as the very last line of a section (after all paragraphs/bullets, before the next ##). Use at least 2 across the article in different sections.

Test: does the surrounding paragraph raise a need the linked page directly answers? If yes, link. Never retrofit.

Each URL used at most once. Never use the same URL for both an inline link and an Also read link.

====================================================
INTERNAL LINKS

Place contextual inline links, Also read links, and closing links wherever they naturally fit. Do not force links to hit a number.

Before placing a link: has the surrounding paragraph just raised a need the linked page answers? If yes, link. If it's just a shared keyword, skip it.

Closing links go in The Bottom Line — contact page + one relevant service or list page.

All links in markdown format: `[anchor text](URL)`

====================================================
PARAGRAPH LENGTH — MANDATORY

Maximum 50 words per paragraph. Count strictly. Break or trim if over. Exception: FAQ answers (3-5 sentences) are exempt — the checker skips the FAQ section.

====================================================
STATS RULES

SEO/content keywords: use 2-3 of the PipeRocket stats listed in Fast Facts above.
Non-SEO keywords: skip these stats entirely.

NEVER invent statistics. Describe patterns in words if no real number exists.

====================================================
E-E-A-T SIGNALS (ALL THREE REQUIRED)

1. A REAL TRADE-OFF: "[Approach X] gives you [benefit], but it [fails] when [condition]. It's worth it if [situation]."
2. A CONTRARIAN INSIGHT: "[Common practice] is wrong because [mechanism]. What works instead is [alternative]."
3. A NUANCED WARNING: "This works for [situation]. For [different situation], it [fails] because [reason]."

These must read like lived experience. Specific to THIS keyword — never recycled.

====================================================
SECONDARY KEYWORDS / LSI

Before writing, generate variations, secondary keywords, entity keywords, and LSI phrases for this keyword. Weave them in naturally — never forced, never clustered.

====================================================
HUMAN WRITING RULES

Contractions always: it's, you're, don't, here's, won't.
Max 50 words per paragraph.
Vary sentence length — short punchy sentences after longer ones.
Never start 2+ paragraphs in a row with the same word.

BANNED WORDS (never use):
delve, tapestry, underscore (verb), unpack, pivotal, paramount, transformative, holistic, synergy, paradigm, groundbreaking, leverage, utilize, robust, streamline, scalable (standalone), comprehensive (vague), empower, foster, facilitate, navigate (metaphor), unlock (metaphor), harness, elevate, actionable, dynamic (filler), ecosystem (metaphor), landscape, space (business context), journey (business), pain points, thought leader/leadership, deep dive, world-class, industry-leading, end-to-end, mission-critical, value-add, content architecture

BANNED OPENERS (never start a sentence with):
Certainly, Absolutely, It's worth noting, It is important to note, As we can see, In order to, At the end of the day, Furthermore, Moreover, Additionally, In conclusion, In today's landscape, What separates X is Y, The answer lies in, Let's explore, Here's why that matters, But here's the thing

Open with the problem or finding — not the topic label.
Write conclusions that say something new — not recaps.
Paragraphs should end with weight, not summaries.

====================================================
FINAL CHECK BEFORE OUTPUTTING

[ ] 1,500-2,500 words
[ ] Opening paragraph 2-3 sentences, no heading, extractable as featured snippet
[ ] TL;DR: 4-5 plain sentences, 15-30 words, no bold labels
[ ] All H2 headings are questions (except The Bottom Line)
[ ] H3 headings are short noun phrases (not questions)
[ ] Contrarian angle in first main H2
[ ] Differentiation signal — at least one section says something top-3 results don't
[ ] 2+ opinion statements as full committed sentences
[ ] All 3 E-E-A-T signals present
[ ] Bold-label bullet format throughout (except TL;DR)
[ ] No numbered lists in body
[ ] Exactly 2 Fast Facts in blockquote format, different sections, not in TL;DR
[ ] FAQ: exactly 3, numbered (### 1.), post-article questions only, no bullets
[ ] The Bottom Line says something new, ends with closing links
[ ] 2-3 micro-examples, no invented outcome metrics on fictional companies
[ ] No invented statistics anywhere
[ ] Internal links placed naturally throughout (inline + Also read + closing)
[ ] No URL used more than once
[ ] All Also read links are full markdown [anchor](URL), last line of section
[ ] Every paragraph ≤ 50 words
[ ] Zero banned words
[ ] Native Hugo markdown only (##, ###, >, **bold**) — no [[markers]]
[ ] 1-2 infographics generated, converted to WebP, and embedded in the article

---

## MANDATORY: run the rule checker before confirming

After saving the `.md` file (and embedding the infographics), you MUST run the
bundled rule checker and act on its output. Do not tell the user the entry is
done until the checker passes its hard checks.

```bash
# run from the repo root (piperocket-site)
python3 .claude/skills/glossary-writer/check_glossary.py content/glossary/<slug>.md
```

The script lives next to this SKILL.md. It mechanically verifies the
deterministic rules and prints PASS / WARNINGS / FAILURES with line numbers:

- **FAILURES** (exit code 1): hard violations — em/en-dashes in prose, banned
  words, "not just X but also Y" framing, missing frontmatter fields,
  metaDescription > 155 chars, paragraphs > 50 words, wrong FAQ count, wrong
  Fast Fact count, Fast Fact inside TL;DR, missing required sections, missing
  infographic, word count < 1500, `[[markers]]`, body horizontal rules.
  **Edit the file to fix every FAILURE, then re-run until it exits 0.**
- **WARNINGS**: review each (non-question H2, question H3, TL;DR bullet count,
  numbered lists, word count > 2500, metaTitle > 60). Fix unless deliberate.
- **MANUAL REVIEW**: the checker prints the rules it can't test mechanically
  (setup-reframe, aphoristic closers, parallel-clause triads, invented
  specifics, voice match, contrarian angle, E-E-A-T signals). Re-read the draft
  against each before confirming.

Only after the checker exits 0 and you've completed the manual-review pass do
you give the user the "Saved to content/glossary/{slug}.md" confirmation.

---

## Infographics

Generate **1–2 SVG infographics** per article. Place each as a standard markdown image immediately after a relevant H2 section — not at the start, not in FAQs or Bottom Line.

### Design spec

| Property | Value |
|---|---|
| SVG root | `<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="1200" height="630" viewBox="0 0 1200 630">` — **must include width and height or it won't render** |
| Background | `<rect width="1200" height="630" fill="#C7E6EE"/>` (palest brand blue; see Global Visual Standard) |
| No panels | Flat layout — no card boxes or coloured backgrounds behind content |
| Title font | `font-family="'IvyPresto Headline', Georgia, Times, serif"` |
| Body font | `font-family="'Helvetica Neue', Helvetica, Arial, sans-serif"` |
| Primary text | `#0D0D0D` |
| Muted text | `rgba(13,13,13,0.45)` for labels; `rgba(13,13,13,0.68)` for descriptions |
| Dividers | `rgba(13,13,13,0.08)` to `rgba(13,13,13,0.15)` |
| Logo | Inline PipeRocket logo paths at `transform="translate(50, 26) scale(0.65)"` — copy from reference SVG below |
| Title | IvyPresto Headline 28px 600, `#0D0D0D`, at x=50 y=86 |
| Header divider | `<rect x="50" y="104" width="1100" height="1.5" fill="rgba(13,13,13,0.15)"/>` |
| Content area | Starts at y=112, x=50 to x=1150 |

### Logo block (copy verbatim into every infographic)

```xml
<defs>
  <linearGradient id="pr-logo-grad" x1="15.9" x2="33.9" y1="16" y2="16" gradientUnits="userSpaceOnUse">
    <stop stop-color="#ff0025"/><stop offset="1" stop-color="#ff0025"/>
  </linearGradient>
</defs>
<g transform="translate(50, 26) scale(0.65)">
  <path fill="#0ba6e2" d="M32.6 0h-16l-.7.3-15.6 16A1 1 0 0 0 .9 18H16v13a1 1 0 0 0 1.6.6l16-15.6q.3-.2.3-.6V1.2Q33.8.1 32.6 0"/>
  <path fill="url(#pr-logo-grad)" d="M16 17.9V31a1 1 0 0 0 1.6.6l16-15.6q.3-.2.3-.6V1.2Q33.8.1 32.6 0h-16q-.6 0-.7.5"/>
  <path fill="#0d0d0d" d="M45.3 21.5V1.2h8.5l1.7.1q1.8.3 3 1.2 1 1 1.7 2.3.5 1.5.5 3.1 0 1.8-.5 3.1t-1.7 2.3-3 1.2l-1.7.1h-4.7v6.9zM49 11h6q.8-.3 1.2-.7.5-.5.6-1.1a5 5 0 0 0 0-2.4q0-.6-.6-1-.5-.6-1.2-.8l-.6-.1H49zm18.7-4.7h-3.9v15.2h3.9zm0-3.7a2 2 0 0 0-3.8 0v.1a2 2 0 0 0 3.8 0m17.7 7a7 7 0 0 0-6.3-3.9 6 6 0 0 0-3.9 1.3v-.8h-3.4v22h3.9v-7.4q1.5 1 3.6 1t3.7-1 2.5-3q.8-1.7.8-4t-.9-4.2M82 16.2q-.3 1-1.2 1.7t-2 .6-2-.6-1.1-1.6q-.4-1-.4-2.4t.4-2.4 1-1.7a3 3 0 0 1 2-.5q1.2 0 2 .6t1.3 1.7.4 2.3-.4 2.3m21.4-1.2q.2-2.8-.6-4.8a6.5 6.5 0 0 0-6.5-4.3q-2.3 0-4 1t-2.7 2.8a9 9 0 0 0-1 4.4 8 8 0 0 0 1 4 7 7 0 0 0 2.8 2.8 8 8 0 0 0 8.1-.2 7 7 0 0 0 2.8-3.2l-3.9-1q-.5.8-1.2 1.3-.8.6-2 .5-1.7 0-2.6-1.1-.7-.9-.9-2.3zm-10.6-3q.3-1 .8-1.7.9-1.2 2.8-1.2t2.5 1q.4.6.6 1.9zm25.8 2a5 5 0 0 0 2.2-1.7 7 7 0 0 0 1.2-4.4q0-1.7-.5-3-.6-1.5-1.7-2.4t-3-1.2h-10.3v20.2h3.9v-6.9h4.2l3.4 6.9h4.3zm-8.2-9.2h4.5l1.3.1q.8.3 1.2.7.4.5.6 1.1l.2 1.2-.2 1.2q-.2.6-.6 1t-1.2.8l-.6.1h-5.2zm21.8 17.1q-2.2 0-4-1t-2.7-2.9q-1-1.8-1-4.1 0-2.4 1-4.2a7 7 0 0 1 2.8-2.8q1.6-1 4-1 2.2 0 4 1t2.7 2.8q1 1.8 1 4.2t-1 4.1a7 7 0 0 1-2.7 2.9q-1.8 1-4 1m0-3.6q2 0 2.8-1.2.9-1.4.9-3.2 0-2-1-3.3-.8-1.2-2.7-1.2-1.2 0-2 .6t-1.2 1.6-.4 2.3q0 2 1 3.2.8 1.2 2.6 1.2m17.4 3.6q-2.3 0-4-1a7 7 0 0 1-2.6-3 9 9 0 0 1-.9-4q0-2.3 1-4.1a7 7 0 0 1 6.6-4q2.7 0 4.5 1.4a6 6 0 0 1 2.3 3.7l-3.8 1q-.3-1.2-1.2-1.8a3 3 0 0 0-1.9-.7q-1.2 0-2 .6-.7.6-1 1.6t-.4 2.3q0 2 .8 3.2 1 1.2 2.6 1.2 1.4 0 2-.6t1-1.7l4 .9a7 7 0 0 1-2.5 3.7 7 7 0 0 1-4.5 1.3m9.7-.4V1.2h4v12.4l5-7.3h4.8l-5.5 7.6 5.9 7.6h-5l-5.3-7.3v7.3zm29.3-6.5q.2-2.8-.6-4.8a7 7 0 0 0-2.5-3.2 7 7 0 0 0-4-1.1q-2.4 0-4 1t-2.8 2.8q-1 1.9-1 4.4a8 8 0 0 0 1 4 7 7 0 0 0 2.9 2.8 8 8 0 0 0 8.1-.2 7 7 0 0 0 2.7-3.2l-3.8-1q-.4.8-1.2 1.3t-2 .5q-1.6 0-2.7-1.1-.6-.9-.8-2.3zM178 12q.2-1 .7-1.7.9-1.2 3-1.2 1.5 0 2.3 1 .5.6.7 1.9zm18.5-2.8v5.6l.3 2.7q.6.9 1.7 1l2.4-.2v3.2q-1.5.3-3 .2-1.6 0-2.8-.5t-1.8-1.6l-.6-2.1V9.2h-2.6v-3h2.6v-4h3.8v4.2h4.4v3z"/>
</g>
```

### GLOBAL VISUAL STANDARD (v2 — applies to EVERY format, overrides any older faint-number / low-contrast guidance below)

The older specs rendered at 1x with ghost-faint giant numerals and washed-out gray text on the light ground, which looked low-quality. Every infographic now follows these rules:

- **BRAND PALETTE — use these exact values (no off-brand navy or pure black):**
  - Background: **`#C7E6EE`** (palest brand blue). This replaces the old `#D2E5EC`.
  - Primary text / titles / values: **`#282828`** (brand dark, NOT `#0D0D0D`). Body `rgba(40,40,40,0.82)`, small labels `rgba(40,40,40,0.5)`, footer note `rgba(40,40,40,0.55)`, hairline dividers `rgba(40,40,40,0.12)`.
  - Accent blue: **`#0BA6E2`** (badges, keylines, accent tick, header underlines, the highlighted/active element).
  - Blue tint scale for funnel / stacked / gradient bars: **`#0BA6E2` → `#3AB6E5` → `#69C6E8` → `#98D6EB`** (darkest = most important/first). NO navy.
  - Red scale for callouts / emphasis only: **`#FD314E`** (or `#FF0025` for the strongest). Use sparingly, e.g. a "watch out" callout.
  - White cards on the blue ground use `#FFFFFF` (or `#F6F6F1`).
- **Render at 2x.** `rsvg-convert -w 2400 -h 1260 file.svg | magick - -quality 92 out.webp` (viewBox stays `0 0 1200 630`; you just rasterize at double). This is the single biggest crispness win on retina screens.
- **Accent tick** under the logo: `<rect x="50" y="74" width="34" height="5" rx="2.5" fill="#0BA6E2"/>` (title then sits at y≈118; without the tick, title at y≈96).
- **Numbered badges, not ghost numerals.** For any sequential / step / ranked format, each item gets a filled circle `r="23"` in `#0BA6E2` with a centered white number (`Helvetica Neue 700 22px`, baseline at `cy+8`). NEVER the old `rgba(13,13,13,0.07)` giant numbers, and never a stray different-colored number.
- **Connect sequential steps** with a thin vertical keyline behind the badges: `<line stroke="#0BA6E2" stroke-width="2.5" stroke-opacity="0.28"/>` from the first badge centre to the last.
- **Contrast floor.** Primary/body text `rgba(40,40,40,0.82)` minimum; titles/values `#282828`. Light-gray-on-light-blue for primary content is banned.
- **Use the full canvas — no dead half.** Default to a two-zone layout: left zone x≈60–560 (badge + IvyPresto step title), a vertical divider at x≈580, right zone x≈610–1140 (description, up to 2 lines). Content should reach ~x1140.
- **Rich style for funnel/comparison content (preferred):** stacked or paired bars filled with the blue tint scale, optional white "why" card on the right, a single red `#FD314E` callout for the one "gotcha." This reads as more designed than flat rows — use it for funnels, build orders, and X-vs-Y comparisons.

The format entries below define each layout's *skeleton*; apply the standard above on top of them (badges, 2x, contrast, full canvas, accent).

### Format — pick what fits (9 tested formats)

**Format: Columns** (keyword has 3–4 distinct components, pillars, or types)
- 3 or 4 equal-width columns from x=50 to x=1150, separated by vertical `<line stroke="rgba(13,13,13,0.12)">` dividers
- Each column: large muted number (IvyPresto 52px, `rgba(13,13,13,0.07)`), label (HN 700 10px uppercase, `rgba(13,13,13,0.45)`), title (HN 700 18px `#0D0D0D`), 2-line description (HN 400 13px `rgba(13,13,13,0.68)`), thin `<rect height="1" fill="rgba(13,13,13,0.1)">` rule, then 4–5 bullet lines (HN 400 13px `#1a1a1a`)
- Use for: SEO pillars, content types, ICP layers, GTM components

**Format: Rows** (keyword is a sequential process or step-by-step)
- 4–5 full-width rows each 90px tall, separated by `<rect height="1" fill="rgba(13,13,13,0.08)"/>`
- Vertical divider `<line>` at x=420 splitting left zone from right zone
- Left zone (x=60–400): muted number (IvyPresto 52px `rgba(13,13,13,0.07)`), label (HN 700 10px uppercase `rgba(13,13,13,0.45)` at x=155), title (HN 700 18px `#0D0D0D` at x=155)
- Right zone (x=440–1140): 2-line description (HN 400 13px `rgba(13,13,13,0.72)`)
- Use for: how X works, audit steps, implementation stages, lifecycle

**Format: Comparison** (keyword contrasts two things directly)
- 3 columns: attribute label (x=50–440), left option (x=460–820), right option (x=840–1150)
- Vertical dividers `<line stroke="rgba(13,13,13,0.1)">` at x=440 and x=820
- Header row with IvyPresto 22px column titles; attribute labels in HN 700 10px uppercase `rgba(13,13,13,0.45)`; values in HN 400 13px `#1a1a1a`
- Horizontal `<rect height="1" fill="rgba(13,13,13,0.08)">` between each row
- Use for: SEO vs SEM, organic vs paid, on-page vs off-page, inbound vs outbound

**Format: Definition + Facts** (one crisp definition + 3–4 key numbers or benchmarks)
- Left zone (x=50–760): "DEFINITION" label (HN 700 10px uppercase muted), then IvyPresto 26px pull-quote `#0D0D0D` (3–4 lines), then 2-line supporting note (HN 400 13px `rgba(13,13,13,0.65)`)
- Vertical divider `<line>` at x=760
- Right zone (x=790–1150): "KEY FACTS" label, then 4 stacked fact blocks each with thin `<rect height="1">` divider above, HN 700 11px label (`rgba(13,13,13,0.5)`), IvyPresto 20px value (`#0D0D0D`)
- Use for: ARR, CAC, CLV, NRR, ROAS, conversion rate, domain authority

**Format: Funnel** (a narrowing qualification or conversion process)
- 4–5 `<polygon>` trapezoids stacked vertically, each narrowing inward by ~80–100px per side
- Fills stack with increasing opacity: `rgba(13,13,13,0.07)` → `rgba(13,13,13,0.18)` top to bottom
- Each stage: centered HN 700 14px stage name + HN 400 12px `rgba(13,13,13,0.6)` one-line description
- 4px gap between stages; italic note below the last stage
- Use for: lead gen funnel, sales pipeline, conversion funnel, content funnel (TOFU→BOFU)

**Format: Nested Rings** (layered or hierarchical relationships within a whole)
- 3 concentric `<circle>` elements centred at ~(420, 375), radii ~200/130/66, cumulative `rgba(13,13,13,0.06)` fills
- Inner ring labels in IvyPresto 15px `rgba(13,13,13,0.4–0.7)` placed inside each ring
- Connector `<line stroke="rgba(13,13,13,0.2)">` from ring edge to right-side callout labels
- Right callout per ring (x≈730): HN 700 11px uppercase label, IvyPresto 20px headline, HN 400 13px `rgba(13,13,13,0.65)` 2-line description; `<rect height="1">` dividers between callouts
- Use for: TAM/SAM/SOM, ICP tiers, market segmentation, topic cluster depth

**Format: Formula** (a calculable metric with defined variables)
- "THE FORMULA" eyebrow (HN 700 10px uppercase centered), IvyPresto 48px equation centered (e.g. `ROAS = Revenue ÷ Ad Spend`)
- Thin horizontal `<rect height="1">` rule below equation
- 3-column variable breakdown (equal widths, vertical `<line>` dividers): HN 700 10px uppercase label, IvyPresto 18px variable name, HN 400 13px `rgba(13,13,13,0.65)` 2-line explanation + benchmark
- Thin `<rect height="1">` rule below variable section
- "WORKED EXAMPLE" eyebrow, IvyPresto 36px worked calculation centered, HN 400 13px explanatory note
- Use for: ROAS, ARR, CAC, CLV, NRR, conversion rate, CPC, CPM

**Format: Spectrum** (a concept that exists on a sliding scale or continuum)
- Directional labels above bar: "PURCHASE INTENT" left, "HIGH INTENT →" right (HN 700 10px uppercase `rgba(13,13,13,0.35)`)
- Gradient `<rect>` bar (height=70, rx=6) using SVG `<linearGradient>` from `rgba(13,13,13,0.06)` to `rgba(13,13,13,0.22)`
- Vertical `<line>` dividers at 1/3 and 2/3 of bar width; zone names in IvyPresto 20px centered in each zone
- Stage label (HN 700 10px uppercase) below each zone
- Three columns below bar (same vertical dividers): example keywords (HN 400 13px `rgba(13,13,13,0.7)` centered), then content type row separated by `<rect height="1">`
- Use for: keyword intent, ad temperature (cold/warm/hot), content funnel stages, lead maturity

**Format: People Pictograph / Isotype** (a "few out of many" proportion, or a worked numeric example where the point is how small the qualifying slice is)
- A grid of 100 small person glyphs (10 columns x 10 rows). Each glyph = a head + shoulders: `<circle r="6.4">` for the head plus `<path d="M cx-9 cy+18 a 9 9 0 0 1 18 0 Z">` for the shoulders dome (NOTE: sweep-flag 1 gives the upward dome that reads as a person). Grid spacing ~42px x / ~37px y, starting around x=80 y=168.
- Fill the qualifying few (e.g. 5) in solid `#0d0d0d`; fill the rest in `rgba(13,13,13,0.16)`. Fill a contiguous top-left block (NOT scattered) so the proportion reads instantly.
- Vertical `<line stroke="rgba(13,13,13,0.12)">` at ~x=540 splitting the grid from a right zone.
- Right zone: a 2-row legend (one filled glyph + HN 700 15px label + HN 400 13px sub; one muted glyph + label + sub), a `<rect height="1">` divider, then a stacked cascade ("THE MATH, STEP BY STEP" eyebrow HN 700 11px uppercase, then IvyPresto 24px value + HN 400 14px label per step), and an emphasized result row (IvyPresto 26px) above a final divider.
- Italic HN 400 13px `rgba(13,13,13,0.55)` note across the bottom.
- Use for: clicks-to-conversions math, ICP-fit ("4 of 100 searchers can buy"), trial-to-paid, MQL-to-SQL, any "the big number is mostly noise" point. This is the strongest visual for proportion. Reusable generator: see the volume-vs-intent blog's infographic-3 (script pattern in the writer's notes).

### SVG quality rules

- `width="1200" height="630"` on the `<svg>` root — mandatory, omitting this breaks rendering
- All `<title>` and `<desc>` elements present for accessibility
- Long text lines use `<tspan>` — never rely on SVG auto-wrap
- No embedded images or base64 — pure SVG primitives only
- No text element extends past x=1150 or y=615

### Generation workflow — output is WebP, not SVG

Infographics are embedded as `.webp` files. SVG is only an intermediate step.

**Step 1 — Write the SVG to a temp file:**
```
/tmp/{slug}-infographic-{n}.svg
```

**Step 2 — Convert to WebP (single command):**
```bash
rsvg-convert -w 2400 -h 1260 /tmp/{slug}-infographic-{n}.svg | magick - -quality 92 /Users/omarsheriff/Desktop/piperocket-site/static/images/glossary-infographics/{slug}-infographic-{n}.webp
```

**Step 3 — Delete the temp SVG:**
```bash
rm /tmp/{slug}-infographic-{n}.svg
```

**Step 4 — Embed in the article markdown after the relevant H2:**
```
![{One sentence describing what the infographic shows}](/images/glossary-infographics/{slug}-infographic-{n}.webp)
```

---

## Frontmatter to generate

```yaml
---
title: "What Is [Keyword]? [Short angle]"
description: "[2-3 sentence summary matching opening paragraph]"
metaTitle: "What Is [Keyword]? [Short angle, max 60 chars]"
metaDescription: "[Max 155 chars. Keyword + value + mild CTA]"
date: [today YYYY-MM-DD]
slug: "what-is-[keyword-slug]"
categorySlug: "[seo | content-marketing | b2b-marketing]"
writtenBy: "kim"
glossaryCategory: "[SEO | Content Marketing | B2B Marketing]"
toc: true
readingTime: "10 min read"
---
```

No `wp_id` or `wp_link` — these are new entries not imported from WordPress.

**categorySlug / glossaryCategory mapping:**
- SEO, technical SEO, keyword research, backlinks, domain authority, schema, crawling, indexing, SERP, GEO, AEO → `seo` / `SEO`
- Content marketing, content audit, thought leadership, editorial → `content-marketing` / `Content Marketing`
- B2B marketing, demand gen, ABM, lead gen, ICP → `b2b-marketing` / `B2B Marketing`

---

## Saving the file

Save to: `/Users/omarsheriff/Desktop/piperocket-site/content/glossary/{slug}.md`

Where `{slug}` is the slug from the frontmatter (e.g. `what-is-anchor-text`).

After saving, confirm: "Saved to content/glossary/{slug}.md — ready to preview at http://localhost:1313/glossary/{slug}/"
