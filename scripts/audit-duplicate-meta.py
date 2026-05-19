#!/usr/bin/env python3
"""
Audit every built HTML file under /public/ for duplicate <head> tags
that should appear exactly once: <title>, <meta name="description">,
<link rel="canonical">, and the og:title / og:description / og:url /
twitter:title / twitter:description tags.
"""

import os
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

# Patterns that should appear AT MOST ONCE per page.
SHOULD_BE_UNIQUE = {
    "<title>":             re.compile(r"<title>[^<]*</title>", re.IGNORECASE),
    "meta description":    re.compile(r'<meta[^>]+name=["\']description["\']', re.IGNORECASE),
    "link canonical":      re.compile(r'<link[^>]+rel=["\']canonical["\']', re.IGNORECASE),
    "og:title":            re.compile(r'<meta[^>]+property=["\']og:title["\']', re.IGNORECASE),
    "og:description":      re.compile(r'<meta[^>]+property=["\']og:description["\']', re.IGNORECASE),
    "og:url":              re.compile(r'<meta[^>]+property=["\']og:url["\']', re.IGNORECASE),
    "og:image":            re.compile(r'<meta[^>]+property=["\']og:image["\']', re.IGNORECASE),
    "og:type":             re.compile(r'<meta[^>]+property=["\']og:type["\']', re.IGNORECASE),
    "twitter:title":       re.compile(r'<meta[^>]+name=["\']twitter:title["\']', re.IGNORECASE),
    "twitter:description": re.compile(r'<meta[^>]+name=["\']twitter:description["\']', re.IGNORECASE),
    "twitter:card":        re.compile(r'<meta[^>]+name=["\']twitter:card["\']', re.IGNORECASE),
    "meta robots":         re.compile(r'<meta[^>]+name=["\']robots["\']', re.IGNORECASE),
    "meta viewport":       re.compile(r'<meta[^>]+name=["\']viewport["\']', re.IGNORECASE),
}


def main():
    if not PUBLIC.is_dir():
        sys.exit("public/ not found — run `hugo` first")

    pages_scanned = 0
    # name -> list of (page, count)
    breach_examples = defaultdict(list)
    counter = Counter()

    for html in PUBLIC.rglob("*.html"):
        pages_scanned += 1
        text = html.read_text(encoding="utf-8", errors="ignore")
        # Only consider the <head> region so body-level mentions don't false-positive.
        head_match = re.search(r"<head[^>]*>(.*?)</head>", text, re.IGNORECASE | re.DOTALL)
        head = head_match.group(1) if head_match else text
        for label, regex in SHOULD_BE_UNIQUE.items():
            n = len(regex.findall(head))
            if n > 1:
                page_url = "/" + str(html.relative_to(PUBLIC)).replace(os.sep, "/")
                page_url = page_url[:-len("index.html")] if page_url.endswith("index.html") else page_url
                breach_examples[label].append((page_url, n))
                counter[label] += 1

    print(f"Scanned {pages_scanned} pages.\n")
    if not counter:
        print("✅  Every page has exactly one of each unique head tag.")
        return

    print(f"❌  {sum(counter.values())} pages have at least one duplicate head tag.\n")
    for label, pages in sorted(breach_examples.items(), key=lambda kv: -len(kv[1])):
        print(f"  ▸ Duplicate '{label}' on {len(pages)} page(s):")
        for p, n in pages[:6]:
            print(f"      · {p}  ({n}x)")
        if len(pages) > 6:
            print(f"      … and {len(pages) - 6} more")
        print()


if __name__ == "__main__":
    main()
