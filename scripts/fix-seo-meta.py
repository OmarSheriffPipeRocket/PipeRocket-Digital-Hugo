#!/usr/bin/env python3
"""
Bulk-fix obvious SEO meta issues:

  1. Strip redundant brand suffixes from metaTitle.
     Hugo's head-meta.html already appends " | PipeRocket" when the
     title doesn't contain the brand. So titles ending in
     "| PipeRocket Digital", "- PipeRocket Digital", or "- PipeRocket"
     are oversized AND inconsistent with the auto-suffix.
     We strip the redundant suffix; head-meta.html will re-append
     " | PipeRocket" automatically.

  2. Apply a curated map of targeted rewrites for:
       · the 5 TOO LONG descriptions
       · the duplicate titles/descriptions

The script is idempotent and only writes a file if its frontmatter
actually changes.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

# Suffixes we strip from metaTitle. Order matters — match the longest first.
STRIP_SUFFIXES = [
    " | PipeRocket Digital",
    " - PipeRocket Digital",
    " | PipeRocket",
    " - PipeRocket",
]

# Curated rewrites for the 5 too-long descriptions and the duplicate set.
# Key: relative path from repo root. Value: dict of frontmatter keys to set.
REWRITES = {
    # ---------- TOO LONG descriptions ----------
    "content/authors/praveen.md": {
        "metaDescription":
            "10+ yrs as in-house marketer and agency operator. Managed $500K+/month budgets at Dentsu and SaaS Labs. Writes about B2B SaaS PPC and pipeline attribution."
    },
    "content/authors/ranjeeth.md": {
        "metaDescription":
            "6 years scaling LinkedIn Ads and Google Ads for B2B SaaS. Obsessed with payback period and CAC. Writes about paid attribution and conversion-focused PPC."
    },
    "content/authors/rohith.md": {
        "metaDescription":
            "Senior SEO Specialist at PipeRocket. Data-driven organic search for B2B SaaS: technical SEO, topical authority, BOFU intent. Previously SEO at Kovai.co."
    },
    "content/list/preview-best-saas-seo-agencies-classic.md": {
        "metaDescription":
            "I ranked the 11 best MarTech marketing agencies for 2026 on positioning, pipeline attribution, real results, transparency, and pricing. From 40+ vendors."
    },
    "content/tools/free-seo-roi-calculator.md": {
        "metaDescription":
            "Free B2B SaaS SEO ROI calculator. Traffic → MQLs → pipeline → ARR with pre-filled benchmarks for Fintech, HR Tech, Dev Tools. See payback in 60 seconds."
    },

    # ---------- Duplicate TITLE fixes (rewrite the secondary copy) ----------
    "content/blogs/b2b-ppc.md": {
        "metaTitle":       "B2B PPC: A Complete 2026 Strategy Guide for SaaS Teams",
        "metaDescription": "B2B PPC strategy for 2026: how to build campaigns that generate qualified pipeline, not just clicks. ICP mapping, intent tiers, and budget allocation."
    },
    "content/blogs/my-picks-for-the-12-best-saas-marketing-agencies-for-2026.md": {
        "metaTitle":       "My Picks: 12 Best SaaS Marketing Agencies for 2026",
        "metaDescription": "Personal picks for the 12 best SaaS marketing agencies in 2026 — scored on B2B SaaS specialization, pipeline attribution, real client outcomes, and pricing."
    },
    "content/list/best-saas-seo-agencies-2.md": {
        "metaTitle":       "Best SaaS SEO Agencies for 2026: 11 Picks Compared",
        "metaDescription": "Compared 50+ SaaS SEO agencies and ranked 11 best for 2026 — pipeline attribution, BOFU-led strategy, client outcomes, and retainer pricing transparency."
    },
    # preview-best-saas-seo-agencies.md is a preview/draft duplicate of the
    # martech listicle — mark it with a unique placeholder so it's no longer
    # a SERP duplicate. (Best long-term: drop it from sitemap.)
    "content/list/preview-best-saas-seo-agencies.md": {
        "metaTitle":       "MarTech Agencies (Preview) — PipeRocket Internal",
        "metaDescription": "Internal preview of the MarTech marketing agencies ranking. Not yet published. See the live list at /list/best-martech-marketing-agencies/."
    },

    # ---------- Duplicate DESC fix (the remaining one not already touched) ----------
    "content/blogs/how-to-run-a-saas-content-audit-that-actually-moves-rankings.md": {
        "metaDescription":
            "A practical SaaS content audit: how to find pages eating crawl budget, decide what to keep, rewrite, merge, or kill, and turn audits into ranking moves."
    },

    # ---------- Trim 11 LONG titles to ≤60 chars ----------
    "content/blogs/how-to-do-saas-seo-keyword-research.md": {
        "metaTitle": "How I Do SaaS SEO Keyword Research in 2026"
    },
    "content/blogs/saas-seo-checklist.md": {
        "metaTitle": "My SaaS SEO Checklist for 2026"
    },
    "content/faqs.md": {
        "metaTitle": "FAQs: Pricing, Process, Services & Results"
    },
    "content/glossary/what-is-brand-positioning.md": {
        "metaTitle": "What Is Brand Positioning? Definition & SaaS Guide"
    },
    "content/glossary/what-is-conversion-rate.md": {
        "metaTitle": "What Is Conversion Rate? How To Measure & Improve"
    },
    "content/glossary/what-is-fid.md": {
        "metaTitle": "What Is FID? Field Data, SEO Impact & Common Mistakes"
    },
    "content/glossary/what-is-google-ads.md": {
        "metaTitle": "What Is Google Ads? A Practical SaaS / B2B Guide"
    },
    "content/glossary/what-is-gpt.md": {
        "metaTitle": "What is GPT? A Clear Guide to Generative AI"
    },
    "content/glossary/what-is-image-alt-text.md": {
        "metaTitle": "What Is Image Alt Text? SEO & Accessibility Guide"
    },
    "content/glossary/what-is-ssl-certificate.md": {
        "metaTitle": "What Is an SSL Certificate? SaaS Guide"
    },
    "content/reviews.md": {
        "metaTitle": "Reviews | Verified B2B SaaS Clients"
    },

    # ---------- Trim 25 LONG descriptions to ≤160 chars ----------
    "content/about-us.md": {
        "metaDescription": "Run by senior B2B SaaS operators. Founded 2020. Pipeline programmes shipped for 70+ SaaS brands including Storylane, Spendflo, HyperVerge."
    },
    "content/aeo-geo-agency.md": {
        "metaDescription": "AEO and GEO agency for B2B SaaS. Rank in ChatGPT, Perplexity, Claude, and Gemini for buyer queries that actually move pipeline."
    },
    "content/authors/kim.md": {
        "metaDescription": "12+ yrs in SaaS SEO, studied 150+ B2B SaaS brands. Co-Founder of PipeRocket. Builds topical authority and BOFU-led organic pipeline."
    },
    "content/authors/varshini.md": {
        "metaDescription": "Builds topical authority programmes for B2B SaaS. Editorial background in tech publications. Writes about SaaS content strategy."
    },
    "content/blogs/b2b-linkedin-marketing-guide.md": {
        "metaDescription": "Master B2B LinkedIn Marketing in 2026 with proven strategies, content frameworks, and lead-gen tactics that grow qualified pipeline."
    },
    "content/blogs/research-ai-seo-statistics.md": {
        "metaDescription": "60+ AI SEO statistics for 2026, from 8 months of real analytics and CRM data across 53 B2B SaaS brands. AI vs organic compared."
    },
    "content/compare/piperocket-vs-directive-consulting.md": {
        "metaDescription": "PipeRocket Digital vs Directive Consulting. Pricing, services, team structure, contract terms compared across 40+ SaaS engagements."
    },
    "content/cybersecurity-marketing-agency.md": {
        "metaDescription": "Cybersecurity marketing agency for SecOps, GRC, identity, and cloud-security SaaS. Technical content + ABM built for CISO buyers."
    },
    "content/devtools-marketing-agency.md": {
        "metaDescription": "Developer-tools marketing agency for B2B SaaS. OSS-friendly content, technical SEO, and developer-led demand gen tied to pipeline."
    },
    "content/faqs.md": {
        "metaDescription": "Answers to questions B2B SaaS founders ask before signing: pricing, contracts, onboarding, reporting, attribution, and results."
    },
    "content/fintech-seo-agency.md": {
        "metaDescription": "Fintech SEO agency for banking, payments, and embedded finance SaaS. Compliance-aware content + BOFU-led pipeline attribution."
    },
    "content/glossary/what-is-evergreen-content.md": {
        "metaDescription": "Evergreen content is timeless, search-optimized info that keeps driving leads. What evergreen means and how SaaS teams get it right."
    },
    "content/glossary/what-is-google-search-console.md": {
        "metaDescription": "Google Search Console is a free tool to track website visibility in Google. What it does, why it matters, how SaaS teams use it."
    },
    "content/glossary/what-is-nrr.md": {
        "metaDescription": "NRR (Net Revenue Retention) shows how much SaaS revenue you keep and expand from current customers. How NRR works and what teams miss."
    },
    "content/glossary/what-is-programmatic-advertising.md": {
        "metaDescription": "Programmatic advertising automates buying and placing digital ads in real time. How it works and what smarter SaaS teams do instead."
    },
    "content/insurancetech-marketing-agency.md": {
        "metaDescription": "InsurTech marketing agency for B2B SaaS — underwriting, claims, policy admin, embedded insurance. Compliance-aware pipeline content."
    },
    "content/legaltech-marketing-agency.md": {
        "metaDescription": "Legal-tech marketing agency for B2B SaaS — practice management, e-discovery, CLM, legal ops. Pipeline-first content for GCs and firms."
    },
    "content/list/best-affordable-b2b-ppc-agencies.md": {
        "metaDescription": "Top 7 affordable B2B PPC agencies for 2026 — scored on specialization, pipeline attribution, results, transparency, and pricing."
    },
    "content/list/best-linkedin-marketing-agencies.md": {
        "metaDescription": "The best LinkedIn marketing agencies for B2B SaaS in 2026 — scored on LinkedIn expertise, pipeline attribution, ABM fluency, pricing."
    },
    "content/martech-marketing-agency.md": {
        "metaDescription": "MarTech marketing agency for B2B SaaS — CDPs, automation, attribution, analytics. Category-positioning + pipeline-first content."
    },
    "content/proptech-marketing-agency.md": {
        "metaDescription": "PropTech marketing agency for B2B real estate, leasing, property management, construction-tech SaaS. Pipeline-tied buyer-journey content."
    },
    "content/research-methodology.md": {
        "metaDescription": "Editorial policy behind every PipeRocket list. Sources, scoring criteria, conflict-of-interest handling, and corrections."
    },
    "content/reviews.md": {
        "metaDescription": "Verified PipeRocket Digital reviews from Clutch, G2, and direct testimonials. Real pipeline outcomes from B2B SaaS engagements."
    },
    "content/terms-and-conditions.md": {
        "metaDescription": "Terms and conditions for using PipeRocket Digital's website and engaging us for B2B SaaS marketing services."
    },
    "content/tools/query-fanout-analyser.md": {
        "metaDescription": "Free AI search query fanout analyser. See how ChatGPT, Perplexity, Claude, and Gemini fan out queries into sub-questions."
    },
}


# Patterns that recognise simple "key: value" lines in YAML/TOML-ish frontmatter
_FM_PATTERN = re.compile(r"^---\s*\n(?P<fm>.+?)\n---\s*\n", re.DOTALL)


def strip_redundant_suffix(title: str) -> str:
    """Return title with the redundant brand suffix removed.
    Hugo head-meta.html will re-append ' | PipeRocket' when missing."""
    for s in STRIP_SUFFIXES:
        if title.endswith(s):
            return title[: -len(s)].rstrip()
    return title


def update_frontmatter(text: str, updates: dict) -> str:
    """Update specific keys in YAML-style frontmatter. Preserves order &
    formatting for unchanged lines."""
    m = _FM_PATTERN.match(text)
    if not m:
        return text
    fm = m.group("fm")
    lines = fm.split("\n")
    keys_set = set()
    new_lines = []
    for line in lines:
        match = re.match(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not match:
            new_lines.append(line)
            continue
        indent, key, raw_val = match.groups()
        if key in updates:
            new_val = updates[key]
            keys_set.add(key)
            new_lines.append(f'{indent}{key}: "{new_val}"')
        else:
            new_lines.append(line)
    # Append keys that didn't exist (rare but safe)
    for key, val in updates.items():
        if key not in keys_set:
            new_lines.append(f'{key}: "{val}"')
    new_fm = "\n".join(new_lines)
    return text[: m.start("fm")] + new_fm + text[m.end("fm") :]


def get_frontmatter_field(text: str, key: str):
    m = _FM_PATTERN.match(text)
    if not m:
        return None
    for line in m.group("fm").split("\n"):
        match = re.match(rf"^\s*{key}:\s*(.*)$", line)
        if match:
            return match.group(1).strip().strip('"').strip("'")
    return None


def main():
    changes = []  # list of (relpath, summary_line)

    # ----- Pass 1: targeted rewrites -----
    for rel, updates in REWRITES.items():
        path = ROOT / rel
        if not path.is_file():
            print(f"  ⚠️  skipped (not found): {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        new_text = update_frontmatter(text, updates)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            for k in updates:
                changes.append((rel, f"set {k}"))

    # ----- Pass 2: strip redundant brand suffixes from metaTitle -----
    stripped = 0
    for md in CONTENT.rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="ignore")
        title = get_frontmatter_field(text, "metaTitle")
        if not title:
            continue
        new_title = strip_redundant_suffix(title)
        if new_title != title:
            rel = str(md.relative_to(ROOT))
            new_text = update_frontmatter(text, {"metaTitle": new_title})
            if new_text != text:
                md.write_text(new_text, encoding="utf-8")
                changes.append((rel, f'strip brand suffix → "{new_title}" ({len(new_title)} chars)'))
                stripped += 1

    if not changes:
        print("No changes to apply.")
        return

    print(f"Applied {len(changes)} edits across {len({c[0] for c in changes})} files.\n")
    for rel, summary in changes:
        print(f"  · {rel}")
        print(f"      {summary}")
    print(f"\nBrand-suffix strips: {stripped}")
    print("Re-run scripts/audit-seo-meta.py to verify.")


if __name__ == "__main__":
    main()
