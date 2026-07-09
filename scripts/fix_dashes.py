#!/usr/bin/env python3
"""
Role-aware em/en-dash converter for the /compare/ and /alternative/ corpora.

These pipelines were never dash-linted (lint_blog.py only covered
content/blogs/), so em-dashes (U+2014) and en-dashes (U+2013) accumulated in
three distinct roles that need three distinct fixes:

  1. Numeric / currency ranges   "10-49", "$5K - $15K", "2024-2025"  -> hyphen
  2. Decision-matrix cell markers  | - |   and   a: "-"              -> hyphen
     (the legend reads "Dash = capable but not the stronger pick", so the
      marker must stay a single dash character, just an ASCII one)
  3. Everything else (prose)      "at the edges, paid"               -> comma

Order matters: ranges and standalone markers are handled BEFORE the blanket
prose rule, or a lone "| - |" cell would become "|, |" and break the table.

Idempotent: files with no dashes are left byte-for-byte unchanged.

Usage:
  python3 scripts/fix_dashes.py --dry   content/compare content/alternative
  python3 scripts/fix_dashes.py         content/compare content/alternative
"""
import sys
import re
import glob
import os

DASH = "—–"  # em, en

RE_RANGE = re.compile(r"([\d\)KkMm%])\s*[" + DASH + r"]\s*(\$?\d)")
RE_QUOTED_MARKER = re.compile(r'"\s*[' + DASH + r']\s*"')
RE_CELL_MARKER = re.compile(r"\|( *)[" + DASH + r"]( *)(?=\|)")
RE_PROSE = re.compile(r"\s*[" + DASH + r"]\s*")
RE_ANY = re.compile(r"[" + DASH + r"]")


def convert(text):
    # 1. numeric/currency ranges -> hyphen (run twice for back-to-back ranges)
    for _ in range(2):
        text = RE_RANGE.sub(r"\1-\2", text)
    # 2a. standalone quoted marker  a: "-"
    text = RE_QUOTED_MARKER.sub('"-"', text)
    # 2b. standalone table-cell marker | - |  (lookahead keeps the shared pipe
    #     so adjacent dash cells all convert in one pass)
    prev = None
    while prev != text:
        prev = text
        text = RE_CELL_MARKER.sub(r"|\1-\2", text)
    # 3. remaining dashes are prose -> comma
    text = RE_PROSE.sub(", ", text)
    # 4. fallback: any dash still standing (e.g. line-terminal) -> hyphen
    text = RE_ANY.sub("-", text)
    return text


def main():
    args = sys.argv[1:]
    dry = "--dry" in args
    targets = [a for a in args if a != "--dry"]
    if not targets:
        print(__doc__)
        sys.exit(2)

    paths = []
    for t in targets:
        if os.path.isdir(t):
            paths += sorted(glob.glob(os.path.join(t, "*.md")))
        else:
            paths.append(t)

    changed = 0
    for p in paths:
        if os.path.basename(p) == "_index.md":
            continue
        with open(p, encoding="utf-8") as f:
            orig = f.read()
        new = convert(orig)
        if new != orig:
            changed += 1
            n = sum(orig.count(c) for c in DASH)
            print(f"{'would fix' if dry else 'fixed'}  {p}  ({n} dashes)")
            if not dry:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(new)
    print(f"\n{'would change' if dry else 'changed'}: {changed} files")


if __name__ == "__main__":
    main()
