#!/usr/bin/env python3
"""
Add first-occurrence glossary links to every blog post.
Rules:
  - Each glossary slug linked at most once per file (first match wins)
  - Longer/more specific terms processed before substrings
  - Never links inside existing markdown links, code spans, code blocks, or bare URLs
"""
import re
import os

BLOGS_DIR = "/Users/omarsheriff/Desktop/piperocket-site/content/blogs"
BASE_URL = "/glossary/"

# (term, slug, case_sensitive)
# Ordered longest-first so compound terms claim their positions before substrings
GLOSSARY_MAP = [
    ("retrieval-augmented generation", "what-is-rag", False),
    ("retrieval augmented generation", "what-is-rag", False),
    ("account-based marketing",        "what-is-abm", False),
    ("account based marketing",        "what-is-abm", False),
    ("cumulative layout shift",        "what-is-cls", False),
    ("programmatic advertising",       "what-is-programmatic-advertising", False),
    ("user-generated content",         "what-is-user-generated-content", False),
    ("user generated content",         "what-is-user-generated-content", False),
    ("go-to-market strategy",          "what-is-go-to-market-strategy", False),
    ("go to market strategy",          "what-is-go-to-market-strategy", False),
    ("customer lifetime value",        "what-is-clv", False),
    ("annual recurring revenue",       "what-is-arr", False),
    ("net revenue retention",          "what-is-nrr", False),
    ("cost per acquisition",           "what-is-cpa", False),
    ("search engine marketing",        "what-is-sem", False),
    ("total addressable market",       "what-is-tam-sam-som", False),
    ("prompt engineering",             "what-is-prompt-engineering", False),
    ("performance marketing",          "what-is-performance-marketing", False),
    ("thought leadership",             "what-is-thought-leadership", False),
    ("inbound marketing",              "what-is-inbound-marketing", False),
    ("content marketing",              "what-is-content-marketing", False),
    ("keyword research",               "what-is-keyword-research", False),
    ("keyword clusters",               "keyword-clusters", False),
    ("keyword cluster",                "keyword-clusters", False),
    ("employer branding",              "what-is-employer-branding", False),
    ("brand positioning",              "what-is-brand-positioning", False),
    ("lead generation",                "what-is-lead-generation", False),
    ("brand identity",                 "what-is-brand-identity", False),
    ("evergreen content",              "what-is-evergreen-content", False),
    ("long-tail keywords",             "what-is-a-long-tail-keyword", False),
    ("long-tail keyword",              "what-is-a-long-tail-keyword", False),
    ("long tail keywords",             "what-is-a-long-tail-keyword", False),
    ("long tail keyword",              "what-is-a-long-tail-keyword", False),
    ("domain authority",               "what-is-domain-authority", False),
    ("structured data",                "what-is-structured-data", False),
    ("conversion rate",                "what-is-conversion-rate", False),
    ("schema markup",                  "what-is-schema-markup", False),
    ("anchor text",                    "what-is-anchor-text", False),
    ("meta descriptions",              "what-is-a-meta-description", False),
    ("meta description",               "what-is-a-meta-description", False),
    ("canonical tags",                 "what-is-a-canonical-tag", False),
    ("canonical tag",                  "what-is-a-canonical-tag", False),
    ("image alt text",                 "what-is-image-alt-text", False),
    ("alt text",                       "what-is-image-alt-text", False),
    ("technical SEO",                  "what-is-technical-seo", False),
    ("on-page SEO",                    "what-is-on-page-seo", False),
    ("off-page SEO",                   "what-is-off-page-seo", False),
    ("on page SEO",                    "what-is-on-page-seo", False),
    ("off page SEO",                   "what-is-off-page-seo", False),
    ("AI hallucinations",              "what-is-ai-hallucination", False),
    ("AI hallucination",               "what-is-ai-hallucination", False),
    ("third-party cookies",            "what-is-third-party-cookies", False),
    ("third party cookies",            "what-is-third-party-cookies", False),
    ("SEO audit",                      "what-is-an-seo-audit", False),
    ("TAM SAM SOM",                    "what-is-tam-sam-som", True),
    ("robots.txt",                     "what-is-robots-txt", False),
    ("Google Search Console",          "what-is-google-search-console", True),
    ("Google Tag Manager",             "what-is-google-tag-manager", True),
    ("301 redirects",                  "what-is-a-301-redirect", False),
    ("301 redirect",                   "what-is-a-301-redirect", False),
    ("backlinks",                      "what-is-a-backlink", False),
    ("backlink",                       "what-is-a-backlink", False),
    ("Meta Ads",                       "what-is-meta-ads", True),
    ("Google Ads",                     "what-is-google-ads", True),
    ("SSL certificates",               "what-is-ssl-certificate", False),
    ("SSL certificate",                "what-is-ssl-certificate", False),
    ("click-through rate",             "what-is-ctr", False),
    ("cost-per-click",                 "what-is-cost-per-click", False),
    ("cost per click",                 "what-is-cost-per-click", False),
    ("return on ad spend",             "what-is-roas", False),
    ("pay-per-click",                  "what-is-ppc", False),
    ("buyer personas",                 "buyer-persona", False),
    ("buyer persona",                  "buyer-persona", False),
    ("upselling",                      "what-is-upsell", False),
    ("upsell",                         "what-is-upsell", False),
    # Acronyms — case-sensitive, word-boundary matched
    ("SERPs",   "what-is-serp",            True),
    ("SERP",    "what-is-serp",            True),
    ("ROAS",    "what-is-roas",            True),
    ("CTR",     "what-is-ctr",             True),
    ("CPC",     "what-is-cost-per-click",  True),
    ("CPM",     "what-is-cpm",             True),
    ("CPA",     "what-is-cpa",             True),
    ("CLV",     "what-is-clv",             True),
    ("ARR",     "what-is-arr",             True),
    ("NRR",     "what-is-nrr",             True),
    ("MQLs",    "mql",                     True),
    ("MQL",     "mql",                     True),
    ("ICP",     "what-is-icp",             True),
    ("ABM",     "what-is-abm",             True),
    ("SEM",     "what-is-sem",             True),
    ("LLMs",    "what-is-an-llm",          True),
    ("LLM",     "what-is-an-llm",          True),
    ("GPT",     "what-is-gpt",             True),
    ("RAG",     "what-is-rag",             True),
    ("SSP",     "what-is-ssp",             True),
    ("GA4",     "what-is-ga4",             True),
    ("CLS",     "what-is-cls",             True),
    ("FID",     "what-is-fid",             True),
    ("SAL",     "what-is-sal-in-saas",     True),
    # Broad single terms last
    ("SEO", "what-is-seo", True),
    ("PPC", "what-is-ppc", True),
]


def get_protected_spans(body):
    protected = []
    # Heading lines — never link inside ## / ### headings
    for m in re.finditer(r'^#{1,6}\s.*$', body, re.MULTILINE):
        protected.append((m.start(), m.end()))
    # Existing markdown links and images: [text](url) / ![alt](src)
    for m in re.finditer(r'!?\[([^\]]*)\]\([^\)]*\)', body):
        protected.append((m.start(), m.end()))
    # Reference-style links: [text][ref]
    for m in re.finditer(r'\[[^\]]*\]\[[^\]]*\]', body):
        protected.append((m.start(), m.end()))
    # Inline code: `...`
    for m in re.finditer(r'`[^`\n]+`', body):
        protected.append((m.start(), m.end()))
    # Fenced code blocks: ```...```
    for m in re.finditer(r'```[\s\S]*?```', body):
        protected.append((m.start(), m.end()))
    # Bare URLs
    for m in re.finditer(r'https?://[^\s\)\]>]+', body):
        protected.append((m.start(), m.end()))
    # HTML tags
    for m in re.finditer(r'<[^>]+>', body):
        protected.append((m.start(), m.end()))
    return protected


def overlaps(s1, e1, spans):
    return any(s1 < pe and e1 > ps for ps, pe in spans)


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---', 2)
    if len(parts) < 3:
        return content, []

    frontmatter = parts[0] + '---' + parts[1] + '---'
    body = parts[2]

    protected = get_protected_spans(body)
    claimed = []
    linked_slugs = set()
    replacements = []  # (start, end, replacement, term, slug)

    for term, slug, case_sensitive in GLOSSARY_MAP:
        if slug in linked_slugs:
            continue

        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = r'\b' + re.escape(term) + r'\b'

        for m in re.finditer(pattern, body, flags):
            s, e = m.start(), m.end()
            if overlaps(s, e, protected) or overlaps(s, e, claimed):
                continue
            # Found the first valid occurrence
            original = m.group()
            replacement = f'[{original}]({BASE_URL}{slug}/)'
            replacements.append((s, e, replacement, term, slug))
            claimed.append((s, e))
            linked_slugs.add(slug)
            break

    if not replacements:
        return content, []

    # Apply right-to-left so earlier positions stay valid
    replacements.sort(key=lambda x: x[0], reverse=True)
    chars = list(body)
    log_entries = []
    for s, e, repl, term, slug in replacements:
        chars[s:e] = list(repl)
        log_entries.append((term, slug))

    new_content = frontmatter + ''.join(chars)
    return new_content, log_entries


def main():
    total_files = 0
    total_links = 0
    log_lines = []

    files = sorted(
        f for f in os.listdir(BLOGS_DIR)
        if f.endswith('.md') and f != '_index.md'
    )

    for filename in files:
        filepath = os.path.join(BLOGS_DIR, filename)
        new_content, log_entries = process_file(filepath)

        if log_entries:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            total_files += 1
            total_links += len(log_entries)
            log_lines.append(f"\n{filename}  ({len(log_entries)} links)")
            for term, slug in sorted(log_entries, key=lambda x: x[0].lower()):
                log_lines.append(f"  [{term}]  →  /glossary/{slug}/")

    print("=" * 65)
    print("GLOSSARY INTERNAL LINKING — CHANGE LOG")
    print("=" * 65)
    print("".join(log_lines))
    print()
    print("=" * 65)
    print(f"TOTAL: {total_links} links added across {total_files} blog files")
    print("=" * 65)


if __name__ == "__main__":
    main()
