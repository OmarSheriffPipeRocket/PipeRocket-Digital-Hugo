#!/usr/bin/env python3
"""
Normalize the colour palette across every SVG infographic so they
match the live site's theme tokens (declared in assets/css/main.css).

Tokens (the site's actual brand palette):
  --pr-cream    #F6F6F1   (already correct in SVGs)
  --pr-cream-2  #E8E4DA   (replace pure cool grays #F0F0EB / #E8E8E8)
  --pr-ink      #0D0D0D   (used for text — replace #444 → #1A1A1A,
                           #666 → #3F3F3F)
  --pr-muted    #6B6B6B   (replace #888)
  --pr-line     #D9D5C9   (warm beige hairline — replace #E8E8E8)
  --pr-cyan     #0CC6F1   (brighter cyan — replace #0BA6E2)
  --pr-red      #E63946   (brand red — NOT replacing #FF6B5C; that
                           coral is used as a secondary accent in
                           the popup + featured-in strip already)

Big dark slabs (#282828) are KEPT — those match the dark hero banner
slabs the site already uses; it's not the same colour as --pr-ink but
is a deliberate softer-dark for big surfaces.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "static" / "images" / "blog-infographics"

# Order matters — most specific first.
REPLACEMENTS = [
    # --- cyan ---
    # Hex
    ("#0BA6E2", "#0CC6F1"),
    ("#0ba6e2", "#0CC6F1"),
    # Common rgba forms used in SVGs:  rgba(11, 166, 226, X)  →  rgba(12, 198, 241, X)
    (re.compile(r"rgba\(\s*11\s*,\s*166\s*,\s*226\s*,"), "rgba(12, 198, 241,"),

    # --- hairline ---
    ("#E8E8E8", "#D9D5C9"),
    ("#e8e8e8", "#D9D5C9"),

    # --- text greys ---
    ("#888\"", "#6B6B6B\""),   # muted labels
    ("#888 ", "#6B6B6B "),
    ("#666\"", "#3F3F3F\""),   # body copy
    ("#666 ", "#3F3F3F "),
    ("#444\"", "#1A1A1A\""),   # darker body copy
    ("#444 ", "#1A1A1A "),

    # --- empty bar-chart tracks ---
    # The cool #F0F0EB used as a track bg → warm cream-2 #E8E4DA
    ("#F0F0EB", "#E8E4DA"),
    ("#f0f0eb", "#E8E4DA"),
]


def normalise(text: str):
    changes = 0
    new = text
    for needle, repl in REPLACEMENTS:
        if isinstance(needle, re.Pattern):
            new, n = needle.subn(repl, new)
        else:
            n = new.count(needle)
            if n:
                new = new.replace(needle, repl)
        changes += n
    return new, changes


def main():
    if not SVG_DIR.is_dir():
        sys.exit(f"static/images/blog-infographics/ not found at {SVG_DIR}")

    total_files = 0
    total_changes = 0
    for svg in sorted(SVG_DIR.glob("*.svg")):
        text = svg.read_text(encoding="utf-8")
        new_text, n = normalise(text)
        if new_text != text:
            svg.write_text(new_text, encoding="utf-8")
            print(f"  {svg.name}  →  {n} replacements")
            total_files += 1
            total_changes += n
        else:
            print(f"  {svg.name}  (no change)")

    print(f"\nDone. {total_files} files updated, {total_changes} total replacements.")


if __name__ == "__main__":
    main()
