# PipeRocket — Content-Map SEO Audit

_All 277 pages in `data/content_map.yml` (241 keyword-target). Deterministic extraction (links, meta, schema, keyword frequency, GSC cannibalization, crawlability) + LLM judgment, adversarially verified for anchor mismatches, keyword targeting, and cannibalization severity._

## Executive summary

| Dimension | Signal |
| --- | --- |
| Pages audited | 277 (241 keyword-target) |
| Title > 60 chars | 17 |
| Meta desc > 160 / < 70 | 29 |
| H1 ≠ 1 | 1 |
| Article pages missing schema | 11 |
| Keyword pages not indexable | 1 |
| Thin internal linking (long body, <2 links) | 0 |
| Confirmed anchor mismatches | 35 |
| Keyword-targeting issues | 19 |
| Confirmed cannibalization pairs | 15 |

## 1. Crawlability

| Page | noindex | in_sitemap | canonical_self | alias |
| --- | --- | --- | --- | --- |
| /list/top-b2b-ppc-agencies/ | False | True | True | False |

## 2. Title tags

| Page | Len | Title |
| --- | --- | --- |
| /author/deepan-siddhu/ | 68 | Deepan Siddhu, Sr. Director of Growth Marketing \| PipeRocket Digital |
| /author/douglas-ribback/ | 74 | Douglas Ribback, VP, Head of Global Demand Generation \| PipeRocket Dig |
| /author/jithesh-joseph/ | 66 | Jithesh Joseph, Associate Director, Marketing \| PipeRocket Digital |
| /content-marketing-agency/ | 62 | AI-First Content Marketing Agency for US B2B SaaS \| PipeRocket |
| /cybersecurity-marketing-agency/ | 68 | AI-First Cybersecurity Marketing Agency for US B2B SaaS \| PipeRocket |
| /devtools-marketing-agency/ | 63 | AI-First DevTools Marketing Agency for US B2B SaaS \| PipeRocket |
| /edtech-marketing-agency/ | 61 | AI-First EdTech Marketing Agency for US B2B SaaS \| PipeRocket |
| /enterprise-ppc-agency/ | 63 | Enterprise PPC Agency \| Pipeline-Attributed Paid Media at Scale |
| /fintech-marketing-agency/ | 62 | AI-First Fintech Marketing Agency for US B2B SaaS \| PipeRocket |
| /healthtech-marketing-agency/ | 66 | AI-First Health Tech Marketing Agency for US B2B SaaS \| PipeRocket |
| /hrtech-marketing-agency/ | 62 | AI-First HR Tech Marketing Agency for US B2B SaaS \| PipeRocket |
| /insurancetech-marketing-agency/ | 64 | AI-First InsurTech Marketing Agency for US B2B SaaS \| PipeRocket |
| /legaltech-marketing-agency/ | 65 | AI-First Legal Tech Marketing Agency for US B2B SaaS \| PipeRocket |
| /martech-marketing-agency/ | 62 | AI-First MarTech Marketing Agency for US B2B SaaS \| PipeRocket |
| /partnership/ | 71 | PipeRocket Partnership Program \| Referral, Agency, Integration, Conten |
| /privacy-policy/ | 14 | Privacy Policy |
| /programmatic-seo-agency/ | 68 | AI-First Programmatic SEO (PSEO) Agency for US B2B SaaS \| PipeRocket |
| /proptech-marketing-agency/ | 63 | AI-First PropTech Marketing Agency for US B2B SaaS \| PipeRocket |

## 3. Meta descriptions

| Page | Desc len |
| --- | --- |
| /blogs/saas-seo/ | 168 |
| /blogs/types-of-keywords-in-seo/ | 161 |
| /alternative/ | 163 |
| /author/ | 161 |
| /compare/ | 168 |
| /glossary/ | 164 |
| /list/ | 169 |
| /tools/ | 162 |
| /vs/ | 161 |
| /account-based-marketing-agency/ | 174 |
| /bing-ads-agency/ | 189 |
| /content-marketing-agency/ | 162 |
| /cybersecurity-marketing-agency/ | 196 |
| /devtools-marketing-agency/ | 199 |
| /edtech-marketing-agency/ | 222 |
| /fintech-marketing-agency/ | 213 |
| /healthtech-marketing-agency/ | 234 |
| /hrtech-marketing-agency/ | 205 |
| /insurancetech-marketing-agency/ | 224 |
| /legaltech-marketing-agency/ | 221 |
| /link-building-agency/ | 167 |
| /marketing-ops/ | 162 |
| /martech-marketing-agency/ | 235 |
| /paid-social-agency/ | 161 |
| /partnership/ | 186 |
| /programmatic-seo-agency/ | 164 |
| /proptech-marketing-agency/ | 240 |
| /technical-seo-agency/ | 173 |
| /terms-and-conditions/ | 178 |

## 4. Heading tags

H1 ≠ 1 (should be exactly one):

| Page | H1 | H2 |
| --- | --- | --- |
| /glossary/what-is-crawling/ | 3 | 7 |

## 5. Schema (JSON-LD)

Article-type pages missing Article/DefinedTerm schema:

| Page | Type | Schema present |
| --- | --- | --- |
| /compare/directive-consulting-vs-refine-labs/ | compare | FAQPage, Organization |
| /compare/klientboost-vs-disruptive-advertising/ | compare | FAQPage, Organization |
| /compare/piperocket-digital-vs-klientboost/ | compare | FAQPage, Organization |
| /compare/piperocket-digital-vs-nogood/ | compare | FAQPage, Organization |
| /compare/piperocket-digital-vs-omniscient-digital/ | compare | FAQPage, Organization |
| /compare/piperocket-digital-vs-siege-media/ | compare | FAQPage, Organization |
| /compare/piperocket-digital-vs-webfx/ | compare | FAQPage, Organization |
| /compare/piperocket-vs-directive-consulting/ | compare | FAQPage, Organization |
| /compare/siege-media-vs-animalz/ | compare | FAQPage, Organization |
| /compare/siege-media-vs-omniscient-digital/ | compare | FAQPage, Organization |
| /compare/simpletiger-vs-skale/ | compare | FAQPage, Organization |

## 6. Internal linking

No thin-linking pages. ✅

_Per-page link counts + full anchor lists are in `content_map_per_page.md`._

## 7. Anchor-text mismatches (verified)

_Internal links whose anchor text points to a less-specific or wrong destination when a better page exists. Adversarially verified._

| Page | Anchor | Currently → | Should → | Why |
| --- | --- | --- | --- | --- |
| /glossary/what-is-a-backlink/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Anchor explicitly says 'early-stage startups' but links to the generic SaaS-SEO- |
| /glossary/what-is-a-canonical-tag/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Same systemic mismatch: the 'early-stage startups' anchor points to the generic  |
| /glossary/what-is-a-long-tail-keyword/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Anchor names 'early-stage startups'; the more specific, better-matching page /li |
| /glossary/what-is-a-meta-description/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Startup-qualified anchor links to the generic hub; the dedicated startups page / |
| /glossary/what-is-an-seo-audit/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Anchor's 'early-stage startups' qualifier is more specific than the hub target;  |
| /glossary/what-is-anchor-text/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Same anchor/destination mismatch; the startup-specific listicle is the better ta |
| /glossary/what-is-cls/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | 'Early-stage startups' anchor should point to /list/best-saas-seo-agencies-for-s |
| /glossary/what-is-domain-authority/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Same systemic mismatch; the dedicated startups page is the better-matching desti |
| /glossary/what-is-evergreen-content/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Anchor is more specific (startups) than the hub it links to; /list/best-saas-seo |
| /glossary/what-is-fid/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Startup-qualified anchor mis-points to the generic hub instead of the dedicated  |
| /glossary/what-is-google-search-console/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Same anchor/destination mismatch; the startup-specific page is the better target |
| /glossary/what-is-image-alt-text/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | 'Early-stage startups' anchor should resolve to /list/best-saas-seo-agencies-for |
| /glossary/what-is-indexing/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Same systemic mismatch between a startup-qualified anchor and the generic hub de |
| /glossary/what-is-on-page-seo/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Anchor names startups; the dedicated startups listicle is the better-matching ta |
| /glossary/what-is-off-page-seo/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Startup-qualified anchor mis-points to the generic hub instead of /list/best-saa |
| /glossary/what-is-schema-markup/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Same systemic anchor/destination mismatch; the startups page is the better targe |
| /glossary/what-is-serp/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | 'Early-stage startups' anchor should link to /list/best-saas-seo-agencies-for-st |
| /glossary/what-is-ssl-certificate/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Same systemic mismatch; the dedicated startups listicle is the more precise dest |
| /glossary/what-is-structured-data/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Anchor is more specific (startups) than the hub target; /list/best-saas-seo-agen |
| /glossary/what-is-technical-seo/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Same systemic anchor/destination mismatch; the startup-specific page is the bett |
| /glossary/what-are-keyword-clusters/ | "best SaaS SEO agencies for early-stage startups" | /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | Startup-qualified anchor links to the generic hub; /list/best-saas-seo-agencies- |
| /blogs/saas-seo/ | "ABM" | /account-based-marketing-agency/ | /glossary/what-is-abm/ | A bare acronym 'ABM' used as a definitional inline term links to the commercial  |
| /blogs/saas-link-building/ | "SaaS SEO agency guide" | /list/best-saas-seo-agencies/ | /list/best-saas-link-building-agencies/ | The sentence reads 'benchmark how top agencies approach this [link building] dif |
| /list/best-devtools-marketing-agencies/ | "SaaS marketing" | /saas-seo-agency/ | / | Anchor reads 'SaaS marketing agency' (PipeRocket described as a full B2B SaaS ma |
| /glossary/what-is-google-ads/ | "how top B2B PPC agencies optimize Google Ads auctions" | /list/best-affordable-b2b-ppc-agencies/ | /list/top-b2b-ppc-agencies/ | Anchor names generic 'B2B PPC agencies' with no 'affordable' qualifier, but link |
| /glossary/what-is-meta-ads/ | "top B2B PPC agency" | /list/best-affordable-b2b-ppc-agencies/ | /list/top-b2b-ppc-agencies/ | Plain 'top B2B PPC agency' anchor (no 'affordable') points to the affordable-var |
| /glossary/what-is-ppc/ | "top B2B PPC agencies for complex buying cycles" | /list/best-affordable-b2b-ppc-agencies/ | /list/top-b2b-ppc-agencies/ | Anchor head is generic 'B2B PPC agencies'; the 'affordable' qualifier in the des |
| /glossary/what-is-roas/ | "how top B2B PPC agencies approach paid SaaS growth" | /list/best-affordable-b2b-ppc-agencies/ | /list/top-b2b-ppc-agencies/ | Generic 'B2B PPC agencies' anchor links to the affordable-variant listicle; /lis |
| /glossary/what-is-sem/ | "top B2B PPC agencies for SaaS and enterprise campaigns" | /list/best-affordable-b2b-ppc-agencies/ | /list/top-b2b-ppc-agencies/ | Anchor refers to 'B2B PPC agencies' broadly (no 'affordable'); /list/top-b2b-ppc |
| /glossary/what-is-programmatic-advertising/ | "top B2B PPC agencies for high-control programmatic campaigns" | /list/best-affordable-b2b-ppc-agencies/ | /list/top-b2b-ppc-agencies/ | Unqualified 'B2B PPC agencies' anchor points to the affordable-variant page; the |
| /blogs/b2b-ppc/ | "top B2B PPC agencies" | /list/best-affordable-b2b-ppc-agencies/ | /list/top-b2b-ppc-agencies/ | The anchor 'top B2B PPC agencies' is a near-exact match for /list/top-b2b-ppc-ag |
| /glossary/what-is-nrr/ | "top SaaS SEO agencies" | /list/best-saas-seo-agencies-for-startups/ | /list/best-saas-seo-agencies/ | The anchor is the generic head term 'top/best SaaS SEO agencies' but it points t |
| /glossary/what-is-content-marketing/ | "best SaaS marketing agencies for content-driven growth" | /list/best-saas-marketing-agencies-2026/ | /list/best-saas-content-marketing-agencies/ | This is the content-marketing glossary and the anchor's qualifier ('content-driv |
| /glossary/what-is-content-marketing/ | "best B2B marketing agencies for content strategy" | /list/best-b2b-marketing-agencies/ | /list/best-b2b-content-marketing-agencies/ | On the content-marketing glossary, the anchor qualifier 'for content strategy' p |
| /list/best-b2b-demand-generation-agencies/ | "B2B demand generation" | /saas-ppc/ | /blogs/b2b-demand-generation-guide/ | The anchor text is the exact phrase 'B2B demand generation' but it points to the |

## 8. Keyword targeting (multiple primary / doubtful secondary)

| Page | Problem | Detail | Suggestion |
| --- | --- | --- | --- |
| /saas-ppc/ | primary_mismatch | Editorial primary is the bare term 'saas ppc', but this is a commercial agency landing pag | Retarget this landing page's primary to 'saas ppc agency' (matches its title and |
| /ai-seo-services/ | primary_mismatch | Primary 'ai seo services' barely registers for this page in GSC (only 'perplexity aeo serv | Tighten this page to the non-enterprise / mid-market AEO+GEO angle in its title  |
| /blogs/saas-seo-strategies-and-framework/ | primary_mismatch | This page's editorial primary is 'saas seo strategies' and its title is 'SaaS SEO Strategi | Decide one canonical owner of 'saas seo strategy/strategies'. Since /blogs/saas- |
| /blogs/how-to-rank-on-chatgpt-in-2026-strategies-and-tips/ | primary_mismatch | Editorial primary is 'how to rank on chatgpt' and the body genuinely covers ranking on Cha | Keep the primary as-is (it is the right editorial target) but strengthen on-page |
| /list/best-legaltech-marketing-agencies/ | primary_mismatch | Editorial primary is 'best legaltech marketing agencies' and the body is correctly about l | Decide which intent the page serves. Keep the legaltech-SaaS focus and strengthe |
| /blogs/saas-ppc-checklist/ | primary_mismatch | Editorial primary is 'saas ppc checklist', but the page's actual GSC impressions are domin | Keep 'saas ppc checklist' as primary, but stop the checklist from competing for  |
| /glossary/what-is-google-ads/ | primary_mismatch | Editorial primary is the definitional 'what is Google Ads', but every top GSC query is the | Keep this glossary page strictly definitional (target 'what is Google Ads'/'goog |
| /blogs/b2b-ppc-guide/ | primary_mismatch | This page and /blogs/b2b-ppc/ are both editorially assigned primary 'b2b ppc'. The guide's | Re-target this page to a how-to head term it actually earns, e.g. primary 'how t |
| /blogs/b2b-ppc/ | primary_mismatch | Editorial primary is 'b2b ppc', but the body and GSC lean SaaS-specific: top query is 'b2b | Keep one of the two blogs on 'b2b ppc' and make this the canonical 'b2b ppc' pag |
| /compare/piperocket-digital-vs-siege-media/ | primary_mismatch | Editorial primary is the navigational/branded term 'piperocket digital vs siege media', bu | Keep the comparison page but reframe its target around the demand it proves it c |
| /compare/piperocket-digital-vs-omniscient-digital/ | primary_mismatch | Editorial primary 'piperocket digital vs omniscient digital' captures no impressions. GSC  | Re-target around 'omniscient digital reviews / clutch rating / pricing' (what it |
| /compare/piperocket-digital-vs-klientboost/ | primary_mismatch | Editorial primary 'piperocket digital vs klientboost' gets no impressions. All GSC demand  | Align the primary with the proven demand: 'klientboost reviews' / 'klientboost p |
| /compare/piperocket-digital-vs-webfx/ | primary_mismatch | Editorial primary 'piperocket digital vs webfx' captures no impressions. GSC demand is Web | Re-target toward 'webfx clutch rating / webfx seo pricing / webfx reviews' (its  |
| /compare/piperocket-digital-vs-nogood/ | primary_mismatch | Editorial primary 'piperocket digital vs nogood' gets no impressions. GSC shows 'nogood ag | Re-target the primary toward the proven query 'nogood agency minimum budget' (an |
| /compare/piperocket-vs-directive-consulting/ | primary_mismatch | Editorial primary 'piperocket vs directive consulting' captures no impressions. GSC demand | Re-target toward Directive's proven demand ('directive consulting clutch rating  |
| /glossary/what-is-keyword-research/ | primary_mismatch | Editorial primary is 'what is Keyword Research' (correct for a definitional glossary, and  | Keep the editorial primary as 'what is keyword research' (it is the right call f |
| /list/best-b2b-seo-agencies/ | primary_mismatch | Editorial primary is 'best b2b seo agencies', but GSC impressions are overwhelmingly on th | Keep this as the single commercial listicle but treat the primary as the broader |
| /list/best-saas-growth-marketing-agencies/ | primary_mismatch | Editorial primary is 'best saas growth marketing agencies', but every top GSC query is the | Treat this as a true duplicate of /list/best-saas-marketing-agencies-2026/ rathe |
| /list/best-saas-marketing-agencies-2026/ | primary_mismatch | Editorial primary 'best saas marketing agencies' matches the page's intent and body, but t | Resolve by consolidating with /list/best-saas-growth-marketing-agencies/ (see th |

## 9. Cannibalization (verified real)

_Pages competing for the same primary keyword in GSC. Confirmed by an adversarial verifier (manual audit + GSC query overlap)._

| Page | Competing page | Severity | Action | Why |
| --- | --- | --- | --- | --- |
| /blogs/saas-seo/ | /blogs/saas-seo-strategies-and-framework/ | medium | differentiate | Both are informational SaaS-SEO blogs (this targets 'saas seo', competitor targe |
| /list/best-geo-agencies/ | /list/best-geo-agency/ | high | canonical | /list/best-geo-agency/ (singular) is a legacy/duplicate URL of this same 'best g |
| /list/best-technical-seo-agencies/ | /blog/best-technical-seo-agencies/ | medium | canonical | /blog/best-technical-seo-agencies/ is a legacy duplicate path (singular '/blog/' |
| /saas-ppc/ | /saas-ppc/faqs/ | medium | canonical | This is a child FAQ subpage of the same landing page ranking for the parent's ow |
| /blogs/saas-marketing-challenges-and-fixes/ | /blog/saas-marketing-companies-challenges/ | medium | canonical | The competitor /blog/saas-marketing-companies-challenges/ is not in the referenc |
| /blogs/saas-seo-strategies-and-framework/ | /blogs/saas-seo/ | high | merge | Genuine head-to-head cannibalization. /blogs/saas-seo/ ('SaaS SEO: The 8-Step Pi |
| /list/best-saas-link-building-agencies/ | /blog/best-saas-link-building-agency/ | medium | canonical | Same legacy-URL pattern: /blog/best-saas-link-building-agency/ is absent from th |
| /list/best-saas-seo-agencies/ | /list/best-saas-seo-agencies-for-startups/ | medium | differentiate | The startups-segment listicle repeatedly surfaces (19+12+5+3+1+1 impressions, al |
| /list/saas-seo-experts/ | /list/best-saas-seo-agencies/ | medium | differentiate | The best-saas-seo-agencies listicle pulls 106 (pos 76) + 1 (pos 78) impressions  |
| /blogs/saas-ppc/ | /blogs/saas-ppc-checklist/ | medium | differentiate | Both are informational SaaS-PPC pages. The checklist (target 'saas ppc checklist |
| /blogs/b2b-ppc-guide/ | /blogs/b2b-ppc/ | high | differentiate | Both blogs carry the identical editorial primary 'b2b ppc' and both target the s |
| /list/best-b2b-advertising-agencies/ | /blogs/best-b2b-marketing-agencies/ | medium | differentiate | A blog-format 'best b2b marketing agencies' roundup is competing with this comme |
| /list/top-b2b-ppc-agencies/ | /list/best-affordable-b2b-ppc-agencies/ | high | differentiate | Two commercial /list/ roundups both ranking for the core 'b2b ppc agency/agencie |
| /list/best-b2b-seo-agencies/ | /blogs/best-b2b-seo-agencies/ | high | canonical | Same exact commercial 'best b2b seo agencies' intent and a near-identical slug.  |
| /list/best-saas-marketing-agencies-2026/ | /list/best-saas-growth-marketing-agencies/ | high | merge | Two near-identical BOFU/commercial listicles in the same SaaS Marketing cluster, |

_All raw GSC cannibalization candidates (incl. unverified) are per-page in `content_map_per_page.md`._
