"""Audit internal-link structure for glossary entries.

For each /glossary/* page:
  - Count inbound internal links from other content (blogs, lists, glossary, service pages)
  - Count outbound internal links it makes
  - Flag orphans (0 inbound) and weakly-linked pages (<3 inbound)
  - Detect glossary entries missing from sitemap
"""

import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/omarsheriff/Desktop/piperocket-site")
CONTENT = ROOT / "content"
GLOSSARY_DIR = CONTENT / "glossary"
SITEMAP_URL = "https://piperocket.digital/glossary-sitemap.xml"

# Pattern: anything that looks like a glossary URL or link
GLOSSARY_LINK_RE = re.compile(r'/glossary/([a-z0-9\-]+)/?')
ANY_INTERNAL_LINK_RE = re.compile(r'(?:href=["\']|\]\()(?:https://piperocket\.digital)?(/[a-z0-9\-/]+)/?["\'\)]')


def slug_from_filename(p: Path) -> str:
    return p.stem


def main():
    # Step 1: collect all glossary slugs from filesystem
    glossary_files = sorted([f for f in GLOSSARY_DIR.iterdir() if f.suffix == ".md" and f.name != "_index.md"])
    glossary_slugs = {slug_from_filename(f) for f in glossary_files}
    print(f"Hugo source glossary entries: {len(glossary_slugs)}")

    # Step 2: sitemap slugs
    try:
        with urllib.request.urlopen(SITEMAP_URL, timeout=10) as r:
            sm = r.read().decode()
        sitemap_slugs = set(re.findall(r'/glossary/([a-z0-9\-]+)/', sm))
        sitemap_slugs.discard("")  # remove root
        print(f"Live sitemap glossary entries: {len(sitemap_slugs)}")

        missing_from_sitemap = glossary_slugs - sitemap_slugs - {""}
        extra_in_sitemap = sitemap_slugs - glossary_slugs - {""}
        print(f"\n--- In Hugo but NOT in live sitemap ({len(missing_from_sitemap)}) ---")
        for s in sorted(missing_from_sitemap):
            print(f"  /glossary/{s}/")
        print(f"\n--- In live sitemap but NOT in Hugo source ({len(extra_in_sitemap)}) ---")
        for s in sorted(extra_in_sitemap):
            print(f"  /glossary/{s}/")
    except Exception as e:
        print(f"Sitemap fetch failed: {e}")
        sitemap_slugs = set()

    # Step 3: scan ALL content for inbound links to each glossary slug
    inbound = defaultdict(list)  # slug -> [referrer paths]
    outbound = defaultdict(set)  # slug -> {target slugs}

    for md in CONTENT.rglob("*.md"):
        try:
            text = md.read_text(errors="ignore")
        except Exception:
            continue
        rel = md.relative_to(CONTENT)
        for m in GLOSSARY_LINK_RE.finditer(text):
            target = m.group(1)
            if target in glossary_slugs:
                if md.parent == GLOSSARY_DIR:
                    src_slug = slug_from_filename(md)
                    if src_slug != target:
                        outbound[src_slug].add(target)
                        inbound[target].append(f"glossary/{src_slug}")
                else:
                    inbound[target].append(str(rel))

    # Step 4: report
    print(f"\n\n=== INBOUND LINK COUNT PER GLOSSARY ENTRY ===")
    rows = []
    for slug in sorted(glossary_slugs):
        rows.append((slug, len(set(inbound[slug])), len(outbound[slug])))
    rows.sort(key=lambda r: (r[1], r[0]))

    print(f"\n{'slug':<55}{'inbound':>10}{'outbound':>10}")
    for slug, ib, ob in rows:
        print(f"{slug:<55}{ib:>10}{ob:>10}")

    orphans = [r for r in rows if r[1] == 0]
    weak = [r for r in rows if 0 < r[1] <= 2]
    print(f"\n\n=== ORPHANS (0 inbound) — {len(orphans)} ===")
    for slug, ib, ob in orphans:
        print(f"  /glossary/{slug}/")
    print(f"\n=== WEAK (1-2 inbound) — {len(weak)} ===")
    for slug, ib, ob in weak:
        print(f"  /glossary/{slug}/  (inbound={ib})")

    # Step 5: GSC-affected slugs — highlight
    affected = ["what-is-schema-markup", "what-is-a-301-redirect", "what-is-serp"]
    print(f"\n=== GSC-AFFECTED GLOSSARY ENTRIES ===")
    for slug in affected:
        ib = len(set(inbound.get(slug, [])))
        ob = len(outbound.get(slug, set()))
        refs = sorted(set(inbound.get(slug, [])))[:5]
        print(f"\n/glossary/{slug}/  inbound={ib}  outbound={ob}")
        for r in refs:
            print(f"   <- {r}")

    print(f"\n--- DONE ---")


if __name__ == "__main__":
    main()
