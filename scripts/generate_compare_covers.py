#!/usr/bin/env python3
"""Generate 1200x630 cream covers for /compare/ pages.

Each cover is a split editorial card: "PipeRocket Digital" on the
left, "vs" mark in the centre, competitor name on the right, with the
PipeRocket brand chip pinned to the bottom-left.

Reads each .md in content/compare/, derives the competitor from the
title ("PipeRocket Digital vs X" → X), and writes
static/images/compare-covers/<slug>.webp.

Idempotent — skips slugs whose cover file already exists unless --force.
Pass --update-frontmatter to also rewrite each page's featuredImage."""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content" / "compare"
OUT_DIR = ROOT / "static" / "images" / "compare-covers"

FONT_TITLE = str(ROOT / "static" / "fonts" / "IvyPresto-Headline-SemiBold.otf")
FONT_BRAND = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
LOGO_PNG = ROOT / "static" / "images" / "piperocket-logo@800.png"

W, H = 1200, 630
LOGO_DISPLAY_W = 220

BG_TOP_LEFT     = (250, 247, 238)
BG_BOTTOM_RIGHT = (242, 237, 224)
TITLE_COLOR     = ( 14,  20,  48)
EYEBROW_COLOR   = ( 14,  20,  48)
TAGLINE_COLOR   = ( 90,  87,  80)
ACCENT          = (255,   0,  37)   # PipeRocket red — used for the "vs" mark

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def read_title(md: Path) -> str:
    text = md.read_text()
    m = FRONTMATTER_RE.search(text)
    if not m:
        return md.stem
    for line in m.group(1).splitlines():
        if line.startswith("title:"):
            return line[len("title:"):].strip().strip('"').strip("'")
    return md.stem


def split_versus(title: str) -> tuple[str, str]:
    """'PipeRocket Digital vs KlientBoost' → ('PipeRocket Digital', 'KlientBoost').
    Falls back to 'PipeRocket' if there's no 'vs' separator."""
    # Drop any trailing ': subheading'
    t = re.split(r"\s*:\s*", title, maxsplit=1)[0]
    m = re.split(r"\s+vs\.?\s+", t, maxsplit=1, flags=re.IGNORECASE)
    if len(m) == 2:
        return m[0].strip(), m[1].strip()
    return "PipeRocket Digital", t.strip()


def set_frontmatter_field(md: Path, key: str, value: str) -> bool:
    text = md.read_text()
    m = FRONTMATTER_RE.search(text)
    if not m:
        return False
    fm = m.group(1)
    new_line = f'{key}: "{value}"'
    rx = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    if rx.search(fm):
        new_fm = rx.sub(new_line, fm)
    else:
        new_fm = fm.rstrip() + "\n" + new_line
    if new_fm == fm:
        return False
    md.write_text(text[: m.start()] + f"---\n{new_fm}\n---\n" + text[m.end():])
    return True


# ──────────────────── PIL composition ──────────────────────────────────────

def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def build_gradient() -> Image.Image:
    img = Image.new("RGB", (W, H), BG_TOP_LEFT)
    px = img.load()
    for y in range(H):
        for x in range(W):
            t = (x / W + y / H) / 2
            px[x, y] = _lerp(BG_TOP_LEFT, BG_BOTTOM_RIGHT, t)
    return img


def draw_split_accent(canvas: Image.Image) -> None:
    """Soft accent washes — left wash in PipeRocket red, right wash in
    a contrasting cool blue — so the two halves feel like opposing sides
    of the comparison."""
    left = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(left)
    ld.ellipse((-120, int(H * 0.20), 480, int(H * 0.20) + 540),
               fill=(255, 110, 100, 60))
    left = left.filter(ImageFilter.GaussianBlur(radius=140))
    canvas.alpha_composite(left)

    right = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(right)
    rd.ellipse((W - 480, int(H * 0.25), W + 120, int(H * 0.25) + 540),
               fill=(110, 180, 255, 60))
    right = right.filter(ImageFilter.GaussianBlur(radius=140))
    canvas.alpha_composite(right)


def draw_grid_texture(canvas: Image.Image) -> None:
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(grid)
    for i in range(-H, W, 32):
        d.line([(i, 0), (i + H, H)], fill=(40, 32, 20, 8), width=1)
    canvas.alpha_composite(grid)


def draw_bottom_rule(canvas: Image.Image) -> None:
    ImageDraw.Draw(canvas).line(
        [(80, H - 120), (W - 80, H - 120)],
        fill=(217, 213, 201, 200),
        width=1,
    )


def paste_logo_top_right(canvas: Image.Image) -> None:
    logo = Image.open(LOGO_PNG).convert("RGBA")
    new_w = LOGO_DISPLAY_W
    new_h = int(logo.height * (new_w / logo.width))
    logo = logo.resize((new_w, new_h), Image.LANCZOS)
    canvas.alpha_composite(logo, (W - 80 - new_w, 80))


def fit_text(text: str, max_w: int, sizes: list[int]) -> tuple[ImageFont.FreeTypeFont, str]:
    for s in sizes:
        f = ImageFont.truetype(FONT_TITLE, s)
        if f.getlength(text) <= max_w:
            return f, text
    # Couldn't fit — return smallest and let it clip slightly.
    return ImageFont.truetype(FONT_TITLE, sizes[-1]), text


def compose(slug: str, left_name: str, right_name: str, out_path: Path) -> None:
    base = build_gradient().convert("RGBA")
    draw_split_accent(base)
    draw_grid_texture(base)
    draw_bottom_rule(base)
    paste_logo_top_right(base)

    draw = ImageDraw.Draw(base)

    # Eyebrow tag top-left
    eyebrow_font = ImageFont.truetype(FONT_BRAND, 18)
    eyebrow_y = 80
    sq = 12
    draw.rectangle((80, eyebrow_y + 3, 80 + sq, eyebrow_y + 3 + sq),
                   fill=ACCENT + (240,))
    draw.text((80 + sq + 10, eyebrow_y), "AGENCY COMPARISON",
              font=eyebrow_font, fill=EYEBROW_COLOR + (235,))

    # Layout the two names + the "vs" mark.
    # Stack them vertically: NAME A on top, vs (red, italic-ish big), NAME B below.
    center_y = (H - 150) // 2 + 30
    name_size_pool = [78, 70, 62, 54, 48, 42]

    # Left name (top line)
    left_font, _ = fit_text(left_name, W - 160, name_size_pool)
    left_text = left_name
    lw = left_font.getlength(left_text)
    draw.text(((W - lw) / 2, center_y - left_font.size - 50),
              left_text, font=left_font, fill=TITLE_COLOR + (255,))

    # "vs" mark — IvyPresto italic-feel using regular semibold + red
    vs_font = ImageFont.truetype(FONT_TITLE, 60)
    vs_w = vs_font.getlength("vs")
    draw.text(((W - vs_w) / 2, center_y - 28),
              "vs", font=vs_font, fill=ACCENT + (240,))

    # Right name (bottom line)
    right_font, _ = fit_text(right_name, W - 160, name_size_pool)
    rw = right_font.getlength(right_name)
    draw.text(((W - rw) / 2, center_y + 50),
              right_name, font=right_font, fill=TITLE_COLOR + (255,))

    # Tagline at bottom-left
    tagline_font = ImageFont.truetype(FONT_BRAND, 16)
    draw.text((80, H - 80),
              "B2B SaaS Marketing  ·  piperocket.digital",
              font=tagline_font, fill=TAGLINE_COLOR + (230,))

    base.convert("RGB").save(out_path, "WEBP", quality=85, method=6)


def process(slug: str, force: bool, update_frontmatter: bool) -> bool:
    md = CONTENT_DIR / f"{slug}.md"
    if not md.exists():
        return False
    title = read_title(md)
    left, right = split_versus(title)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{slug}.webp"
    if out.exists() and not force:
        print(f"[skip] {slug} → exists")
        if update_frontmatter:
            set_frontmatter_field(md, "featuredImage", f"/images/compare-covers/{slug}.webp")
        return False
    print(f"[{slug}]  {left}  vs  {right}")
    compose(slug, left, right, out)
    print(f"   ✓ {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB)")
    if update_frontmatter:
        if set_frontmatter_field(md, "featuredImage", f"/images/compare-covers/{slug}.webp"):
            print(f"   ✓ featuredImage written to {md.name}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--update-frontmatter", action="store_true")
    ap.add_argument("--only")
    args = ap.parse_args()

    slugs = [args.only] if args.only else sorted(
        p.stem for p in CONTENT_DIR.glob("*.md") if p.stem != "_index"
    )
    made = 0
    for s in slugs:
        if process(s, args.force, args.update_frontmatter):
            made += 1
    print(f"\n=== Summary === processed:{len(slugs)} new:{made}")


if __name__ == "__main__":
    main()
