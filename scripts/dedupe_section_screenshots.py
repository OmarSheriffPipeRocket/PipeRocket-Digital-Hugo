#!/usr/bin/env python3
"""Remove duplicate `/images/agencies/{slug}-home.webp` references that
appear more than once inside the same H3 agency section. Keeps the FIRST
occurrence (which is usually the SEO-friendly alt-text injection) and
strips any subsequent occurrences along with their surrounding blank lines.

Idempotent. Run from repo root."""
import argparse
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST_DIR = os.path.join(ROOT, "content/list")

# Matches any markdown image tag pointing to /images/agencies/<slug>-home.webp.
IMG_RE = re.compile(
    r'(!\[[^\]]*\]\(/images/agencies/(?P<slug>[a-zA-Z0-9_-]+)-home\.webp\))'
)
H3_RE = re.compile(r'^###\s+(?:\*\*)?\s*(\d+)\.\s+(.+?)\s*(?:\*\*)?\s*$', re.MULTILINE)


def find_section_bounds(text: str):
    """Yield (start, end) byte offsets for each agency H3 section."""
    matches = list(H3_RE.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield m, start, end


def dedupe(text: str):
    """Return (new_text, removed_count). For each H3 section, keep only the
    first markdown-image ref per slug; subsequent refs are removed along
    with one neighbouring blank line so paragraph spacing collapses cleanly."""
    removed = 0
    # Build a list of edits (offset, original_substring, replacement). We then
    # apply them right-to-left to preserve offsets.
    edits = []

    for m, start, end in find_section_bounds(text):
        seen_slugs = set()
        # Search images within this section
        for img_m in IMG_RE.finditer(text, pos=start, endpos=end):
            slug = img_m.group("slug")
            if slug in seen_slugs:
                # Strip this image + one preceding blank line + one trailing
                # blank line so the markdown collapses.
                img_start = img_m.start()
                img_end = img_m.end()
                # eat leading blank line(s)
                while img_start > start and text[img_start - 1] == "\n":
                    img_start -= 1
                # eat one trailing blank line (single newline already eaten)
                if img_end < end and text[img_end] == "\n":
                    img_end += 1
                # leave at least one newline between surrounding paragraphs
                edits.append((img_start, img_end, "\n"))
                removed += 1
            else:
                seen_slugs.add(slug)

    if not edits:
        return text, 0

    # Apply edits right-to-left
    edits.sort(key=lambda e: -e[0])
    out = text
    for s, e, repl in edits:
        out = out[:s] + repl + out[e:]
    return out, removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total_removed = 0
    files_touched = 0
    for fname in sorted(os.listdir(LIST_DIR)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(LIST_DIR, fname)
        with open(path) as fh:
            original = fh.read()
        new, removed = dedupe(original)
        if removed:
            print(f"[{fname}] removed {removed} duplicate(s)")
            files_touched += 1
            total_removed += removed
            if not args.dry_run:
                with open(path, "w") as fh:
                    fh.write(new)

    print(f"\n=== Summary ===")
    print(f"Files touched:    {files_touched}")
    print(f"Duplicates removed: {total_removed}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'WRITE'}")


if __name__ == "__main__":
    main()
