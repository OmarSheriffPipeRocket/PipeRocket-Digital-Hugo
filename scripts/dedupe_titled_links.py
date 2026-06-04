#!/usr/bin/env python3
"""
De-duplicate internal links by target across each blog body — title-attribute
aware. The older strip_early_anchors.py groups by the raw URL capture, so a
titled link [x](/u/ "T") and an untitled [y](/u/) hash to different keys and a
cross-pair duplicate slips through. This normalizes the URL (drops the
"title" and trailing slash) before grouping.

Rule: for a target that appears 2+ times in the body, keep the earliest
occurrence and unwrap (strip the link markup, keep anchor text) from the rest.
Frontmatter and image links are ignored.

Usage:
  python3 scripts/dedupe_titled_links.py            # dry-run
  python3 scripts/dedupe_titled_links.py --apply
"""
import argparse
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOGS = ROOT / "content" / "blogs"
# group(1)=anchor, group(2)=url path, group(3)=optional ` "title"`
LINK = re.compile(r'(?<!!)\[([^\]]+)\]\((/[^)\s"]+)(\s+"[^"]*")?\)')


def split_fm(t):
    if t.startswith("---"):
        end = t.find("\n---", 3)
        if end != -1:
            nl = t.find("\n", end + 1)
            return t[: nl + 1], t[nl + 1:]
    return "", t


def process(path, apply):
    raw = path.read_text(encoding="utf-8")
    fm, body = split_fm(raw)
    if not fm:
        return []
    groups = defaultdict(list)
    for m in LINK.finditer(body):
        norm = m.group(2).rstrip("/") + "/"
        groups[norm].append((m.start(), m.end(), m.group(1)))

    edits, actions = [], []
    for norm, occ in groups.items():
        if len(occ) < 2:
            continue
        occ.sort()
        keeper = occ[0]
        for s, e, anchor in occ[1:]:
            edits.append((s, e, anchor))
        actions.append((norm, [o[0] for o in occ]))

    if apply and edits:
        for s, e, anchor in sorted(edits, key=lambda x: -x[0]):
            body = body[:s] + anchor + body[e:]
        path.write_text(fm + body, encoding="utf-8")
    return actions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    total_links = total_files = 0
    for f in sorted(BLOGS.glob("*.md")):
        acts = process(f, args.apply)
        if not acts:
            continue
        total_files += 1
        print(f"\n### {f.name}")
        for norm, positions in acts:
            stripped = len(positions) - 1
            total_links += stripped
            print(f"   {norm}  x{len(positions)} @ {positions}  -> keep first, unwrap {stripped}")
    print("\n" + "=" * 60)
    print(f"{'APPLIED' if args.apply else 'DRY-RUN'}: {total_links} duplicate links unwrapped across {total_files} files")


if __name__ == "__main__":
    main()
