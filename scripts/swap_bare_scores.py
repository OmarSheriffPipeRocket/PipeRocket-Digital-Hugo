#!/usr/bin/env python3
"""Replace bare numeric agency-score lines with {{< score N >}}.

A "bare numeric score" is a markdown line that contains nothing except
a 2- or 3-digit integer between 50 and 100. These appear immediately
after the {{< agency-triptych >}} call in our listicles and represent
the agency's overall PipeRocket Score. Converting them to a shortcode
lets the score render as a styled chip instead of inline text.

To avoid false positives we require:
  - The line must contain only the integer (no other characters).
  - Value must be between 50 and 100.
  - Conservatively, the line must be preceded within 8 prior lines by
    either an {{< agency-triptych ...>}} call or an `### N. <Brand>` H3
    so we don't swap unrelated numbers."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

LIST_DIR = Path("/Users/luckychamp/Desktop/claude/piperocket-site/content/list")
SCORE_RE = re.compile(r"^(\d{2,3})\s*$")
H3_RE = re.compile(r"^###\s+\**\s*\d+\.")


def is_anchor(line: str) -> bool:
    return "agency-triptych" in line or bool(H3_RE.match(line))


def transform(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    swapped = 0
    for i, line in enumerate(lines):
        m = SCORE_RE.match(line)
        if not m:
            continue
        n = int(m.group(1))
        if not 50 <= n <= 100:
            continue
        # Look backward for an anchor within 8 lines
        ok = False
        for j in range(i - 1, max(-1, i - 9), -1):
            if is_anchor(lines[j]):
                ok = True
                break
        if not ok:
            continue
        lines[i] = f"{{{{< score {n} >}}}}"
        swapped += 1
    return "\n".join(lines), swapped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    args = ap.parse_args()

    total = 0
    files = 0
    for md in sorted(LIST_DIR.glob("*.md")):
        if md.stem == "_index":
            continue
        if args.only and md.name != args.only:
            continue
        text = md.read_text()
        new_text, n = transform(text)
        if n == 0:
            continue
        print(f"  [{'dry' if args.dry_run else 'wrote'}] {md.name}: {n} swap(s)")
        files += 1
        total += n
        if not args.dry_run:
            md.write_text(new_text)
    print(f"\n=== Summary ===")
    print(f"Files: {files}, swaps: {total}, mode: {'DRY RUN' if args.dry_run else 'WRITE'}")


if __name__ == "__main__":
    main()
