#!/usr/bin/env python3
"""
Diagnose WHY each orphan page (0 inbound, per interlink_full_report_by_page.csv)
has no inbound links — not just that it doesn't.

Classifies every orphan into one of:
  - author-no-byline        contributor never assigned writtenBy/reviewedBy anywhere
  - no-linkmap-structural   type (tool/service/case-study) add_interlinks.py doesn't
                            support as a LINK_MAP target category at all yet
  - no-linkmap-content      supported type (blog/list/glossary) but nobody has
                            authored a LINK_MAP anchor for it yet
  - no-natural-anchor       LINK_MAP entry exists, but the anchor phrase never
                            occurs on any OTHER page's body — nothing to wrap
  - blocked-compare-bridge  LINK_MAP entry exists and the anchor is mentioned on
                            other pages, but the target is a neutral "A vs B"
                            compare page — add_interlinks.py's bridge-insert only
                            parses "PipeRocket vs X" competitor names, so it never
                            fires for neutral tool/agency comparisons
  - blocked-routing-policy  LINK_MAP entry exists and the anchor is mentioned on
                            other pages, but only on page types whose outbound
                            routing to this target type isn't in ALLOWED_FLOWS
                            (e.g. alternative -> listicle/blog is disallowed)
  - investigate             mention exists on an eligible source/flow but still
                            didn't get wrapped — needs a manual look (word-gate,
                            paragraph dedup, protected span, etc.)

Writes audit/orphan_root_cause.csv.

Usage: python3 scripts/audit_orphan_root_cause.py
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import add_interlinks as ai  # noqa: E402
from interlink_full_report import collect_pages  # noqa: E402 — correct url->file resolution (url:/slug: aware)

try:
    from link_map_generated import GENERATED_LINK_MAP
    FULL_MAP = ai.LINK_MAP + GENERATED_LINK_MAP
except Exception:
    FULL_MAP = ai.LINK_MAP

AUDIT_DIR = ROOT / "audit"
CONTENT_DIR = ROOT / "content"
BY_PAGE_CSV = AUDIT_DIR / "interlink_full_report_by_page.csv"

STRUCTURAL_TYPES = {"tool", "service", "case-study"}


def load_orphans():
    with open(BY_PAGE_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    return [(r[0], r[1], r[2]) for r in rows[1:] if r[5] == "YES"]


def build_target_map():
    out = {}
    for anchor, target, cs, prio in FULL_MAP:
        norm_t = target.rstrip("/") + "/"
        out.setdefault(norm_t, []).append(anchor)
    return out


def find_mentions(anchors, own_file, all_files):
    """Return [(filepath, source_dir, count)] for every OTHER page that
    contains one of `anchors` as a whole-word/phrase match. `own_file` is the
    target page's actual Path (from collect_pages), not a guess from its URL —
    several pages have a `slug:`/`url:` override that makes those differ."""
    hits = []
    for path, txt in all_files.items():
        if path == str(own_file):
            continue
        total = 0
        for a in anchors:
            total += len(re.findall(r"\b" + re.escape(a) + r"\b", txt, re.IGNORECASE))
        if total:
            rel = Path(path).relative_to(CONTENT_DIR)
            top = rel.parts[0] if len(rel.parts) > 1 else "service"
            hits.append((path, top, total))
    return hits


def any_writtenby_or_reviewedby(slug, all_files):
    pat_w = re.compile(r'^writtenBy:\s*"?' + re.escape(slug) + r'"?\s*$', re.M)
    pat_r = re.compile(r'^reviewedBy:\s*"?' + re.escape(slug) + r'"?\s*$', re.M)
    for txt in all_files.values():
        if pat_w.search(txt) or pat_r.search(txt):
            return True
    return False


def main():
    orphans = load_orphans()
    target_map = build_target_map()
    pages = collect_pages()  # url -> {"path": Path, ...}, url:/slug:-aware
    all_files = {str(f): f.read_text(encoding="utf-8", errors="ignore")
                 for f in CONTENT_DIR.rglob("*.md")}

    rows = []
    for url, typ, title in orphans:
        slug = url.strip("/").split("/")[-1]

        if typ == "author":
            any_writtenby_or_reviewedby(slug, all_files)
            rows.append((url, typ, title, "author-no-byline",
                         "No writtenBy/reviewedBy frontmatter anywhere in content/ names this author slug",
                         "Assign this person as writtenBy or reviewedBy on a relevant future post, "
                         "or remove the unused author page"))
            continue

        anchors = target_map.get(url)
        if not anchors:
            if typ in STRUCTURAL_TYPES:
                rows.append((url, typ, title, "no-linkmap-structural",
                             f"add_interlinks.py's CONTENT_TYPES/LINK_MAP has no entries for {typ} pages at all",
                             "Author LINK_MAP anchor phrases for this page and add matching source mentions "
                             "in relevant blogs/listicles (tools/service/case-study aren't wired into the "
                             "automated interlinking pass yet)"))
            else:
                rows.append((url, typ, title, "no-linkmap-content",
                             "No LINK_MAP anchor phrase has been authored for this target yet",
                             "Add an anchor phrase + target entry to LINK_MAP in scripts/add_interlinks.py, "
                             "then confirm the phrase actually appears in some source page's body"))
            continue

        own_file = pages[url]["path"]
        mentions = find_mentions(anchors, own_file, all_files)
        if not mentions:
            rows.append((url, typ, title, "no-natural-anchor",
                         f"LINK_MAP anchors {anchors} exist but never occur on any OTHER page's body text",
                         "Hand-write a bridging sentence on a topically related page rather than relying "
                         "on the automatic phrase-wrap (there's no natural mention to wrap)"))
            continue

        src_types_found = {t for _p, t, _n in mentions}
        dst_class = ai.classify_target(url)

        # The plain phrase-wrap path in add_interlinks.py unconditionally skips
        # dst in ("compare", "alternative") — those targets are ONLY reachable
        # via the bridge-insert mechanism, which only parses a competitor name
        # out of "piperocket(-digital)-vs-X" URLs. Any neutral "A vs B" compare
        # (or alternative) target with a real mention elsewhere is blocked by
        # this same gap regardless of which page type mentions it.
        if dst_class in ("compare", "alternative"):
            slug_part = url.rstrip("/").split("/")[-1]
            is_piperocket_pattern = bool(re.match(r"^piperocket(-digital)?-vs-", slug_part))
            if not is_piperocket_pattern:
                sample = ", ".join(f"{Path(p).name} ({n}x)" for p, _t, n in mentions[:3])
                rows.append((url, typ, title, "blocked-compare-bridge",
                             f"Mentioned on: {sample}. This is a neutral 'A vs B' {dst_class} page, but "
                             f"add_interlinks.py's bridge-insert only parses 'piperocket-vs-X' URLs for a "
                             f"competitor name, so it silently never fires here",
                             f"Extend add_interlinks.py's bridge logic to also handle neutral A-vs-B {dst_class} "
                             "targets (derive both names from the slug, not just a PipeRocket competitor)"))
                continue

        # ALLOWED_FLOWS keys are source *directory* names (blogs/list/alternative/glossary/compare)
        dir_alias = {"blog": "blogs", "blogs": "blogs", "list": "list", "listicle": "list",
                     "alternative": "alternative", "glossary": "glossary", "compare": "compare"}
        blocked = True
        for t in src_types_found:
            src_dir = dir_alias.get(t, t)
            if ai.ALLOWED_FLOWS.get((src_dir, dst_class)):
                blocked = False
        if blocked:
            sample = ", ".join(f"{Path(p).name} ({n}x)" for p, _t, n in mentions[:3])
            src_kinds = "/".join(sorted(src_types_found))
            rows.append((url, typ, title, "blocked-routing-policy",
                         f"Mentioned on {src_kinds} page(s): {sample}, but ALLOWED_FLOWS in add_interlinks.py "
                         f"doesn't permit a {src_kinds} -> {dst_class} link",
                         "Either add a manual link on one of the mentioning pages, or add "
                         f"a ({src_kinds!r}, {dst_class!r}) entry to ALLOWED_FLOWS if that flow should be permitted"))
            continue

        sample = ", ".join(f"{Path(p).name} ({n}x)" for p, _t, n in mentions[:3])
        rows.append((url, typ, title, "investigate",
                     f"Eligible mention found ({sample}) via an allowed flow, but add_interlinks.py's dry run "
                     f"still didn't wrap it — check word-position gate, per-paragraph dedupe, or protected spans",
                     "Run: python3 scripts/add_interlinks.py --slug <mentioning-page-slug> and inspect why"))

    out_csv = AUDIT_DIR / "orphan_root_cause.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Page URL", "Type", "Title", "Root Cause", "Evidence", "Recommended Action"])
        for r in sorted(rows, key=lambda x: (x[3], x[1], x[0])):
            w.writerow(r)

    from collections import Counter
    c = Counter(r[3] for r in rows)
    print(f"Diagnosed {len(rows)} orphans -> {out_csv}")
    for cause, n in c.most_common():
        print(f"  {cause:24s}: {n}")


if __name__ == "__main__":
    main()
