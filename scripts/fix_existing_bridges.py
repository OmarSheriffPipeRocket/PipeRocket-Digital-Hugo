#!/usr/bin/env python3
"""
Apply the fixes identified by scripts/audit_existing_bridges.py:
  - MISPLACED bridge sentences are removed from their current spot and
    reinserted at the correct location (recomputed fresh, post-removal).
  - FALSE-POSITIVE bridge sentences are removed outright (no valid location
    exists for them anymore).
  - OK and UNRESOLVED bridges are left untouched.

Dry-run by default (prints what would change per file). Pass --apply to write.

Usage:
  python3 scripts/fix_existing_bridges.py            # dry-run
  python3 scripts/fix_existing_bridges.py --apply
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import add_interlinks as ai  # noqa: E402
from audit_existing_bridges import (  # noqa: E402
    find_bridge_paragraphs, strip_paragraphs, resolve_expected_name,
)

CONTENT_DIR = ROOT / "content"


def classify_bridges(f, body):
    """Return [(start, end, sentence, target_url, btype, verdict, name)]."""
    bridges = find_bridge_paragraphs(body)
    if not bridges:
        return []
    stripped = strip_paragraphs(body, [(s, e) for s, e, *_ in bridges])
    out = []
    for start, end, sentence, target_url, btype in bridges:
        dst_class = ai.classify_target(target_url)
        name = resolve_expected_name(f, target_url, dst_class)
        if not name:
            out.append((start, end, sentence, target_url, btype, "UNRESOLVED", name))
            continue
        loc = ai.find_listicle_agency_section(stripped, name)
        if not loc:
            loc = ai.find_alternative_agency_block(stripped, name)
        if not loc:
            out.append((start, end, sentence, target_url, btype, "FALSE-POSITIVE", name))
            continue
        # OK vs MISPLACED — same check as the audit script
        headings = None
        verdict = "OK" if loc[0] <= start <= loc[1] else "MISPLACED"
        out.append((start, end, sentence, target_url, btype, verdict, name))
    return out


def fix_file(f, apply):
    raw = f.read_text(encoding="utf-8", errors="ignore")
    fm, body = ai.split_frontmatter(raw)
    if not fm:
        return None

    classified = classify_bridges(f, body)
    to_fix = [c for c in classified if c[5] in ("MISPLACED", "FALSE-POSITIVE")]
    if not to_fix:
        return None

    # 1) remove all misplaced/false-positive spans, right-to-left
    removals = sorted(to_fix, key=lambda c: c[0], reverse=True)
    new_body = body
    for start, end, *_ in removals:
        new_body = new_body[:start] + new_body[end:]

    # 2) reinsert the MISPLACED ones at a freshly-computed correct location,
    # one at a time (recompute on the current body state each time)
    reinserted, dropped = 0, 0
    for start, end, sentence, target_url, btype, verdict, name in to_fix:
        if verdict == "FALSE-POSITIVE":
            dropped += 1
            continue
        loc = ai.find_listicle_agency_section(new_body, name)
        if loc:
            section_start, section_end = loc
            insert_at = section_end
            while insert_at > section_start and new_body[insert_at - 1] in " \t\r\n":
                insert_at -= 1
        else:
            loc = ai.find_alternative_agency_block(new_body, name)
            insert_at = loc[1] if loc else None
        if insert_at is None:
            # shouldn't happen (audit already verified a location exists) —
            # if it does, don't silently drop content: leave it out and flag.
            print(f"  WARNING: could not re-locate '{name}' in {f.name} — dropping bridge (was: {sentence!r})")
            dropped += 1
            continue
        new_body = new_body[:insert_at] + f"\n\n{sentence}\n\n" + new_body[insert_at:]
        reinserted += 1

    if apply:
        f.write_text(fm + new_body, encoding="utf-8")

    return {"misplaced_moved": reinserted, "false_positive_removed": dropped}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = sorted(CONTENT_DIR.glob("alternative/*.md")) + sorted(CONTENT_DIR.glob("list/*.md")) + sorted(CONTENT_DIR.glob("blogs/*.md"))
    total_moved = 0
    total_removed = 0
    files_changed = 0
    for f in files:
        result = fix_file(f, args.apply)
        if result is None:
            continue
        files_changed += 1
        total_moved += result["misplaced_moved"]
        total_removed += result["false_positive_removed"]
        print(f"[{f.relative_to(CONTENT_DIR)}] moved={result['misplaced_moved']} removed={result['false_positive_removed']}")

    print("\n" + "=" * 60)
    print(f"{'APPLIED' if args.apply else 'DRY RUN'}")
    print(f"  files changed   : {files_changed}")
    print(f"  bridges moved   : {total_moved}")
    print(f"  bridges removed : {total_removed}")


if __name__ == "__main__":
    main()
