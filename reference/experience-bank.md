# PipeRocket Experience Bank

A repository of first-hand experience, proprietary data, and named frameworks — mined once from real sources, reused across every article. The `tofu-mofu-writer` skill reads this during Phase 1 and pre-allocates relevant entries to article sections, the same way it reads the content-plan CSV.

This file is internal. It lives in Hugo's `data/` directory so it's version-controlled but never rendered as a page.

---

## How the skill uses this

1. During Pre-flight / Phase 1, grep this file by the article's topic tags.
2. Surface every entry whose `Tags` overlap the article topic.
3. **Apply the discipline layer** (see below) — drop over-used entries, honor verify flags, respect rotation.
4. In the Pass 1 brief's EXPERT CONTENT PRE-ALLOCATION block, assign the surviving entries to sections — alongside any CSV Q&A answers.
5. In Pass 2, weave them in per the `Usage` and `Type` rules (see the skill's Expert Content Rules).
6. **After publishing, record what was used in the USAGE LEDGER** (below).

The CSV Q&A cell and this bank are two inputs to the same pre-allocation step. CSV answers are article-specific; bank entries are reusable across many articles.

---

## Entry schema

```
### [short-id]
Source: report:ai-seo-stats | blog:<slug> | linkedin:<handle> | video:linkedin | qa:csv
Author: kim | praveen | ranjeeth | ...
Tags: comma, separated, topic, tags
Type: stat | anecdote | framework | opinion | trade-off | warning
Tier: 1 (first-party data / real client) | 2 (named framework / spoken opinion) | 3 (pattern observation)
Usage: exact-quote-ok | paraphrase-only | anonymize-client
Verify: [optional] a specific claim in this entry that is third-party/unconfirmed — confirm before publishing as fact, or cut it
Content: the actual number, claim, story, or quote
```

**Realness tiers** — prefer higher tiers when both fit a section:
- **Tier 1** — real numbers from the proprietary dataset or named real clients. Un-fakeable. Strongest E-E-A-T.
- **Tier 2** — named internal frameworks, spoken opinions from interviews/LinkedIn.
- **Tier 3** — general pattern observations ("most teams I've seen...").

**Usage flags:**
- `exact-quote-ok` — the wording can be used verbatim as a blockquote.
- `paraphrase-only` — weave the substance into narrative voice; don't quote verbatim.
- `anonymize-client` — never name the client; describe by vertical/size only.

---

## THE DISCIPLINE LAYER (read before every selection)

The bank is large enough that the risk is no longer "too little material" — it's the same stories and POVs getting reused until they become a tell. These rules are mandatory during Phase 1 selection.

### 1. Rotation (check the Usage Ledger)
Before assigning any entry, check the **Usage Ledger** at the bottom of this file.
- **A Tier-1 client story (anecdote) may not be reused within 5 published articles.** If it was used recently, pick a different one or rely on the framework entries instead.
- **A specific POV/framework should not headline more than 1 in 3 consecutive articles.** The recurring greatest-hits — "pipeline not traffic," "BOFU-first," "intent over volume," "narrow your audience," "search-terms waste" — can appear as a supporting line anytime, but should anchor a section only if they haven't anchored the last two articles.

### 2. Anti-stacking
- Max **one Tier-1 client story per section**. Two real before/afters in one section reads like a highlight reel and invites "are these even real?"
- Max **3 bank entries per article** as section anchors. More than that and the piece stops being the author's argument and becomes a clip show.

### 3. Verification gate
- Any entry with a `Verify:` field: do NOT publish that specific claim as fact unless it's confirmed. Either confirm it, cut the number and keep the qualitative point, or attribute it ("industry estimates suggest…"). PipeRocket-measured numbers (AI report, real client stories) are exempt.

### 4. Collision check
- If two surfaced entries carry similar-but-different numbers (e.g. two audience-penetration stories, two "$10M client" stories), use only ONE per article. Mixing them in the same piece reads inconsistent.

### 5. Attribution honesty
- Use an entry's `Author` to decide voice. If the entry author ≠ the article author, attribute to "our team"/"we've seen", never first-person "I". Never put a colleague's story in another person's mouth under their byline.

---

# SOURCE: AI SEO Statistics Report (proprietary)

Proprietary 8-month analysis of 53 B2B SaaS brands. Published at `/research/ai-seo-statistics/`. All entries below are Tier 1 first-party data. Author: Kim. These are the strongest stats available — real, defensible, citable. Always frame them as "across the 53 B2B SaaS brands we analysed over 8 months" so the provenance is clear.

> Note: the report's section 7 contains third-party industry stats (Gartner, Forrester, etc.) with inline sources. Those are NOT first-party and are not stored here — cite them directly from the report when needed.

### aiseo-organic-vs-ai-traffic-share
Source: report:ai-seo-stats
Author: kim
Tags: ai-search, organic-vs-ai, traffic-volume, geo, aeo
Type: stat
Tier: 1
Usage: exact-quote-ok
Content: Across the 53 B2B SaaS brands we analysed over 8 months, 91.3% of all traffic came from organic search and only 8.7% from AI engines combined — organic drove 11x more traffic than every AI engine put together.

### aiseo-leads-37x
Source: report:ai-seo-stats
Author: kim
Tags: ai-search, organic-vs-ai, lead-generation, pipeline, conversion
Type: stat
Tier: 1
Usage: exact-quote-ok
Content: Organic generated 37x more leads in absolute terms than all AI referral sources combined, and converted visitors to leads at 0.92% — nearly 3.5x the AI rate of 0.26%.

### aiseo-lead-to-sql
Source: report:ai-seo-stats
Author: kim
Tags: ai-search, organic-vs-ai, lead-generation, pipeline, sql, conversion
Type: stat
Tier: 1
Usage: exact-quote-ok
Content: Organic leads converted to Sales Qualified Leads at 33.3%, versus 28.6% for AI-sourced leads — organic doesn't just send more traffic, it sends traffic that closes better.

### aiseo-chatgpt-dominance
Source: report:ai-seo-stats
Author: kim
Tags: ai-search, chatgpt, perplexity, ai-platforms, geo
Type: stat
Tier: 1
Usage: exact-quote-ok
Content: ChatGPT drove 65.8% of all AI referral traffic across the dataset, with Perplexity second at 24.6% — the two together own 90.4% of AI referrals. Gemini (5.4%), Copilot (3.1%), and Claude (1.1%) split the rest.

### aiseo-copilot-quality-over-volume
Source: report:ai-seo-stats
Author: kim
Tags: ai-search, copilot, ai-platforms, pipeline, sql, enterprise
Type: stat
Tier: 1
Usage: exact-quote-ok
Content: Despite contributing only 3.1% of AI traffic, Microsoft Copilot delivered the highest Lead-to-SQL rate (35%) and highest engagement (73.4%) of any AI platform — its users arrive from inside enterprise productivity tools, already in "work mode." Volume does not equal quality.

### aiseo-platform-spread
Source: report:ai-seo-stats
Author: kim
Tags: ai-search, ai-platforms, sql, conversion
Type: stat
Tier: 1
Usage: paraphrase-only
Content: There was a 20-percentage-point spread in Lead-to-SQL rates across the five AI platforms — Copilot 35%, ChatGPT 30%, Perplexity 25%, Gemini 20%, Claude 15%. Treating "AI traffic" as one bucket hides which platforms actually convert.

### aiseo-engagement-gap
Source: report:ai-seo-stats
Author: kim
Tags: ai-search, organic-vs-ai, engagement, bounce-rate, on-site-behaviour
Type: stat
Tier: 1
Usage: exact-quote-ok
Content: Organic visitors spent an average of 4 minutes 40 seconds on page — 75 seconds longer than AI-referred visitors (3m 25s) — and bounced less often (36.7% vs 43.6%).

### aiseo-bofu-skew
Source: report:ai-seo-stats
Author: kim
Tags: funnel-stage, bofu, tofu, ai-search, organic-vs-ai, search-intent
Type: stat
Tier: 1
Usage: exact-quote-ok
Content: AI sessions skewed harder toward bottom-of-funnel than organic — 44% BoFu vs 41% — but organic still drove 4.4x more BoFu traffic in absolute volume across the dataset.

### aiseo-brand-intent-gap
Source: report:ai-seo-stats
Author: kim
Tags: brand-intent, search-intent, ai-search, organic-vs-ai, branded-search
Type: stat
Tier: 1
Usage: exact-quote-ok
Content: Only 11.8% of AI-referred sessions carried brand-name search intent, versus 28.1% for organic — a 16.3-point gap. AI surfaces categories before brands; 88.2% of AI sessions were non-branded.

### aiseo-cybersecurity-trust
Source: report:ai-seo-stats
Author: kim
Tags: vertical, cybersecurity, trust, sql, conversion, organic-vs-ai
Type: stat
Tier: 1
Usage: exact-quote-ok
Content: In Cybersecurity SaaS, organic leads converted to SQLs at 81% while AI-referred leads converted at just 20% — a 61-point gap. In trust-heavy categories, buyers verify through branded organic search before they convert.

### aiseo-fintech-shortlist-then-verify
Source: report:ai-seo-stats
Author: kim
Tags: vertical, fintech, buyer-journey, trust, compliance, ai-search
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: In Fintech, buyers appear to use AI to shortlist vendors, then switch to organic search for compliance and security verification before converting — both channels underperformed on raw Lead-to-SQL (organic 25%, AI 20%) because of the high-scrutiny due-diligence process.

### aiseo-homepage-branded-discovery
Source: report:ai-seo-stats
Author: kim
Tags: ai-search, branded-search, attribution, dark-funnel, discovery
Type: stat
Tier: 1
Usage: paraphrase-only
Content: Homepage conversions grew 6–9% month-over-month for 6 consecutive months — consistent with AI-driven discovery feeding into branded organic searches that standard attribution never credits to AI.

### aiseo-customer-support-direct
Source: report:ai-seo-stats
Author: kim
Tags: vertical, customer-support, branded-search, organic-vs-ai
Type: stat
Tier: 1
Usage: paraphrase-only
Content: In Customer Support SaaS, organic accounted for 87% of all traffic — the highest organic dominance of any vertical studied. In established categories, buyers bypass AI and search directly for vendors they already know.

---

# SOURCE: Blog corpus (first-hand, already published)

Extracted from the 14+ first-hand experience blogs. Tier 2 unless a real client/number makes it Tier 1. Tag thoroughly so a new article on any topic can surface a relevant passage Kim or Praveen already wrote.

## From: how-to-do-saas-seo-keyword-research (Kim, SEO)

### blog-kw-sprinto-internal-teams
Source: blog:how-to-do-saas-seo-keyword-research
Author: kim
Tags: keyword-research, saas-seo, internal-teams, tam, sprinto
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: Working with Sprinto in 2023, Kim stopped opening Ahrefs first and instead sent a simple keyword sheet to every team that touches the customer — Sales, CS, Product, and the marketing sub-teams. He expected duplicates of what competitors (Vanta, Drata) already ranked for. Instead it surfaced 900+ keywords they'd never have found from a tool, taking the list from ~1,500 to ~2,400. Real buyers don't search like SEO pros — they use the messy, layman language sales hears on discovery calls.

### blog-kw-people-before-tools
Source: blog:how-to-do-saas-seo-keyword-research
Author: kim
Tags: keyword-research, saas-seo, internal-teams, discovery, content-strategy
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim's core keyword-research principle: start with people, not tools. Tools are for validation, not discovery — rely 100% on Ahrefs/Semrush and you only ever see what competitors already found. Interview Sales, CS, Product, and Product Marketing to build a "human" list first, then bring in Google Keyword Planner (volume), Ahrefs/Semrush (gap analysis), and G2/Gartner (the industry's official category name) to validate.

### blog-kw-topics-not-lists
Source: blog:how-to-do-saas-seo-keyword-research
Author: kim
Tags: keyword-research, topic-clusters, content-strategy, content-planning, budget
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Group keywords into Topics, not lists. A spreadsheet of 2,000 keywords is noise; 250 Topics is a strategy. Topics tell you how many pages to build — "What is GRC," "GRC components," "GRC examples" all map to ONE pillar page, not three thin articles. It turns content from a random ask ("write 30 articles this quarter") into a business case: "the TAM is 250 articles — 60 BOFU, 70 MOFU, 200 TOFU."

### blog-kw-40-60-bofu-rule
Source: blog:how-to-do-saas-seo-keyword-research
Author: kim
Tags: bofu, keyword-research, content-strategy, benchmark, saas-seo
Type: framework
Tier: 2
Usage: exact-quote-ok
Content: The "40-60 rule": most single-product SaaS companies have a maximum of 40 to 60 Bottom-of-Funnel pages — software pages, alternatives, comparisons, pricing. Try to force more than that and you're stretching. It rarely exceeds 60.

### blog-kw-master-sheet
Source: blog:how-to-do-saas-seo-keyword-research
Author: kim
Tags: keyword-research, content-planning, template, process
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim's keyword "Master Sheet" columns: Keyword, Search Volume, Intent (info/nav/transactional), Category, Sub-Category, Topic (the grouping pillar — the crucial one), Priority (P0/P1/P2). Merging team insight + Keyword Planner + competitor gaps + G2 categories into this sheet takes 3–4 days done right — but it maps the full TAM.

## From: how-to-run-google-ads-for-saas (Praveen, PPC)

### blog-gads-10m-client-turnaround
Source: blog:how-to-run-google-ads-for-saas
Author: praveen
Tags: google-ads, ppc, account-structure, intent, case-data, client-win
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: Praveen audited a $10M+ revenue SaaS client whose Google Ads account treated every use case the same — someone searching "best messaging app for teams" and someone searching "Whatsapp alternative" saw the same ad, with ~60% junk traffic. The fix was intent-led restructuring: dedicated campaigns per use-case/ICP, strict ToFu/MoFu/BoFu segmentation, and ad copy aligned to each query. Over three quarters: ~27% less ad spend, ~59% more revenue (~$250k spend → ~$1.3M revenue). Anonymise the client.

### blog-gads-never-start-with-keywords
Source: blog:how-to-run-google-ads-for-saas
Author: praveen
Tags: google-ads, ppc, discovery, icp, ad-copy, messaging
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen never starts a Google Ads account in the keyword box — he grills product and sales first with five questions: (1) what real pain does it solve (not the feature — the HR director up at midnight fearing a compliance lawsuit), (2) the specific features, (3) what the market actually calls it (you branded it "Revenue Intelligence Architecture," they search "sales dashboard"), (4) who the decision-maker is (CTO cares about implementation/security; CEO cares about ROI), (5) the triggers that make someone search today.

### blog-gads-six-keyword-buckets
Source: blog:how-to-run-google-ads-for-saas
Author: praveen
Tags: google-ads, ppc, keyword-strategy, segmentation, competitor-bidding
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen's six SaaS Google Ads keyword buckets, segmented by user psychology: Category (broad, expensive, necessary), Feature (lower volume, higher convert — where B2B SaaS shines), Competitor (bid on rivals' brand terms — aggressive but works), Integration (an overlooked goldmine — "CRM that integrates with Slack"), Solution (the problem, not the software), Brand (defend your own name).

### blog-gads-bofu-first-not-tofu
Source: blog:how-to-run-google-ads-for-saas
Author: praveen
Tags: google-ads, ppc, bofu, funnel, budget, intent
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: Praveen is ruthless about prioritisation in paid: do NOT start SaaS PPC with ToFu. ToFu terms ("what is employee engagement?") bring students, researchers, and people months from buying — they burn budget fast. Start every client on BoFu and MoFu ("best employee engagement software," "X vs Y"). Only when you've saturated high-intent spend and genuinely can't spend more profitably do you open ToFu to scale.

### blog-gads-broad-match-enemy
Source: blog:how-to-run-google-ads-for-saas
Author: praveen
Tags: google-ads, ppc, match-types, broad-match, negative-keywords, account-structure
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: On a new SaaS account Praveen treats Broad Match as the enemy. It's Google's default because it spends your budget faster — bid "CRM Software" broad and you pay for "CRM jobs in Chicago" and "what does CRM stand for." Stick to Phrase and Exact only, with a heavy negative list, until you've earned the right to use Broad with real conversion data behind it.

### blog-gads-roi-forecast-formula
Source: blog:how-to-run-google-ads-for-saas
Author: praveen
Tags: google-ads, ppc, forecasting, cpa, ltv, budget, roas
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen's pre-launch ROI forecast, run before a dollar is spent: total search volume → impressions (aim ~60% impression share) → clicks (~5% CTR) → conversions (~3% landing CVR) → cost (clicks × avg CPC) → CPA (cost ÷ conversions). The CPA must be below the sale/LTV value. Worked example: 4,560 searches → 2,736 impressions → 136 clicks → ~4 leads at $77 CPC = ~$2,618 CPA — which is a no-brainer if LTV is $90k.

### blog-gads-negatives-and-monitoring
Source: blog:how-to-run-google-ads-for-saas
Author: praveen
Tags: google-ads, ppc, negative-keywords, search-terms-report, optimization, monitoring
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen's budget shields: upload a standard SaaS negative list before launch (open source, jobs/career/internship, wrong company sizes, wrong industries, "login," "support" — or you pay every time existing customers search your login). Post-launch, review the Search Terms Report weekly (the most honest report in marketing) and add irrelevant terms as negatives; cap CPC on any keyword that runs expensive without converting. Minimum viable daily budget = ~10 clicks/day × your CPC.

## From: how-to-do-saas-seo-competitor-analysis (Kim, SEO)

### blog-comp-money-pages
Source: blog:how-to-do-saas-seo-competitor-analysis
Author: kim
Tags: competitor-analysis, money-pages, bofu, content-strategy, saas-seo
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim's five "Money Pages" — the only competitor pages worth analysing because that's where the credit card comes out: Use Case pages, Industry Vertical pages, Comparison (X vs Y) pages, Alternative pages, and Listicles. Ignore high-volume blog posts and vanity metrics; if a competitor has these five and you don't, you're leaving money on the table.

### blog-comp-direct-vs-serp
Source: blog:how-to-do-saas-seo-competitor-analysis
Author: kim
Tags: competitor-analysis, serp, messaging, content-structure, saas-seo
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Split competitors into two types and use both: Direct competitors (business rivals — steal their product messaging and sales arguments) and SERP competitors (whoever actually ranks #1, often G2 or an aggregator — copy their content structure and depth). Combine the persuasive sales logic of a direct rival with the structural blueprint of a SERP winner. Don't blindly copy a giant's structure — they often rank on brand power, not keyword strategy, and you lack their domain authority.

### blog-comp-page2-to-1-copy-fix
Source: blog:how-to-do-saas-seo-competitor-analysis
Author: kim
Tags: competitor-analysis, serp-intent, landing-page, copy, case-data, client-win
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: A client was stuck on page 2–3 for a core keyword. The diagnosis: their page was too academic — all "methodologies" and "frameworks" — while searchers wanted a fix for a mess. Kim switched the copy to a strict Problem→Solution structure, rewriting the first fold from "We are an X firm with Y years of experience" to "Struggling with X? We help you fix it in weeks, not months." Within days the page went from page 2 to position 2 on page 1, with a ~30% traffic increase. No backlinks bought — just SERP-intent-matched copy. Anonymise the client.

### blog-comp-trust-signal-top3
Source: blog:how-to-do-saas-seo-competitor-analysis
Author: kim
Tags: competitor-analysis, listicle, trust-signals, citations, eeat, case-data
Type: anecdote
Tier: 2
Usage: paraphrase-only
Content: To rank a competitive listicle keyword against G2, Capterra, and big blogs, Kim's team added a top-of-page comparison table of the top 10 tools and pulled real pricing from each competitor's page / G2, with a dated transparency disclaimer ("we gathered this data from [source] as of [date] — verify with the provider"). Acting like a neutral journalist and citing high-authority sources borrowed their authority and landed a top-3 ranking.

### blog-comp-outcome-over-output
Source: blog:how-to-do-saas-seo-competitor-analysis
Author: kim
Tags: positioning, agency, outcomes, philosophy
Type: opinion
Tier: 2
Usage: exact-quote-ok
Content: "Most agencies execute tasks. We own outcomes." Kim's revenue-first philosophy — prioritise money pages over volume, outcomes over output, and tie every SEO play to the actual sales pipeline rather than dashboard vanity metrics.

## From: the-no-nonsense-guide-to-auditing-your-saas-ppc-account (Praveen, PPC)

### blog-ppcaudit-data-not-settings
Source: blog:the-no-nonsense-guide-to-auditing-your-saas-ppc-account
Author: praveen
Tags: ppc-audit, google-ads, strategy, process
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: Praveen's core audit principle: audit the strategy before the settings, and audit data, not settings. The biggest mistake is judging whether a keyword is "good" before you know who's supposed to be searching for it. Start top-down — product clarity, ICP, funnel health (Leads→MQLs→SQLs→customers), benchmarks — then go to keywords. Otherwise you optimise efficiently toward the wrong audience.

### blog-ppcaudit-70pct-drop-cpc
Source: blog:the-no-nonsense-guide-to-auditing-your-saas-ppc-account
Author: praveen
Tags: ppc-audit, google-ads, cpc, diagnosis, case-data, client-win
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: A Series A/B SaaS ($10–15M revenue) suddenly saw qualified leads drop 70%, CPL skyrocket, and clicks fall. The team had been changing creatives, landing pages, and bids all at once, destroying data clarity. Praveen isolated only the campaigns that used to work, drilled in week-over-week, and found the real culprit: CPC had skyrocketed, exhausting the daily budget by noon so they showed for only ~20% of searches. The fix wasn't new ads or a new landing page — just bid caps to control CPC. Lower CPC → budget lasts → impression share recovers → clicks and conversions return. Audit data, not settings. Anonymise the client.

### blog-ppcaudit-eagles-view
Source: blog:the-no-nonsense-guide-to-auditing-your-saas-ppc-account
Author: praveen
Tags: ppc-audit, google-ads, linkedin-ads, budget, framework
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen's PPC audit flow: take the "Eagle's View" first — spend by channel and CPL/CPSQL — to find the "Bleeders" (e.g. LinkedIn eating 60% of budget for 10% of SQLs). Then classify every campaign into three buckets: High Spend/No Return (wrong targeting or broken LP), Low Spend/High Return (starving winners — feed them budget now), High Spend/Low ROI (the optimisation trap — do CRO). Benchmarks to anchor on: ~3% visitor→lead, 45–50% Lead→MQL. Audit Google (captures demand — search terms, intent) and LinkedIn (generates demand — targeting hygiene, demographics tab, audience penetration) differently.

## From: how-to-do-saas-content-audit (Kim, SEO)

### blog-contentaudit-8-questions
Source: blog:how-to-do-saas-content-audit
Author: kim
Tags: content-audit, content-strategy, serp-intent, eeat, schema, secondary-keywords
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim's 8-question SaaS content audit: (1) does it match SERP intent AND user intent, (2) does it answer the query directly (lead with the answer), (3) are internal/external links working, (4) is it readable (short paras, simple words, WEBP images — non-negotiable since load time is a ranking factor), (5) right schema (Article + FAQ), (6) E-E-A-T signals (author bios, real outcomes), (7) secondary keywords covered, (8) FAQs built from People Also Ask + Reddit, not guesswork.

### blog-contentaudit-serp-intent-highest-impact
Source: blog:how-to-do-saas-content-audit
Author: kim
Tags: content-audit, serp-intent, format, rankings, content-strategy
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: The single highest-impact content-audit fix is SERP intent/format alignment. Most content stuck between positions 8–20 is there because the format fights the SERP — a 2,000-word narrative where every top result is a listicle loses regardless of writing quality. Change the format to match what Google is rewarding and rankings often move within weeks, before you touch anything else.

### blog-contentaudit-secondary-keywords-lever
Source: blog:how-to-do-saas-content-audit
Author: kim
Tags: content-audit, secondary-keywords, compounding, content-strategy
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: Secondary keywords are the most underrated lever in SaaS SEO. A single post ranking for 20 secondary keywords instead of two does the work of 10 articles — multiply that across 50–100 pieces and the compounding traffic is enormous. Most teams write around one primary keyword and leave this completely untouched.

### blog-contentaudit-when-to-audit
Source: blog:how-to-do-saas-content-audit
Author: kim
Tags: content-audit, timing, content-strategy, cannibalization
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Four signals it's time for a content audit: rankings dropping consistently week-over-week (almost always an intent/format alignment problem), organic traffic gone stale (you've hit a ceiling / topical authority gaps / cannibalisation), you've crossed 30–50 blog posts (content starts working against itself), or you're about to fund a new SEO push (fix the 40 underperforming posts before paying for 10 new ones).

## From: how-to-write-saas-comparison-pages-for-seo (Kim, SEO)

### blog-compare-vs-alternative-intent
Source: blog:how-to-write-saas-comparison-pages-for-seo
Author: kim
Tags: comparison-pages, alternative-pages, bofu, search-intent, content-strategy
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Comparison pages and Alternative pages are NOT the same and must be written differently. A comparison-page visitor ("Brand A vs Brand B") is confused and choosing between two viable options — weigh specific criteria. An alternative-page visitor ("Zendesk alternatives") is already frustrated with a tool they use and looking for an escape — speak to the pain that tool failed to solve. One is an argument ("we're better than X because Y"); the other is a rescue ("here's what solves the pain X caused you").

### blog-compare-page-structure
Source: blog:how-to-write-saas-comparison-pages-for-seo
Author: kim
Tags: comparison-pages, bofu, conversion, page-structure, ctas
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim's converting comparison-page structure (a landing page, not a blog post): hero with the verdict in the subhead ("A vs B: why A wins for enterprise security") → frame the pain before the solution → a credible table (real G2/Capterra ratings, starting price, migration offer — not lazy green-check/red-X) → product overview (founded year, focus) → deep-dive feature evaluation (setup, automation, integrations, support SLAs, security certs) → industry verdicts → honest pricing → a Value-Added Section → CTAs mapped to scroll depth.

### blog-compare-industry-verdicts-honesty
Source: blog:how-to-write-saas-comparison-pages-for-seo
Author: kim
Tags: comparison-pages, trust, conversion, honesty, eeat
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: On comparison pages, concede the verticals where the competitor genuinely wins ("for e-commerce, Product B is the obvious winner; for healthcare compliance, choose Product A"). The honesty shocks readers and makes them trust your recommendation for their industry. Never change a competitor's pricing or hide that you're more expensive — explain the value (implementation included vs a $5k onboarding bill). Fight on value, not price.

### blog-compare-value-added-section
Source: blog:how-to-write-saas-comparison-pages-for-seo
Author: kim
Tags: comparison-pages, differentiation, conversion, interactive
Type: framework
Tier: 2
Usage: paraphrase-only
Content: The "Value-Added Section" is the secret weapon that separates a comparison page from every identical competitor page — an interactive or unique element the competitor's page lacks. Best example: a pricing calculator ("Help Desk software for 20 people" → live A-vs-B cost), or a migration checklist / ROI calculator. It answers "what will this actually cost me?" and keeps the user on-page longer, which both helps conversion and ranking.

## From: how-do-i-run-linkedin-ads-for-saas / saas-linkedin-ads-mistakes (Praveen, PPC)

### blog-li-capture-vs-influence
Source: blog:how-do-i-run-linkedin-ads-for-saas-an-experts-take
Author: praveen
Tags: linkedin-ads, ppc, attribution, demand-gen, brand
Type: opinion
Tier: 2
Usage: exact-quote-ok
Content: "Google is for capture; LinkedIn is for influence." Praveen's one-line frame for the whole channel: nobody on LinkedIn is in buying mode — they're scrolling. The ad plants a seed so that weeks later, when the VP/CXO actually needs the solution, they Google your brand and convert. Judge LinkedIn on last-click attribution and you'll pause campaigns that were working. Selling a $20/mo tool to freelancers? LinkedIn's high CPC will kill you — it's for high-ACV B2B only.

### blog-li-abm-tiers
Source: blog:how-do-i-run-linkedin-ads-for-saas-an-experts-take
Author: praveen
Tags: linkedin-ads, abm, targeting, ppc, icp
Type: framework
Tier: 2
Usage: paraphrase-only
Content: LinkedIn charges by impressions, not clicks — so Praveen always runs against an ABM list to ensure every paid impression hits a company that can afford the product. Three tiers: 1:1 for must-win "whale" accounts (target only the CXOs/VPs/Directors there with tailored campaigns), 1:Few for a cluster of 10–20 similar companies, 1:Many to scale across a 1,000–5,000 company ICP list.

### blog-li-penetration-1000pct
Source: blog:how-do-i-run-linkedin-ads-for-saas-an-experts-take
Author: praveen
Tags: linkedin-ads, audience-penetration, targeting, bidding, case-data, client-win
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: A SaaS client was running "spray and pray" LinkedIn targeting — a modest budget aimed at hundreds of thousands of people on Broad + Max Delivery bidding, hitting ~1.7% audience penetration (influencing almost no one) with junior, irrelevant impressions. Praveen restructured by region/product, applied strict ICP filters (seniority, industry, company size) to right-size the audience to the budget, and switched to manual bidding. Audience penetration went from ~1.70% to 19.20% — a ~1000% increase. Anonymise the client.

### blog-li-content-repurposing-icp
Source: blog:saas-linkedin-ads-mistakes-to-avoid
Author: praveen
Tags: linkedin-ads, icp, targeting, job-title, content-marketing, case-data
Type: anecdote
Tier: 2
Usage: paraphrase-only
Content: A client's product repurposes content. The intuitive target is Demand Gen / Growth Marketers — but the person who actually cares is a Content Director, Head of Content, or Content Marketing Manager. The right audience split was ~80% content-focused titles, 20% broader marketing — not the other way around. Targeting the obvious "marketing" roles would have thrown money away. Start from the problem your product solves, then find the exact title that owns it.

### blog-li-recently-visited-conference
Source: blog:saas-linkedin-ads-mistakes-to-avoid
Author: praveen
Tags: linkedin-ads, targeting, events, location, case-data
Type: anecdote
Tier: 2
Usage: paraphrase-only
Content: For a client with a conference booth in San Francisco, attendees were flying in from across the country — so targeting permanent SF residents would have missed them. Praveen used LinkedIn's little-known "recently visited" location option to reach people physically in the area during the event window, putting ads in attendees' feeds while they were at the conference. Booth traffic increased noticeably. Use "recently visited" for time-bound events, "permanent" for always-on prospecting.

### blog-li-measure-by-lift
Source: blog:how-do-i-run-linkedin-ads-for-saas-an-experts-take
Author: praveen
Tags: linkedin-ads, attribution, measurement, brand-search, demand-gen
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Because LinkedIn is an influence channel, attribution tools mis-credit "direct" or "organic" for leads it actually started. Praveen measures the Lift instead: after launching a heavy LinkedIn campaign, did direct traffic rise, did brand-name searches on Google rise, did total lead count go up even if LinkedIn isn't claiming credit? Concrete read: if you were getting ~10 leads/mo on Google alone and adding LinkedIn pushes you to a consistent 13–15, it's working.

### blog-li-settings-traps
Source: blog:saas-linkedin-ads-mistakes-to-avoid
Author: praveen
Tags: linkedin-ads, audience-network, bidding, creatives, settings, optimization
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen's LinkedIn setting fixes that quietly save budget: turn OFF the Audience Network (don't pay LinkedIn premiums to show on random third-party sites you can't track), use Classic not Accelerate (the AI mode spends inefficiently), use Manual not Max Delivery (Max Delivery optimises for speed of spend, not efficiency), and launch with a minimum of 5 creatives — LinkedIn only shows the same ad to the same person twice before suppressing it, so one creative kills your own reach.

## From: how-to-write-google-ads-copy-for-saas-in-2026 (Praveen, PPC)

### blog-gadscopy-15-headline-math
Source: blog:how-to-write-google-ads-copy-for-saas-in-2026
Author: praveen
Tags: google-ads, ad-copy, rsa, headlines, ppc
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen's mathematical RSA headline mix for the 15 available slots: pin exactly 4 headlines to position 1 that match the target Topic almost perfectly (proves the searcher clicked the right result), assign 2 purely to the CTA/offer (book a demo, free trial), and use the remaining 9 for heavy lifting — features, integrations, social proof with real numbers, and the specific job title/industry you target ("Built for Healthcare HR"). Fill every slot; five headlines chokes the algorithm.

### blog-gadscopy-ai-intent-mapping
Source: blog:how-to-write-google-ads-copy-for-saas-in-2026
Author: praveen
Tags: google-ads, ad-copy, ai, intent, psychology, ppc
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen reverse-engineers searcher psychology with AI before writing copy: feed ChatGPT/Gemini the core BoFu Topics and ask what terrifies the buyer behind the search (e.g. "what terrifies a COO searching 'cloud ERP for mid-market manufacturing'?" → implementation downtime and broken inventory integrations), then write headlines that answer that exact fear instead of generic features. Also ask the AI for the "must-have" elements the persona expects to see before they'll click.

### blog-gadscopy-job-title-filter
Source: blog:how-to-write-google-ads-copy-for-saas-in-2026
Author: praveen
Tags: google-ads, ad-copy, job-title, qualification, ppc, ctr
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: Putting the specific job title in the headline ("Built specifically for CFOs," "Built for Healthcare HR") acts as both a magnet and a filter — the target persona feels understood and clicks; unqualified juniors and wrong-fit buyers self-select out, saving the click cost. Praveen has seen this single tactic dramatically lift CTR from the right persona.

### blog-gadscopy-test-and-prune
Source: blog:how-to-write-google-ads-copy-for-saas-in-2026
Author: praveen
Tags: google-ads, ad-copy, testing, optimization, ppc, ctr
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen's copy testing loop: launch 3 distinct RSAs per ad group, each on a different angle (speed / security / cost), rotate evenly for 1–2 weeks to get unbiased data (don't let Google pick a winner early on random clicks), then cut to the best by CTR and Ad Rank. After that, continuously prune — find the single lowest-CTR headline, weed it out, and replace it with a variation of your best-performing headline so the ad keeps competing against its own best numbers.

## From: the-8-common-saas-google-ads-mistakes-to-avoid-in-2026 (Praveen, PPC)

### blog-gadsmistakes-brand-protection
Source: blog:the-8-common-saas-google-ads-mistakes-to-avoid-in-2026
Author: praveen
Tags: google-ads, brand-keywords, ppc, competitor-bidding, account-structure
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: Run a branded keyword campaign from day one — it's non-negotiable, not a "when budget allows." In virtually every competitive SaaS category a competitor is bidding on your name right now, and a warm prospect who searches for you can see their pitch above your organic listing. Brand CPCs are very low (your relevance for your own name is maxed), and a branded campaign lets you control the headline, CTA and offer a high-intent searcher sees. Go search your brand incognito — whatever shows up is what your prospects see.

### blog-gadsmistakes-extensions-and-cadence
Source: blog:the-8-common-saas-google-ads-mistakes-to-avoid-in-2026
Author: praveen
Tags: google-ads, ad-extensions, ppc-audit, quality-score, landing-page, optimization
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen's most-preventable Google Ads mistakes: launching without ad extensions (sitelinks, callouts, structured snippets are free, enlarge your footprint, and lift CTR — 20-min fix), keeping the target keyword out of the ad copy (kills Quality Score → raises CPC; write the copy starting from the keyword), routing all traffic to a generic homepage instead of a dedicated per-campaign landing page that delivers what the ad promised, and having no audit cadence — run a full account audit every two weeks (long enough for real data, short enough that problems don't compound on a CPC channel).

## From: saas-seo-checklist (Kim, SEO)

### blog-seochecklist-50k-programmatic
Source: blog:saas-seo-checklist
Author: kim
Tags: programmatic-seo, scaling, indexing, b2b, case-data, client-win
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: A client wanted the Indian B2B market only, but general keywords were pulling freelancers and consumers — the wrong ICP. Kim's team proposed programmatic SEO targeting specific B2B use cases. They didn't dump 50,000 pages at once — they tested the architecture with 100 pages first. Google initially struggled to index them; they reworked the page architecture and within a day indexing kicked in. Then they scaled 100 → 1,000 → 10,000 → 50,000 pages. Because intent was strictly B2B, sign-ups skyrocketed and the client made it a separate revenue line. The lesson: prove the architecture small before you scale programmatic. Anonymise the client.

### blog-seochecklist-revenue-math
Source: blog:saas-seo-checklist
Author: kim
Tags: keyword-research, conversion, revenue, volume-vs-intent, benchmark
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim's "volume trap" math: a 1,000-search keyword, even ranking top 3, might bring ~100 clicks; at a typical SaaS conversion rate of 2–4%, that's 4–5 actual conversions. Run that math before you write content. High volume with wrong intent loses to low volume with buying intent every time.

### blog-seochecklist-intent-reporting-benchmarks
Source: blog:saas-seo-checklist
Author: kim
Tags: reporting, conversion, page-type, benchmark, measurement
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim reports conversion by page TYPE, not aggregate traffic — and holds each to its own benchmark: alternative/comparison pages (high intent) should convert at ~3–4%; general top-of-funnel pages at ~0.75% (often on an asset download, not a demo). Judge a blog post by a comparison page's benchmark and you'll make bad cut/scale decisions.

### blog-seochecklist-crawlability-over-speed
Source: blog:saas-seo-checklist
Author: kim
Tags: technical-seo, crawlability, core-web-vitals, indexing, saas-seo
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: Kim doesn't obsess over perfect PageSpeed/LCP scores — top-ranking pages for competitive keywords rarely score above 80, and it's over-hyped. SaaS sites have ~1,000–2,000 pages, not millions like e-commerce, so crawlability and indexability are 90% of technical SEO. Fix 404s, 301/302s, canonicals and sitemaps, keep UX smooth, and Google rewards the rest.

## From: how-to-write-saas-seo-content-with-ai-that-actually-ranks (Kim, SEO)

### blog-aicontent-interview-method
Source: blog:how-to-write-saas-seo-content-with-ai-that-actually-ranks
Author: kim
Tags: ai-content, content-creation, eeat, first-hand-experience, interview-method, content-process
Type: framework
Tier: 1
Usage: paraphrase-only
Content: Kim's "Interview Method" — the core of how PipeRocket writes content AI can't replicate: find a subject-matter expert (your own founder, a colleague, someone on LinkedIn), offer them credit, record a 30-minute conversation asking hard questions ("does this actually work? give me an example of when it failed"), then turn the transcript into a blog. AI cannot hallucinate experience, but it can process yours perfectly. "Meaningful Content = Expert Input + AI Efficiency + Human Verification." Treat a blog as a 1-on-1 with your ICP, not a 1-to-many broadcast.

### blog-aicontent-gemini-transcript
Source: blog:how-to-write-saas-seo-content-with-ai-that-actually-ranks
Author: kim
Tags: ai-content, tools, gemini, transcription, content-process
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: For turning interview transcripts into blogs Kim's clear winner is Gemini — ChatGPT over-"fixes" the writing until it sounds robotic and strips the personality, while Gemini keeps the expert's tone, the "I" and "we," the stories. Recording stack: dual-record (phone audio recorder as the primary + the meeting transcript as backup), then upload the audio to Gemini, which captures ~100% even with accents or non-studio audio. "Google doesn't hate AI content; it hates bad content."

### blog-aicontent-10-blogs-result
Source: blog:how-to-write-saas-seo-content-with-ai-that-actually-ranks
Author: kim
Tags: ai-content, results, eeat, case-data, content-process
Type: anecdote
Tier: 2
Usage: paraphrase-only
Content: Kim is running this exact interview-to-transcript-to-blog playbook himself — ~10 blogs written by sitting with a founder/colleague for 30 minutes, transcribing and formatting with Gemini, then editing and publishing. All ten rank in the top two pages of the SERP. Proof that satisfying the human first (real experience) makes the rankings follow.

## From: optimize-saas-landing-pages-for-seo (Kim, SEO)

### blog-lp-sprinto-inline-cta
Source: blog:optimize-saas-landing-pages-for-seo
Author: kim
Tags: landing-page, cro, sprinto, inline-cta, heatmaps, case-data, client-win
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: Kim's "Risk Register Software" landing page for Sprinto was a lead cash-cow, then leads dried up over 2–3 months while traffic held. Two fixes: he found a keyword gap (the market's language had shifted; he added the new long-tail secondary keywords into a revamped FAQ), and using VWO heatmaps he spotted "dead clicks" — users clicking mid-paragraph where there was no link, while the "Book a Demo" button sat far down the page. He added a simple inline contextual text CTA right in the paragraph ("if you want to automate this risk assessment, talk to our expert"). Within a day or two it contributed two high-value leads the next week. A usability fix, not a keyword fix. (Sprinto cleared — Kim names it publicly.)

### blog-lp-search-validation
Source: blog:optimize-saas-landing-pages-for-seo
Author: kim
Tags: landing-page, search-validation, serp-intent, keyword-research, page-type
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Before building any landing page Kim runs "Search Validation" — put the target keyword into the SERP and see what Google already rewards. If the top 10 are informational blogs (e.g. "What is HR Automation?"), you can't rank a hard-sell product page there; if they're product pages, build a product page. Validate the keyword matches the page TYPE before writing a word, no matter how good the volume looks.

### blog-lp-structure-and-schema
Source: blog:optimize-saas-landing-pages-for-seo
Author: kim
Tags: landing-page, page-structure, schema, cro, social-proof
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim's SaaS landing-page flow: hero (problem statement + CTA, clear in 3 seconds) → visuals/demo GIF → features framed as benefits → comparison table (A vs B vs you, honest) → social signals (logos, testimonials, G2/Capterra ratings) → FAQ/objection handling. Title tag doubles as a filter ("HR Software for SMBs" repels enterprise junk traffic). Three must-have schemas: Product, FAQ, and Review (Review gets you star rich-snippets that lift CTR). Catch leavers with exit-intent popups and contextual chatbot flows.

## From: saas-ppc-checklist (Praveen, PPC)

### blog-ppcchecklist-pmax-research
Source: blog:saas-ppc-checklist
Author: praveen
Tags: google-ads, performance-max, keyword-discovery, ppc, optimization
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen uses Performance Max as a keyword-discovery research tool, not a black box: PMax's AI surfaces high-intent search terms you'd never brainstorm manually. Audit the PMax Search Terms report regularly, "graduate" new high-performers into manual Search campaigns (where you control bids and copy), and add your existing target keywords as negatives in PMax so it stays focused on finding NEW opportunities.

### blog-ppcchecklist-competitor-conquest
Source: blog:saas-ppc-checklist
Author: praveen
Tags: google-ads, competitor-bidding, conquest, trademark, ppc, ad-copy
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: Competitor "conquest" campaigns are standard in SaaS — you're legally allowed to bid on a rival's brand name as a keyword. But the trademark trap: you cannot use their trademarked name in your ad copy or Google will flag and pull the ad. Focus the copy on your USPs ("faster implementation," "better UI," "lower seat costs") without naming the rival.

### blog-ppcchecklist-cross-channel-retargeting
Source: blog:saas-ppc-checklist
Author: praveen
Tags: ppc, retargeting, linkedin-ads, google-ads, cross-channel, abm
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Praveen's cross-channel retargeting move: use UTM parameters to identify visitors who came from Google Search ads, then retarget those same high-intent users on LinkedIn with social proof and case studies. Combine with retargeting LinkedIn ad-engagers (people who watched 50% of a video or clicked "Learn More") to build a storytelling sequence toward a demo — not just website-visitor retargeting.

<!-- EXTRACTION COMPLETE: all 14 first-hand blogs mined.
  Done: keyword-research, run-google-ads, competitor-analysis, ppc-audit,
  content-audit, comparison-pages, linkedin-ads, linkedin-ads-mistakes,
  google-ads-copy, google-ads-mistakes, saas-seo-checklist, ai-content,
  landing-pages, saas-ppc-checklist.
  When new first-hand blogs publish, extract them here the same way. -->

---

# SOURCE: LinkedIn (founder + employee posts)

Fed in from screenshots Omar provides. Author: Kim (kamarajkkl) unless noted. Posts were public on LinkedIn, so client names Kim shared publicly (Osfin.ai, Apty, Xflow) are cleared for use. Metrics without a named client should be framed by vertical only. Most entries are Tier 2 (spoken opinion / named framework); real-client wins are Tier 1.

## Kim's recurring POVs (opinion — the through-lines across his posts)

### li-kim-first-hand-ranking-signal
Source: linkedin:kamarajkkl
Author: kim
Tags: ai-search, geo, aeo, content-strategy, eeat, first-hand-experience, ranking-signal
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: First-hand experience is becoming a ranking signal. The internet is full of information and AI systems are searching for conviction — founder- or practitioner-led explanations beat anonymous writing. The shift Kim keeps pointing to: real examples and decisions over abstract definitions, depth in one category over broad surface-level content. It's why SEO conversations are moving from keywords to "credibility architecture."

### li-kim-chase-signals-not-traffic
Source: linkedin:kamarajkkl
Author: kim
Tags: enterprise-seo, pipeline, measurement, bofu, lead-scoring, content-strategy
Type: opinion
Tier: 2
Usage: exact-quote-ok
Content: "Stop chasing traffic. Start chasing signals." Kim's framing of SEO as an influence channel for $100K+ enterprise deals — rankings are not the finish line, traffic is not the full story. The work is to answer buying questions, shape perception through aggregator mentions, and feed lead-scoring signals (who visited, what pages, how often) into enrichment and conversion — not to maximise sessions.

### li-kim-ai-not-changing-fundamentals
Source: linkedin:kamarajkkl
Author: kim
Tags: ai-search, seo-fundamentals, content-strategy, bofu
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: AI is not changing SEO slowly — it's changing what gets rewarded. Rankings are no longer the finish line and traffic is no longer the full story. The fundamentals hold, but the conversation moves from keyword targeting to credibility and brand. (From his B2B marketing mixer talks in Chennai.)

### li-kim-content-as-product
Source: linkedin:kamarajkkl
Author: kim
Tags: content-strategy, topic-clusters, bofu, compounding, content-as-product
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Treat content as a product, not a publishing treadmill — Kim's "SaaS SEO Compounding Revenue Machine." Content compounds when it's built as a connected system that keeps returning pipeline, rather than one-off posts that decay.

## Kim's named frameworks (from his carousel/visual posts)

### li-kim-query-mindmap
Source: linkedin:kamarajkkl
Author: kim
Tags: keyword-research, bofu, content-planning, topic-clusters, query-mapping
Type: framework
Tier: 2
Usage: paraphrase-only
Content: The "Query Mindmap" — a matrix for generating BoFu page ideas across seven columns: Category, Buyer, Industry, Price, Validation, Problem, Trust. e.g. "procurement software / for startups / healthcare / under $1000 / ranked high on G2 / solve source-to-pay issues / worked with Fortune 500." Each row becomes a high-intent page.

### li-kim-seo-success-matrix
Source: linkedin:kamarajkkl
Author: kim
Tags: seo-strategy, eeat, topical-authority, technical-seo, backlinks, brand-signals, ai-readiness
Type: framework
Tier: 2
Usage: paraphrase-only
Content: The "2025 SEO Success Matrix" — six dimensions scored Weak / Good / Great execution: AI & Future Readiness, Brand Signals, Topical Authority, User Intent Mapping, Technical SEO & UX, Backlinks/Authority. Modern SEO brands win by hitting "Great" across all six, not by maxing one.

### li-kim-bofu-first-cluster
Source: linkedin:kamarajkkl
Author: kim
Tags: topic-clusters, bofu, content-strategy, internal-linking, funnel
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim's BoFu-first cluster shape: What Is → How To → Automate → Tools → Alternatives → Pricing / Reviews / Case Studies → Conversion. Decision-stage nodes (Alternatives, Pricing, Case Studies) are built first and everything links toward Conversion.

### li-kim-three-year-mindmap-plan
Source: linkedin:kamarajkkl
Author: kim
Tags: seo-strategy, content-strategy, topic-clusters, planning
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim's "Strategic Approach to SEO" — quality content on a 3-year plan built on top of a mind map. (Illustrated with a SOC 2 topic map: Overview, TSCs, Scope, Frequency, For Startups, Audit, Functional, Automation, Process to Certification.) The mind map defines the full topic universe before any publishing starts.

## Kim's real client wins / data points (Tier 1 — cleared, posted publicly by Kim)

### li-kim-osfin-qbr
Source: linkedin:kamarajkkl
Author: kim
Tags: client-relationship, qbr, outcomes, partnership, agency
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: On the Osfin.ai QBR: the conversations that matter aren't about deliverables — they're "are we aligned on outcomes, are we solving the right problems, and are we honest about what is working and what is not." When the client understands the product inside out, strategy gets sharper. Good partnerships make good marketing possible.

### li-kim-apty-qbr
Source: linkedin:kamarajkkl
Author: kim
Tags: client-relationship, qbr, partnership, honesty, agency
Type: anecdote
Tier: 1
Usage: exact-quote-ok
Content: On the Apty partnership: "We had lows. Hard reviews. Direct feedback. Moments where we had to rework our approach." The clarity came from one simple question asked every conversation — "How is this moving the business forward?" Real partnerships are built, not given.

### li-kim-mission-30k
Source: linkedin:kamarajkkl
Author: kim
Tags: client-win, organic-growth, gsc, traffic-growth, case-data
Type: stat
Tier: 1
Usage: paraphrase-only
Content: "Mission 30k in 150 days" — a real client tracked in GSC growing from 6.37k to 13.4k clicks (9.35M impressions) over the period, with average position climbing from 17.8 to 6.9. (Anonymise the client; the numbers are real.)

### li-kim-550-percent-traffic
Source: linkedin:kamarajkkl
Author: kim
Tags: client-win, organic-growth, traffic-growth, case-data
Type: stat
Tier: 1
Usage: paraphrase-only
Content: A client that grew organic traffic ~550% from Aug 2024 to Feb 2025 (roughly 4.5K to 18K monthly organic visits on the Ahrefs curve). Anonymise the client.

### li-kim-url-clicks-ramp
Source: linkedin:kamarajkkl
Author: kim
Tags: client-win, organic-growth, gsc, traffic-growth, case-data, compounding
Type: stat
Tier: 1
Usage: paraphrase-only
Content: A client's URL clicks compounding month over month: 1,858 (Jan) → 2,038 (Mar) → 3,006 (Jun) → 4,248 (Jul) → 6,610 (Aug) → 7,610 (Sep). The curve shows the compounding effect kicking in around month 6. Anonymise the client.

### li-kim-ai-engine-bofu-spike
Source: linkedin:kamarajkkl
Author: kim
Tags: ai-search, bofu, healthcare, vertical, gsc, traffic-spike, case-data
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: A sudden traffic spike from AI engines landing on BoFu healthcare pages (referral-management, patient-engagement, appointment-scheduling software) — real GSC data showing AI engines now driving bottom-of-funnel discovery, not just awareness. Anonymise the client.

### li-kim-hubspot-drop-lessons
Source: linkedin:kamarajkkl
Author: kim
Tags: competitor-teardown, traffic-drop, content-strategy, lessons
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: "Hubspot Traffic Drop Lessons" — Kim's teardown of HubSpot's organic decline (Ahrefs showing organic traffic and keywords falling through late 2024 into 2025) as a cautionary lesson on what happens to even category leaders when content strategy drifts.

## Additional distinct POVs (from the full read of the screenshot set)

### li-kim-seo-budget-benchmarks
Source: linkedin:kamarajkkl
Author: kim
Tags: seo-budget, agency, planning, saas-metrics, investment
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: On how much B2B companies should spend on SEO: roughly 10–15% of the marketing budget as a working benchmark, weighted by stage — early/startup closer to ~20% of marketing spend to establish presence, scaling companies settling around ~30% as SEO becomes the primary pipeline channel. Treat it as a stage-dependent range, not a fixed number.

### li-kim-llm-tracking-is-guesswork
Source: linkedin:kamarajkkl
Author: kim
Tags: ai-search, ai-visibility, measurement, geo, aeo, tools
Type: opinion
Tier: 2
Usage: exact-quote-ok
Content: "Most LLM SEO tracking tools right now? Pure guesswork." Kim's caution that the current crop of AI-visibility / share-of-model tracking tools is immature — directional at best — so teams should treat their AI-visibility numbers as estimates, not precise measurement, in 2026.

### li-kim-programmatic-seo-not-for-everyone
Source: linkedin:kamarajkkl
Author: kim
Tags: programmatic-seo, content-strategy, bofu, saas, scaling
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: "Programmatic SEO isn't for everyone." It's not a magic button — it works for specific types of companies: B2B SaaS targeting a niche by industry or country, software tools, content aggregators, businesses with genuine data-rich variation per page. For thin, generic use cases it produces pages Google has no reason to rank. Validate you have real per-page variation before going programmatic.

### li-kim-rank-in-ai-search
Source: linkedin:kamarajkkl
Author: kim
Tags: ai-search, geo, aeo, chatgpt, perplexity, ranking, content-structure
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: On ranking in ChatGPT, Perplexity and other AI search models: the same credibility signals that win traditional SEO win here — clear structure, answer-first formatting, first-party data, and brand mentions across third-party platforms. AI engines surface categories before brands, so non-branded, well-structured BoFu content is what gets pulled into answers.

<!-- COMPLETE: Full folder read — all ~50 Kim screenshots + 13 visual jpegs.
  The set is dominated by repeats of the POVs and client wins captured above.
  NOTE: Praveen Ravi (praveenravi14) appears as a commenter/poster in several
  captures, but only his post HEADERS were visible — his post bodies were cut off,
  so no Praveen entries could be extracted. When Praveen screenshots with full
  body text are provided, add a "## Praveen's POVs" subsection here. -->

---

# SOURCE: LinkedIn video scripts (Notion library)

1-minute LinkedIn video scripts from the team. Attribution note: only Kim's and Praveen's and Vishnu's scripts are individually identifiable; the rest are attributed by domain or to "our team" (use "we"/"our team", not first-person "I", when the author is uncertain). Many contain real client numbers (Tier 1) — anonymise the client unless named.

### vid-ppc-cmo-120k-90k
Source: video:linkedin
Author: praveen
Tags: google-ads, ppc, scaling, cpa, roas, case-data, client-win
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: A CMO told us on a call: "we spent $120K and made just $90K back." We asked four questions — what did the funnel look like post-scale, where were the leaks, which campaigns got the scale budget and why, were the search queries even aligned with the ICP. The findings: 25% of ICP leads never scheduled because there were no demo slots in the next 48 hours (instant drop-off); the new campaigns used broad match + search partners and pulled 90% more irrelevant traffic; CPC on the best campaigns jumped $9.40 → $21.20 chasing top-page share while clicks dropped 30%; 45% of search queries were informational, not buying intent. The fixes: auto-slot balancing on scheduling, paused broad + search partners, portfolio bidding to stabilise CPC, refocused on real buyer-intent terms. Result: ARR grew $70K → $150K on a spend increase of only $100K → $130K — $30K more spend for $80K more ARR, a 1.5x return with fixed fundamentals. "Fix the leaks. Scale with precision."

### vid-seo-agent-seo
Source: video:linkedin
Author: kim
Tags: ai-search, geo, agent-seo, reddit, brand-mentions, future-of-search
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: Someone searched "SaaS SEO agency in USA" and Google's AI didn't show 10 blue links — it recommended agencies by name, and ours was one of them, with the citation pulled straight from a Reddit thread. The point: in ~2 years buyers (and agents) won't scroll, they'll trust a short AI-generated shortlist per query. You don't get on that list by stuffing keywords — you get there by showing up where AI looks: Reddit threads answering real founder questions, G2/Clutch reviews with real client wins, and comparison pages the AI can quote verbatim. If you're not on Reddit/Quora/G2 or in AI-friendly content, you're invisible to the next wave. "Agent SEO is the new SEO."

### vid-seo-repositioning
Source: video:linkedin
Author: kim
Tags: seo, repositioning, icp, lead-quality, off-site-authority, content-strategy
Type: framework
Tier: 2
Usage: paraphrase-only
Content: If a SaaS company repositioned in the last 12 months and lead quality still hasn't improved, the SEO is probably still ranking the OLD version of the company. SEO doesn't update automatically when you change ICP, move upmarket, or shift messaging — the ranking pages, traffic-driving keywords, backlinks, and topical authority all still reflect the old positioning. Traffic looks healthy while the wrong people land. The fix is a strategic SEO rebuild, not a metadata refresh: audit what aligns / rewrite / consolidate / delete, rebuild keyword strategy around the NEW ICP's language and intent, and fix off-site authority signals (how backlinks, mentions, review sites, and listicles describe the company). Treat SEO as part of the repositioning, not cleanup after it.

### vid-seo-ai-content-no-context
Source: video:linkedin
Author: kim
Tags: ai-content, content-strategy, core-update, eeat, context, traffic-loss
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: SaaS teams are scaling AI content aggressively — more blogs, more pages — and it feels like momentum, but traffic isn't moving. Most AI content has no original POV; it's built on a keyword and a generic prompt and reads identically to everything else on the SERP. When a core update lands, sites built on it don't dip — they fall off entirely; we've seen SaaS brands lose 80–90% of organic traffic almost overnight, not because they used AI but because they used it without context. The brands that grow feed the model first — positioning, ICP pain points, competitor battle cards, sales objections, real customer language — so the output reflects how the brand actually thinks. Not more content. Better content.

### vid-seo-3-to-15-opportunities
Source: video:linkedin
Author: kim
Tags: seo, low-volume-keywords, high-intent, pipeline, enterprise, case-data, client-win
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: We grew a client from 3 sales opportunities to 15 in two quarters — no budget increase, no extra content. At first we did what most SEO teams do: target high-volume BOFU keywords, publish traffic-focused content. Traffic grew, pipeline didn't, leads weren't qualified. So we changed the question from "what keywords get the most searches?" to "what does someone search when they already have a problem and need a solution now?" — implementation problems, scaling challenges, operational bottlenecks. Most had very low or near-zero search volume, but the searchers were decision-makers. A page might get only 5–10 visitors a week, almost all highly qualified. In enterprise SaaS, one high-intent visitor is worth more than thousands of random clicks. If traffic is growing but pipeline isn't, you may not have a traffic problem — you have an audience problem. Anonymise the client.

### vid-seo-april-update-not-indexed
Source: video:linkedin
Author: kim
Tags: seo, google-update, indexing, gsc, tofu, content-quality
Type: framework
Tier: 2
Usage: paraphrase-only
Content: If TOFU traffic dropped after Google's April update, those pages may not be in the index at all. Open Google Search Console → Pages report → Not Indexed, and look at "Crawled but not indexed" and "Discovered but not indexed" — if those numbers are climbing, that's your answer. The update wasn't about penalties; it cleared out pages Google no longer considers worth showing. TOFU content with no real POV, unique insight, or genuine depth goes quiet. Recovery isn't publishing more — it's making what's there worth showing: add a real POV (your ICP's actual situation, your own market take, fresh data), go deeper, then resubmit in Search Console. Treat TOFU as a credibility signal, not a volume play.

### vid-ppc-split-campaigns
Source: video:linkedin
Author: praveen
Tags: google-ads, ppc, account-structure, ad-groups, budget, intent, case-data
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: In a client account, one ad group was spending well and converting demos to customers, so it looked fine — but deeper in the data, two other ad groups had barely run (almost no spend, almost no traffic). They never had space to prove themselves. The fix was purely structural: split the three out of one campaign so each intent got its own campaign, its own budget, its own room to learn. No new creative, no bid changes — just separation. The previously invisible ad groups started generating pipeline. When a campaign underperforms, look at structure first, before bidding strategy or campaign type — the signal is often there but has no space to come through.

### vid-seo-kim-ai-traffic-skeptic
Source: video:linkedin
Author: kim
Tags: ai-search, ai-visibility, measurement, attribution, bofu, skepticism
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: Kim's AI-traffic skepticism, from real testing: one page showed 309 clicks in 28 days from AI for a keyword that gets only 480 searches/month on Google — on platforms where most people don't click source links. While testing AI-monitoring tools over months, traffic numbers rose before doing anything — no new content, no backlinks; in one case the team had just started a free trial (not even set up) while on a business trip and the dashboard already showed growth. The spike then spread across 20+ pages, almost all bottom-funnel, and dropped just as fast. Real demand builds slowly; it doesn't appear across your 20 most valuable pages overnight and vanish. AI visibility is real and worth pursuing — but there's a difference between showing up in an AI response and influencing a buying decision, and the market is treating those as the same thing.

### vid-seo-kim-track-5-things
Source: video:linkedin
Author: kim
Tags: ai-search, ai-visibility, measurement, pipeline, brand-search, framework
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Kim's answer to "if you don't trust AI traffic, what would you track?" — five things, not AI sessions: (1) are you showing up in the RIGHT prompts (alternatives, comparisons, best-tool-for-use-case/industry/team-size — not random ones); (2) are you showing up again and again (one citation is noise; appearing across 20–30 prompt variations is a pattern); (3) what's happening on your bottom-funnel pages (more direct visits, branded search, alternatives-page performance is more believable than "AI sessions up 400%"); (4) what is sales actually hearing ("I saw you in ChatGPT," "I found you comparing tools"); (5) is pipeline actually changing (better inbound quality, faster trust, buyers already knowing your brand). Treat AI visibility as an early signal, not a mature reporting channel.

### vid-lp-four-fixes
Source: video:linkedin
Author: praveen
Tags: landing-page, cro, conversion, ctas, headlines, social-proof, case-data
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Four landing-page fixes that changed a client's paid results (the leak was the page, not the ads): (1) Kill the optionality — strip multiple competing CTAs down to one ask ("schedule a 30-minute demo"); (2) Write the headline for outcomes, not features — a cybersecurity client's "Pentest at the pace of your code push cycle" (a feature) became "Know where you're exposed. Act before hackers do." (an emotional trigger); (3) Make proof specific — "trusted by 500+ companies" is wallpaper; use named customers, real quotes, defined outcomes; (4) One CTA, three times — same button above the fold, mid-page, and bottom, same copy, no alternatives. The ad earns the click; the page earns the customer.

### vid-analytics-ga4-total-users
Source: video:linkedin
Author: kim
Tags: analytics, ga4, measurement, reporting, returning-users
Type: framework
Tier: 2
Usage: paraphrase-only
Content: In GA4, New Users + Returning Users never sums to Total Users — and nothing is broken. Total Users counts unique people in the period, so someone who visits Monday (New) and returns Thursday (Returning) is two rows in New+Returning but one person in Total. The gap between the sum and Total Users isn't an error — it's real people who came back within the reporting window. The bigger that gap, the stronger your content is pulling people back. Use it as a signal rather than being confused by it.

### vid-li-dynamic-exclusions
Source: video:linkedin
Author: praveen
Tags: linkedin-ads, audience-penetration, dynamic-exclusions, abm, prospecting, budget
Type: framework
Tier: 2
Usage: paraphrase-only
Content: You can raise LinkedIn audience penetration without spending an extra dollar. With 100 target accounts, LinkedIn's algorithm doesn't cycle all 100 — it keeps hitting the same ~30 who've "memorised your voice" while 70 never see you, like a sales rep calling the same 30 of 100 prospects for two months. The fix is dynamic audience exclusions: exclude your highly-engaged accounts from prospecting and push budget to the 70 who haven't seen you. LinkedIn now builds this automatically under the Companies tab (companies that already engaged) — no manual lists. Setup: keep clean campaign naming conventions (you'll be running hundreds), upload a COMPANY list not a contact list for ABM (contacts won't let you build the dynamic audience), then exclude the dynamic audience from prospecting and run a separate small high-value campaign to nurture the engaged group. Two campaigns, two jobs: reach and nurture. (Relevant if spending >$50K/month on LinkedIn.)

### vid-positioning-partner-not-vendor
Source: video:linkedin
Author: vishnu-prasad
Tags: positioning, agency, partnership, honesty, philosophy
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: PipeRocket's differentiation: "Although we're an agency, we don't feel like one." In a typical agency-brand relationship the brand commands and the agency nods and executes; we see ourselves as partners, not vendors. That means being brutally honest — we'll say "your entire pipeline needs to change," "you'll need to invest at least $40,000 to see real results," "the first month might not look good" — which builds trust because the client knows we're here to fix, not to please. We go deep (study the customers, sales data, lead journey, sit with the people who build the product) to diagnose the root problem before designing strategy, and we're doers/executors who stay in the trenches until the math works. "Great marketing isn't loud. It's honest."

### vid-ppc-hire-vs-outsource
Source: video:linkedin
Author: praveen
Tags: ppc, agency, hiring, outsourcing, founders, case-data
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: A founder told Praveen he'd let go of his third marketing hire in 18 months, always thinking the next one would be different. The hidden cost of the "hire someone junior and train them" default: ~4 months to ramp, ~12 hours/week of management time, and by month six ~$60K in salary plus ~$25K of the founder's own time — and the lost momentum you never get back while a competitor scales with a team that's done it 100 times. The 1% of founders ($1M–$20M ARR) keep only the core in-house and treat SEO/paid/content as levers — when a pipe leaks you call an expert, you don't hire a plumber full-time. That founder eventually hired an agency for paid at $15K/month and booked 2x more qualified meetings in 60 days than his last hire did in a year. Outsource non-core execution; build in-house only when direction is crystal clear and volume demands it.

### vid-ppc-brand-competitor-campaigns
Source: video:linkedin
Author: vishnu-prasad
Tags: google-ads, ppc, brand-keywords, competitor-bidding, bidding-strategy, intent
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Across 10+ accounts, brand and competitor campaigns — not generic ones — are the top lead drivers, because Google Ads is intent-driven and nothing shows higher intent than your brand name and a competitor's. Treat your own brand like a competitor and cover every angle: "[brand] pricing," "[brand] alternatives," "[brand] competitors," "[brand] software" — this is usually your lowest CAC and highest-quality traffic. For competitor campaigns, you can't use their trademarked name in ad copy, but you can use smart keyword variations and equivalent intent terms. For brand bidding strategy, use Target Impression Share (brand campaigns are about ownership, not experimentation) with bid caps to protect spend — most advertisers don't know bid caps exist inside Target Impression Share. (Works only when both your brand and competitors have decent search traffic.)

### vid-li-abm-1to1
Source: video:linkedin
Author: praveen
Tags: linkedin-ads, abm, sales-alignment, personalization, founder-led
Type: framework
Tier: 2
Usage: paraphrase-only
Content: ABM 1:1 on LinkedIn is worth it, but only if you know what you're doing — instead of catching 100 small fish you're catching one whale. Why 1:1 campaigns fail: wrong expectations (people want leads in a week; it's long-term), no sales alignment (marketing runs ads, sales runs away), and generic content to high-value accounts ("like sending a forwarded message to a crush"). Don't judge it on instant ROAS — the dashboard may look depressing (low clicks/CTR/conversions) and then sales says "this account replied, they mentioned seeing our ads on the call." Personalise by company name, the role you target, and the exact problem they care about; founder-led videos work insanely well because people trust people, not logos. Without 100% marketing-sales alignment, ABM 1:1 is dead on arrival.

### vid-aitools-40-tools-evaluated
Source: video:linkedin
Author: kim
Tags: ai-search, ai-visibility, tools, measurement, geo, llm
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: We evaluated 40+ AI-monitoring tools, spending 30+ hours on each. The hard truths: (1) they do NOT track real user queries — there's no "Search Console" for LLMs; ChatGPT and Gemini don't share first-party intent data, so the tools rely on synthetic prompts and guesstimates, not real usage; (2) there's no universal rank — LLM outputs are hyper-personalised by location, IP, chat history, and context, so "you rank #3 for CRM software" is misleading (you ranked #3 for their bot, maybe not your customer); (3) under the hood they still lean on traditional signals — content quality, domain authority, citations. Until LLMs open their data, these dashboards are a guessing game. If your SEO fundamentals are strong, you're likely already showing up in AI answers — build real visibility, don't chase the metric.

### vid-seo-authority-led-bofu
Source: video:linkedin
Author: kim
Tags: seo, tofu, bofu, topical-authority, content-strategy, internal-links
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Everyone says TOFU is dying (AI answers informational queries, Google summarises before the click) so teams go BOFU-only — but BOFU doesn't rank in isolation. The best "Best X," "X vs Y," and "X alternatives" pages sit on page 2–3 without topical authority behind them. TOFU-heavy sites get traffic but few demos; BOFU-only sites get intent but no rankings — both fail by treating TOFU and BOFU as separate problems instead of one engine. The fix is Authority-led BOFU: pick ONE category to dominate (not ten), build deep support content that addresses pain points (workflows, templates, implementation steps) to earn citations and warm buyers, keep BOFU pages lean but intentional (alternatives, category, integrations), and hold it together with internal links. TOFU may lose clicks but authority stays, and BOFU ranks.

### vid-ppc-2025-paid-lessons
Source: video:linkedin
Author: praveen
Tags: ppc, paid-media, brand-demand, founders, strategy, scaling
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: From 100+ founder conversations in 2025: the "scale fast and figure it out later" approach broke. Teams that moved up-market hit longer sales cycles and had to shift from "more leads" to "better pipeline." Google can't carry the whole weight — search demand maxes out quickly; the teams that grew steadily built brand demand through SEO, content, and strong founder presence, and their cost per opportunity dropped quarter over quarter because the market trusted them more. The smartest founders treated paid like R&D, not a vending machine — every dollar tested angle, language, and positioning. The winners tuned the whole system first (message, offer, landing page, follow-up, sales rhythm) then turned up spend with confidence. Capital helps you go faster; clarity keeps you from running in circles.

### vid-ppc-crm-70L-to-25L
Source: video:linkedin
Author: praveen
Tags: google-ads, ppc, account-restructure, efficiency, case-data, client-win
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: A top CRM SaaS client was spending ~₹70 lakhs/month on Google Ads with great-looking dashboards (traffic, clicks) but no leads moving down the funnel — the strategy wasn't built to move prospects from intent to opportunity. We cut underperforming campaigns, turned off search partners, removed mobile/tablet traffic that wasn't converting, rebuilt the campaign structure from the ground up, revamped all ad assets (callouts, sitelinks, snippets), and rewrote ad copy + landing-page messaging aligned to the ICP's true intent, then shifted budget toward high-intent keywords. Result: monthly spend down from ₹70 lakhs to ₹25 lakhs while achieving the same number of SALs — but this time the leads moved down the funnel, CTR rose, and lead quality stepped up. Anonymise the client.

### vid-seo-wikipedia-ai-visibility
Source: video:linkedin
Author: kim
Tags: ai-search, geo, wikipedia, entity, citations, case-data
Type: framework
Tier: 2
Usage: paraphrase-only
Verify: "Wikipedia in 60%+ of AI citations" comes from a soft internal scan, not a rigorous study — frame as "in our experience" / "we've seen," not as a hard published stat.
Content: AI engines (ChatGPT, Perplexity, Gemini) keep citing Wikipedia on top — in our study of AI answers for competitive B2B queries, Wikipedia appeared in 60%+ of citations. So we started getting clients listed on Wikipedia for entity credibility and AI-search presence, not backlinks. It's not a regular SEO project: no CTAs, no keywords, no promotion — everything must be neutral, fact-based, and fully cited. We used GPT as a teammate to curate, validate facts, and review tone, and failed 3–4 times before getting it right, which produced our internal rulebook/checklist. Rules: use credible references (analyst reports, PR mentions), keep tone neutral (no "top provider"/"fastest growing"), draft in the Wikipedia sandbox before publishing, and verify every citation. Done right, client pages appeared in GPT and Perplexity citations within weeks.

### vid-li-remarketing
Source: video:linkedin
Author: praveen
Tags: linkedin-ads, remarketing, retargeting, money-pages, audience
Type: framework
Tier: 2
Usage: paraphrase-only
Content: LinkedIn remarketing done right: you can retarget people who engaged with your ads (image, video, carousel, document), attended your event, or visited your site/page. Window matters — 14 days is too soon (they're still deciding if they like you), 180 is too long (they've moved on), 90 days is the sweet spot. Two pro tips: (1) add ALL your prospecting campaigns into the remarketing audience and update it every time you launch a new campaign, or you throw away warm leads; (2) for website-visitor retargeting don't go broad — homepage traffic includes job seekers, blog readers, and competitors stalking you; focus on high-intent money pages (product, pricing, demo).

### vid-li-2026-spend-data
Source: video:linkedin
Author: vishnu-prasad
Tags: linkedin-ads, scaling, roas, prospecting, remarketing, creative, case-data
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: We're increasing LinkedIn spend for 80%+ of clients in 2026, with the data behind it. One SaaS client scaled from $2,000/month (2024) to $60,000/month (2025), LinkedIn-influenced revenue only: January $40K spend → $105K ARR (3x), by April 5.7x, and ~4x consistently even at higher spend. The approach: thought-leadership ads build awareness (but TL CPMs are rising, so mix in cost-effective image and video), 70% of budget on prospecting (named accounts AND beyond — some best customers came from companies not on the original list), 30% on remarketing high-intent users (pricing/demo/G2 visitors, Google Ads traffic). Three success factors: continuously expand reach (add exclusions, track net-new accounts reached monthly), creative does 70% of the work (different content per buyer-journey stage), and always link to landing pages in thought-leadership posts for attribution. Anonymise the client.

### vid-seo-audit-conversion-layer
Source: video:linkedin
Author: kim
Tags: seo-audit, conversion, search-intent, content-type, ctas, pipeline
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Most SEO audits stop at rankings and traffic and miss the conversion layer. One client ranked top-3 for high-intent keywords but conversions weren't moving — they were ranking with blogs while searchers now wanted product/comparison pages; the intent had shifted from information to purchase and the content no longer matched. Another had steady traffic but seconds-long visits because the content sounded polished but lacked depth. When conversions don't move: check which pages have actually converted before, study how search intent for those topics has changed, check whether CTAs clearly guide the next step, and review the full experience (form flow, internal links). Ranking with the wrong content type is as good as not ranking — good SEO brings traffic, smart SEO builds pipeline.

### vid-li-2pct-to-40pct
Source: video:linkedin
Author: praveen
Tags: linkedin-ads, audience-penetration, targeting, attribution, factors, case-data
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: Opening a client's LinkedIn dashboard, three red flags: (1) audience too broad, budget too small — reaching 2 of 100 reachable people = 2% penetration; (2) targeting was off — they knew the ICP (decision-makers, founders, senior folks) but were showing ads to everyone from interns to managers who'd never buy; (3) creatives were all over the place — showing testimonial ads to people who didn't know the brand yet ("like proposing marriage on the first date"). The fix: rebuilt a focused audience with job-function/seniority/company-size filters (cutting audience from lakhs to thousands), added exclusions, switched to manual bidding (max delivery is a budget killer). Penetration jumped 2% → 40% without increasing budget. Bonus: the Factors attribution report showed LinkedIn drove awareness while Google Ads closed the deals — a perfect synergy. Anonymise the client.

### vid-agency-longevity
Source: video:linkedin
Author: kim
Tags: agency, retention, qbr, pods, process, ownership
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Most agencies don't last a year; some PipeRocket clients have stayed 2–4 years by design, on trust, alignment, and ownership ("most agencies execute tasks, we own outcomes"). Relationships break from misalignment, not performance. What we do differently: (1) avoid checklist mode — every quarter we plan Goals, Results, and Actions that move the business, not "publish 10 blogs"; (2) every review starts with "what's not working?" instead of pretty dashboards, which builds trust; (3) every quarter Kim or Praveen runs a QBR with the client POC's manager so work actually gets prioritised when the POC gets busy; (4) pods — a fixed team (manager + specialist + intern) per client with everything documented, so a team change never kills momentum. Clients don't renew, they grow with you.

### vid-positioning-proactive-honesty
Source: video:linkedin
Author: praveen
Tags: agency, positioning, honesty, pipeline, philosophy
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: "We don't wait for you to ask, we tell you when things aren't working." Most agencies buy time and send a dashboard saying "it's too early to tell"; we watch performance daily and flag a wrong direction within the first couple of weeks — with a plan ready. Real examples of the honesty: telling a client not to scale spend even when ads were converting because sales couldn't follow up fast enough; pausing campaigns when tracking wasn't clean (no decisions on junk data); telling a client "paid isn't your answer right now — you need clarity on positioning first." Traffic means nothing if pipeline doesn't move.

### vid-ppc-search-terms-waste
Source: video:linkedin
Author: praveen
Tags: google-ads, ppc, search-terms-report, wasted-spend, negative-keywords, retargeting
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: The most underrated, always-deprioritised section of a Google Ads account is the Search Terms Report. Across accounts we've audited, teams routinely spend 50–60% of budget on irrelevant terms — even with phrase and exact match, Google floods in irrelevant queries; in one recent audit 60% of budget went to terms that would never convert. The damage isn't just wasted money: irrelevant clicks poison the data sent to the ad platform, corrupting retargeting and making it optimise for people who'll never buy. The fix isn't rocket science — a recurring habit of digging into search terms, identifying junk, and tightening targeting — but because it's boring, most teams skip it, and that's where the money vanishes.

### vid-lp-clarity-data-fix
Source: video:linkedin
Author: praveen
Tags: landing-page, cro, clarity, ga4, conversion, case-data
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: A client's paid traffic was ~70% qualified but none of it converted — the landing page was the issue, but the client wasn't convinced, so we used data. Microsoft Clarity showed 90% of users dropping off right after the first fold, most navigating to the homepage; GA4 showed a page that should convert 15–20% to CTA clicks driving under 5%. We built a mockup that redesigned the first and second folds for clarity, rewrote copy to sound human and solution-focused, simplified problem statements to highlight customer pain, and removed unnecessary contact-form fields. With the data in hand the client happily approved. One month after implementation: CTA click rate went 4.5% → 13%, conversion rate 0 → 2.75%. Sometimes it's not about more ads — it's helping the client zoom into the real problem with data they can't ignore. Anonymise the client.

### vid-seo-hiring-outcome-over-traffic
Source: video:linkedin
Author: kim
Tags: seo, hiring, pipeline, revenue, outcomes, tools, philosophy
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: Interviewing for SEO manager/specialist roles, Kim sees a pattern: candidates are great at execution (grow traffic, publish, fix technical) but stop at traffic. One showed real wins — ranking, traffic up, regular publishing — so Kim asked "what business impact did you create?" and there was no answer. Most don't focus on who the customer is, their pain, what they care about; reports exist but no real insight; dashboards exist but nobody acts on them; tools (GA4, GSC, Clarity, Factors) are under-utilised; everyone chases ranking and traffic, not outcomes. Kim was there too until he asked himself "am I really contributing to the business?" — then started talking to performance marketers (ROAS, pipeline, revenue), following data not gut, and taking ownership of SQLs, not just traffic or demo counts. If you're in SEO and want to grow fast, think pipeline and revenue, not ranking.

### vid-ppc-500k-budget-lessons
Source: video:linkedin
Author: praveen
Tags: ppc, paid-media, budget-management, kpis, scaling, forecasting
Type: framework
Tier: 2
Usage: paraphrase-only
Content: Lessons from managing a $500K/month paid budget: (1) start with channel scope, not campaigns — map keyword volume/CPC/realistic max clicks for search and ICP reach/cost for social to set boundaries; (2) use past data like cheat codes — YoY/QoQ/MoM across the full journey from impression → click → demo → pipeline → revenue; (3) lock KPIs with stakeholders early — when one tracks SQL and another ROAS, align everyone on one main KPI (pipeline); (4) check performance daily — $500K/month is ~$16K/day, so a two-day-late catch on a broken signup is $32K gone; (5) scaling ≠ growth — doubling spend won't double pipeline at a CPC ceiling (clicks that cost $30 started costing $70; watch impression share and auction insights); (6) cut wrong clicks daily via search-term checks and audience clean-ups. The spend isn't the problem, the systems are.

### vid-attribution-influence
Source: video:linkedin
Author: praveen
Tags: attribution, measurement, incrementality, view-through, roas, case-data
Type: anecdote
Tier: 1
Usage: paraphrase-only
Verify: "~8% of traffic from LLMs" and "Apple killed ~90% of tracking" are third-party/industry claims, not PR-measured — confirm or attribute ("industry estimates suggest…") before publishing as fact. The client revenue numbers ($90K→$105K, $80K→$287K) are PR-measured and fine.
Content: No company has attribution figured out — if you think you do, you're fooling yourself. In a QBR a client asked "which channel actually influenced the conversions?" and we had no answer. The data is broken: ~8% of website traffic now comes from LLMs (users get answered without visiting), Apple killed ~90% of tracking, cookies are disappearing, people share content on untrackable channels. That forced a reporting overhaul — bringing back view-through conversions, stopping the "which touchpoint gets credit?" question and asking "what's actually influencing results?", and running incrementality tests. The shift in numbers: January 2025 $90K spend → ~$105K (barely breaking even); June 2025 $80K spend → $287K actual revenue (not pipeline) — $15K less spend than January. Two other clients saw similar results. Traditional attribution is dead; channel influence is the future. Anonymise the client.

### vid-ppc-restructure-subproducts
Source: video:linkedin
Author: praveen
Tags: google-ads, ppc, account-structure, sub-products, bofu, clarity, competitor
Type: framework
Tier: 2
Usage: paraphrase-only
Content: When restructuring a messy Google Ads account (scattered campaigns, illogical ad groups, irrelevant keywords/copy), Praveen goes deep into the website session by session first. A common finding: multiple sub-products under one parent, but the ads treat everything the same — a huge red flag. The fixes: build dedicated campaigns per sub-product, group keywords by buyer intent (favour BOFU and MOFU), write fresh ad copy aligned to each ad group's keywords, watch Microsoft Clarity session recordings and fix landing pages accordingly, and replace competitor brand-name targeting with the real alternative keywords prospects actually search. Result: not just higher CTR but better-qualified leads — not more leads.

### vid-ppc-search-maxed-to-linkedin
Source: video:linkedin
Author: praveen
Tags: ppc, google-ads, linkedin-ads, brand-demand, awareness, case-data
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: On a January call, a B2B SaaS client's CEO/CMO were unhappy: we'd scaled Google spend 25% but pipeline was stagnant and revenue flat — we'd hit the ceiling, category keywords were maxed, no search volume left, every extra Google dollar burning. The bold call: keep search on a lean budget to capture in-market demand, and reallocate to building brand awareness toward the right ICP via LinkedIn (the only platform with technographic + firmographic targeting). One rule: this is NOT lead gen — no vanity MQLs, no forms, no gated PDFs; the only metric that mattered was ICP accounts reached, measured with a new framework (frequency, CTR, audience penetration, ICP reach, and influenced pipeline via a reverse-IP tool tied to their CRM). Two months later: revenue grew $105K → $238K ARR, average deal size $2.5K → $7.3K MRR, pipeline sharper and more qualified. When search is tapped and the category is maxed, don't keep squeezing Google — invest where your audience pays attention. Anonymise the client.

### vid-cro-10m-conversion-fix
Source: video:linkedin
Author: kim
Tags: cro, conversion, forms, ctas, user-journey, path-exploration, case-data
Type: anecdote
Tier: 1
Usage: paraphrase-only
Content: A $10M SaaS company had ~100K traffic growing nicely but flat conversions for eight months despite more content/keywords/traffic. Digging in: only 4% of traffic was BOFU, of that only 2% clicked the CTA into the demo page, and only 10% filled the form — so 4,000 visitors produced ~10 form fills. A conversion problem, not a volume problem. Three fixes: (1) replaced a multi-field form (first/last name, email, phone…) with a single primary-email field, and turned the CTA into a same-page popup to remove the demo-page friction; (2) improved the user journey — a Path Exploration report in GA4 revealed drop-off points, so we added exit popups and on-scroll-triggered CTAs; (3) replaced one generic site-wide CTA with contextual CTAs that vary by page and intent (TOFU blog vs BOFU blog vs pricing vs feature). Result: CTA clicks 2% → 6%, demo-form conversion +55%, in just two weeks — no traffic increase, just fixing what was broken. Anonymise the client.

### vid-agency-red-flag-clients
Source: video:linkedin
Author: praveen
Tags: agency, client-fit, qualification, funnel-data, philosophy
Type: opinion
Tier: 2
Usage: paraphrase-only
Content: After 10+ years in B2B SaaS marketing, the red flags that signal a client engagement will go badly: (1) won't reveal funnel data — if we can't see beyond the ad click to MQL→SQL→Revenue, we're driving blind; that's gambling, not partnership; (2) panic-driven decisions — one bad week and strategy gets tossed, trust replaced by fear; (3) micromanaging every metric — obsessing over CTR and avg position while ignoring qualified leads, asking for 3 ad variants weekly with no positioning doc; (4) missing internal ownership — when internal teams aren't accountable, everything becomes "the agency's fault"; (5) founders chasing hacks not building brands — if you want a "secret button" to 10x leads, we're not your agency. We now choose partnerships as carefully as campaigns.

<!-- VIDEO SCRIPTS: captured the distinct high-value insights from the Notion
  script library (~37 scripts). Near-duplicates of already-captured POVs
  (broad-match, BOFU-first, generic AI-visibility skepticism) were consolidated.
  Attribution: Kim/Praveen/Vishnu where identifiable, else by domain.
  When the per-script speaker mapping is available, refine Author fields. -->

# SOURCE: Q&A interviews (batch)

Reserved for batch interview transcripts or voice notes. Per-article Q&A still lives in the content-plan CSV; this section is for reusable cross-topic answers.

<!-- TO POPULATE: when batch interviews or voice memos are recorded. -->

---

# USAGE LEDGER

Records which entries have been used in which published articles, so client stories and POVs rotate instead of repeating. **Check this before selecting entries (Discipline Rule 1); append to it after publishing each article.**

Format, one line per published article (most recent at top):
```
YYYY-MM-DD | <article-slug> | entries: <id>, <id>, ... | anchored-POV: <the POV that headlined a section>
```

2026-06-06 | how-to-do-keyword-gap-analysis | entries: blog-comp-money-pages, blog-seochecklist-revenue-math, blog-kw-topics-not-lists, blog-seochecklist-intent-reporting-benchmarks, blog-comp-direct-vs-serp, blog-comp-outcome-over-output | anchored-POV: gap-as-money-pages
2026-06-06 | how-to-fix-keyword-cannibalization | entries: blog-contentaudit-when-to-audit, vid-seo-repositioning, blog-contentaudit-serp-intent-highest-impact, blog-contentaudit-secondary-keywords-lever, blog-seochecklist-crawlability-over-speed, li-kim-mission-30k | anchored-POV: the-consolidation-decision
2026-06-06 | how-to-build-topic-clusters | entries: blog-kw-topics-not-lists, li-kim-bofu-first-cluster, blog-kw-sprinto-internal-teams, blog-contentaudit-secondary-keywords-lever, li-kim-three-year-mindmap-plan, blog-kw-40-60-bofu-rule, li-kim-content-as-product, li-kim-seo-success-matrix, blog-comp-direct-vs-serp | anchored-POV: topic-cluster-architecture
2026-06-06 | how-to-rank-bofu-keywords-saas | entries: vid-seo-authority-led-bofu, blog-comp-page2-to-1-copy-fix, blog-comp-money-pages, blog-compare-vs-alternative-intent, blog-lp-search-validation, blog-comp-trust-signal-top3, blog-comp-direct-vs-serp, blog-seochecklist-intent-reporting-benchmarks, blog-comp-outcome-over-output | anchored-POV: authority-led-bofu
2026-06-06 | types-of-keywords-in-seo | entries: blog-kw-people-before-tools, blog-seochecklist-revenue-math, vid-seo-3-to-15-opportunities, blog-kw-master-sheet, blog-kw-40-60-bofu-rule, li-kim-bofu-first-cluster, blog-compare-vs-alternative-intent | anchored-POV: intent-over-volume

<!-- Example of what a line looks like once you publish:
2026-06-10 | how-to-rank-bofu-keywords-saas | entries: blog-kw-40-60-bofu-rule, blog-comp-page2-to-1-copy-fix, vid-seo-3-to-15-opportunities | anchored-POV: low-volume-high-intent
-->

## Reuse watchlist (auto-derived — scan before selecting)
After a few articles, the most-reused entries and POVs accumulate here as a quick "don't reach for these again yet" list. Update it whenever you add a ledger line.

- Tier-1 client stories used in the last 5 articles: li-kim-mission-30k (how-to-fix-keyword-cannibalization), blog-kw-sprinto-internal-teams (how-to-build-topic-clusters), blog-comp-page2-to-1-copy-fix (how-to-rank-bofu-keywords-saas), vid-seo-3-to-15-opportunities (types-of-keywords-in-seo) — note: how-to-do-keyword-gap-analysis anchored on a framework entry (blog-comp-money-pages), no Tier-1 client story used
- POVs anchored in the last 3 articles: gap-as-money-pages (how-to-do-keyword-gap-analysis), the-consolidation-decision (how-to-fix-keyword-cannibalization), topic-cluster-architecture (how-to-build-topic-clusters)
