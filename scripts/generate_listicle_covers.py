#!/usr/bin/env python3
"""Generate 1200x630 listicle cover images — pure-PIL, no API.

Each cover is composed entirely in Pillow:
  • Dark navy gradient base (top-left → bottom-right).
  • Two soft blurred "orb" shapes in a niche-specific accent color so
    cybersecurity covers feel different from healthtech covers without
    breaking brand consistency.
  • A thin diagonal grid texture for editorial depth.
  • Eyebrow tag (top-left) + IvyPresto serif title (wrapped, 2-4 lines)
    + small PipeRocket Digital brand chip (bottom-left).

Output: static/images/listicle-covers/<slug>.webp at 1200×630
(Open Graph standard — also looks good as the index thumbnail).

Idempotent. Re-runs skip slugs whose .webp already exists unless --force.

Usage:
  python3 scripts/generate_listicle_covers.py --samples
  python3 scripts/generate_listicle_covers.py            # all 34
  python3 scripts/generate_listicle_covers.py --force
  python3 scripts/generate_listicle_covers.py --update-frontmatter
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    print("✗ pip install pillow")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content" / "list"
OUT_DIR = ROOT / "static" / "images" / "listicle-covers"

FONT_TITLE = str(ROOT / "static" / "fonts" / "IvyPresto-Headline-SemiBold.otf")
FONT_BRAND = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
LOGO_PNG = ROOT / "static" / "images" / "piperocket-logo@800.png"

W, H = 1200, 630
LOGO_DISPLAY_W = 220  # px on the cover; original is 800x127 @2x

# Brand base colors — cream editorial style.
BG_TOP_LEFT     = (250, 247, 238)    # cream
BG_BOTTOM_RIGHT = (242, 237, 224)    # warmer beige
TITLE_COLOR     = ( 14,  20,  48)    # deep navy, near-black
EYEBROW_COLOR   = ( 14,  20,  48)    # same navy (color comes from accent rule)
BRAND_COLOR     = ( 14,  20,  48)
TAGLINE_COLOR   = ( 90,  87,  80)    # site --pr-text-secondary

# ──────────────────── Niche mapping ─────────────────────────────────────────
# (eyebrow label, accent RGB) per niche key.
NICHES = {
    "b2b-ppc":             ("B2B PPC",                (255, 170,  80)),   # warm amber
    "saas-ppc":            ("SaaS PPC",               (255, 140,  90)),   # coral
    "google-ads":          ("Google Ads",             (66, 133, 244)),    # google blue
    "saas-seo":            ("SaaS SEO",               ( 90, 200, 255)),   # cyan
    "b2b-seo":             ("B2B SEO",                ( 80, 180, 255)),   # azure
    "enterprise-seo":      ("Enterprise SEO",         (110, 160, 220)),   # steel blue
    "fintech-seo":         ("Fintech SEO",            (250, 200,  90)),   # gold
    "technical-seo":       ("Technical SEO",          (110, 220, 210)),   # teal
    "content-marketing":   ("Content Marketing",      (200, 160, 255)),   # lavender
    "saas-content-marketing": ("SaaS Content",        (180, 180, 255)),   # periwinkle
    "demand-gen":          ("Demand Gen",             (255, 100, 130)),   # rose
    "lead-gen":            ("Lead Gen",               (255, 120, 110)),   # coral-pink
    "b2b-marketing":       ("B2B Marketing",          (140, 200, 255)),
    "saas-marketing":      ("SaaS Marketing",         ( 90, 220, 200)),
    "growth-marketing":    ("Growth Marketing",       (130, 240, 170)),   # mint
    "performance-marketing": ("Performance Marketing",(255, 200,  90)),
    "b2b-advertising":     ("B2B Advertising",        (255, 130, 180)),
    "linkedin":            ("LinkedIn Marketing",     ( 14, 118, 168)),   # linkedin blue
    "link-building":       ("Link Building",          (200, 220, 110)),   # chartreuse
    "aeo":                 ("AEO",                    (160, 130, 255)),   # ai violet
    "geo":                 ("GEO",                    (180, 110, 255)),   # gen-ai violet
    "saas-geo":            ("SaaS GEO",               (190, 130, 255)),
    "cybersecurity":       ("Cybersecurity",          (255, 100,  90)),   # red
    "fintech-marketing":   ("Fintech Marketing",      (240, 190,  80)),
    "edtech":              ("EdTech",                 (255, 170, 110)),   # warm orange
    "devtools":            ("DevTools",               (160, 130, 255)),   # dev purple
    "healthtech":          ("HealthTech",             (120, 230, 170)),   # mint-green
    "hrtech":              ("HR Tech",                (255, 160, 200)),   # pink
    "martech":             ("MarTech",                (130, 200, 240)),
    "proptech":            ("PropTech",               (180, 220, 130)),   # olive
    "default":             ("B2B SaaS Reviews",       (110, 200, 255)),
}

SLUG_NICHE = {
    "11-best-saas-growth-marketing-agencies-2026": "growth-marketing",
    "12-best-answer-engine-optimization-aeo-agencies-in-the-usa-2026": "aeo",
    "12-best-saas-seo-agencies-for-startups-2026": "saas-seo",
    "best-affordable-b2b-ppc-agencies": "b2b-ppc",
    "best-b2b-content-marketing-agencies": "content-marketing",
    "best-b2b-google-ads-agencies": "google-ads",
    "best-b2b-lead-generation-companies": "lead-gen",
    "best-b2b-marketing-agencies": "b2b-marketing",
    "best-b2b-seo-agencies-2": "b2b-seo",
    "best-cybersecurity-marketing-agencies": "cybersecurity",
    "best-devtools-marketing-agencies-in-2026": "devtools",
    "best-edtech-marketing-agencies": "edtech",
    "best-enterprise-seo-agencies": "enterprise-seo",
    "best-geo-agencies": "geo",
    "best-healthtech-marketing-agencies-in-2026": "healthtech",
    "best-hr-tech-marketing-agencies": "hrtech",
    "best-linkedin-marketing-agencies": "linkedin",
    "best-martech-marketing-agencies": "martech",
    "best-proptech-marketing-agencies": "proptech",
    "best-saas-content-marketing-agencies": "saas-content-marketing",
    "best-saas-geo-agencies": "saas-geo",
    "best-saas-marketing-agencies-2026": "saas-marketing",
    "best-saas-ppc-agencies": "saas-ppc",
    "best-saas-seo-agencies-2": "saas-seo",
    "best-saas-seo-agencies": "saas-seo",
    "preview-best-saas-seo-agencies": "martech",
    "the-10-best-saas-link-building-agencies-in-2026": "link-building",
    "the-11-best-b2b-demand-generation-agencies-in-2026": "demand-gen",
    "the-11-best-technical-seo-agencies-for-2026": "technical-seo",
    "the-best-b2b-advertising-agencies-2026-rankings": "b2b-advertising",
    "top-b2b-ppc-agencies": "b2b-ppc",
    "top-fintech-marketing-agencies": "fintech-marketing",
    "top-fintech-seo-agencies": "fintech-seo",
    "top-performance-marketing-agencies": "performance-marketing",
}

SAMPLE_SLUGS = [
    "best-cybersecurity-marketing-agencies",
    "best-healthtech-marketing-agencies-in-2026",
    "best-affordable-b2b-ppc-agencies",
]


# ──────────────────── Front-matter helpers ──────────────────────────────────

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def read_frontmatter(md_path: Path) -> dict:
    text = md_path.read_text()
    m = FRONTMATTER_RE.search(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^(\w+):\s*(.*)$", line)
        if not kv:
            continue
        val = kv.group(2).strip().strip('"').strip("'")
        fm[kv.group(1)] = val
    return fm


def set_frontmatter_field(md_path: Path, key: str, value: str) -> bool:
    text = md_path.read_text()
    m = FRONTMATTER_RE.search(text)
    if not m:
        return False
    fm = m.group(1)
    new_line = f'{key}: "{value}"'
    key_re = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    if key_re.search(fm):
        new_fm = key_re.sub(new_line, fm)
    else:
        new_fm = fm.rstrip() + "\n" + new_line
    if new_fm == fm:
        return False
    new_text = text[: m.start()] + f"---\n{new_fm}\n---\n" + text[m.end():]
    md_path.write_text(new_text)
    return True


# ──────────────────── Composition ───────────────────────────────────────────

def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def build_gradient() -> Image.Image:
    """Diagonal navy gradient base — top-left dark, bottom-right slightly
    lighter so the lower portion has enough lift for the brand chip."""
    img = Image.new("RGB", (W, H), BG_TOP_LEFT)
    pixels = img.load()
    for y in range(H):
        for x in range(W):
            # diagonal distance 0..1
            t = (x / W + y / H) / 2
            pixels[x, y] = _lerp(BG_TOP_LEFT, BG_BOTTOM_RIGHT, t)
    return img


def draw_accent_shape(canvas: Image.Image, accent: tuple[int, int, int]) -> None:
    """One large soft accent wash plus a flat geometric arc — editorial,
    not glowy. Sits on the right two-thirds so the title (left) stays
    on the cream background where it reads cleanest."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    # Soft tint wash — a big ellipse in the accent at low opacity, blurred
    r = 360
    cx, cy = int(W * 0.85), int(H * 0.48)
    draw.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        fill=accent + (55,),
    )
    layer = layer.filter(ImageFilter.GaussianBlur(radius=110))
    canvas.alpha_composite(layer)

    # Crisp circle outline as a graphic accent (no fill)
    outline = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(outline)
    od.ellipse(
        (int(W * 0.72), int(H * 0.10),
         int(W * 0.72) + 460, int(H * 0.10) + 460),
        outline=accent + (180,),
        width=2,
    )
    # second smaller offset circle for layered depth
    od.ellipse(
        (int(W * 0.83), int(H * 0.52),
         int(W * 0.83) + 240, int(H * 0.52) + 240),
        outline=accent + (140,),
        width=2,
    )
    canvas.alpha_composite(outline)


def draw_grid_texture(canvas: Image.Image) -> None:
    """Faint diagonal grid lines for editorial paper texture."""
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid)
    step = 32
    for i in range(-H, W, step):
        # very faint warm-grey lines on the cream
        draw.line([(i, 0), (i + H, H)], fill=(40, 32, 20, 8), width=1)
    canvas.alpha_composite(grid)


def draw_bottom_rule(canvas: Image.Image) -> None:
    """Thin warm-grey rule across the bottom of the cover, ~120px in from
    the edge, anchoring the brand chip visually without darkening the
    background."""
    d = ImageDraw.Draw(canvas)
    d.line(
        [(80, H - 120), (W - 80, H - 120)],
        fill=(217, 213, 201, 200),  # --pr-line
        width=1,
    )


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if font.getlength(test) <= max_width:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def shorten_title(title: str) -> str:
    """Make over-long sub-titled listicle titles fit gracefully.
    Drops "My Picks for", "We Ranked", "I Ranked", "Ranking", parentheticals."""
    t = title
    # strip leading "My picks for the", "We ranked the top", "I ranked the"
    t = re.sub(r'^(My Picks for|We Ranked|I Ranked|Ranking)\s+(the|The)?\s*', '', t)
    # strip leading "Top N" if title also includes "Best"
    t = re.sub(r'\s*\(2026 Rankings\)\s*$', ' 2026', t)
    return t.strip()


def paste_logo_top_right(canvas: Image.Image) -> None:
    """Composite the PipeRocket logo PNG into the top-right corner.
    Logo PNG is 800x127 with transparent BG; we scale it to LOGO_DISPLAY_W
    and place 80px from the right edge, 80px from the top."""
    logo = Image.open(LOGO_PNG).convert("RGBA")
    new_w = LOGO_DISPLAY_W
    new_h = int(logo.height * (new_w / logo.width))
    logo = logo.resize((new_w, new_h), Image.LANCZOS)
    x = W - 80 - new_w
    y = 80
    canvas.alpha_composite(logo, (x, y))


def compose(slug: str, title: str, niche_key: str, out_path: Path) -> None:
    eyebrow, accent = NICHES.get(niche_key, NICHES["default"])

    base = build_gradient().convert("RGBA")
    draw_accent_shape(base, accent)
    draw_grid_texture(base)
    draw_bottom_rule(base)
    paste_logo_top_right(base)

    draw = ImageDraw.Draw(base)

    # Eyebrow tag (small, uppercase, with thin accent rule beneath).
    eyebrow_font = ImageFont.truetype(FONT_BRAND, 18)
    eyebrow_y = 80
    eyebrow_text = eyebrow.upper()
    # Small accent square then eyebrow text in dark navy
    sq = 12
    draw.rectangle(
        (80, eyebrow_y + 3, 80 + sq, eyebrow_y + 3 + sq),
        fill=accent + (240,),
    )
    draw.text((80 + sq + 10, eyebrow_y), eyebrow_text, font=eyebrow_font,
              fill=EYEBROW_COLOR + (235,))

    # Title — IvyPresto SemiBold in deep navy. Downscale until it fits.
    title_text = shorten_title(title)
    for size in (78, 72, 66, 60, 54, 48):
        title_font = ImageFont.truetype(FONT_TITLE, size)
        lines = wrap_text(title_text, title_font, max_width=W - 160)
        if len(lines) <= 4:
            break
    line_h = title_font.size + 8
    total_h = line_h * len(lines)
    # Block centered vertically between eyebrow row and the bottom rule.
    block_top = eyebrow_y + 60
    block_bot = H - 140
    y = block_top + max(0, ((block_bot - block_top) - total_h) // 2)
    for line in lines:
        draw.text((80, y), line, font=title_font, fill=TITLE_COLOR + (255,))
        y += line_h

    # Bottom-left chip — just a short tagline, since the logo top-right
    # already establishes the brand. Stays below the thin rule.
    tagline_font = ImageFont.truetype(FONT_BRAND, 16)
    draw.text(
        (80, H - 80),
        "B2B SaaS Marketing  ·  piperocket.digital",
        font=tagline_font,
        fill=TAGLINE_COLOR + (230,),
    )

    base.convert("RGB").save(out_path, "WEBP", quality=85, method=6)


# ──────────────────── Driver ────────────────────────────────────────────────

def list_md_slugs() -> list[str]:
    slugs = []
    for f in CONTENT_DIR.glob("*.md"):
        if f.stem == "_index":
            continue
        slugs.append(f.stem)
    return sorted(slugs)


def process(slug: str, force: bool = False, update_frontmatter: bool = False) -> bool:
    md = CONTENT_DIR / f"{slug}.md"
    if not md.exists():
        print(f"[skip] {slug}: no .md found")
        return False
    fm = read_frontmatter(md)
    title = fm.get("title") or slug.replace("-", " ").title()
    niche_key = SLUG_NICHE.get(slug, "default")
    eyebrow, _ = NICHES.get(niche_key, NICHES["default"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{slug}.webp"
    if out_path.exists() and not force:
        print(f"[skip] {slug} → already exists")
        # still update frontmatter if requested
        if update_frontmatter:
            rel = f"/images/listicle-covers/{slug}.webp"
            if set_frontmatter_field(md, "featuredImage", rel):
                print(f"   ✓ updated featuredImage in {md.name}")
        return False

    print(f"[{slug}]  ({eyebrow})")
    print(f"   title: {title}")
    compose(slug, title, niche_key, out_path)
    size_kb = out_path.stat().st_size // 1024
    print(f"   ✓ {out_path.relative_to(ROOT)}  ({size_kb} KB)")
    if update_frontmatter:
        rel = f"/images/listicle-covers/{slug}.webp"
        if set_frontmatter_field(md, "featuredImage", rel):
            print(f"   ✓ updated featuredImage in {md.name}")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", action="store_true")
    ap.add_argument("--only", help="Process a single slug")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--update-frontmatter", action="store_true")
    args = ap.parse_args()

    if args.only:
        slugs = [args.only]
    elif args.samples:
        slugs = SAMPLE_SLUGS
    else:
        slugs = list_md_slugs()

    made = 0
    for slug in slugs:
        if process(slug, force=args.force, update_frontmatter=args.update_frontmatter):
            made += 1

    print(f"\n=== Summary ===")
    print(f"Processed: {len(slugs)}")
    print(f"New covers written: {made}")


if __name__ == "__main__":
    main()
