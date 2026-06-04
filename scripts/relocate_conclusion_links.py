#!/usr/bin/env python3
"""
Move non-LP links out of Conclusion sections (rule: a Conclusion may only hold
LP/CTA links; links to blogs, glossary, research, comparisons, etc. are not
allowed there). FAQ/author sections are exempt — any link is fine there.

Per non-LP link inside a Conclusion section:
  A. If the same target is already linked in the body (outside the conclusion)
     -> unwrap the conclusion copy (redundant).
  B. Else find the first clean plain-text mention of the anchor phrase in the
     body (post-w450, outside any skip section, not already inside a link)
     -> wrap that, unwrap the conclusion copy.
  C. Else unwrap the conclusion copy (no valid body home).

Usage:
  python3 scripts/relocate_conclusion_links.py            # dry-run
  python3 scripts/relocate_conclusion_links.py --apply
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOGS = ROOT / "content" / "blogs"
sys.path.insert(0, str(ROOT / "scripts"))
import add_interlinks as ai

FLOOR = 450
NON_LP = ("/blogs/", "/glossary/", "/research/", "/compare/", "/alternative/", "/list/", "/case-study")
LINK = re.compile(r'(?<!!)\[([^\]]+)\]\((/[^)\s"]+)(\s+"[^"]*")?\)')


def visible_words(s):
    s = re.sub(r"(?<!!)\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", s)
    s = re.sub(r"\{\{.*?\}\}", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[#>*_`~|-]", " ", s)
    return len([w for w in s.split() if any(c.isalnum() for c in w)])


def floor_offset(body):
    lo, hi = 0, len(body)
    while lo < hi:
        mid = (lo + hi) // 2
        if visible_words(body[:mid]) >= FLOOR:
            hi = mid
        else:
            lo = mid + 1
    return lo


def conclusion_spans(body):
    spans = []
    hs = list(re.finditer(r"^(#{2,3})\s+(.+)$", body, re.MULTILINE))
    for i, h in enumerate(hs):
        if not ai.CONCLUSION_RE.search(h.group(2).strip()):
            continue
        lvl = len(h.group(1)); end = len(body)
        for h2 in hs[i + 1:]:
            t2 = h2.group(2).strip()
            # End at next same-or-higher heading, OR at any FAQ/author heading
            # (a nested ### FAQ must not be swallowed into the conclusion).
            if len(h2.group(1)) <= lvl or ai.FAQ_RE.search(t2) or ai.SKIP_HEADING_RE.search(t2):
                end = h2.start(); break
        spans.append((h.start(), end))
    return spans


def protected_spans(body):
    spans = list(ai.build_excluded_section_spans(body))  # FAQ + Conclusion + author
    for pat in (r"```.*?```", r"`[^`\n]+`", r"\{\{.*?\}\}", r"<[^>]+>",
                r"!\[[^\]]*\]\([^)]*\)"):  # image incl. alt text
        for m in re.finditer(pat, body, flags=re.S):
            spans.append((m.start(), m.end()))
    for m in re.finditer(r"(?m)^#{1,6}\s.*$", body):
        spans.append((m.start(), m.end()))
    return spans


def in_spans(p, spans):
    return any(s <= p < e for s, e in spans)


def process(path, apply):
    raw = path.read_text(encoding="utf-8")
    fm, body = ai.split_frontmatter(raw)
    if not fm:
        return []
    cspans = conclusion_spans(body)
    if not cspans:
        return []
    foff = floor_offset(body)
    pspans = protected_spans(body)
    links = [(m.start(), m.end(), m.group(1), m.group(2).rstrip("/") + "/",
              m.group(0)) for m in LINK.finditer(body)]
    body_targets = {u for s, e, t, u, raw_ in links if not in_spans(s, cspans)}

    actions, edits, consumed = [], [], []
    for s, e, anchor, url, full in links:
        if not in_spans(s, cspans):
            continue
        if not url.startswith(NON_LP):
            continue  # LP/CTA links are allowed in conclusions
        phrase = re.sub(r"[*`]", "", anchor).strip()
        if url in body_targets:
            edits.append((s, e, anchor))
            actions.append(("UNWRAP (body link exists)", phrase, url))
            continue
        moved = False
        if phrase:
            for m in re.compile(r"\b" + re.escape(phrase) + r"\b", re.I).finditer(body):
                ms, me = m.start(), m.end()
                if ms >= s:  # don't relocate into/after the conclusion
                    break
                if visible_words(body[:ms]) < FLOOR:
                    continue
                if in_spans(ms, pspans) or in_spans(ms, [(a, b) for a, b, *_ in links]):
                    continue
                if any(a <= ms < b for a, b in consumed):
                    continue
                # strip the link's optional title to keep insert clean
                clean_url = "/" + url.strip("/") + "/"
                edits.append((ms, me, f"[{m.group(0)}]({clean_url})"))
                edits.append((s, e, anchor))
                consumed.append((ms, me))
                body_targets.add(url)
                actions.append((f"MOVE -> w{visible_words(body[:ms])}", phrase, url))
                moved = True
                break
        if not moved:
            # No body mention to relocate to — leave for a hand-written bridge.
            actions.append(("SKIP (needs bridge)", phrase, url))

    if apply and edits:
        for st, en, rep in sorted(edits, key=lambda x: -x[0]):
            body = body[:st] + rep + body[en:]
        path.write_text(fm + body, encoding="utf-8")
    return actions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    moved = unwrapped = 0
    for f in sorted(BLOGS.glob("*.md")):
        acts = process(f, args.apply)
        if not acts:
            continue
        print(f"\n### {f.name}")
        for kind, phrase, url in acts:
            print(f"   [{kind}]  {phrase!r} -> {url}")
            if kind.startswith("MOVE"):
                moved += 1
            else:
                unwrapped += 1
    print("\n" + "=" * 60)
    print(f"{'APPLIED' if args.apply else 'DRY-RUN'}: {moved} moved, {unwrapped} unwrapped")


if __name__ == "__main__":
    main()
