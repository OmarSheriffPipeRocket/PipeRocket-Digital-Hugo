#!/usr/bin/env python3
"""
SEO meta audit across every content file.

Reads frontmatter for title/metaTitle/description/metaDescription, then
classifies each page on length, presence, and uniqueness. The output is
a punch list of pages that need attention.

Ideal length bands (Google's typical SERP truncation):
  · meta title:       50–60 characters    (under 70 hard cap)
  · meta description: 150–160 characters  (under 170 hard cap)
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

TITLE_GOOD = (40, 60)
TITLE_HARD_MAX = 70
DESC_GOOD = (140, 160)
DESC_HARD_MAX = 170
DESC_MIN = 70

# Skip certain helpers
SKIP_FILES = {"_index.md"}


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.match(r"^---\s*\n(.+?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    fm = m.group(1)
    out = {}
    for line in fm.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key not in out:
            out[key] = val
    return out


def classify_title(s):
    if not s:
        return "MISSING"
    n = len(s)
    if n > TITLE_HARD_MAX:
        return f"TOO LONG ({n})"
    if n < TITLE_GOOD[0]:
        return f"SHORT ({n})"
    if n > TITLE_GOOD[1]:
        return f"LONG ({n})"
    return f"OK ({n})"


def classify_desc(s):
    if not s:
        return "MISSING"
    n = len(s)
    if n > DESC_HARD_MAX:
        return f"TOO LONG ({n})"
    if n < DESC_MIN:
        return f"TOO SHORT ({n})"
    if n < DESC_GOOD[0]:
        return f"SHORT ({n})"
    if n > DESC_GOOD[1]:
        return f"LONG ({n})"
    return f"OK ({n})"


def main():
    rows = []
    titles_seen = defaultdict(list)
    descs_seen = defaultdict(list)
    for md in sorted(CONTENT.rglob("*.md")):
        if md.name in SKIP_FILES:
            continue
        fm = parse_frontmatter(md)
        title = fm.get("metaTitle") or fm.get("title") or ""
        desc = fm.get("metaDescription") or fm.get("description") or ""
        rel = str(md.relative_to(ROOT))
        rows.append((rel, title, desc))
        titles_seen[title.strip().lower()].append(rel)
        descs_seen[desc.strip().lower()].append(rel)

    # Print summary buckets
    issue_count = Counter()
    issues = defaultdict(list)
    for rel, t, d in rows:
        ct = classify_title(t)
        cd = classify_desc(d)
        bucket = (ct.split(" ")[0], cd.split(" ")[0])
        if "OK" in (bucket[0], bucket[1]) and bucket == ("OK", "OK"):
            continue
        issues["all"].append((rel, ct, cd, t, d))
        if ct != "OK":
            issue_count[f"title {ct.split(' ')[0]}"] += 1
        if cd != "OK":
            issue_count[f"desc {cd.split(' ')[0]}"] += 1

    print(f"Total pages scanned: {len(rows)}\n")
    print("=== Summary of issues ===")
    for k, v in sorted(issue_count.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<20} {v}")
    print()

    # Per-bucket breakdown
    buckets = {
        "MISSING title":   lambda t, d: not t,
        "MISSING desc":    lambda t, d: not d,
        "TOO LONG title":  lambda t, d: t and len(t) > TITLE_HARD_MAX,
        "TOO LONG desc":   lambda t, d: d and len(d) > DESC_HARD_MAX,
        "TOO SHORT desc":  lambda t, d: d and len(d) < DESC_MIN,
        "SHORT title":     lambda t, d: t and len(t) < TITLE_GOOD[0],
        "LONG title":      lambda t, d: t and TITLE_GOOD[1] < len(t) <= TITLE_HARD_MAX,
        "LONG desc":       lambda t, d: d and DESC_GOOD[1] < len(d) <= DESC_HARD_MAX,
    }

    for name, pred in buckets.items():
        matches = [(rel, t, d) for (rel, t, d) in rows if pred(t, d)]
        if not matches:
            continue
        print(f"=== {name} ({len(matches)}) ===")
        for rel, t, d in matches[:50]:
            content = t if "title" in name else d
            n = len(content)
            print(f"  · {rel}   ({n} chars)")
            print(f"      {content}")
        if len(matches) > 50:
            print(f"  … and {len(matches) - 50} more")
        print()

    # Duplicates
    dup_titles = {k: v for k, v in titles_seen.items() if k and len(v) > 1}
    dup_descs = {k: v for k, v in descs_seen.items() if k and len(v) > 1}
    if dup_titles:
        print(f"=== Duplicate titles ({len(dup_titles)}) ===")
        for t, pages in dup_titles.items():
            print(f"  · \"{t[:80]}\"  used on {len(pages)} pages")
            for p in pages[:4]:
                print(f"      {p}")
        print()
    if dup_descs:
        print(f"=== Duplicate descriptions ({len(dup_descs)}) ===")
        for d, pages in dup_descs.items():
            print(f"  · \"{d[:80]}…\"  used on {len(pages)} pages")
            for p in pages[:4]:
                print(f"      {p}")


if __name__ == "__main__":
    main()
