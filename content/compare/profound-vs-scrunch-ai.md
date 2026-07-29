---
title: "Profound vs Scrunch AI"
description: "A neutral head-to-head comparison of Profound and Scrunch AI across AI engine coverage, pricing, bot-traffic detection, content workflows, and G2 ratings for teams buying an AEO platform."
metaTitle: "Profound vs Scrunch AI: AEO Tools Compared (2026)"
metaDescription: "Profound vs Scrunch AI compared on engine coverage, pricing, bot-traffic tracking, and G2 ratings. An independent 2026 breakdown for AEO tool buyers."
date: 2026-07-27
category: "Head-to-head"
readingTime: "9 min read"
sources_count: 26
writtenBy: "omar"
reviewedBy: "kim"
neutral: true

product_a:
  name: "Profound"
product_b:
  name: "Scrunch AI"

toc:
  - { label: "The short answer",       anchor: "short-answer" }
  - { label: "At a glance",            anchor: "at-a-glance" }
  - { label: "Vendor profile",         anchor: "backgrounds" }
  - { label: "Decision matrix",        anchor: "decision-matrix---who-fits-which-side" }
  - { label: "Capability comparison",  anchor: "services" }
  - { label: "Pricing",                anchor: "pricing" }
  - { label: "Strengths & tradeoffs",  anchor: "strengths--tradeoffs" }
  - { label: "Ratings & track record", anchor: "ratings--track-record" }
  - { label: "FAQ",                    anchor: "faqs" }

short_answer:
  heading: "The short answer"
  intro: >-
    Profound and Scrunch AI are both platforms built for answer-engine
    optimization (AEO): tracking how a brand shows up inside ChatGPT,
    Perplexity, Gemini, and other AI answers. The honest split is scale and
    ownership. Profound is the larger, better-funded, still-independent
    platform (a $1B valuation, roughly 140 to 165 staff, up to 9 engines on
    Enterprise) with a content-authoring layer that can draft and publish AEO
    fixes into a CMS. Scrunch AI is the smaller team, acquired by Sitecore in
    June 2026 for a reported $225M, whose product edge is edge-served,
    code-light page delivery to detected AI bots plus its full platform list
    on the cheapest paid tier. Both vendors now offer server-log and CDN
    detection of AI bot traffic that Google Analytics misses, so that
    capability is table stakes rather than a differentiator for either.
    Neither company has a deep, independently verified review base yet; treat
    public ratings on both as directional.
  callouts:
    - label: "Profound fits"
      title: "Enterprise teams that want scale, independence, and content workflows"
      body: >-
        If you need the **broader top-end engine list** (up to 9 engines on
        Enterprise, and the only one of the two that lists DeepSeek),
        demand-side "Prompt Volumes" data on what people actually ask AI, and
        an **autonomous content layer** that can draft and publish fixes
        straight into WordPress or Sanity, Profound's scale and funding back
        that roadmap. Budget past the $99/mo Starter tier (ChatGPT-only)
        toward Growth at $399/mo for real multi-engine coverage.
    - label: "Scrunch AI fits"
      title: "Teams that want multi-engine coverage on the entry tier"
      body: >-
        If your priority is **the full platform list on the cheapest paid
        tier** (7 platforms named on Starter versus ChatGPT only on
        Profound's), **edge-served, code-light pages for detected AI bots**
        via the Agent Experience Platform, and published **month-to-month
        billing at $300/mo**, Scrunch AI is the sharper pick. Factor in that
        it is now a Sitecore company, which helps if you run Sitecore and
        adds roadmap risk if you do not.

at_a_glance:
  - { label: "Founded / Vendor",  a: "Profound Inc. (tryprofound.com), founded 2024, independent",  b: "Scrunch AI (scrunch.com), founded 2023, launched Nov 2024, acquired by Sitecore June 2026" }
  - { label: "HQ / Offices",      a: "New York, NY, plus San Francisco, London, Buenos Aires",       b: "Salt Lake City, UT" }
  - { label: "Funding / Ownership", a: "$155M total; $96M Series C at a $1B valuation (Feb 2026, Lightspeed)", b: "$19M raised; acquired by Sitecore June 2026 for a reported $225M" }
  - { label: "Starting price",    a: "$99/mo (Starter, ChatGPT only, 50 prompts)",                  b: "$250/mo annual (Starter, 7 platforms listed) or $300/mo month to month" }
  - { label: "Public rating",     a: "~4.5 to 4.6/5 G2 (review counts cited from 140 to 1,037; sources conflict, verify live)", b: "4.7/5 G2 (about 59 reviews, secondary sourced; verify live)" }
  - { label: "Best for",          a: "Enterprise scale, DeepSeek and Grok coverage, agentic content workflows", b: "Full platform list on the entry tier, edge-served pages for AI bots, Sitecore stacks" }

backgrounds:
  heading: "Vendor profile"
  companies:
    - name: "Profound"
      meta: "AEO platform · founded 2024 · New York with SF, London, Buenos Aires offices"
      body: >-
        Profound was founded in 2024 by James Cadwallader (CEO) and Dylan
        Babbs (CTO, previously a design engineer on Uber Maps). It raised a
        $96M Series C in February 2026 led by Lightspeed Venture Partners at
        a $1B valuation, bringing total funding to $155M. Headcount was
        roughly 140 across four cities at the time of that raise, and
        third-party trackers now list higher figures (PitchBook about 165),
        so treat the number as a floor rather than a current headcount. The
        platform tracks brand representation across nine engines on Enterprise
        (ChatGPT, Perplexity, Claude, Gemini, Grok, Copilot, Meta AI,
        DeepSeek, and Google AI Overviews) and adds "Prompt Volumes"
        demand-side data, an "Agent Analytics" module that reads server logs
        and CDN traffic to detect AI crawler activity GA4 misses, and
        autonomous Agents that can draft and publish content directly into
        WordPress or Sanity. Named customers include Ramp, Figma, MongoDB,
        Target, Walmart, and DocuSign; the company states it serves 700+
        enterprises including more than 10% of the Fortune 500. G2 rating data
        for Profound is genuinely inconsistent across secondary sources
        (figures ranging from 4.5 to 4.6/5 and review counts cited anywhere
        from 140 to 1,037), and the 1,037 figure appears to come from a
        rolled-up G2 seller page rather than the single product listing, so
        treat it as unverified. Capterra shows 0 reviews for Profound as of
        this research.
      facts:
        - { label: "Founded",         value: "2024" }
        - { label: "HQ",              value: "New York, NY, plus SF, London, Buenos Aires" }
        - { label: "Founders",        value: "James Cadwallader (CEO), Dylan Babbs (CTO)" }
        - { label: "Team",            value: "~140 at the Feb 2026 Series C; trackers now list ~165 (PitchBook)" }
        - { label: "Funding",         value: "$155M total; $96M Series C at $1B valuation (Feb 2026)" }
        - { label: "Ownership",       value: "Independent, venture-backed" }
        - { label: "Notable clients", value: "Ramp, Figma, MongoDB, Target, Walmart, DocuSign, Plaid, Deel" }
        - { label: "Public rating",   value: "~4.5 to 4.6/5 G2 (conflicting review counts, verify live); 0 on Capterra" }
      credentials:
        awards: ["G2 Winter 2026 \"Definitive Leader\" in the AEO category (per Profound's own announcement)"]
        certifications: ["SOC 2 Type II (stated on Profound's feature and pricing pages)"]
    - name: "Scrunch AI"
      meta: "AEO platform · founded 2023 · Salt Lake City, UT · a Sitecore company since June 2026"
      body: >-
        Scrunch AI was founded in 2023 by Chris Andrew (CEO) and Robert
        MacCloy (CTO), publicly launching the product in November 2024. It
        raised $19M total, including a $15M Series A in July 2025 led by
        Decibel on top of an earlier seed round backed by Mayfield and
        angels including Clara Shih and TJ Parker. In June 2026 the company
        was acquired by the digital-experience vendor Sitecore for a reported
        $225M (Bloomberg's figure; Sitecore did not disclose terms), and
        Sitecore has said existing Scrunch customers can keep using it as a
        standalone product while Scrunch-driven features are folded into the
        Sitecore platform over time. Reported headcount before the deal was
        inconsistent across data providers (PitchBook cites 77 employees,
        Crunchbase lists a 51 to 100 range, Wellfound lists 11 to 50), so
        treat team size as roughly 50 to 80 people rather than a precise
        figure. Scrunch's clearest technical differentiator is the "Agent
        Experience Platform," which serves an optimized, code-light version of
        pages to detected AI bots at the network edge. It also runs direct CDN
        and edge-network integrations (Cloudflare, Akamai, Fastly, AWS
        CloudFront, Google Cloud CDN, Vercel, Netlify, WordPress) that catch
        AI-bot crawl traffic GA4 never records, though Profound now ships an
        equivalent server-log and CDN layer, so that is no longer unique to
        Scrunch. Its FAQ lists eight supported platforms today, with Grok
        marked as coming soon, and it has completed a SOC 2 Type II audit.
        Named customers include Lenovo, BairesDev, Clerk, Skims, and Penn
        State University; the company states 500+ companies and agencies use
        the platform. G2 shows 4.7/5 across about 59 reviews per secondary
        aggregation of the G2 seller page (direct G2 fetch was blocked during
        research, and one secondary source cites "50+" rather than 59);
        Capterra shows 0 reviews.
      facts:
        - { label: "Founded",         value: "2023 (launched Nov 2024)" }
        - { label: "HQ",              value: "Salt Lake City, UT" }
        - { label: "Founders",        value: "Chris Andrew (CEO), Robert MacCloy (CTO)" }
        - { label: "Team",            value: "Roughly 50 to 80 employees pre-acquisition (sources disagree)" }
        - { label: "Funding",         value: "$19M raised; $15M Series A (July 2025, Decibel)" }
        - { label: "Ownership",       value: "Acquired by Sitecore, June 2026, reported $225M" }
        - { label: "Notable clients", value: "Lenovo, BairesDev, Clerk, Skims, Penn State University" }
        - { label: "Public rating",   value: "4.7/5 G2 (~59 reviews, secondary sourced); 0 on Capterra" }
      credentials:
        certifications: ["SOC 2 Type II (audit confirmed in Scrunch's own FAQ)"]

services:
  heading: "Capability comparison"
  intro: >-
    Both platforms cover the AEO core: multi-engine visibility monitoring,
    brand/citation tracking, and server-log or CDN detection of AI crawler
    traffic. The real gaps are narrower than the marketing suggests. Profound
    built out content authoring, demand-side prompt data, and the only engine
    list that includes DeepSeek; Scrunch AI built out edge-served page
    delivery for AI bots and puts its whole platform list on the cheapest
    paid tier.
  table:
    - { label: "Top-tier engine list",                      a: "✓ (up to 9 on Enterprise, the only one listing DeepSeek)", b: "~ (8 platforms today, Grok listed as coming soon)" }
    - { label: "Entry-tier engine coverage",                a: "~ (Starter tier is ChatGPT only)", b: "✓ (Starter tier lists 7 platforms)" }
    - { label: "Brand/citation/sentiment monitoring",       a: "✓", b: "✓" }
    - { label: "Demand-side prompt-volume data",            a: "✓ (\"Prompt Volumes\")", b: "✕ (not described in public materials)" }
    - { label: "Autonomous content drafting and CMS publish", a: "✓ (Agents, native WordPress/Sanity)", b: "✕ (monitoring and edge-serving rather than content authoring)" }
    - { label: "CDN/edge AI bot-traffic detection",         a: "✓ (\"Agent Analytics\": server logs plus Cloudflare, Akamai, Fastly, CloudFront, GCP, Vercel, Netlify)", b: "✓ (Cloudflare, Akamai, Fastly, CloudFront, GCP, Vercel, Netlify)" }
    - { label: "Bot-optimized page delivery at the edge",   a: "✕ (recommendations only, no edge-served variant)", b: "✓ (Agent Experience Platform)" }
    - { label: "SOC 2 Type II",                            a: "✓ (stated on feature and pricing pages)", b: "✓ (audit confirmed in vendor FAQ)" }
    - { label: "Native Slack alerting",                     a: "✓", b: "~ (not confirmed in public materials)" }
    - { label: "Enterprise data API",                       a: "✓ (documented REST API, Enterprise tier, beta on request)", b: "✓ (Enterprise Data API)" }
    - { label: "SSO / SAML",                                a: "✓ (Enterprise tier)", b: "✓ (Enterprise tier, SAML 2.0/OIDC, Okta, Entra ID)" }
    - { label: "Independent vendor (not owned by a DXP suite)", a: "✓", b: "✕ (Sitecore company since June 2026)" }

pricing:
  heading: "Pricing: what you'll actually pay"
  intro: >-
    Both pricing pages were verified live on 29 July 2026. Profound's
    headline entry looks cheaper, but it only unlocks ChatGPT tracking;
    genuine multi-engine coverage starts at $399/mo. Scrunch AI's Starter
    tier is priced higher on paper but already lists 7 platforms, so the
    real per-engine cost runs the other way at the entry level.
  table:
    - { label: "Starting price",              a: "$99/mo (Starter, ChatGPT only, 50 prompts, 1,500 responses)", b: "$250/mo annual, $300/mo monthly (Starter, 7 platforms, 350 custom + 1,000 industry prompts, 3 seats)" }
    - { label: "First genuine multi-engine tier", a: "$399/mo (Growth, 3 engines: ChatGPT, Perplexity, AI Overviews)", b: "Included at Starter ($250 to $300/mo, 7 platforms)" }
    - { label: "Mid tier",                     a: "Growth, $399/mo (3 engines, 100 prompts, 9,000 responses, \"Popular\")", b: "Growth, $417/mo annual, $500/mo monthly (same platform list, 700 custom + 2,500 industry prompts, 5 personas)" }
    - { label: "Enterprise tier",              a: "Custom, demo-gated (up to 9 engines, SSO/SAML, SOC 2, dedicated Slack support)", b: "Custom (SAML/OIDC, Enterprise Data API, dedicated GTM team)" }
    - { label: "Add-on cost structure",        a: "Agents feature billed as credits (100/400/custom per month by tier)", b: "None noted in public materials" }
    - { label: "Billing flexibility",          a: "Published tier prices are billed yearly (2 months free)", b: "Both annual and month-to-month prices published (17% annual discount)" }

faqs:
  - q: "What is the main difference between Profound and Scrunch AI?"
    a: >-
      Profound is the larger, independent, better-funded platform: a $1B
      valuation, roughly 140 to 165 employees, up to 9 engines on Enterprise,
      plus autonomous Agents that can draft and publish AEO content into a
      CMS. Scrunch AI is the smaller team, now owned by Sitecore after a June
      2026 acquisition, whose product edge is serving code-light, AI-optimized
      pages to detected bots at the network edge, plus an entry tier that
      already lists 7 platforms.
  - q: "Is Profound or Scrunch AI cheaper?"
    a: >-
      It depends on what you need on day one. Profound's headline Starter
      price ($99/mo) is lower, but it only tracks ChatGPT with 50 prompts;
      real multi-engine coverage requires Growth at $399/mo. Scrunch AI's
      Starter tier costs more upfront ($250 to $300/mo) but already lists
      7 platforms, so per-engine cost is lower at the entry level.
  - q: "Which platform has more AI engines covered?"
    a: >-
      They are close at the top end. Profound's Enterprise tier lists up to 9
      engines and is the only one of the two to include DeepSeek; Scrunch AI's
      FAQ lists 8 supported platforms with Grok marked as coming soon. At the
      entry level the gap is real: Scrunch AI's Starter tier lists 7 platforms
      out of the box, while Profound's Starter tier is limited to ChatGPT only.
  - q: "Does either tool detect AI bot traffic that Google Analytics misses?"
    a: >-
      Both do, and this is no longer a Scrunch-only capability. Scrunch AI's
      CDN and edge-network integrations (Cloudflare, Akamai, Fastly, AWS
      CloudFront, Vercel, Netlify, WordPress) detect AI crawler visits at the
      network layer. Profound's "Agent Analytics" module does the same job from
      server logs plus the same set of CDN and hosting integrations, and it
      explicitly markets capturing crawler activity that GA4 misses.
  - q: "Can either tool automatically publish content changes?"
    a: >-
      Profound is the one with a content-authoring layer. Its Agents feature
      can draft AEO-oriented content and push it directly into WordPress or
      Sanity through native CMS integrations. Scrunch AI's public materials
      describe monitoring, auditing, and edge-serving an optimized page
      version to AI bots, but not autonomous content drafting or publishing.
  - q: "Does Sitecore's acquisition of Scrunch AI matter when you buy?"
    a: >-
      It should factor in. Sitecore acquired Scrunch in June 2026 for a
      reported $225M, and Sitecore has said existing customers can keep
      running Scrunch standalone while its capabilities get folded into the
      Sitecore platform over time. That is a plus if you already run Sitecore
      and a roadmap risk if you want a vendor whose only product is AEO.
      Profound remains independent and venture-backed.
  - q: "How reliable are the public review ratings for each tool?"
    a: >-
      Both should be treated as directional rather than settled. Profound's G2
      figures conflict across secondary sources (4.5 to 4.6/5, with review
      counts cited anywhere from 140 to over 1,000, the higher figure
      likely inflated by a rolled-up seller page), and it shows 0 reviews on
      Capterra. Scrunch AI shows 4.7/5 across about 59 reviews via secondary
      aggregation of its G2 seller page, with another source citing "50+",
      and also 0 Capterra reviews. Direct G2 verification was blocked for both
      during this research; confirm current figures on G2 before relying on
      either rating.

sources:
  - { id: 1, title: "Profound, homepage", url: "https://www.tryprofound.com/", accessed: "July 2026" }
  - { id: 2, title: "Profound, pricing", url: "https://www.tryprofound.com/pricing", accessed: "July 2026" }
  - { id: 3, title: "Profound, integrations", url: "https://www.tryprofound.com/integrations", accessed: "July 2026" }
  - { id: 4, title: "Profound, Series C announcement", url: "https://www.tryprofound.com/blog/profound-raises-96m-series-c", accessed: "July 2026" }
  - { id: 5, title: "Profound, G2 Winter 2026 AEO leader post", url: "https://www.tryprofound.com/blog/profound-named-definitive-aeo-leader-in-g2-winter-report-2026", accessed: "July 2026" }
  - { id: 6, title: "Crunchbase, Profound organization profile", url: "https://www.crunchbase.com/organization/profound-1b0a", accessed: "July 2026" }
  - { id: 7, title: "Fortune, Profound raises $96M Series C", url: "https://fortune.com/2026/02/24/exclusive-as-ai-threatens-search-profound-raises-96-million-to-help-brands-stay-visible/", accessed: "July 2026" }
  - { id: 8, title: "Sequoia Capital, Profound partner profile", url: "https://sequoiacap.com/article/partnering-with-profound-winning-on-the-ai-stage/", accessed: "July 2026" }
  - { id: 9, title: "Capterra, Profound listing (0 reviews)", url: "https://www.capterra.com/p/10041880/Profound/", accessed: "July 2026" }
  - { id: 10, title: "Vismore, Profound review (G2 rating aggregation)", url: "https://www.vismore.ai/blog/profound-review", accessed: "July 2026" }
  - { id: 11, title: "Scrunch AI, homepage", url: "https://scrunch.com/", accessed: "July 2026" }
  - { id: 12, title: "Scrunch AI, pricing", url: "https://scrunch.com/pricing/", accessed: "July 2026" }
  - { id: 13, title: "Scrunch AI, about", url: "https://scrunch.com/about/", accessed: "July 2026" }
  - { id: 14, title: "TechCrunch, Scrunch AI coverage", url: "https://techcrunch.com/2025/03/04/scrunch-ai-is-helping-companies-stand-out-in-ai-search/", accessed: "July 2026" }
  - { id: 15, title: "PitchBook, Scrunch AI company profile", url: "https://pitchbook.com/profiles/company/708134-32", accessed: "July 2026" }
  - { id: 16, title: "The SaaS News, Scrunch AI raises $15M Series A", url: "https://www.thesaasnews.com/news/scrunch-ai-raises-15-million-in-series-a/", accessed: "July 2026" }
  - { id: 17, title: "Scrunch AI Help Center, supported CDN integrations", url: "https://helpcenter.scrunchai.com/en/articles/12845473-supported-cdn-integrations-for-agent-traffic", accessed: "July 2026" }
  - { id: 18, title: "Capterra, Scrunch AI listing (no reviews yet)", url: "https://www.capterra.com/p/10030499/Scrunch-AI/", accessed: "July 2026" }
  - { id: 19, title: "G2, Scrunch AI seller listing (59 reviews)", url: "https://www.g2.com/sellers/scrunch-7a57483c-7011-4906-8549-2ba209b7b851", accessed: "July 2026" }
  - { id: 20, title: "Profound, Agent Analytics feature page (AI crawler tracking, CDN and server-log integrations)", url: "https://www.tryprofound.com/features/agent-analytics", accessed: "July 2026" }
  - { id: 21, title: "Profound, Prompt Volumes feature page", url: "https://www.tryprofound.com/features/prompt-volumes", accessed: "July 2026" }
  - { id: 22, title: "Profound, REST API documentation", url: "https://docs.tryprofound.com/rest-api/introduction", accessed: "July 2026" }
  - { id: 23, title: "GlobeNewswire, Profound Series C release (700+ enterprises, Fortune 500 claim, named customers)", url: "https://www.globenewswire.com/news-release/2026/2/24/3243475/0/en/profound-raises-series-c-at-1b-valuation-to-lead-a-new-category-of-marketing.html", accessed: "July 2026" }
  - { id: 24, title: "Scrunch AI, FAQ: which AI platforms and LLMs Scrunch tracks", url: "https://scrunch.com/faqs/which-ai-platforms-and-llms-can-scrunch-track-and-monitor/", accessed: "July 2026" }
  - { id: 25, title: "Scrunch AI, FAQ: SOC 2 Type II compliance", url: "https://scrunch.com/faqs/is-scrunch-soc-2-type-ii-compliant-and-what-security-standards-does-it-meet", accessed: "July 2026" }
  - { id: 26, title: "TechTarget, Sitecore acquires Scrunch for answer engine optimization", url: "https://www.techtarget.com/searchcustomerexperience/news/366643973/Sitecore-acquires-Scrunch-for-answer-engine-optimization", accessed: "July 2026" }
featuredImage: "/images/compare-covers/profound-vs-scrunch-ai.webp"
---

## Decision matrix - who fits which side

| Criterion | Profound | Scrunch AI |
|---|:---:|:---:|
| Need CDN or server-log AI bot-traffic detection GA4 can't see | ✓ | ✓ |
| Need autonomous content Agents that draft and publish to a CMS | ✓ | ✕ |
| Need lowest-cost genuine multi-engine entry (5+ engines) | ✕ | ✓ |
| Need DeepSeek in the tracked engine list | ✓ | ✕ |
| Need demand-side data on what people actually ask AI | ✓ | ✕ |
| Need a completed SOC 2 Type II audit | ✓ | ✓ |
| Need the larger, better-known enterprise reference roster | ✓ | ~ |
| Need bot-optimized page delivery served at the edge | ✕ | ✓ |
| Need the deepest review-volume social proof | ✓ | ✕ |
| Need an independent, AEO-only vendor | ✓ | ✕ |
| Need native fit with a Sitecore DXP stack | ✕ | ✓ |

*Check = clear edge. Tilde = capable but not the stronger pick. Cross = outside the model.*

## Strengths & tradeoffs

Both platforms are still young products (2023 to 2024 launches) without a deep, independently verified review history. The honest comparison is what each one built its engineering effort around, and each side wins rows the other does not.

| Axis | Profound | Scrunch AI |
|---|---|---|
| **Scale and funding** | $155M raised, $1B valuation, ~140 to 165 staff across 4 offices | $19M raised pre-acquisition, ~50 to 80 staff, single HQ |
| **Ownership** | Independent, venture-backed | Acquired by Sitecore June 2026 (reported $225M); continues standalone, features to be folded into Sitecore |
| **Engine coverage (top end)** | Up to 9 engines on Enterprise, includes DeepSeek and Grok | 8 platforms supported today, Grok listed as coming soon, no DeepSeek |
| **Engine coverage (entry tier)** | ChatGPT only on Starter ($99/mo) | 7 platforms on Starter ($250 to $300/mo) |
| **AI bot-traffic detection** | "Agent Analytics": server logs plus CDN integrations across ~10 providers | CDN/edge integrations across 8 providers, detects GA4-invisible bot traffic |
| **Content workflow** | Autonomous Agents draft and publish into WordPress/Sanity | Monitoring, auditing, and edge-serving only, no content authoring |
| **Demand-side data** | "Prompt Volumes" panel data on real AI queries | Not described in public materials |
| **Bot-facing delivery** | Recommendations only, no edge-served page variant | Agent Experience Platform serves code-light pages to detected AI bots |
| **Security posture** | SOC 2 Type II stated, SSO/SAML on Enterprise | SOC 2 Type II audit completed, SAML 2.0/OIDC, RBAC, audit logs |
| **Customer roster** | Ramp, Figma, MongoDB, Target, Walmart, DocuSign | Lenovo, BairesDev, Clerk, Skims, Penn State |
| **Public review volume** | Low to mid hundreds on G2 (figures conflict), 0 on Capterra | ~59 on G2 (secondary sourced), 0 on Capterra |
| **Reported user friction** | Steep learning curve, data-heavy UI, manual setup | No bulk export, thin visualization/reporting, some reliability complaints |

## Ratings & track record

| Metric | Profound | Scrunch AI |
|---|---|---|
| G2 rating | ~4.5 to 4.6 / 5 (sources conflict) | 4.7 / 5 |
| G2 reviews | Cited anywhere from ~140 to ~300+ (product-page level); a 1,037 figure exists but likely rolls up a seller account rather than the single product | ~59 (secondary sourced from a G2 seller listing; one source cites "50+") |
| Capterra reviews | 0 | 0 |
| Founded | 2024 | 2023 (launched Nov 2024) |
| Total funding | $155M ($1B valuation) | $19M raised before acquisition |
| Ownership | Independent | Sitecore (acquired June 2026, reported $225M) |
| Team size | ~140 at Feb 2026 Series C, ~165 per PitchBook | ~50 to 80 (sources disagree) |
| Notable signal | G2 Winter 2026 "Definitive Leader" in AEO (vendor's own claim) | SOC 2 Type II audit completed |

Both companies launched their products within the last two to three years, so neither has the multi-year, thousand-plus-review track record that older SaaS categories take for granted. Direct G2 verification was blocked for both vendors during this research (403 responses on automated fetch), so every rating above comes from secondary aggregation of G2 data rather than a live direct pull. Profound's figures are the least consistent of the two, with three different secondary sources citing three different review counts for what should be the same underlying G2 page. Scrunch AI's 59-review figure is more consistently repeated across independent sources, giving it slightly more confidence despite the smaller pool. Confirm both ratings directly on G2 before treating either as a settled fact.

One more track-record note that will not show up in a ratings table: Scrunch AI is no longer an independent company. Sitecore acquired it in June 2026 for a reported $225M, and Sitecore's stated plan is to keep Scrunch available standalone for existing customers while integrating its capabilities into the wider Sitecore platform. If you already run Sitecore, that is an advantage. If you do not, weigh how a suite owner is likely to prioritize a point solution against Profound, which is still independent and funding a dedicated AEO roadmap.

For teams comparing the wider AEO category rather than just these two, [Profound](/alternative/profound-alternatives/) and [Scrunch AI](/alternative/scrunch-ai-alternatives/) each have their own alternatives roundups, and both tools also appear side by side in our broader [AI visibility tools](/list/best-ai-visibility-tools/) and [AEO tools](/list/best-aeo-tools/) reviews.

---

*Both tools' data is sourced from publicly available information as of 29 July 2026. Direct G2 verification was blocked for both vendors during research; all G2 figures above come from secondary aggregation and should be reconfirmed live before purchase. Deal value for the Sitecore/Scrunch acquisition is Bloomberg's reported figure; Sitecore did not disclose terms. This comparison is independent; we take no affiliate or referral fees from either vendor.*
