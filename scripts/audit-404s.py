#!/usr/bin/env python3
"""
Site-wide 404 audit for the built PipeRocket Hugo site.

What it does
------------
1. Walks every *.html file under public/.
2. Extracts every <a href> link.
3. For internal links, resolves them against /public and checks whether
   the target page actually exists (either as an exact file or as
   <slug>/index.html).
4. Groups missing destinations and prints the source pages each broken
   link appeared on — so it's obvious which content files to edit.

External links (http://, https://, mailto:, tel:, #anchors) are skipped.
"""

import os
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urlsplit, urldefrag, unquote

ROOT = os.path.join(os.path.dirname(__file__), "..", "public")
ROOT = os.path.abspath(ROOT)
SITE_HOST = "piperocket.digital"

# Patterns we deliberately ignore (third-party, anchors, mail).
SKIP_PREFIXES = ("mailto:", "tel:", "javascript:", "data:", "#")


class Hrefs(HTMLParser):
    """Collect every (a-href, img-src) pair from the document."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v.strip())


def is_internal(url: str) -> bool:
    if not url:
        return False
    if url.startswith(SKIP_PREFIXES):
        return False
    s = urlsplit(url)
    if s.scheme and s.scheme not in ("http", "https"):
        return False
    if s.netloc and s.netloc.lower() not in ("", SITE_HOST):
        return False
    return True


def to_path(url: str) -> str:
    """Strip query/fragment + decode percent-escapes → URL path only."""
    s = urlsplit(url)
    path = s.path or ""
    path, _ = urldefrag(path)
    return unquote(path)


def exists_under_public(rel_url: str) -> bool:
    """True if the page or asset is rendered into /public."""
    if not rel_url or rel_url in ("/", ""):
        return True
    if not rel_url.startswith("/"):
        # relative URL — Hugo emits everything absolute, treat as broken
        # unless it's a same-page anchor (already filtered above)
        return False
    rel = rel_url.lstrip("/")
    fs = os.path.join(ROOT, rel)
    # Case 1: exact file (e.g. /sitemap.xml, /robots.txt, /images/foo.svg)
    if os.path.isfile(fs):
        return True
    # Case 2: pretty URL → fs/index.html
    if os.path.isfile(os.path.join(fs, "index.html")):
        return True
    # Case 3: pretty URL given without trailing slash
    if os.path.isfile(fs + ".html"):
        return True
    return False


def public_url_of(html_path: str) -> str:
    """Convert public/foo/index.html → /foo/"""
    rel = os.path.relpath(html_path, ROOT).replace(os.sep, "/")
    if rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    return "/" + rel.lstrip("/") if rel else "/"


def main():
    if not os.path.isdir(ROOT):
        sys.exit(f"public/ not found at {ROOT}. Run `hugo` first.")

    # missing_target_url -> list of (source_page_url, raw_href)
    broken = defaultdict(list)
    pages_scanned = 0
    links_checked = 0

    for dirpath, _dirs, files in os.walk(ROOT):
        for fname in files:
            if not fname.endswith(".html"):
                continue
            html_path = os.path.join(dirpath, fname)
            pages_scanned += 1
            with open(html_path, "r", encoding="utf-8", errors="replace") as fh:
                p = Hrefs()
                p.feed(fh.read())
            src_url = public_url_of(html_path)
            for h in p.hrefs:
                if not is_internal(h):
                    continue
                target = to_path(h)
                if target.startswith("//"):
                    continue
                if target == "":
                    continue
                links_checked += 1
                if not exists_under_public(target):
                    broken[target].append((src_url, h))

    print(f"Scanned {pages_scanned} pages · checked {links_checked} internal links.\n")
    if not broken:
        print("✅  Zero broken internal links.")
        return

    # Sort by number of source pages (most-broken first)
    items = sorted(broken.items(), key=lambda kv: -len(kv[1]))
    total_pages_with_breakage = len({src for _, refs in items for (src, _h) in refs})
    print(
        f"❌  {len(items)} unique broken destinations across "
        f"{total_pages_with_breakage} source pages.\n"
    )
    for target, refs in items:
        srcs = sorted({s for (s, _h) in refs})
        print(f"  ▸ {target}")
        print(f"      linked from {len(srcs)} page(s):")
        for s in srcs[:8]:
            print(f"        · {s}")
        if len(srcs) > 8:
            print(f"        … and {len(srcs) - 8} more")
        print()


if __name__ == "__main__":
    main()
