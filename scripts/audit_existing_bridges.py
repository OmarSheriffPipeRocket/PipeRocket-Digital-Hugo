#!/usr/bin/env python3
"""
Audit every ALREADY-APPLIED bridge sentence (PipeRocket-vs, alternative-vs,
neutral-compare) across content/ for the two bug classes fixed in
add_interlinks.py on 2026-07-27:

  1. Misplacement — landed under a TL;DR/intro list instead of inside the
     target agency's own numbered card (the neutral-bridge word-gate bug).
  2. False-positive match — the "competitor" matched a substring of an
     unrelated compound agency name (e.g. "Convert" inside "Grow and
     Convert") or a name-dropped mention in a "Notable Clients" table row.

For each existing bridge, re-derives the competitor/tool name from its
target URL (or the NEUTRAL_COMPARE_BRIDGES map for neutral entries), re-runs
the NOW-FIXED find_listicle_agency_section / find_alternative_agency_block
against the file's current body, and compares the freshly-computed correct
section to the section the bridge sentence is CURRENTLY sitting in.

Read-only — writes audit/existing_bridges_audit.csv, changes nothing.

Usage: python3 scripts/audit_existing_bridges.py
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import add_interlinks as ai  # noqa: E402

CONTENT_DIR = ROOT / "content"
AUDIT_DIR = ROOT / "audit"

# (regex over the WHOLE bridge paragraph, bridge type) — captures nothing;
# we just need the paragraph's span + the first markdown link's target inside it.
BRIDGE_PREFIXES = [
    (re.compile(r"^Want a side-by-side\? See our \["), "piperocket-vs"),
    (re.compile(r"^For a head-to-head on paid, organic, and pricing, see \["), "piperocket-vs"),
    (re.compile(r"^Weighing PipeRocket against "), "piperocket-vs"),
    (re.compile(r"^Also evaluating "), "alt-vs"),
    (re.compile(r"^Looking at "), "alt-vs"),
    (re.compile(r"^If .+ isn't quite the fit, check our \["), "alt-vs"),
    (re.compile(r"^Weighing the two directly\? See our neutral \["), "neutral"),
    (re.compile(r"^For a side-by-side on features and pricing, read our \["), "neutral"),
    (re.compile(r"^We put these head-to-head in our \["), "neutral"),
]
LINK_RE = re.compile(r"\[([^\]]+)\]\((/[^\s)]+)\)")


def find_bridge_paragraphs(body):
    """Return [(start, end, sentence_text, target_url, btype), ...] for every
    paragraph in body matching a known bridge-sentence prefix."""
    out = []
    cursor = 0
    paras = []
    for m in re.finditer(r"\n\s*\n", body):
        paras.append((cursor, m.start()))
        cursor = m.end()
    if cursor < len(body):
        paras.append((cursor, len(body)))
    for start, end in paras:
        text = body[start:end].strip()
        for pat, btype in BRIDGE_PREFIXES:
            if pat.match(text):
                lm = LINK_RE.search(text)
                if lm:
                    out.append((start, end, text, lm.group(2), btype))
                break
    return out


def heading_before(body, pos):
    """Return (start, text) of the last numbered '### N. Heading' at or
    before pos, or None."""
    best = None
    for m in re.finditer(r"^(#{2,3})\s+(\d+[\.\)]\s+.+)$", body, re.MULTILINE):
        if m.start() <= pos:
            best = (m.start(), m.group(2))
        else:
            break
    return best


def strip_paragraphs(body, spans):
    """Return body with the given (start,end) spans blanked out (replaced
    with spaces, preserving offsets) so a fallback search can't match text
    inside an already-inserted bridge sentence."""
    chars = list(body)
    for s, e in spans:
        for i in range(s, e):
            if chars[i] not in ("\n",):
                chars[i] = " "
    return "".join(chars)


PIPEROCKET_VS_RE = re.compile(r"^piperocket(?:-digital)?-vs-")


def resolve_expected_name(filepath, target_url, dst_class):
    """Return the competitor/tool name that SHOULD be searched for, given
    the bridge's target URL and the source file it lives on."""
    if dst_class == "alternative":
        _slug, name = ai.parse_competitor_from_alternative_url(target_url)
        return name
    if dst_class == "compare":
        # parse_competitor_from_compare_url ALWAYS returns a (garbled) name
        # for a neutral "A-vs-B" slug too — it only strips a real prefix for
        # genuine "piperocket-vs-X" URLs, so only trust it when that prefix
        # is actually present; otherwise this is a neutral bridge, looked up
        # by source-file-stem in NEUTRAL_COMPARE_BRIDGES instead.
        slug_m = re.match(r"/compare/([^/]+)/?$", target_url.rstrip("/") + "/")
        slug = slug_m.group(1) if slug_m else ""
        if PIPEROCKET_VS_RE.match(slug):
            _slug, name = ai.parse_competitor_from_compare_url(target_url)
            return name
        for locate_tool, t_url, _display in ai.NEUTRAL_COMPARE_BRIDGES.get(filepath.stem, []):
            if t_url.rstrip("/") + "/" == target_url.rstrip("/") + "/":
                return locate_tool
    return None


def main():
    rows = []
    files = sorted(CONTENT_DIR.glob("alternative/*.md")) + sorted(CONTENT_DIR.glob("list/*.md")) + sorted(CONTENT_DIR.glob("blogs/*.md"))
    total_bridges = 0
    for f in files:
        raw = f.read_text(encoding="utf-8", errors="ignore")
        fm, body = ai.split_frontmatter(raw)
        if not fm:
            continue
        bridges = find_bridge_paragraphs(body)
        if not bridges:
            continue
        stripped = strip_paragraphs(body, [(s, e) for s, e, *_ in bridges])
        for start, end, sentence, target_url, btype in bridges:
            total_bridges += 1
            dst_class = ai.classify_target(target_url)
            name = resolve_expected_name(f, target_url, dst_class)
            current_heading = heading_before(body, start)

            if not name:
                rows.append((str(f.relative_to(CONTENT_DIR)), btype, target_url, "?",
                             current_heading[1] if current_heading else "(before any heading)",
                             "UNRESOLVED", "could not determine expected competitor name"))
                continue

            loc = ai.find_listicle_agency_section(stripped, name)
            source = "heading"
            if not loc:
                loc = ai.find_alternative_agency_block(stripped, name)
                source = "paragraph"

            if not loc:
                rows.append((str(f.relative_to(CONTENT_DIR)), btype, target_url, name,
                             current_heading[1] if current_heading else "(before any heading)",
                             "FALSE-POSITIVE", "fixed matcher finds NO valid location at all now"))
                continue

            expected_heading = heading_before(stripped, loc[0]) if source == "heading" else None
            cur_h_text = current_heading[1] if current_heading else "(before any heading)"

            if source == "heading":
                exp_h_text = expected_heading[1] if expected_heading else "(none)"
                verdict = "OK" if (current_heading and expected_heading and current_heading[0] == expected_heading[0]) else "MISPLACED"
            else:
                # paragraph-fallback: verdict by whether the CURRENT position
                # falls inside the freshly-computed paragraph span
                exp_h_text = f"paragraph @ {loc[0]}-{loc[1]}"
                verdict = "OK" if loc[0] <= start <= loc[1] else "MISPLACED"

            rows.append((str(f.relative_to(CONTENT_DIR)), btype, target_url, name,
                         cur_h_text, verdict, exp_h_text))

    out_csv = AUDIT_DIR / "existing_bridges_audit.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["File", "Bridge Type", "Target URL", "Expected Name",
                    "Currently Under Heading", "Verdict", "Expected Location"])
        for r in rows:
            w.writerow(r)

    from collections import Counter
    c = Counter(r[5] for r in rows)
    print(f"Scanned {len(files)} files, found {total_bridges} existing bridge sentences")
    for v, n in c.most_common():
        print(f"  {v:14s}: {n}")
    print(f"Wrote {out_csv}")


if __name__ == "__main__":
    main()
