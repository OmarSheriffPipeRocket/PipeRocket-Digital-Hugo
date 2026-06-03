#!/usr/bin/env python3
"""
Generate static/_redirects for the WP → Hugo cutover.

Strategy
--------
1. Walk every public/**/index.html and learn the canonical Hugo permalink.
2. For each, peek at the underlying content file's `wp_link:` frontmatter
   (the page's URL on the old WordPress site).
3. If wp_link != hugo permalink, emit a 301 from wp_link → permalink.
4. Bolt on a curated list of:
     a) WordPress system paths to block (/wp-admin/, /wp-json/, etc.)
     b) Old slug renames we already know about from the link-fix script
        (e.g. /blogs/saas-seo-strategy-and-framework/ → /blogs/saas-seo-strategies-and-framework/)
     c) Trailing-slash + case redirects
5. Write to static/_redirects so Netlify picks it up at build time.

The output is sorted: more-specific rules first, splats last (Netlify
processes top-to-bottom and stops at the first match).
"""

import os
import re
import sys
from pathlib import Path
from collections import OrderedDict

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
PUBLIC = ROOT / "public"
OUT = ROOT / "static" / "_redirects"

# -----------------------------------------------------------------------------
# Curated rules — applied first, before per-page wp_link redirects.
# -----------------------------------------------------------------------------

# Manual slug-rename map (subset of fix-broken-internal-links.py REWRITES,
# limited to entries the live WP site historically served that aren't
# captured by wp_link frontmatter).
MANUAL_SLUG_REDIRECTS = OrderedDict([
    # Blog renames
    ("/blogs/saas-seo-strategy-and-framework/",        "/blogs/saas-seo-strategies-and-framework/"),
    ("/blogs/how-to-rank-on-chatgpt/",                  "/blogs/how-to-rank-on-chatgpt-in-2026-strategies-and-tips/"),
    ("/blogs/how-to-run-linkedin-ads-for-saas/",        "/blogs/how-do-i-run-linkedin-ads-for-saas-an-experts-take/"),
    ("/blogs/saas-google-ads-mistakes-to-avoid/",       "/blogs/the-8-common-saas-google-ads-mistakes-to-avoid-in-2026/"),
    ("/blogs/how-to-conduct-a-saas-ppc-audit/",         "/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account/"),
    ("/blogs/how-to-conduct-saas-ppc-audit/",           "/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account/"),
    ("/blogs/how-to-do-saas-ppc-audit/",                "/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account/"),
    ("/blogs/how-to-write-saas-seo-content-with-ai/",   "/blogs/how-to-write-saas-seo-content-with-ai-that-actually-ranks/"),
    ("/blogs/how-to-write-saas-google-ads-copy/",       "/blogs/how-to-write-google-ads-copy-for-saas-in-2026/"),
    ("/blogs/optimize-saas-landing-pages-for-seo/",     "/blogs/blogs-optimize-saas-landing-pages-for-seo/"),
    # Glossary slug normalization
    ("/glossary/mql/",                                  "/glossary/"),
    ("/glossary/buyer-persona/",                        "/glossary/"),
    ("/glossary/keyword-clusters/",                     "/glossary/what-are-keyword-clusters/"),
    # /blogs/best-*-agencies/ → /list/*
    ("/blogs/best-saas-marketing-agencies/",            "/list/best-saas-marketing-agencies-2026/"),
    ("/blogs/best-saas-seo-agencies/",                  "/list/best-saas-seo-agencies/"),
    ("/blogs/best-b2b-seo-agencies/",                   "/list/best-b2b-seo-agencies-2/"),
    ("/blogs/best-saas-ppc-agencies/",                  "/list/best-saas-ppc-agencies/"),
    ("/blogs/best-b2b-marketing-agencies/",             "/list/best-b2b-marketing-agencies/"),
    ("/blogs/best-enterprise-seo-agencies/",            "/list/best-enterprise-seo-agencies/"),
    ("/blogs/top-b2b-ppc-agencies/",                    "/list/top-b2b-ppc-agencies/"),
    ("/blogs/best-b2b-google-ads-agencies/",            "/list/best-b2b-google-ads-agencies/"),
    ("/blogs/best-b2b-content-marketing-agencies/",     "/list/best-b2b-content-marketing-agencies/"),
    ("/blogs/best-saas-geo-agencies/",                  "/list/best-saas-geo-agencies/"),
    ("/blogs/top-fintech-seo-agencies/",                "/list/top-fintech-seo-agencies/"),
    ("/blogs/best-saas-content-marketing-agencies/",    "/list/best-saas-content-marketing-agencies/"),
    ("/blogs/top-performance-marketing-agencies/",      "/list/top-performance-marketing-agencies/"),
    ("/blogs/best-geo-agencies/",                       "/list/best-geo-agencies/"),
    ("/blogs/best-technical-seo-agencies/",             "/list/the-11-best-technical-seo-agencies-for-2026/"),
    ("/blogs/best-saas-link-building-agencies/",        "/list/the-10-best-saas-link-building-agencies-in-2026/"),
    ("/blogs/best-b2b-advertising-agencies/",           "/list/the-best-b2b-advertising-agencies-2026-rankings/"),
    # Section aliases that humans / external sites sometimes link
    ("/case-studies/*",                                 "/case-study/:splat"),
    ("/success-stories/*",                              "/case-study/:splat"),
    ("/articles/*",                                     "/blogs/:splat"),
    # Service-page rename — AEO/GEO agency repositioned as AI SEO services (2026-06)
    ("/aeo-geo-agency/",                                "/ai-seo-services/"),
    # Service-page aliases (old shorter URLs without -agency suffix)
    ("/account-based-marketing/",                       "/account-based-marketing-agency/"),
    ("/content-marketing/",                             "/content-marketing-agency/"),
    ("/link-building/",                                 "/link-building-agency/"),
    ("/fintech-seo/",                                   "/fintech-seo-agency/"),
    # Old /blog/<slug>/ WordPress URLs (singular path) — Hugo serves /blogs/ now
    ("/blog/b2b-buyers-journey/",                       "/blogs/"),
    ("/blog/b2b-seo/",                                  "/list/best-b2b-seo-agencies/"),
    ("/blog/best-b2b-demand-generation-agencies/",      "/list/"),
    ("/blog/best-b2b-google-ads-agencies/",             "/list/best-b2b-google-ads-agencies/"),
    ("/blog/best-b2b-lead-generation-agencies/",        "/list/best-b2b-lead-generation-companies/"),
    ("/blog/best-b2b-linkedin-ads-agencies/",           "/list/best-linkedin-marketing-agencies/"),
    ("/blog/best-b2b-marketing-agencies/",              "/list/best-b2b-marketing-agencies/"),
    ("/blog/best-b2b-ppc-agencies/",                    "/list/top-b2b-ppc-agencies/"),
    ("/blog/best-b2b-saas-seo-agencies/",               "/list/best-saas-seo-agencies/"),
    ("/blog/best-b2b-seo-agencies/",                    "/list/best-b2b-seo-agencies/"),
    ("/blog/best-b2b-social-media-marketing-agencies/", "/list/"),
    ("/blog/best-enterprise-seo-agencies/",             "/list/best-enterprise-seo-agencies/"),
    ("/blog/best-linkedin-marketing-agencies/",         "/list/best-linkedin-marketing-agencies/"),
    ("/blog/best-performance-marketing-agencies/",      "/list/top-performance-marketing-agencies/"),
    ("/blog/best-saas-demand-generation-agencies/",     "/list/"),
    ("/blog/best-saas-link-building-agency/",           "/list/the-10-best-saas-link-building-agencies-in-2026/"),
    ("/blog/best-saas-marketing-agencies/",             "/list/best-saas-marketing-agencies-2026/"),
    ("/blog/best-technical-seo-agencies/",              "/list/the-11-best-technical-seo-agencies-for-2026/"),
    ("/blog/choose-best-saas-seo-agency-saas-companies/", "/saas-seo-agency/"),
    ("/blog/enterprise-seo-guide/",                     "/blogs/enterprise-seo-guide/"),
    ("/blog/saas-marketing-companies-challenges/",      "/blogs/saas-marketing-challenges-and-fixes/"),
    ("/blog/saas-seo/",                                 "/saas-seo-agency/"),
    ("/blog/saas-seo-services/",                        "/saas-seo-agency/"),
    ("/blog/seo-for-saas-companies/",                   "/saas-seo-agency/"),
    ("/blog/the-complete-guide-to-b2b-seo-for-2025/",   "/list/best-b2b-seo-agencies/"),
    # Old /seo/<slug>/ pattern (predecessor of /list/)
    ("/seo/best-b2b-demand-generation-agencies/",       "/list/"),
    ("/seo/best-b2b-google-ads-agencies/",              "/list/best-b2b-google-ads-agencies/"),
    ("/seo/best-b2b-linkedin-ads-agencies/",            "/list/best-linkedin-marketing-agencies/"),
    ("/seo/best-b2b-marketing-agencies/",               "/list/best-b2b-marketing-agencies/"),
    ("/seo/best-b2b-ppc-agencies/",                     "/list/top-b2b-ppc-agencies/"),
    ("/seo/best-enterprise-seo-agencies/",              "/list/best-enterprise-seo-agencies/"),
    ("/seo/best-linkedin-marketing-agencies/",          "/list/best-linkedin-marketing-agencies/"),
    ("/seo/best-performance-marketing-agencies/",       "/list/top-performance-marketing-agencies/"),
    ("/seo/best-saas-demand-generation-agencies/",      "/list/"),
    ("/seo/best-saas-link-building-agency/",            "/list/the-10-best-saas-link-building-agencies-in-2026/"),
    ("/seo/best-saas-marketing-agencies/",              "/list/best-saas-marketing-agencies-2026/"),
    ("/seo/best-technical-seo-agencies/",               "/list/the-11-best-technical-seo-agencies-for-2026/"),
    ("/seo/enterprise-seo-guide/",                      "/blogs/enterprise-seo-guide/"),
    ("/seo/saas-seo/",                                  "/saas-seo-agency/"),
    # Old single-section service path
    ("/b2b-seo/best-b2b-seo-agencies/",                 "/list/best-b2b-seo-agencies/"),
    # One-off legacy URLs
    ("/SaaS-SEO/",                                      "/saas-seo-agency/"),
    ("/mark-ops/",                                      "/marketing-ops/"),
    ("/programmetic-seo/",                              "/"),
    # Duplicate cornerstone consolidated into canonical /list/best-saas-seo-agencies/
    # (Red Flags + lastmod refresh merged 2026-05-26)
    ("/list/best-saas-seo-agencies-2/",                 "/list/best-saas-seo-agencies/"),
    # Author slug mismatches — data-file key differs from canonical URL slug
    # (templates fall back to /author/<key>/ when GetPage fails; redirect to the
    # real URL so the click works instead of 404'ing)
    ("/author/kim/",                                    "/author/kamaraj-mathiarasan/"),
    ("/author/praveen/",                                "/author/praveen-ravi/"),
    # PSEO acronym alias — redirect /pseo-agency/ to the full-keyword canonical
    ("/pseo-agency/",                                   "/programmatic-seo-agency/"),
    ("/pseo/",                                          "/programmatic-seo-agency/"),
    ("/programmatic-seo/",                              "/programmatic-seo-agency/"),
])

# WordPress system paths to permanently kill.
WP_KILL_PATHS = [
    ("/wp-admin/*",        "/", 410),
    ("/wp-admin",          "/", 410),
    ("/wp-login.php",      "/", 410),
    ("/wp-content/uploads/*",  "/images/:splat", 301),  # legacy image URLs
    ("/wp-content/*",      "/", 410),
    ("/wp-json/*",         "/", 410),
    ("/wp-json",           "/", 410),
    ("/feed/*",            "/", 410),
    ("/feed",              "/", 410),
    ("/comments/feed/*",   "/", 410),
    ("/xmlrpc.php",        "/", 410),
    ("/category/*",        "/blogs/", 301),
    ("/blog/category/*",   "/blogs/", 301),
    ("/tag/*",             "/blogs/", 301),
    # NOTE: do NOT blanket-redirect /author/* — Hugo serves real author
    # pages at /author/<slug>/ now. Use specific redirects below for the
    # known slug mismatches where the data-file key differs from the
    # canonical URL slug.
    ("/?p=*",              "/", 301),  # legacy /?p=123 permalinks
    ("/?page_id=*",        "/", 301),
    ("/sitemap_index.xml", "/sitemap.xml", 301),
    ("/sitemap-*.xml",     "/sitemap.xml", 301),
]

# Decommissioned URL patterns — kept here so the script is the single
# source of truth and re-running it doesn't wipe these out.
#
# • Thin auto-generated FAQ pages were pruned; redirect to the curated
#   /faqs/ hub so any inbound link equity flows somewhere useful.
# • Programmatic /saas-seo-agency/<city|state>/ pages were removed for
#   the same thin-content reason; collapse to the parent service page.
# • A handful of one-off WP URLs that no longer have a Hugo equivalent.
#
# Catch-alls go last so more specific curated rules above always win.
DECOMMISSIONED_PATHS = [
    # Curated section-level redirects (preserve link equity)
    ("/blog/",                          "/blogs/", 301),
    ("/gtm-lp/",                        "/",       301),
    ("/saas-seo/",                      "/saas-seo-agency/", 301),
    ("/us/b2b-seo-agency-california/",  "/saas-seo-agency/", 301),
    ("/webinar/",                       "/",       301),
    # Permanently gone — empty/decommissioned, no replacement
    ("/locations.kml",                  "/",       410),
    ("/manage-subscriptions/",          "/",       410),
    ("/webinar-nivas/",                 "/",       410),
    # Thin auto-generated FAQ pages — 301 to curated FAQ hub
    ("/blogs/faqs/*",                   "/faqs/",  301),
    ("/faqs/*",                         "/faqs/",  301),
    # Programmatic city/state SEO pages — collapse to parent service page.
    # Listed as a catch-all; legitimate sub-paths (/saas-seo-agency/faqs/,
    # /saas-seo-agency/faqs1) have specific rules earlier or live as
    # static files which take precedence over non-forced redirects.
    ("/saas-seo-agency/*",              "/saas-seo-agency/", 301),
]


def parse_frontmatter(path):
    """Return (wp_link, url_override, slug_override) from frontmatter."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.match(r"^---\s*\n(.+?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None, None, None
    fm = m.group(1)
    wp = url = slug = None
    for line in fm.splitlines():
        if line.startswith("wp_link:"):
            wp = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("url:"):
            url = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("slug:"):
            slug = line.split(":", 1)[1].strip().strip('"').strip("'")
    return wp, url, slug


def canonical_url_for_content(path):
    """Compute the URL Hugo actually serves for a given content file.

    Precedence:
      1. Explicit `url:` override (Hugo respects it verbatim)
      2. `slug:` override → replace the last path segment
      3. Filename-derived default
    """
    fm_wp, fm_url, fm_slug = parse_frontmatter(path)
    if fm_url:
        if not fm_url.endswith("/") and "." not in fm_url.split("/")[-1]:
            fm_url += "/"
        # Strip trailing duplicate slash a few files have (e.g. ".../")
        fm_url = re.sub(r"/+$", "/", fm_url)
        return fm_wp, fm_url
    rel = path.relative_to(CONTENT)
    parts = list(rel.parts)
    name = parts[-1]
    if name in ("_index.md", "index.md"):
        parts = parts[:-1]
    else:
        parts[-1] = name.removesuffix(".md")
    if fm_slug:
        # Replace the last segment with the slug
        if parts:
            parts[-1] = fm_slug
        else:
            parts = [fm_slug]
    derived = "/" + "/".join(parts) + "/"
    # Collapse any accidental double slash
    derived = re.sub(r"/+", "/", derived)
    return fm_wp, derived


def collect_live_urls():
    """Return the set of URL paths Hugo currently builds (with trailing /).
    Used to refuse any redirect whose source would shadow a real page."""
    live = set()
    if not PUBLIC.is_dir():
        return live
    for html in PUBLIC.rglob("index.html"):
        rel = html.relative_to(PUBLIC).parent
        url = "/" + str(rel).replace(os.sep, "/")
        if url == "/.":
            url = "/"
        if not url.endswith("/"):
            url += "/"
        live.add(url)
    return live


def main():
    if not CONTENT.is_dir():
        sys.exit(f"content/ not found at {CONTENT}")

    live_urls = collect_live_urls()
    print(f"Live URL set has {len(live_urls)} entries (built from /public/)")

    auto_redirects = OrderedDict()
    skipped_same = 0
    skipped_shadow = 0   # source URL is itself a live page — would shadow it

    for md in sorted(CONTENT.rglob("*.md")):
        wp, canonical = canonical_url_for_content(md)
        if not wp:
            continue
        # Normalise trailing slashes for comparison
        wp_norm = wp if wp.endswith("/") or "." in wp.split("/")[-1] else wp + "/"
        if wp_norm == canonical:
            skipped_same += 1
            continue
        if wp in MANUAL_SLUG_REDIRECTS or wp_norm in MANUAL_SLUG_REDIRECTS:
            continue
        # Refuse to redirect FROM a URL that's already a live page.
        if wp_norm in live_urls:
            skipped_shadow += 1
            print(f"  ⚠️  skipped (would shadow live page): {wp} → {canonical}")
            continue
        auto_redirects[wp] = canonical

    # ----- Build output -----
    lines = []
    lines.append("# ─── PipeRocket Digital — Netlify _redirects ───────────────────────────")
    lines.append("# Auto-generated by scripts/generate-redirects.py. Re-run after any URL")
    lines.append("# rename so this stays in sync with the actual Hugo permalinks.")
    lines.append("")
    lines.append("# ============================================================")
    lines.append("#  A. WordPress system paths — kill or hard-redirect")
    lines.append("# ============================================================")
    lines.append("")
    for src, dst, code in WP_KILL_PATHS:
        lines.append(f"{src:<40} {dst:<35} {code}")
    lines.append("")
    lines.append("# ============================================================")
    lines.append("#  B. Curated slug renames + section aliases")
    lines.append("# ============================================================")
    lines.append("")
    for src, dst in MANUAL_SLUG_REDIRECTS.items():
        lines.append(f"{src:<55} {dst:<55} 301")
    lines.append("")
    lines.append("# ============================================================")
    lines.append("#  C. Auto-generated per-page redirects (wp_link → permalink)")
    lines.append("# ============================================================")
    lines.append(f"#  {len(auto_redirects)} rules, generated from frontmatter")
    lines.append("")
    for src, dst in sorted(auto_redirects.items()):
        lines.append(f"{src:<60} {dst:<60} 301")
    lines.append("")
    lines.append("# ============================================================")
    lines.append("#  D. Decommissioned URLs (thin content + legacy WP paths)")
    lines.append("# ============================================================")
    lines.append("")
    for src, dst, code in DECOMMISSIONED_PATHS:
        lines.append(f"{src:<60} {dst:<60} {code}")
    lines.append("")
    lines.append("# ============================================================")
    lines.append("#  E. Final fallback — anything unmatched returns HTTP 404")
    lines.append("# ============================================================")
    lines.append("")
    lines.append(f"{'/*':<60} {'/404.html':<60} 404")

    out_text = "\n".join(lines) + "\n"
    OUT.write_text(out_text, encoding="utf-8")

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"  WordPress system rules:   {len(WP_KILL_PATHS)}")
    print(f"  Curated slug renames:     {len(MANUAL_SLUG_REDIRECTS)}")
    print(f"  Auto wp_link → permalink: {len(auto_redirects)}")
    print(f"  Decommissioned URLs:      {len(DECOMMISSIONED_PATHS)}")
    print(f"  (skipped {skipped_same} pages where wp_link == permalink)")
    print(f"  (skipped {skipped_shadow} pages where wp_link is a live URL)")
    print(f"  Total lines: {len(lines)}")


if __name__ == "__main__":
    main()
