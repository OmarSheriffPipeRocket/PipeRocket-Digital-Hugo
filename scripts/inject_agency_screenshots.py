#!/usr/bin/env python3
"""Inject agency homepage screenshots into listicle markdown.

For each `### N. Agency Name` (or `### **N. Agency Name**`) heading in content/list/*.md:
  - Slugify the agency name
  - Find a matching `{slug}-home.webp` in static/images/agencies/
  - If the section doesn't already contain a screenshot ref for that slug, insert
    the canonical screenshot markdown immediately after the heading (separated
    by one blank line, before the score line).

Idempotent: re-running won't duplicate existing screenshots.

Run from repo root: python3 scripts/inject_agency_screenshots.py [--dry-run] [--only file.md]
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST_DIR = os.path.join(ROOT, "content/list")
STATIC_DIR = os.path.join(ROOT, "static/images/agencies")

H3_RE = re.compile(r'^###\s+(?:\*\*)?\s*(\d+)\.\s+(.+?)\s*(?:\*\*)?\s*$')
SCREENSHOT_RE = re.compile(r'!\[[^\]]*\]\(/images/agencies/([a-zA-Z0-9_-]+)\.webp\)')

# Manual slug overrides for agency names that don't map cleanly via slugify.
OVERRIDES = {
    "Simple Tiger": "simpletiger",
    "MADX Digital": "madx-digital",
}


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[.&'’]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def resolve_slug(name: str, available: set) -> str | None:
    if name in OVERRIDES:
        cand = OVERRIDES[name]
        return cand if cand in available else None
    s = slugify(name)
    if s in available:
        return s
    concat = s.replace("-", "")
    if concat in available:
        return concat
    return None


def process_file(path: str, available: set, dry_run: bool):
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    # Pre-scan: section boundaries (H3 line indices)
    section_starts = []
    for i, ln in enumerate(lines):
        if H3_RE.match(ln):
            section_starts.append(i)
    section_starts.append(len(lines))  # sentinel

    injections = []  # (insert_line_index, text_block, agency_name)

    for idx in range(len(section_starts) - 1):
        start = section_starts[idx]
        end = section_starts[idx + 1]
        m = H3_RE.match(lines[start])
        if not m:
            continue
        rank, name = m.group(1), m.group(2).strip().rstrip("*").strip()

        slug = resolve_slug(name, available)
        if not slug:
            continue

        # Check if any screenshot already exists in this section
        section_text = "".join(lines[start:end])
        existing = SCREENSHOT_RE.findall(section_text)
        if existing:
            continue  # already has at least one screenshot in this section

        # Find insertion point: first non-blank line index after the H3.
        # We want: H3 \n \n ![alt](...) \n \n {rest}.
        # Insert AT that first-non-blank line, pushing it down. If next line is
        # already blank, we still need to keep one blank between H3 and image.
        insert_at = start + 1
        # skip exactly one blank line if present so the image sits in the gap
        if insert_at < end and lines[insert_at].strip() == "":
            insert_at += 1

        alt = f"{name} homepage screenshot — B2B marketing agency"
        block = f"![{alt}](/images/agencies/{slug}-home.webp)\n\n"
        injections.append((insert_at, block, name, slug))

    if not injections:
        return 0

    # Apply injections from bottom up so line indices stay stable
    new_lines = list(lines)
    for insert_at, block, name, slug in sorted(injections, key=lambda x: -x[0]):
        new_lines.insert(insert_at, block)

    fname = os.path.basename(path)
    print(f"\n[{fname}] {len(injections)} injection(s):")
    for _, _, name, slug in injections:
        print(f"  + {name:35s} -> /images/agencies/{slug}-home.webp")

    if not dry_run:
        with open(path, "w", encoding="utf-8") as fh:
            fh.writelines(new_lines)

    return len(injections)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Don't write files")
    ap.add_argument("--only", help="Only process this filename (basename)")
    args = ap.parse_args()

    available_slugs = {f.replace("-home.webp", "")
                       for f in os.listdir(STATIC_DIR)
                       if f.endswith("-home.webp")}

    files = sorted(f for f in os.listdir(LIST_DIR) if f.endswith(".md") and f != "_index.md")
    if args.only:
        files = [f for f in files if f == args.only]

    total = 0
    touched = 0
    for fname in files:
        path = os.path.join(LIST_DIR, fname)
        n = process_file(path, available_slugs, args.dry_run)
        if n:
            touched += 1
            total += n

    print(f"\n=== Summary ===")
    print(f"Files touched: {touched}")
    print(f"Screenshots injected: {total}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'WRITE'}")


if __name__ == "__main__":
    main()
