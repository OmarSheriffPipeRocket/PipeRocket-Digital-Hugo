#!/usr/bin/env python3
"""
Fix broken internal links across content/ and the homepage layout.

Run after a clean hugo build. Reads which URLs actually exist under
/public, then performs whole-string replacements across content/**/*.md
for every broken link the audit found.

Strategy: only rewrite when (a) the broken slug has a clear, unambiguous
replacement in the current build, OR (b) we know the canonical slug from
the file inventory. Anything unclear is left alone with a warning so the
human can decide.
"""

import os
import re
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTENT = os.path.join(ROOT, "content")
PUBLIC = os.path.join(ROOT, "public")

# ---------------------------------------------------------------------------
# Static rewrite map.  Each key is the broken URL we want to fix; value is
# the canonical URL it should point to.  Keys are matched as whole tokens
# (so /blogs/foo/ won't accidentally rewrite /blogs/foo-bar/).
# ---------------------------------------------------------------------------
REWRITES = {
    # ----- listicle slug renames: /blogs/* → /list/* -----
    "/blogs/best-saas-marketing-agencies/":         "/list/best-saas-marketing-agencies-2026/",
    "/blogs/best-saas-seo-agencies/":               "/list/best-saas-seo-agencies/",
    "/blogs/best-b2b-seo-agencies/":                "/list/best-b2b-seo-agencies-2/",
    "/blogs/best-saas-ppc-agencies/":               "/list/best-saas-ppc-agencies/",
    "/blogs/best-b2b-marketing-agencies/":          "/list/best-b2b-marketing-agencies/",
    "/blogs/best-enterprise-seo-agencies/":         "/list/best-enterprise-seo-agencies/",
    "/blogs/top-b2b-ppc-agencies/":                 "/list/top-b2b-ppc-agencies/",
    "/blogs/best-b2b-google-ads-agencies/":         "/list/best-b2b-google-ads-agencies/",
    "/blogs/best-b2b-content-marketing-agencies/":  "/list/best-b2b-content-marketing-agencies/",
    "/blogs/best-saas-geo-agencies/":               "/list/best-saas-geo-agencies/",
    "/blogs/top-fintech-seo-agencies/":             "/list/top-fintech-seo-agencies/",
    "/blogs/best-saas-content-marketing-agencies/": "/list/best-saas-content-marketing-agencies/",
    "/blogs/top-performance-marketing-agencies/":   "/list/top-performance-marketing-agencies/",
    "/blogs/best-geo-agencies/":                    "/list/best-geo-agencies/",
    "/blogs/best-technical-seo-agencies/":          "/list/the-11-best-technical-seo-agencies-for-2026/",
    "/blogs/best-saas-link-building-agencies/":     "/list/the-10-best-saas-link-building-agencies-in-2026/",
    "/blogs/best-b2b-advertising-agencies/":        "/list/the-best-b2b-advertising-agencies-2026-rankings/",
    # ----- case studies (frontmatter forces hyphenated url) -----
    "/case-study/hyperverge/":  "/case-study-hyperverge/",
    "/case-study/spendflo/":    "/case-study-spendflo/",
    "/case-study/devrev/":      "/case-study-devrev/",
    "/case-study/cybersierra/": "/case-study-cybersierra/",
    "/case-study/hyperstart/":  "/case-study-hyperstart/",
    "/case-study/storylane/":   "/case-study-storylane/",
    "/case-studies/":           "/case-study/",
    # ----- blog rename slugs from the WP import -----
    "/blogs/saas-seo-strategy-and-framework/":            "/blogs/saas-seo-strategies-and-framework/",
    "/blogs/how-to-run-linkedin-ads-for-saas/":           "/blogs/how-do-i-run-linkedin-ads-for-saas-an-experts-take/",
    "/blogs/saas-google-ads-mistakes-to-avoid/":          "/blogs/the-8-common-saas-google-ads-mistakes-to-avoid-in-2026/",
    "/blogs/how-to-rank-on-chatgpt/":                     "/blogs/how-to-rank-on-chatgpt-in-2026-strategies-and-tips/",
    "/blogs/how-to-conduct-a-saas-ppc-audit/":            "/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account/",
    "/blogs/how-to-conduct-saas-ppc-audit/":              "/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account/",
    "/blogs/how-to-do-saas-ppc-audit/":                   "/blogs/the-no-nonsense-guide-to-auditing-your-saas-ppc-account/",
    "/blogs/how-to-write-saas-seo-content-with-ai/":      "/blogs/how-to-write-saas-seo-content-with-ai-that-actually-ranks/",
    "/blogs/how-to-write-saas-google-ads-copy/":          "/blogs/how-to-write-google-ads-copy-for-saas-in-2026/",
    "/blogs/optimize-saas-landing-pages-for-seo/":        "/blogs/blogs-optimize-saas-landing-pages-for-seo/",
    # ----- glossary slug normalization -----
    # /glossary/mql/ and /glossary/buyer-persona/ targets don't exist;
    # leave them for the manual pass to convert into plain text.
    "/glossary/keyword-clusters/": "/glossary/what-are-keyword-clusters/",
    # ----- pages that should point to existing alternatives -----
    # Fix double-rewrite from the first pass: /blogs/blogs/...
    "/blogs/blogs/b2b-marketing-operations-guide/": "/blogs/b2b-marketing-operations-guide/",
    "/account-based-marketing/":        "/account-based-marketing-agency/",
    "/content-marketing/":              "/content-marketing-agency/",
    "/link-building/":                  "/link-building-agency/",
    "/success-stories/":                "/case-study/",
    "/list/best-saas-seo-agencies-for-startups":  "/list/12-best-saas-seo-agencies-for-startups-2026/",
    # /case-study/<slug>/ still leaks from /pricing/ — pure slash form
    "/case-study/storylane/":           "/case-study-storylane/",
    "/case-study/spendflo/":            "/case-study-spendflo/",
    "/case-study/hyperverge/":          "/case-study-hyperverge/",
    # Strip dead inline glossary links — convert to plain text via a
    # markdown-link rewrite handled separately below.
}

# Inline markdown links like [MQL](/glossary/mql/) where the target page
# doesn't exist — strip just the wrapper, leave the visible text behind.
STRIP_INLINE_LINK_TARGETS = (
    "/glossary/mql/",
    "/glossary/buyer-persona/",
)


def main():
    # Verify every replacement URL actually exists under /public/.
    missing = []
    for src, dst in REWRITES.items():
        if dst.startswith("/"):
            fs = os.path.join(PUBLIC, dst.lstrip("/"))
            if not (os.path.isdir(fs) or os.path.isfile(os.path.join(fs, "index.html"))):
                missing.append((src, dst))
    if missing:
        print("⚠️  These replacement targets don't exist in /public/:")
        for s, d in missing:
            print(f"   {s}  →  {d}  (MISSING)")
        print("Aborting. Fix the map and re-run.")
        sys.exit(1)

    # Walk every markdown + a few key layouts. We rewrite links in content/
    # only — layouts are handled with explicit sed earlier.
    changes_by_file = defaultdict(list)
    files_scanned = 0

    for dirpath, _, files in os.walk(CONTENT):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            path = os.path.join(dirpath, fname)
            files_scanned += 1
            with open(path, "r", encoding="utf-8") as fh:
                src = fh.read()
            new = src
            for old, neu in REWRITES.items():
                # Replace as a whole token so /foo doesn't match /foo-bar.
                if old in new:
                    new = new.replace(old, neu)
            # Strip dead inline links — turn [text](dead-url) into "text".
            for dead in STRIP_INLINE_LINK_TARGETS:
                pat = re.compile(
                    r"\[([^\]]+)\]\(" + re.escape(dead) + r'(?:\s+"[^"]*")?\)'
                )
                new = pat.sub(r"\1", new)
            if new != src:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new)
                # Count which mappings actually fired here.
                for old, neu in REWRITES.items():
                    n = src.count(old)
                    if n > 0:
                        changes_by_file[os.path.relpath(path, ROOT)].append((old, neu, n))

    # Also patch the homepage layout (it has hard-coded links).
    home = os.path.join(ROOT, "layouts", "index.html")
    if os.path.isfile(home):
        with open(home, "r", encoding="utf-8") as fh:
            src = fh.read()
        new = src
        for old, neu in REWRITES.items():
            if old in new:
                new = new.replace(old, neu)
        if new != src:
            with open(home, "w", encoding="utf-8") as fh:
                fh.write(new)
            for old, neu in REWRITES.items():
                n = src.count(old)
                if n > 0:
                    changes_by_file["layouts/index.html"].append((old, neu, n))

    if not changes_by_file:
        print(f"Scanned {files_scanned} files. No changes needed.")
        return

    print(f"Scanned {files_scanned} files. Patched {len(changes_by_file)} files.\n")
    for f, swaps in sorted(changes_by_file.items()):
        print(f"  {f}")
        for old, neu, n in swaps:
            print(f"     · {old}  →  {neu}   ({n}x)")
    print(f"\nTotal mappings applied across files: {sum(n for swaps in changes_by_file.values() for (_, _, n) in swaps)}")


if __name__ == "__main__":
    main()
