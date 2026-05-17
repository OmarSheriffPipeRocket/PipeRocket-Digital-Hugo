#!/usr/bin/env python3
"""Replace every standalone `![…](/images/agencies/<slug>-home.webp)`
markdown image line in content/list/*.md with a Hugo shortcode call:

    {{< agency-triptych slug="<slug>" name="<display-name>" >}}

The shortcode renders 1-3 cards depending on what URLs exist in
data/agencies.toml; when no entry exists it falls back to a single home
image. So this swap unifies markdown across all 34 listicles without
requiring full pricing/contact captures up front.

We also normalise two duplicate slugs:
  simple-tiger  → simpletiger
  ninja-promo   → ninjapromo
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST_DIR = ROOT / "content" / "list"

# Matches a full-line agency image:
#   ![Alt text — anything](/images/agencies/<slug>-home.webp)
# Captures the brand name we infer from the alt text + the slug.
IMG_LINE_RE = re.compile(
    r"^!\[([^\]]*?)\]\(/images/agencies/(?P<slug>[a-zA-Z0-9_-]+)-home\.webp\)\s*$",
    re.MULTILINE,
)

SLUG_NORMALISE = {
    "simple-tiger": "simpletiger",
    "ninja-promo":  "ninjapromo",
}


def brand_name_from_alt(alt: str, slug: str) -> str:
    """Extract a display name from the existing alt text.
    Example alts in the wild:
      "PipeRocket Digital homepage screenshot — B2B marketing agency"
      "SimpleTiger Homepage"
      "TheSEOWorks Homepage"
    Strategy: take everything before the first " homepage"/" Homepage" or
    em-dash. Fall back to a humanised slug."""
    if not alt:
        # humanise slug
        return slug.replace("-", " ").title()
    s = alt.strip()
    # cut on " homepage" (case-insensitive)
    s = re.split(r"\s+homepage", s, maxsplit=1, flags=re.IGNORECASE)[0]
    # cut on em/en-dash
    s = re.split(r"\s*[–—-]\s*", s, maxsplit=1)[0]
    s = s.strip()
    return s or slug.replace("-", " ").title()


def transform(text: str) -> tuple[str, int, int]:
    swaps = 0
    slug_fixes = 0

    def repl(m: re.Match) -> str:
        nonlocal swaps, slug_fixes
        alt = m.group(1)
        slug = m.group("slug")
        norm = SLUG_NORMALISE.get(slug, slug)
        if norm != slug:
            slug_fixes += 1
            slug = norm
        name = brand_name_from_alt(alt, slug)
        swaps += 1
        return f'{{{{< agency-triptych slug="{slug}" name="{name}" >}}}}'

    new_text = IMG_LINE_RE.sub(repl, text)
    return new_text, swaps, slug_fixes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    args = ap.parse_args()

    total = 0
    fixes = 0
    files = 0
    for md in sorted(LIST_DIR.glob("*.md")):
        if md.stem == "_index":
            continue
        if args.only and md.name != args.only:
            continue
        text = md.read_text()
        new_text, swaps, slug_fixes = transform(text)
        if swaps == 0:
            continue
        print(f"  [{ 'dry' if args.dry_run else 'wrote' }] {md.name}: {swaps} swap(s){', ' + str(slug_fixes) + ' slug fix(es)' if slug_fixes else ''}")
        files += 1
        total += swaps
        fixes += slug_fixes
        if not args.dry_run:
            md.write_text(new_text)
    print(f"\n=== Summary ===")
    print(f"Files touched:  {files}")
    print(f"Swaps:          {total}")
    print(f"Slug fixes:     {fixes}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'WRITE'}")


if __name__ == "__main__":
    main()
