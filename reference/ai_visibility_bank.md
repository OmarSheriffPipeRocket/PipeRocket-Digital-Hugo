# PipeRocket AI Visibility Bank

Tracks **why competitors get named/cited by AI engines** (AI Overviews, ChatGPT, Perplexity, Gemini, Copilot) for our target queries — and where *we* have a gap. The point is to replace "they're a big brand" with a decomposed, actionable cause.

Companion to `stat_bank.md` (numbers) and `news_bank.md` (events). This bank is about **citation/recommendation share** in AI answers.

Mental model: **GEO is influencer marketing for machines.** AI doesn't get convinced directly — it aggregates consensus from the sources it trusts. The "influencers" are the listicles, review sites, and communities it cites. You win by getting those sources to vouch for you, with a *specific, consistent* claim — earned, not faked.

---

## The 4 layers of AI visibility (diagnose which one a gap belongs to)

| Layer | Question | Dominant for | Signal: whose URL does AI cite? |
|---|---|---|---|
| 1. **Access** | Can AI crawlers read us? | everything (prerequisite) | — (foundation check) |
| 2. **Entity** | Does AI know who PipeRocket *is*? | brand recognition, non-brand recall | cites nobody / answers from memory |
| 3. **Corroboration** | Do trusted third parties vouch, with the specific claim? | commercial / "best X" queries | cites a **third party** (Clutch, listicle, Reddit) |
| 4. **Extractability** | Is *our own* content answer-ready? | informational (how-to, what-is) | cites **our own** page |

> Rule of thumb for each query: look at **whose URL the engine cited**. Third-party → corroboration play (layer 3). Our own → extractability play (layer 4). Nobody → entity/access (layers 1–2). Prescribing outreach when the fix was schema (or vice-versa) is the classic GEO mistake this column prevents.

---

## FOUNDATION CHECKLIST (layers 1–2 — check ~quarterly, not per query)

**Access (layer 1)**
- [ ] AI crawlers not blocked in robots.txt: `GPTBot`, `Google-Extended`, `PerplexityBot`, `ClaudeBot`, `CCBot`, `Bytespider` (decide allow/deny deliberately)
- [ ] `llms.txt` present and current
- [ ] Key pages render server-side / aren't JS-buried
- [ ] Sitemap fresh; important pages indexable

**Entity (layer 2)**
- [ ] Consistent one-line description of PipeRocket across site, Clutch, G2, LinkedIn, socials (same words)
- [ ] Wikidata / Knowledge Graph entity exists and is correct
- [ ] `Organization` + `sameAs` schema linking all official profiles
- [ ] Named authors (Kim, Praveen, …) have consistent author entities + bios
- [ ] HQ/NAP consistent everywhere (Chennai — see `piperocket.toml`)

_(Status: not yet audited — first foundation pass pending.)_

---

## Per-query entry schema (layers 3–4)

```
## Query: "<query>"  | intent: commercial|informational | cluster: <entity_map cluster>
Checked: <engines> | <date> | <#phrasings, fresh session>
PipeRocket named?: AIO _ / ChatGPT _ / Perplexity _ / Gemini _   → AI share: x/4
Primary lever: corroboration | extractability   (from "whose URL is cited")

### Competitor: <name>   (roster: data/agencies.toml)
Named in: <engines>
Cited sources: <urls — flag each as THIRD-PARTY or OWN-SITE>
Specific claim made: "<the exact thing the sources assert, e.g. 'a top SaaS SEO agency'>"
Why-category: list-inclusion | direct-answer | data/stat | comparison | third-party-validation | community
Corroboration count: <# of distinct trusted sources naming them with this claim>
On-site support: <their page + what makes it extractable>
Replicable?: yes | partial (brand-authority component) | no
Our gap: corroboration (which of those sources omit us) + extractability (our page vs theirs)
Action: get listed in <sources> | optimise/create <page> | community seeding | entity fix
```

---

## SEED QUERIES (v1)

> **Data status: SOURCE-LAYER proxy** (Google SERP + listicle contents, 2026-06-23). This captures layer 3 (corroboration) — *which third-party "influencers" rank and whom they name*. It is **NOT** a live per-engine citation check; the AIO/ChatGPT/Perplexity/Gemini "named?" scoreboard is still pending (see Data Collection). Roster: `data/agencies.toml`. Blocklist still applies to *featuring* (TripleDart, RevvGrowth, etc.) but we track them as competitors.

### Cross-query insight (the pattern, not the excuse)
The agencies that win these queries — **First Page Sage, Onely, Searchbloom, MADX, Omniscient** — are *both the cited source AND the named competitor*. They run a two-part play: **(1) publish a "best X agencies" listicle that ranks, and rank themselves in it; (2) get named across other publishers' lists.** That's replicable, not "they're big." PipeRocket already executes exactly this for **PPC** — and it's the *only* query of the four where we appear. We own listicles for all four (`best-saas-seo-agencies.md`, `best-saas-ppc-agencies.md`, `best-ai-seo-agencies.md`, `best-enterprise-seo-agencies.md`) — but only the PPC one ranks.

**Source-layer PipeRocket share: 1/4 queries.**

## Query: "best saas seo agencies"  | intent: commercial | cluster: saas-seo
Source layer (SERP/listicle, 2026-06-23): top "influencers" = firstpagesage.com, position.digital, onely.com, seoprofy.com, aimers.io, newmedia.com, cuttingedgepr.com, aeoengine.ai, tripledart.com *(blocklist)*
Competitors named: MADX Digital, Onely, Position Digital, Rock The Rankings, Omniscient Digital, Grow and Convert, First Page Sage
PipeRocket present?: **NO** — not named in top third-party lists; own `best-saas-seo-agencies.md` not ranking p1
Primary lever: corroboration + self-published listicle (we have the asset; it isn't ranking)
Our gap: absent from third-party lists **and** own listicle under-ranking
Action: (a) SEO/GEO push to rank `best-saas-seo-agencies.md`; (b) earn inclusion in First Page Sage / Position / Onely / SEOProfy lists; (c) compare why our PPC listicle ranks but this one doesn't (links/age/freshness)
Per-engine "named?": _pending live run_

## Query: "best saas ppc agencies"  | intent: commercial | cluster: saas-paid-marketing
Source layer (SERP/listicle, 2026-06-23): our own `/list/best-saas-ppc-agencies/` AND `/blogs/best-saas-ppc-agencies/` both rank p1; other sources = linkquest, disruptiveadvertising, rightleft, heydigital, scopicstudios, thesmarketers, revvgrowth *(blocklist)*
Competitors named: Directive, Disruptive Advertising, Powered by Search, KlientBoost, Hey Digital, Bay Leaf Digital, HawkSEM
PipeRocket present?: **YES** — own listicles rank and PipeRocket is named in aggregate summaries
Primary lever: working (self-published listicle ranks)
Our gap: smaller — we're absent from *some* third-party lists (heydigital, scopic, linkquest name others)
Action: keep own listicle fresh; pursue inclusion in the third-party lists that omit us; this is the template to copy to the other three queries
Per-engine "named?": _pending live run_

## Query: "best ai seo agencies"  | intent: commercial | cluster: ai-seo
Source layer (SERP/listicle, 2026-06-23): top "influencers" = onely.com, firstpagesage.com, searchbloom.com, spicymargarita.co, thriveagency.com, seoprofy.com, embarque.io (29-agency list), commercepundit.com, revvgrowth *(blocklist)*
Competitors named: Searchbloom, The SEO Works, Tinuiti, Digital Authority Partners, Omniscient, First Page Sage, Thrive, Intero, Victorious
PipeRocket present?: **NO** — not named; own `best-ai-seo-agencies.md` not ranking p1 (note: we also have `best-geo-agencies.md`, `best-saas-geo-agencies.md`, `best-aeo-agency.md`)
Primary lever: corroboration + self-published listicle
Our gap: absent from both; large-N lists (Embarque's 29, Spicy Margarita's B2B-focused) are the **easiest inclusion targets**
Action: rank our AI/GEO/AEO listicles; pitch for inclusion in Embarque + Spicy Margarita first (lower bar than First Page Sage's curated top-10)
Per-engine "named?": _pending live run_

## Query: "best enterprise seo agencies"  | intent: commercial | cluster: saas-seo (enterprise)
Source layer (SERP/listicle, 2026-06-23): top "influencers" = siegemedia.com, madx.digital, firstpagesage.com, searchbloom.com, ipullrank.com, onelittleweb.com, omniscient, semrush agencies directory, serpsculpt.com, fuelonline.com
Competitors named: Searchbloom, Directive, Seer Interactive, First Page Sage, iPullRank, NetPeak, OneLittleWeb
PipeRocket present?: **NO** — not named; own `best-enterprise-seo-agencies.md` not ranking p1
Primary lever: corroboration — **but entity/authority component is largest here** (named agencies cite Logitech/Verizon/Salesforce-tier clients)
Strategic question: is "enterprise" actually our ICP? PipeRocket positions to B2B SaaS (often mid-market). If enterprise isn't a real target, **deprioritise this query** rather than chase a positioning we don't hold.
Action: confirm ICP fit first; if yes, inclusion + rank own listicle + lean on case studies; if no, drop from the bank
Per-engine "named?": _pending live run_

---

## SHARE-OF-AI-VOICE TRACKER (trend over time)
Source-layer proxy first; per-engine columns fill once live runs start.
| Date | Query | Source-layer (PR present?) | AIO | ChatGPT | Perplexity | Gemini |
|---|---|---|---|---|---|---|
| 2026-06-23 | best saas seo agencies | ✗ | — | — | — | — |
| 2026-06-23 | best saas ppc agencies | ✓ | — | — | — | — |
| 2026-06-23 | best ai seo agencies | ✗ | — | — | — | — |
| 2026-06-23 | best enterprise seo agencies | ✗ | — | — | — | — |

---

## DATA COLLECTION — METHOD TBD (deciding with Omar)
Source layer (layer 3) is done via web research above. The per-engine "named?" scoreboard (layer A) still needs live runs — options: manual (4 queries is small), custom API pipeline (Perplexity Sonar + OpenAI web_search + Gemini grounding + SerpApi for AIO), or an off-the-shelf GEO tool. Whatever we pick must: hit multiple engines, fresh/no-personalization sessions, 2–3 phrasings/query, re-run on a cadence.

## MAINTENANCE LEDGER
- 2026-06-23 — Bank framework created (4-layer model, foundation checklist, per-query schema, 4 seed queries).
- 2026-06-23 — Source-layer research done for all 4 queries (Google SERP + listicle contents). Finding: PipeRocket appears only for "best saas ppc agencies" (own listicles rank); absent from SaaS-SEO, AI-SEO, Enterprise-SEO despite owning listicles for all. Recurring winners (First Page Sage, Onely, Searchbloom, MADX, Omniscient) run the "publish-a-ranking-list + get-cross-listed" play we already win at for PPC. Per-engine live scoreboard still pending.
