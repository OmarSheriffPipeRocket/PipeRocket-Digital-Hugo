# PipeRocket News Bank

A registry of **meaningful industry updates** (SEO, paid, AI search) that may affect what our content tells readers. Maintained by a weekly scan; consumed by the blog refresher to insert or reframe mentions.

The discipline is the **significance gate**: most weeks the scan logs *nothing*. We only bank an update if it changes what we'd advise — not because news happened.

This file is internal and version-controlled. One of the PipeRocket "bank" family, kept non-overlapping: `stat_bank.md` (third-party numbers), `experience-bank.md` (first-party data/frameworks), `news_bank.md` (this file — events), `ai_visibility_bank.md` (who AI engines cite/name for our queries). Routing: numbers → stat_bank; events → here; AI citation share → ai_visibility_bank.

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

> First scan: 2026-06-23, 30-day backfill (~late-May → 2026-06-23), all three clusters. 5 items cleared the significance gate (3 major, 2 medium). AI-Overview *numbers* (zero-click 58.5%, CTR 27%→11%, −38% clicks) are NOT banked here — they belong in `stat_bank.md` and supersede the existing `semrush-57pct-zero-click` / `semrush-aio-13-14pct` entries.

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
Does-mention: content/blogs/b2b-saas-seo.md
Notes: AI Mode citations only ~14% overlap with AI Overview citations — implies optimizing for both surfaces separately. Higher weight on structured answers, schema, demonstrable expertise. Verify the primary Google announcement URL before publishing claims. (2026-06-23 maintenance add: same I/O announcement also introduced user-created "information agents" in Search, rolling out summer 2026, and confirmed AI-generated search now reaches ~200 countries — both part of this entry, not separate items.)

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
Does-mention: content/blogs/how-to-do-saas-content-audit.md (re-homed 2026-06-23 as a 5th "when to audit" trigger, after the saas-seo pillar rewrite clobbered the original insertion)
Notes: Rolled out May 21, completed ~June 4. Standard Google guidance ("people-first content"). Use only where a post discusses ranking volatility/recovery; don't bolt onto unrelated guides. Next core update expected ~June–July 2026 — watch. RE-HOME options: re-insert into the rewritten saas-seo.md, or use saas-seo-strategies-and-framework.md / how-to-do-saas-content-audit.md (both in Should-mention).

### gads-budget-pacing-2026-06
Event: Google Ads budget pacing for ad scheduling — from June 1 2026, campaigns using daily budgets with ad schedules pace toward the full monthly limit (30.4× daily budget) regardless of active days (can raise spend on dayparted campaigns). [Separate from, but related to, the May 7 "demand-led budget pacing" AI feature.]
Date: 2026-06-01 (effective)  [CONFIRMED by official Google Ads notification — earlier Feb/Mar dates were wrong]
Cluster: saas-paid-marketing
Significance: major
Source: Official Google Ads in-product notification "Updates to Google Ads Budget Pacing for Ad Scheduling" (screenshot supplied by Omar 2026-06-23) [PRIMARY — Google's own wording]
Related-official: https://business.google.com/us/accelerate/announcements/demand-led-budget-pacing/ (the separate May 7 demand-led pacing AI feature)
Secondary: https://searchengineland.com/google-changes-budget-pacing-rules-for-scheduled-campaigns-475107
Status: VERIFIED — the 30.4×/regardless-of-schedule behavior is now confirmed as OFFICIAL Google wording (not trade interpretation)
Reframe-by: 2026-09
Action: update-advice
Should-mention:
  - content/blogs/how-to-run-google-ads-for-saas.md
  - content/blogs/saas-ppc.md
  - content/blogs/b2b-ppc.md
  - content/blogs/b2b-ppc-guide.md
  - content/blogs/saas-ppc-checklist.md
  - content/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account.md
Does-mention: content/blogs/how-to-run-google-ads-for-saas.md
Notes: PUBLISHING GUIDANCE — now fully primary-backed by Google's own notification. Exact Google wording: "On June 01, 2026, budget pacing will change for campaigns using daily budgets in conjunction with ad schedules. This change will make it easier for advertisers to hit their monthly spending goals." / "Previously, our systems would typically pace towards spending your daily budget times the number of active days in your ad schedule. Starting June 1, we will pace towards spending the monthly limit (30.4 times your daily budget) regardless of any ad schedules." / "Billing limits are unchanged. Your monthly bill remains capped at 30.4 times your daily budget and your daily bill remains capped at 2 times your daily budget." / "Campaigns will never run on days disabled by ad schedules." Safe to state the 30.4×/regardless-of-schedule behavior as official fact. Practical impact for dayparted campaigns: e.g. a weekend-only $100/day campaign that previously spent ~$800/mo could now pace toward the full 30.4× ≈ $1,600/mo unless the daily budget is lowered.

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
Does-mention: content/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account.md
Notes: Effective June 1, 2026. Granular (hourly/daily/weekly) reporting data retained 37 months; monthly/quarterly/annual for 11 years; reach & frequency 3 years. Queries for granular data >37 months old return DateRangeError. Affects Ads API, scripts, GA Data API, BigQuery transfer. Relevant to reporting/measurement & audit guides.

### gads-signals-analytics-override-2026-06
Event: Google removes Analytics' ability to override Ads behaviour ("destination-specific controls")
Date: 2026-06
Cluster: saas-paid-marketing
Significance: medium
Source: https://support.google.com/analytics/answer/17016975  [PRIMARY — Google Analytics Help Center]
Secondary: https://ppc.land/google-strips-analytics-of-ad-data-authority-in-june-2026-consent-overhaul/ ; https://www.dataslayer.ai/blog/ga4-google-ads-data-controls-june-15-2026
Status: VERIFIED
Reframe-by: 2026-09
Action: insert-mention
Should-mention:
  - content/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account.md
  - content/blogs/b2b-marketing-operations-guide.md
Does-mention: content/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account.md
Notes: Effective June 15, 2026. Per Google: "Google Ads settings will exclusively control Google Ads data" and "Google Analytics settings will exclusively control data used within Google Analytics." `ad_storage` in Consent Mode becomes the single gate for ad-data collection; Google Signals in GA4 no longer controls Ads data. Conversion tracking itself unchanged — what changes is how Ads cookies/IDs are collected via the GA4 tag. Primary confirmed via Google Analytics Help Center.

### gads-bidding-budgeting-overhaul-2026-06
Event: Google Ads bidding & budgeting overhaul — 3 changes announced June 15 2026: (1) Bidding Target Optimization (auto Aug 17; pulls budget-limited over-delivering campaigns back to target; Bid Target Adjustment Tool ships July 6); (2) Smart Bidding Exploration expands to all PMax w/o feeds (+18% query categories, +19% conversions); (3) Promotion Mode beta (temporary ROAS/budget boosts for peak events). Also a RENAME: "Maximize conversions w/ Target CPA" → "Target CPA"; "Maximize conversion value w/ Target ROAS" → "Target ROAS".
Date: 2026-06-15 (announced) — Bidding Target Optimization auto-applies 2026-08-17
Cluster: saas-paid-marketing
Significance: major
Source: https://business.google.com/us/accelerate/announcements/  [PRIMARY — Google Ads product announcements; confirm exact post]
Secondary: https://ppc.land/google-ads-gets-promotion-mode-and-a-major-bidding-overhaul-this-august/ ; https://almcorp.com/news/google-ads-three-bidding-budgeting-updates-june-2026/
Status: breaking
Reframe-by: 2026-10
Action: update-advice
Should-mention:
  - content/blogs/how-to-run-google-ads-for-saas.md
  - content/blogs/saas-ppc.md
  - content/blogs/b2b-ppc-guide.md
  - content/blogs/the-8-common-saas-google-ads-mistakes-to-avoid-in-2026.md
Does-mention: none
Notes: The Target CPA/ROAS RENAME matters for our PPC content — any guide using the old "Maximize conversions w/ a target CPA" phrasing should update (rename-lint candidate). Bidding Target Optimization is the behavioral change to flag (auto Aug 17). Verify the exact Google announcement post before publishing.

### google-unconfirmed-update-2026-06-19
Event: Unconfirmed Google ranking update (~June 19 2026) — community reports of movement hitting spam/black-hat tactics; most volatility trackers stayed calm; Google has NOT confirmed or named it
Date: 2026-06-19 (reported)
Cluster: saas-seo
Significance: medium
Source: https://www.seroundtable.com/google-search-ranking-volatility-41523.html  [SECONDARY — Search Engine Roundtable]
Status: RESOLVED — superseded by the confirmed June 2026 spam update (see june-2026-spam-update)
Reframe-by: n/a
Action: watch → closed
Should-mention: (none — watch only)
Does-mention: none
Notes: Per the primary-source rule, was never published as a "Google update" — unconfirmed and unnamed. RESOLVED 2026-06-29: the June-19 black-hat-targeting volatility was almost certainly the leading edge of the now-confirmed Google June 2026 SPAM update (rolled out Jun 24, completed Jun 26), which explicitly targets manipulative/spam tactics. Closing this watch item; the real, citable event is june-2026-spam-update.

### chatgpt-brand-links-2026-05
Event: ChatGPT made brand names clickable callouts inside responses (May 7 2026) — total ChatGPT referrals reportedly +157.7% week-over-week after the change
Date: 2026-05-07
Cluster: ai-seo
Significance: medium
Source: https://higoodie.com/blog/ai-search-traffic-report-2026/  [SECONDARY — trade/traffic report; find a primary OpenAI/ChatGPT source before publishing the +157.7% figure]
Status: VERIFY
Reframe-by: 2026-09
Action: insert-mention
Should-mention:
  - content/blogs/how-to-rank-on-chatgpt-in-2026-strategies-and-tips.md
  - content/blogs/research-ai-seo-statistics.md
Does-mention: none
Notes: Strengthens the "get cited inside AI answers" thesis — citations are now clickable, so AI-citation traffic is more measurable. The +157.7% WoW is a third-party traffic-tool figure; treat as illustrative until a primary confirms.
Corroboration (2026-06-29): Similarweb's 2026 GenAI Brand Visibility Index independently reports the same +157.7% WoW ChatGPT referrals and +354.7% homepage referrals after the May 7 clickable-brand-links change — two trade sources now agree, but still no primary OpenAI confirmation, so EVENT is solid / the exact % stays vendor-sourced. Related stat banked: similarweb-ai-rec-2.5x-traffic-2026 (stat_bank).

### google-ai-search-guidance-2026
Event: Google published official AI-search guidance (mid-2026) stating AEO/GEO are "still SEO" (not separate disciplines) and that **llms.txt, content chunking, AI-specific rewriting, and special schema are NOT needed** for its generative AI features; AI-focused site files may be crawled but get no special treatment.
Date: 2026-06
Cluster: ai-seo, saas-seo
Significance: major
Source: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide  [PRIMARY — Google Search Central, confirmed 2026-06-23]
Secondary: https://www.searchenginejournal.com/googles-new-ai-search-guide-calls-aeo-and-geo-still-seo/575026/
Status: VERIFIED
Does-mention: content/blogs/how-to-write-saas-seo-content-with-ai-that-actually-ranks.md (live as of 2026-06-23 rewrite)
Reframe-by: 2026-10
Action: update-advice
Should-mention:
  - content/blogs/how-to-rank-on-chatgpt-in-2026-strategies-and-tips.md
  - content/blogs/how-to-write-saas-seo-content-with-ai-that-actually-ranks.md
  - content/blogs/saas-seo.md
Does-mention: content/blogs/llms-txt-for-saas.md (2026-07-01, cites primary as the "not-as-relevant" backing)
Notes: ⚠️ CONTENT-CHECK NEEDED — this may CONTRADICT our own advice. saas-seo.md Step 8 recommends `llms.txt`; our GEO/AEO framing treats AI optimisation as somewhat distinct. Google now says those special tactics aren't required and AEO/GEO ≈ SEO. Decide our editorial stance (we can still argue llms.txt is low-cost insurance, but must acknowledge Google's position) and reconcile across the ai-seo cluster. Strong "take" candidate for the newsletter (pattern: Google keeps collapsing "AI SEO" hype back into fundamentals).

### gads-campaign-type-migrations-2026
Event: Google Ads campaign-type shifts (2026): (a) DSA→AI Max auto-migration DELAYED from Sept 2026 to Feb 2027, DSA creation returned, and AI Max is now the DEFAULT for new Search campaigns; (b) standalone Display campaigns being retired in favour of Demand Gen, with an in-product migration tool rolling out June 2026; (c) new Gemini-powered ad formats from GML 2026 (Conversational Discovery ads, Highlighted Answers, AI Shopping ads, Business Agent for Leads).
Date: 2026-06
Cluster: saas-paid-marketing
Significance: medium
Source: https://searchengineland.com/google-delays-dynamic-search-ads-migration-to-ai-max-480049  [SECONDARY]
Secondary: https://www.searchenginejournal.com/google-is-retiring-standalone-display-campaigns-in-favor-of-demand-gen/575889/ ; https://searchengineland.com/google-tests-new-conversational-ad-formats-in-ai-mode-and-search-478115
Status: breaking
Reframe-by: 2026-12
Action: update-advice
Should-mention:
  - content/blogs/how-to-run-google-ads-for-saas.md
  - content/blogs/saas-ppc.md
  - content/blogs/b2b-ppc-guide.md
Does-mention: none
Notes: Net direction = Google pushing advertisers onto AI-driven campaign types (AI Max, Demand Gen) and Gemini ad formats. Relevant to any guide that discusses campaign-type selection or DSA. AI Max default + DSA-migration timeline (now Feb 2027) is the actionable bit. Confirm exact primaries (Google Ads announcements) before publishing specifics.

### june-2026-spam-update
Event: Google June 2026 spam update (2nd spam update of 2026) — global, all languages; targets manipulative/spam tactics with scaled AI-generated spam squarely in scope. No policy change: existing spam policies remain the framework.
Date: 2026-06 (rolled out Jun 24, completed Jun 26)
Cluster: saas-seo
Significance: major
Source: https://searchengineland.com/google-june-2026-spam-update-done-rolling-out-481063  [SECONDARY — SEL; the Google Search Status Dashboard has a SEPARATE June-spam incident, NOT the May-core-update incident wdAXJk6LRRihEjpzEeWE]
Status: breaking
Reframe-by: 2026-09
Action: update-advice
Should-mention:
  - content/blogs/how-to-write-saas-seo-content-with-ai-that-actually-ranks.md
  - content/blogs/saas-seo.md
  - content/blogs/how-to-do-saas-content-audit.md
Does-mention: none
Notes: Direction is consistent — Google keeps tightening on AI-content-at-scale (this is the through-line across recent spam + core updates). Take: scaled, low-effort AI spam is the explicit target; well-sourced, genuinely-useful AI-assisted content is not. Use only where a post discusses spam policy, AI-content quality, or ranking volatility/recovery. RESOLVES the google-unconfirmed-update-2026-06-19 watch item (that June-19 black-hat volatility was the leading edge of this).

### gsc-genai-performance-reports-2026-06
Event: Google launched Search Console "Search Generative AI" performance reports (impressions/pages inside AI Overviews, AI Mode, and Discover — no click data yet) AND a new content control letting sites opt their content out of AI features. Shipped with a deep-dive help doc.
Date: 2026-06 (live Jun 17, initially a UK subset, expanding)
Cluster: ai-seo
Significance: medium
Source: https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports  [PRIMARY — Google Search Central]
Status: breaking
Reframe-by: 2026-10
Action: insert-mention
Should-mention:
  - content/blogs/research-ai-seo-statistics.md
  - content/blogs/how-to-write-saas-seo-content-with-ai-that-actually-ranks.md
  - content/blogs/how-to-rank-on-chatgpt-in-2026-strategies-and-tips.md
  - content/blogs/how-to-report-seo-to-the-board.md
Does-mention: none
Notes: Implication — AI visibility is becoming MEASURABLE in first-party tooling (a reporting/board-reporting hook), and Google again reiterates "no special AI optimization needed" (reinforces google-ai-search-guidance-2026: AEO/GEO ≈ SEO). The opt-out control is the actionable lever for sites that want to block AI-feature use. No click data yet — flag that limitation when citing.

---

## MAINTENANCE LEDGER
- 2026-06-23 — Bank created with source list, significance gate, and schema.
- 2026-06-23 — First scan (30-day backfill, all clusters). Banked 5 items: I/O 2026 AI Mode (major), May 2026 core update (major), Google Ads budget pacing (major), Ads data retention (medium), Analytics/Ads override removal (medium). Spun off a stat_bank action: update zero-click % to 58.5% and AIO coverage from the I/O figures.
- 2026-06-23 — Primary-source verification pass: I/O 2026 → blog.google primary confirmed (+ AI Mode 1B / AI Overviews 2.5B MAU data); May core update → Google Status Dashboard primary confirmed; budget pacing → NO primary found (advertiser comms + LinkedIn only) → marked VERIFY. "Biggest change in 25 years" softened to Google's framing. Data-retention + override entries still need primaries.
- 2026-06-23 — Deeper verification + corrections: data-retention → PRIMARY found (Google Ads Developer Blog, May 1; 37-month detail added); budget-pacing dates CORRECTED (public Feb 19 / effective Mar 1 in waves — earlier "June 1" was wrong; status established); override → effective June 15, ad_storage becomes single gate (ppc.land secondary, Google consent-mode doc still to confirm). Does-mention computed: all 5 items = none currently in content (work queue = all candidates).
- 2026-06-23 — ALL 5 items inserted into best-fit posts (one home each, primary-cited, with a pattern/implication take): AI Mode → b2b-saas-seo.md; May core update → saas-seo.md; budget pacing → how-to-run-google-ads-for-saas.md; data-retention + override → the-no-nonsense-guide-to-auditing-your-saas-ppc-account.md. Does-mention updated accordingly. Budget-pacing screenshot (official Google Ads notification) confirmed the 30.4×/June-1 detail as official. Also (stat_bank): ppcsurvey upgraded 2025→2026 (53%); Gartner 75%/67% collision reconciled in saas-content-marketing.md.
- 2026-06-23 — MAINTENANCE RUN (confirm scan). No new bankable items beyond the same-day backfill. Folded two sub-details into the I/O 2026 entry: user-created "information agents" (summer 2026 rollout) + AI-generated search now in ~200 countries. Next full scan due ~2026-06-30 (weekly cadence).
- 2026-06-23 — Budget-pacing VERIFIED: found the official primary — it's Google's "demand-led budget pacing" (Ads & Commerce Blog, May 7). Reframed the entry: the FEATURE is official; the "30.4× / full-monthly-regardless-of-schedule overspend" detail is trade interpretation (SEL), not in Google's wording. Publishing guidance added.
- 2026-06-23 — Override VERIFIED: ppc.land + dataslayer both cite the same primary — Google Analytics Help Center answer/17016975. Entry upgraded to PRIMARY. ALL 5 first-scan items now have confirmed Google primaries.
- 2026-06-23 — Budget-pacing fully RESOLVED: Omar supplied the official Google Ads notification screenshot ("Updates to Google Ads Budget Pacing for Ad Scheduling"). Corrects the effective date to June 1, 2026 (the Feb/Mar dates were wrong) and confirms the 30.4×/regardless-of-schedule behavior as OFFICIAL Google wording (no longer trade interpretation). Also clarified this ad-scheduling change is SEPARATE from the May 7 "demand-led budget pacing" AI feature — they were conflated earlier.
- 2026-06-23 — RECHECK (newer-news sweep, mid→late June). Added 3 entries: (1) gads-bidding-budgeting-overhaul (June 15, MAJOR — Bidding Target Optimization auto Aug 17, Smart Bidding Exploration → all PMax, Promotion Mode beta, + Target CPA/ROAS rename); (2) google-unconfirmed-update-2026-06-19 (medium, VERIFY — unconfirmed/unnamed, watch only); (3) chatgpt-brand-links (May 7, medium, VERIFY — clickable brand callouts, +157.7% WoW referrals per trade tool). Stat side flagged separately: AI Overviews coverage now ~50% (was ~16%) → stat_bank needs-fix.
- 2026-06-23 — SEJ + SEL targeted scan (Omar request). Added 2 more: (4) google-ai-search-guidance-2026 (MAJOR — "AEO/GEO still SEO"; llms.txt/chunking/special-schema NOT needed → ⚠️ may contradict our saas-seo.md llms.txt advice; content-check flagged); (5) gads-campaign-type-migrations-2026 (medium — DSA→AI Max delayed to Feb 2027 + AI Max now default; Display→Demand Gen; new Gemini ad formats). News_bank now holds 10 entries.
- 2026-06-29 — WEEKLY SCAN (email + web; first automated weekly-news-scan run). Banked 2: june-2026-spam-update (MAJOR, PRIMARY Google Status Dashboard — 2nd spam update of 2026, Jun 24–26, scaled-AI-spam in scope) and gsc-genai-performance-reports-2026-06 (medium, PRIMARY Google Search Central — AI-features impression reporting + content opt-out, live Jun 17 UK subset). RESOLVED watch item google-unconfirmed-update-2026-06-19 → it was the leading edge of the confirmed spam update. 7 items reviewed below gate (Ads API v24.2, Std-Shopping max-conv-value bidding, Google-hosted lead form, Smart Campaigns creation off Aug 3, Demand Gen AI tools, Merchant Center agency roles, Ads ToS Jul 1 — all incremental/ecommerce/admin, no advice change). News_bank now holds 12 entries (1 resolved/closed). Stat candidates routed to stat_bank for verification (see stat ledger 2026-06-29).
- 2026-06-29 — FULL MAINTENANCE RUN (status-lifecycle + reframe-due check, all 12 entries). NO reframes due: earliest Reframe-by is 2026-08 (may-2026-core-update); all others 2026-08→2026-12; today 2026-06-29. Statuses left as-is (breaking items are genuine June events, not yet "old"). Updated 1 VERIFY item: chatgpt-brand-links-2026-05 now CORROBORATED by a 2nd independent trade source (Similarweb 2026 GenAI Index reports the same +157.7% WoW / +354.7% homepage) — event solid, exact % still vendor-sourced (no OpenAI primary), so stays VERIFY on the figure. No items aged into historical. Next weekly scan ~2026-07-06.
