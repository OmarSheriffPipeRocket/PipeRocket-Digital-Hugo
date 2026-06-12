# PipeRocket News Bank

A registry of **meaningful industry updates** (SEO, paid, AI search) that may affect what our content tells readers. Maintained by a weekly scan; consumed by the blog refresher to insert or reframe mentions.

The discipline is the **significance gate**: most weeks the scan logs *nothing*. We only bank an update if it changes what we'd advise — not because news happened.

This file is internal and version-controlled. It is the events companion to `stat_bank.md` (numbers) and `experience-bank.md` (first-party). No overlap: numbers → stat_bank; events → here.

---

## Sources to scan (weekly)

**Primary (first-hand — highest weight):**
- Google Search Central Blog — https://developers.google.com/search/blog
- Google SearchLiaison (X) — https://twitter.com/searchliaison
- Google Ads & Commerce Blog — https://blog.google/products/ads-commerce/
- OpenAI blog, Google Gemini/AI blog, Perplexity blog — AI-search shifts (`ai-seo`)
- Microsoft Advertising blog, LinkedIn Marketing blog

**Secondary (fast daily aggregators):**
- Search Engine Land — https://searchengineland.com (SEO + PPC desks)
- Search Engine Journal — https://www.searchenginejournal.com
- Search Engine Roundtable — https://www.seroundtable.com (fastest on algo/SERP volatility)
- Martech.org — martech/AI tooling

**Research/data (also feed stat_bank):**
- Ahrefs blog, Semrush blog (original studies), HubSpot, CMI, Gartner/Forrester press

> Rule: prefer the **primary** announcement over a secondary recap. Use SEL/SEJ/Roundtable to *spot* a change fast, then cite Google's own post.

### Finding the primary (do this every scan)
When a secondary says "Google **did**/**said** X," a primary almost always exists — and is usually **linked inside that same article**. Open the secondary and pull the primary URL from it (Google Search Central, blog.google, status dashboard, Ads Help). Two outcomes:
- **Primary found** → record it as `Source` and mark `[PRIMARY — confirmed]`.
- **No primary in the article** (only "advertisers report…", a LinkedIn post, or unnamed comms) → that's a real signal the item is **less verified than it looks**. Mark `Status: VERIFY` and do NOT let it be published as "Google announced…" until a primary is located.

---

## The significance gate (apply at intake)

Bank an update ONLY if it clears one of these:
1. **Algorithm/feature change** that alters SEO/content advice (core update, AI Overviews behavior, new SERP feature).
2. **Platform change** in a channel we cover (Google Ads, LinkedIn, Microsoft Ads) that changes how to run campaigns.
3. **Deprecation / launch** of something we reference (a feature retired, a major new capability).

If it's incremental, vendor PR, or doesn't change our advice → **do not bank it.** "Nothing this week" is the correct, common outcome.

---

## Entry schema

```
### [news-id]
Event: one-line description
Date: YYYY-MM (when it happened)
Cluster: ai-seo | saas-seo | saas-paid-marketing      # routes via data/entity_map.yml
Significance: major | medium
Source: primary URL
Status: breaking | established | historical
Reframe-by: YYYY-MM   # when "just announced" phrasing must change to "since the … update"
Action: insert-mention | reframe | update-advice
Should-mention: [candidate pages from the cluster]
Does-mention: [AUTO — grep of pages already referencing it]
Notes: what specifically changes in our advice
```

**Status lifecycle:** `breaking` (just happened, may insert fresh mention) → `established` (absorbed; stop calling it new) → `historical` (reframe to past-tense / dated reference). The refresher's job on aging news is usually **reframe**, not delete.

### The "take" (for the weekly newsletter that consumes this bank)
Each banked item should carry an analytical angle — NOT a fabricated client action. Two valid modes:
- **Pattern / trajectory** — situate the update in a larger arc ("4th update in 18 months demoting thin AI spam — the direction is clear").
- **Implication** — the "so what" for SEO / PPC / AI SEO.
A genuine first-hand observation from `experience-bank.md` may be layered in *only when one actually exists*; never invent one. This analytical take — not the recap — is the E-E-A-T signal.

---

## ENTRIES

> First scan: 2026-06-12, 30-day backfill (mid-May → mid-June 2026), all three clusters. 5 items cleared the significance gate (3 major, 2 medium). AI-Overview *numbers* (zero-click 58.5%, CTR 27%→11%, −38% clicks) are NOT banked here — they belong in `stat_bank.md` and supersede the existing `semrush-57pct-zero-click` / `semrush-aio-13-14pct` entries.

### io-2026-ai-mode-gemini
Event: Google I/O 2026 — Search rebuilt around Gemini 3.5 Flash ("AI Mode"); Google framed it as "the biggest change to Search in 25+ years" (marketing language — attribute, don't state as fact)
Date: 2026-05
Cluster: ai-seo, saas-seo
Significance: major
Source: https://blog.google/products-and-platforms/products/search/search-io-2026/  [PRIMARY — confirmed]
Primary-data: AI Mode 1B MAU; AI Overviews 2.5B MAU; AI Mode queries run 3× longer; follow-ups +40%/mo (Google AI Mode first-anniversary report, 2026-05-19) → candidate stat_bank entries
Status: breaking
Reframe-by: 2026-09
Action: update-advice
Should-mention:
  - content/blogs/how-to-rank-on-chatgpt-in-2026-strategies-and-tips.md
  - content/blogs/research-ai-seo-statistics.md
  - content/blogs/how-to-write-saas-seo-content-with-ai-that-actually-ranks.md
  - content/blogs/b2b-saas-seo.md
  - content/blogs/saas-seo.md
  - content/blogs/fintech-seo-guide.md
  - content/blogs/saas-seo-strategies-and-framework.md
Does-mention: [AUTO — pending]
Notes: AI Mode citations only ~14% overlap with AI Overview citations — implies optimizing for both surfaces separately. Higher weight on structured answers, schema, demonstrable expertise. Verify the primary Google announcement URL before publishing claims.

### may-2026-core-update
Event: Google May 2026 broad core update (2nd core update of 2026)
Date: 2026-05
Cluster: saas-seo
Significance: major
Source: https://status.search.google.com/incidents/wdAXJk6LRRihEjpzEeWE  [PRIMARY — Google Search Status Dashboard]
Secondary: https://searchengineland.com/google-may-2026-core-update-rolling-out-now-478430
Status: established
Reframe-by: 2026-08
Action: reframe
Should-mention:
  - content/blogs/saas-seo.md
  - content/blogs/saas-seo-strategies-and-framework.md
  - content/blogs/how-to-do-saas-content-audit.md
  - content/blogs/how-to-do-saas-seo-competitor-analysis.md
Does-mention: [AUTO — pending]
Notes: Rolled out May 21, completed ~June 4. Standard Google guidance ("people-first content"). Use only where a post discusses ranking volatility/recovery; don't bolt onto unrelated guides. Next core update expected ~June–July 2026 — watch.

### gads-budget-pacing-2026-06
Event: Google Ads changes budget pacing — campaigns now pace toward the full monthly limit (30.4× daily) regardless of schedule
Date: 2026-02 (public Feb 19) → effective 2026-03-01 in notification waves  [CORRECTED — earlier "June 1" was wrong]
Cluster: saas-paid-marketing
Significance: major
Source: https://searchengineland.com/google-changes-budget-pacing-rules-for-scheduled-campaigns-475107  [SECONDARY]
Related-official: https://support.google.com/google-ads/answer/13685469 (Google Ads Help — budget pacing insights; not a press release)
Status: established — partial-VERIFY
Reframe-by: 2026-09
Action: update-advice
Should-mention:
  - content/blogs/how-to-run-google-ads-for-saas.md
  - content/blogs/saas-ppc.md
  - content/blogs/b2b-ppc.md
  - content/blogs/b2b-ppc-guide.md
  - content/blogs/saas-ppc-checklist.md
  - content/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account.md
Does-mention: none (zero posts currently mention it)
Notes: ⚠️ Still NO single official press release — Google communicated it via direct email to advertisers (first public Feb 19, 2026) and rolled it out in waves from March 1. The Google Ads Help "budget pacing insights" page exists but doesn't announce this specific change. Safe to publish as "Google began pacing campaigns toward the full monthly limit in early 2026" (well-corroborated); avoid implying a formal press announcement. Directly changes daily-budget math for dayparted campaigns — e.g. a weekend-only $100/day campaign could jump from ~$800 to ~$1,600/mo.

### gads-data-retention-2026-06
Event: New Google Ads data retention policy takes effect
Date: 2026-06
Cluster: saas-paid-marketing
Significance: medium
Source: https://ads-developers.googleblog.com/2026/05/new-data-retention-policy-for-google.html  [PRIMARY — Google Ads Developer Blog, May 1 2026]
Related-official: https://support.google.com/google-ads/answer/15188209 (Google Ads Help)
Status: breaking
Reframe-by: 2026-09
Action: insert-mention
Should-mention:
  - content/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account.md
  - content/blogs/saas-ppc.md
Does-mention: none
Notes: Effective June 1, 2026. Granular (hourly/daily/weekly) reporting data retained 37 months; monthly/quarterly/annual for 11 years; reach & frequency 3 years. Queries for granular data >37 months old return DateRangeError. Affects Ads API, scripts, GA Data API, BigQuery transfer. Relevant to reporting/measurement & audit guides.

### gads-signals-analytics-override-2026-06
Event: Google removes Analytics' ability to override Ads behaviour ("destination-specific controls")
Date: 2026-06
Cluster: saas-paid-marketing
Significance: medium
Source: https://ppc.land/google-strips-analytics-of-ad-data-authority-in-june-2026-consent-overhaul/  [SECONDARY — trade]
Related-official: Google Consent Mode / destination-specific controls docs (confirm exact Google URL before publishing)
Status: breaking
Reframe-by: 2026-09
Action: insert-mention
Should-mention:
  - content/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account.md
  - content/blogs/b2b-marketing-operations-guide.md
Does-mention: none
Notes: Effective June 15, 2026. After this, `ad_storage` in Consent Mode becomes the single gate for what ad data Google Ads collects; Google Signals in GA4 no longer controls Ads data collection. Conversion tracking itself unchanged — what changes is how Ads cookies/IDs are collected via the GA4 tag. Still want a direct Google doc before publishing as fact.

---

## MAINTENANCE LEDGER
- 2026-06-11 — Bank created with source list, significance gate, and schema.
- 2026-06-12 — First scan (30-day backfill, all clusters). Banked 5 items: I/O 2026 AI Mode (major), May 2026 core update (major), Google Ads budget pacing (major), Ads data retention (medium), Analytics/Ads override removal (medium). Spun off a stat_bank action: update zero-click % to 58.5% and AIO coverage from the I/O figures.
- 2026-06-12 — Primary-source verification pass: I/O 2026 → blog.google primary confirmed (+ AI Mode 1B / AI Overviews 2.5B MAU data); May core update → Google Status Dashboard primary confirmed; budget pacing → NO primary found (advertiser comms + LinkedIn only) → marked VERIFY. "Biggest change in 25 years" softened to Google's framing. Data-retention + override entries still need primaries.
- 2026-06-12 — Deeper verification + corrections: data-retention → PRIMARY found (Google Ads Developer Blog, May 1; 37-month detail added); budget-pacing dates CORRECTED (public Feb 19 / effective Mar 1 in waves — earlier "June 1" was wrong; status established); override → effective June 15, ad_storage becomes single gate (ppc.land secondary, Google consent-mode doc still to confirm). Does-mention computed: all 5 items = none currently in content (work queue = all candidates).
