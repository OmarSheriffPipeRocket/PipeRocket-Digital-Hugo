#!/usr/bin/env python3
"""
Auto-generate the `Referenced-by:` index in reference/stat_bank.md.

Each stat entry stores a canonical `Source:` URL. The `Referenced-by:` block
under it should list every content page that actually cites that source — but
hand-maintaining that list rots the moment a blog is edited, added, or removed
(a stale index of the stale-stat tracker — the exact failure the bank exists to
prevent). This script regenerates it deterministically:

  for each entry:
    1. read its `Source:` URL
    2. normalise it (drop scheme / www / query / fragment / trailing slash)
    3. grep that normalised key across content/**/*.md
    4. rewrite the `Referenced-by:` block with the files found (+ ×N if cited
       more than once in a file)

Matching is substring-on-the-normalised-key, so it's robust to the protocol,
www, trailing-slash, query-string, and #fragment variations that differ between
the bank entry and the in-content link (e.g. the HubSpot tracking-string case).

Usage:
    python3 scripts/sync_stat_bank_refs.py            # --check (dry run; exits 1 on drift)
    python3 scripts/sync_stat_bank_refs.py --write     # apply changes in place
    python3 scripts/sync_stat_bank_refs.py --file reference/stat_bank.md --content-root content

Notes:
  - Only the `Referenced-by:` field is auto-managed. news_bank.md's
    `Does-mention` is intentionally left manual: "mentions this news" is a
    semantic judgement, not a URL grep, so automating it would give false
    confidence. (`Should-mention` is curated and never touched.)
  - Entries whose `Source:` has no URL (e.g. an in-product notification) are
    skipped and left exactly as written.
  - The fenced ``` schema example in the file header is ignored.
"""

import argparse
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BANK = os.path.join("reference", "stat_bank.md")
DEFAULT_CONTENT = "content"

URL_RE = re.compile(r"https?://[^\s\]\)]+")
SOURCE_RE = re.compile(r"^\s*Source:\s*(.*)$")
REFBY_RE = re.compile(r"^(\s*)Referenced-by:.*$")
LIST_ITEM_RE = re.compile(r"^\s*-\s+")


def normalise(url):
    """Reduce a URL to a domain+path key for substring matching."""
    u = url.strip().rstrip(".,;")
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("#", 1)[0].split("?", 1)[0]
    u = u.rstrip("/")
    return u


def load_content_files(content_root):
    """Return {path: text} for every markdown file under content_root."""
    out = {}
    for dirpath, _dirs, files in os.walk(content_root):
        for fn in files:
            if fn.endswith(".md"):
                p = os.path.join(dirpath, fn)
                with open(p, encoding="utf-8") as fh:
                    out[os.path.relpath(p, REPO_ROOT)] = fh.read()
    return out


def find_references(key, content):
    """Return sorted [(relpath, count)] for files whose text contains key."""
    if not key or "/" not in key:
        # bare domain (no path) → too broad to match safely; skip.
        return None
    hits = []
    for path, text in content.items():
        c = text.count(key)
        if c:
            hits.append((path, c))
    return sorted(hits)


def split_entries(lines):
    """Yield (is_entry, block_lines). Skips ### headers inside ``` fences."""
    blocks = []
    cur = []
    in_fence = False
    started = False
    for ln in lines:
        if ln.lstrip().startswith("```"):
            in_fence = not in_fence
        if ln.startswith("### ") and not in_fence:
            if cur:
                blocks.append((started, cur))
            cur = [ln]
            started = True
        else:
            cur.append(ln)
    if cur:
        blocks.append((started, cur))
    return blocks


def entry_source_key(block):
    for ln in block:
        m = SOURCE_RE.match(ln)
        if m:
            um = URL_RE.search(m.group(1))
            return normalise(um.group(0)) if um else None
    return None


def rebuild_block(block, content):
    """Return (new_block, changed, entry_id, key, files)."""
    entry_id = block[0][4:].strip() if block[0].startswith("### ") else "?"
    key = entry_source_key(block)

    # locate the Referenced-by header line
    rb_i = None
    indent = ""
    for i, ln in enumerate(block):
        m = REFBY_RE.match(ln)
        if m:
            rb_i, indent = i, m.group(1)
            break
    if rb_i is None:
        return block, False, entry_id, key, None  # no field to manage

    # consume the existing list items immediately under the header
    j = rb_i + 1
    while j < len(block) and LIST_ITEM_RE.match(block[j]):
        j += 1
    old_list = block[rb_i + 1:j]

    if key is None:
        return block, False, entry_id, key, None  # no URL → leave manual

    files = find_references(key, content)
    if files is None:
        return block, False, entry_id, key, None  # bare-domain guard

    new_list = []
    if files:
        for path, count in files:
            suffix = f" (×{count})" if count > 1 else ""
            new_list.append(f"{indent}  - {path}{suffix}\n")
    else:
        new_list.append(f"{indent}  - (none — no content currently cites this source)\n")

    new_block = block[:rb_i + 1] + new_list + block[j:]
    changed = old_list != new_list
    return new_block, changed, entry_id, key, files


def main():
    ap = argparse.ArgumentParser(description="Regenerate Referenced-by in a bank file.")
    ap.add_argument("--file", default=DEFAULT_BANK, help="bank markdown file (default reference/stat_bank.md)")
    ap.add_argument("--content-root", default=DEFAULT_CONTENT, help="content directory to grep")
    ap.add_argument("--write", action="store_true", help="apply changes (default is --check / dry-run)")
    args = ap.parse_args()

    bank_path = os.path.join(REPO_ROOT, args.file) if not os.path.isabs(args.file) else args.file
    content_root = os.path.join(REPO_ROOT, args.content_root) if not os.path.isabs(args.content_root) else args.content_root

    with open(bank_path, encoding="utf-8") as fh:
        lines = fh.readlines()

    content = load_content_files(content_root)
    blocks = split_entries(lines)

    out_lines = []
    n_entries = n_changed = n_skipped = 0
    drift = []

    for is_entry, block in blocks:
        if not is_entry:
            out_lines.extend(block)
            continue
        n_entries += 1
        new_block, changed, entry_id, key, files = rebuild_block(block, content)
        out_lines.extend(new_block)
        if key is None or files is None:
            n_skipped += 1
            continue
        if changed:
            n_changed += 1
            drift.append((entry_id, [f for f, _ in files]))

    print(f"Entries: {n_entries} | drifted: {n_changed} | skipped (no URL): {n_skipped}")
    for entry_id, files in drift:
        shown = ", ".join(os.path.basename(f) for f in files) if files else "(none)"
        print(f"  ~ {entry_id}: -> {shown}")

    if args.write:
        with open(bank_path, "w", encoding="utf-8") as fh:
            fh.writelines(out_lines)
        print(f"\nWrote {args.file}.")
        return 0

    if n_changed:
        print("\nDrift detected. Re-run with --write to apply.")
        return 1
    print("\nReferenced-by index is up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
