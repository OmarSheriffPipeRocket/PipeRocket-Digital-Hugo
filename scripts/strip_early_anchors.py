#!/usr/bin/env python3
"""
Strip pre-floor glossary anchors + duplicate URLs from Hugo content.

Per-type word floors come from add_interlinks.py:
  blogs:  w450 · list: w200 · alternative: w200 · glossary/compare: w0 (no-op)

Strip rules:
  1. Glossary links before the word_gate floor.
  2. Any link to a target URL that appears 2+ times on the page:
     - If any occurrence is post-floor → keep the earliest post-floor one,
       strip the rest.
     - If all occurrences are pre-floor AND it's a glossary target → strip
       ALL so add_interlinks.py can re-place a single anchor at a valid
       post-floor position.
     - If all occurrences are pre-floor AND it's NOT glossary → keep the
       latest occurrence (preserves intentional editorial intro service-page
       references).
  3. Single-occurrence non-glossary pre-floor anchors are preserved
     (intentional editorial choices).

Usage:
  python3 scripts/strip_early_anchors.py             # dry-run
  python3 scripts/strip_early_anchors.py --apply     # write changes
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import add_interlinks as ai

LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\((/[^)]+)\)")


def strip_in_file(filepath: Path, word_gate: int):
    content = filepath.read_text(encoding="utf-8")
    fm, body = ai.split_frontmatter(content)
    if not fm:
        return content, []
    protected = ai.get_protected_spans(body)
    word_index = ai.build_word_index(body, protected)

    all_links = []
    for m in LINK_RE.finditer(body):
        wpos = ai.word_at(word_index, m.start())
        all_links.append((m.start(), m.end(), m.group(1), m.group(2), wpos))

    groups = defaultdict(list)
    for link in all_links:
        norm = link[3].rstrip("/") + "/"
        groups[norm].append(link)

    to_strip = []
    for norm_target, links in groups.items():
        is_glossary = norm_target.startswith("/glossary/")
        n = len(links)
        if n == 1:
            s, e, atext, tgt, wpos = links[0]
            if is_glossary and wpos < word_gate:
                to_strip.append(links[0])
            continue
        post_floor = [l for l in links if l[4] >= word_gate]
        if post_floor:
            keeper = post_floor[0]
            for link in links:
                if link is keeper: continue
                to_strip.append(link)
        else:
            if is_glossary:
                to_strip.extend(links)
            else:
                keeper = max(links, key=lambda l: l[4])
                for link in links:
                    if link is keeper: continue
                    to_strip.append(link)

    if not to_strip:
        return content, []

    to_strip.sort(key=lambda l: -l[0])
    chars = list(body)
    stripped_records = []
    for s, e, anchor_text, target, wpos in to_strip:
        chars[s:e] = list(anchor_text)
        stripped_records.append({"anchor": anchor_text, "target": target, "word_pos": wpos})

    return fm + "".join(chars), list(reversed(stripped_records))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    p.add_argument("--type", choices=list(ai.CONTENT_TYPES.keys()) + ["all"], default="all")
    args = p.parse_args()

    types = list(ai.CONTENT_TYPES.keys()) if args.type == "all" else [args.type]
    files = ai.collect_files(types)

    total = 0
    by_type = defaultdict(int)
    by_target = defaultdict(int)
    for fpath, ctype, wgate in files:
        if wgate <= 0:
            continue
        new_content, stripped = strip_in_file(fpath, wgate)
        if not stripped:
            continue
        total += len(stripped)
        by_type[ctype] += len(stripped)
        for s in stripped:
            by_target[s["target"]] += 1
        print(f"[{ctype}] {fpath.name}: {len(stripped)} stripped")
        for s in stripped:
            print(f"    w{s['word_pos']:>4}  [{s['anchor']}]({s['target']})")
        if args.apply:
            fpath.write_text(new_content, encoding="utf-8")

    print()
    print("=" * 60)
    print(f"TOTAL: {total} pre-floor/duplicate anchors {'STRIPPED' if args.apply else '(dry-run)'}")
    for t, n in sorted(by_type.items()):
        print(f"  {t}: {n}")
    print()
    print("Top affected targets:")
    for u, n in sorted(by_target.items(), key=lambda x: -x[1])[:10]:
        print(f"  {n:>3}  {u}")


if __name__ == "__main__":
    main()
