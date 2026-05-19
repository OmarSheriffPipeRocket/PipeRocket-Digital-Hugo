#!/usr/bin/env python3
"""
Convert every infographic SVG to a fully cream-on-cream design.

The previous infographics used dark slabs (#282828 for the header band,
#0D0D0D / #282828 for interior "highlight" cards) which clashed with
the site's cream theme. This script does two things on every SVG:

1. Replaces dark background fills:
     #282828 → #E8E4DA   (cream-2, warm differentiation, no dark slab)
     #0D0D0D → #E8E4DA   (interior dark cards)

2. Walks the XML, finds every <text> element nested inside a parent
   <g> that *previously* had a dark rect fill, and flips its colour
   from white to dark — so the text stays legible on the new cream
   card. White-on-dark patterns also handled for rgba(255,255,255,X).

Header band specifically: the top `<rect x="0" y="0" width="…" height="110"`
band was visible as a dark strip across the top of every infographic.
We make it light cyan tint (matches the site's section-header pattern)
so the title + eyebrow stay easy to scan.

Run multiple times — idempotent.
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "static" / "images" / "blog-infographics"

ET.register_namespace("", "http://www.w3.org/2000/svg")
NS = "{http://www.w3.org/2000/svg}"


def is_dark(fill: str) -> bool:
    """Return True if the fill value is one of the dark theme colours we're
    replacing. Accepts hex (any case) and rgba forms."""
    if not fill:
        return False
    f = fill.strip().lower()
    if f in ("#282828", "#0d0d0d"):
        return True
    # rgba(40,40,40,X) or rgba(13,13,13,X)
    m = re.match(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,", f)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if (r, g, b) in {(40, 40, 40), (13, 13, 13)}:
            return True
    return False


def is_white(fill: str) -> bool:
    if not fill:
        return False
    f = fill.strip().lower()
    if f in ("#ffffff", "#fff", "white"):
        return True
    m = re.match(r"rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*([\d.]+)\s*\)", f)
    return bool(m)


def flip_white_to_dark(fill: str) -> str:
    """Turn a white text fill into a dark equivalent."""
    if not fill:
        return fill
    f = fill.strip().lower()
    if f in ("#ffffff", "#fff", "white"):
        return "#0D0D0D"
    m = re.match(r"rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*([\d.]+)\s*\)", f)
    if m:
        alpha = m.group(1)
        return f"rgba(13, 13, 13, {alpha})"
    return fill


def banding_replacement(width: int):
    """Build a cream-on-cream replacement for the standard top header band."""
    # We keep the same height + position, just lighter visual treatment.
    return f'<rect x="0" y="0" width="{width}" height="110" fill="#E8E4DA"/>'


def transform_svg(path: Path):
    text = path.read_text(encoding="utf-8")
    changes = 0

    # 1. Standard top header band — full-width #282828 rect at the top.
    #    Replace with cream-2 banner. Keeps the same visual rhythm but
    #    drops the harsh dark slab.
    band_re = re.compile(
        r'(<rect\s+x="0"\s+y="0"\s+width="(\d+)"\s+height="110"\s+)fill="#282828"\s*/>',
        re.IGNORECASE,
    )

    def band_repl(m):
        nonlocal changes
        changes += 1
        return f'{m.group(1)}fill="#E8E4DA"/>'

    text = band_re.sub(band_repl, text)

    # 2. Parse the resulting XML and flip text colours inside any <g> that
    #    has a dark rect as a direct child (e.g. cards that used to be
    #    dark slabs).
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        print(f"  ⚠️  XML parse failed for {path.name}: {e}", file=sys.stderr)
        # Fall back to non-DOM replacements: just blanket-swap dark fills
        # and white text. Less precise but still much improved.
        text = text.replace('fill="#282828"', 'fill="#E8E4DA"')
        text = text.replace('fill="#0D0D0D"', 'fill="#E8E4DA"')
        # Don't blanket-flip white text — risky without context.
        path.write_text(text, encoding="utf-8")
        return changes + 2

    # Walk: find every <g> that has a direct <rect> with a dark fill.
    # For those <g>s, flip white text fills to dark.
    def collect_dark_groups(parent, into):
        for child in list(parent):
            if child.tag == f"{NS}g":
                # Does this group have a direct dark rect child?
                has_dark_rect = any(
                    c.tag == f"{NS}rect" and is_dark(c.get("fill", ""))
                    for c in list(child)
                )
                if has_dark_rect:
                    into.append(child)
                collect_dark_groups(child, into)

    dark_groups = []
    collect_dark_groups(root, dark_groups)

    # Inside each "previously dark" group:
    #   · change the dark rect's fill to #E8E4DA (cream-2)
    #   · add a cyan stroke if the rect didn't already have one
    #   · flip every white text fill to dark
    for g in dark_groups:
        for el in g.iter():
            if el.tag == f"{NS}rect" and is_dark(el.get("fill", "")):
                el.set("fill", "#E8E4DA")
                # If no stroke already, add a soft cyan accent border.
                if not el.get("stroke"):
                    el.set("stroke", "#0CC6F1")
                    el.set("stroke-width", "1.5")
                changes += 1
            elif el.tag == f"{NS}text":
                fill = el.get("fill")
                if is_white(fill):
                    el.set("fill", flip_white_to_dark(fill))
                    changes += 1
                # Inline tspans
                for tspan in el.iter(f"{NS}tspan"):
                    tfill = tspan.get("fill")
                    if is_white(tfill):
                        tspan.set("fill", flip_white_to_dark(tfill))
                        changes += 1

    # 3. Also handle standalone dark rects (NOT inside a <g> that had any
    #    other dark rect — e.g. the header-band rect inside <g> transform
    #    blocks).  Walk top-level dark rects.
    for el in root.iter(f"{NS}rect"):
        if is_dark(el.get("fill", "")):
            el.set("fill", "#E8E4DA")
            if not el.get("stroke"):
                el.set("stroke", "#0CC6F1")
                el.set("stroke-width", "1.5")
            changes += 1

    # Also pickup any top-level <text> with white fill positioned within
    # the header band (y < 110). These were on the dark slab — flip them.
    for el in root.iter(f"{NS}text"):
        y = el.get("y", "0")
        try:
            yval = float(y)
        except ValueError:
            yval = 0
        if yval < 115 and is_white(el.get("fill", "")):
            el.set("fill", flip_white_to_dark(el.get("fill")))
            changes += 1

    if changes:
        # Serialize back. Preserve the XML declaration.
        new_text = ET.tostring(root, encoding="unicode")
        path.write_text(new_text, encoding="utf-8")

    return changes


def main():
    if not SVG_DIR.is_dir():
        sys.exit(f"static/images/blog-infographics/ not found at {SVG_DIR}")
    total_files = 0
    total_changes = 0
    for svg in sorted(SVG_DIR.glob("*.svg")):
        n = transform_svg(svg)
        if n:
            total_files += 1
            total_changes += n
            print(f"  {svg.name}  →  {n} changes")
        else:
            print(f"  {svg.name}  (no change)")
    print(f"\nDone. {total_files} files updated, {total_changes} colour changes applied.")


if __name__ == "__main__":
    main()
