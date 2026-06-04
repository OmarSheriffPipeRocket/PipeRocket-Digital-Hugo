#!/usr/bin/env python3
"""
Relocate internal interlinks that sit before the w450 floor to a valid
post-floor position, by visible-word count (headings/code/shortcodes excluded
from the count, links collapsed to their anchor text).

Per early internal link [anchor](/internal/url):
  A. If the same target URL already appears at >= w450 elsewhere -> just
     unwrap the early link (a valid post-floor link already exists).
  B. Else find the first clean plain-text mention of the anchor phrase after
     the floor (not inside a link/heading/code/shortcode) -> unwrap early,
     wrap that later mention.
  C. Else leave the early link untouched and report it (no later mention).

External links (http/https) are ignored - only internal "/..." targets count.

Usage:
  python3 scripts/relocate_early_interlinks.py            # dry-run
  python3 scripts/relocate_early_interlinks.py --apply
  python3 scripts/relocate_early_interlinks.py --slug saas-seo
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOGS = ROOT / "content" / "blogs"
FLOOR = 450

MDLINK = re.compile(r'(?<!!)\[([^\]]+)\]\((/[^)]+)\)')


def split_fm(t):
    if t.startswith("---"):
        end = t.find("\n---", 3)
        if end != -1:
            nl = t.find("\n", end + 1)
            return t[: nl + 1], t[nl + 1 :]
    return "", t


def visible_words(s):
    s = re.sub(r"(?<!!)\[([^\]]+)\]\([^)]+\)", r"\1", s)   # md link -> text
    s = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", s)            # images out
    s = re.sub(r"\{\{.*?\}\}", " ", s, flags=re.S)         # shortcodes
    s = re.sub(r"<[^>]+>", " ", s)                         # html tags
    s = re.sub(r"[#>*_`~|-]", " ", s)                      # md punctuation
    return len([w for w in s.split() if any(c.isalnum() for c in w)])


def floor_offset(body):
    """Smallest char offset whose prefix holds >= FLOOR visible words."""
    lo, hi = 0, len(body)
    while lo < hi:
        mid = (lo + hi) // 2
        if visible_words(body[:mid]) >= FLOOR:
            hi = mid
        else:
            lo = mid + 1
    return lo


def protected_spans(body):
    spans = []
    for pat in (r"```.*?```", r"`[^`\n]+`", r"\{\{.*?\}\}", r"<[^>]+>"):
        for m in re.finditer(pat, body, flags=re.S):
            spans.append((m.start(), m.end()))
    for m in re.finditer(r"(?m)^#{1,6}\s.*$", body):       # headings
        spans.append((m.start(), m.end()))
    return spans


def in_spans(pos, spans):
    return any(s <= pos < e for s, e in spans)


def phrase_visible(anchor):
    """Anchor text reduced to plain visible phrase (strip **, *, `)."""
    return re.sub(r"[*`]", "", anchor).strip()


def process(path, apply):
    raw = path.read_text(encoding="utf-8")
    fm, body = split_fm(raw)
    if not fm:
        return []
    foff = floor_offset(body)
    links = [(m.start(), m.end(), m.group(1), m.group(2)) for m in MDLINK.finditer(body)]
    # targets that already have (or will have, as we relocate) a post-floor link
    placed = {l[3].rstrip("/") + "/" for l in links if l[0] >= foff}

    actions = []   # (kind, detail) for reporting
    edits = []     # (start, end, replacement)

    spans = protected_spans(body)
    link_spans = [(l[0], l[1]) for l in links]

    # consumed later-mention regions so two early links don't grab the same spot
    consumed = []

    for s, e, anchor, url in links:
        if s >= foff:
            continue
        norm = url.rstrip("/") + "/"
        phrase = phrase_visible(anchor)
        # A: a post-floor link to same target already exists -> unwrap early
        if norm in placed:
            edits.append((s, e, anchor))
            actions.append(("UNWRAP (dup post-floor exists)", phrase, url))
            continue
        # B: find first clean later mention of the phrase
        moved = False
        if phrase:
            pat = re.compile(r"\b" + re.escape(phrase) + r"\b", re.I)
            for m in pat.finditer(body, foff):
                ms, me = m.start(), m.end()
                if in_spans(ms, spans) or in_spans(ms, link_spans):
                    continue
                if any(cs <= ms < ce for cs, ce in consumed):
                    continue
                # wrap later mention, unwrap early one
                edits.append((ms, me, f"[{m.group(0)}]({url})"))
                edits.append((s, e, anchor))
                consumed.append((ms, me))
                placed.add(norm)
                actions.append((f"MOVE w-> {visible_words(body[:ms])}", phrase, url))
                moved = True
                break
        if not moved:
            actions.append(("LEFT (no later mention)", phrase, url))

    if apply and edits:
        for st, en, rep in sorted(edits, key=lambda x: -x[0]):
            body = body[:st] + rep + body[en:]
        path.write_text(fm + body, encoding="utf-8")

    return actions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--slug")
    args = ap.parse_args()

    files = sorted(BLOGS.glob("*.md"))
    if args.slug:
        files = [f for f in files if f.stem == args.slug]

    moved = unwrapped = left = 0
    for f in files:
        acts = process(f, args.apply)
        if not acts:
            continue
        print(f"\n### {f.name}")
        for kind, phrase, url in acts:
            print(f"   [{kind}]  {phrase!r} -> {url}")
            if kind.startswith("MOVE"):
                moved += 1
            elif kind.startswith("UNWRAP"):
                unwrapped += 1
            else:
                left += 1
    print("\n" + "=" * 60)
    verb = "APPLIED" if args.apply else "DRY-RUN"
    print(f"{verb}: {moved} moved, {unwrapped} unwrapped (dup), {left} left in place")


if __name__ == "__main__":
    main()
