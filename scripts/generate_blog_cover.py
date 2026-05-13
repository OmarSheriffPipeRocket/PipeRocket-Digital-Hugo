#!/usr/bin/env python3
"""
Blog cover image generator for PipeRocket Digital.

Usage:
    python3 generate_blog_cover.py "Best **SaaS SEO** Agencies in 2026"
    python3 generate_blog_cover.py "Best **SaaS SEO** Agencies in 2026" --template 3
    python3 generate_blog_cover.py "Best **SaaS SEO** Agencies in 2026" --out /path/to/output.png

Wrap words in **bold** to render them in IvyPresto Headline SemiBold.
Without markers, all text uses IvyPresto Headline Light.

Templates 1–9 map to frames: 89 90 91 92 93 94 95 96 97
Default: random template.
"""

import os
import re
import random
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

TEMPLATES_DIR = "/Users/omarsheriff/Downloads/+ Piperocket website design (23)"
FONT_REGULAR  = "/Users/omarsheriff/Desktop/piperocket-site/static/fonts/IvyPresto-Headline-Light.otf"
FONT_BOLD     = "/Users/omarsheriff/Desktop/piperocket-site/static/fonts/IvyPresto-Headline-SemiBold.otf"
TEXT_COLOR    = (20, 20, 20)

TEMPLATE_FILES = [
    "Frame 89.png", "Frame 90.png", "Frame 91.png",
    "Frame 92.png", "Frame 93.png", "Frame 95.png",
    "Frame 96.png", "Frame 97.png", "Frame 98.png",
]

# Templates with a pre-drawn blue underline: (underline_y, line_number)
# line_number = 1 → underline acts as underline for the first line of text
# line_number = 2 → underline acts as underline for the second line of text
TEMPLATE_UNDERLINE = {
    "Frame 97.png": (134, 1),
    "Frame 96.png": (181, 2),
}

# Safe text zone (pixels) — 468×279 templates
ZONE_X1, ZONE_X2 = 35, 430
ZONE_Y1, ZONE_Y2 = 38, 245
ZONE_CY = (ZONE_Y1 + ZONE_Y2) // 2


def parse_segments(title: str):
    segments = []
    pattern = re.compile(r'\*\*(.+?)\*\*|([^*]+)')
    for m in pattern.finditer(title):
        if m.group(1):
            for word in m.group(1).split():
                segments.append((word, True))
        elif m.group(2):
            for word in m.group(2).split():
                if word:
                    segments.append((word, False))
    return segments


def word_wrap(segments, font_reg, font_bold, max_width):
    lines = []
    current_line = []
    current_w = 0
    space_w = font_reg.getlength(" ")

    for word, bold in segments:
        font = font_bold if bold else font_reg
        word_w = font.getlength(word)
        gap = space_w if current_line else 0
        if current_line and current_w + gap + word_w > max_width:
            lines.append(current_line)
            current_line = [(word, bold)]
            current_w = word_w
        else:
            current_line.append((word, bold))
            current_w += gap + word_w

    if current_line:
        lines.append(current_line)
    return lines


def render_line(draw, line, x_start, y, font_reg, font_bold, space_w):
    x = x_start
    for i, (word, bold) in enumerate(line):
        font = font_bold if bold else font_reg
        draw.text((x, y), word, font=font, fill=TEXT_COLOR)
        x += font.getlength(word)
        if i < len(line) - 1:
            x += space_w


def line_width(line, font_reg, font_bold, space_w):
    total = 0
    for i, (word, bold) in enumerate(line):
        font = font_bold if bold else font_reg
        total += font.getlength(word)
        if i < len(line) - 1:
            total += space_w
    return total


LONG_RATIO = 0.50       # line is "long" if its width exceeds this fraction of image width
CLEAR_THRESHOLD = 600   # illustration pixels allowed in a half before it's considered "occupied"


def illus_mask(img):
    """Return boolean mask of illustration pixels (dark, non-blue)."""
    arr = np.array(img.convert("RGB")).astype(int)
    lum = 0.299 * arr[:,:,0] + 0.587 * arr[:,:,1] + 0.114 * arr[:,:,2]
    not_blue = arr[:,:,2] < arr[:,:,0] + 60
    return (lum < 140) & not_blue


def check_overlap(illus, lines, img_width, img_height, font_reg, font_bold, space_w):
    """
    Rule: if line 0 (top) is long → top half of template must be clear.
          if line 1 (bottom) is long → bottom half must be clear.
    'Long' = line width > LONG_RATIO * image width.
    'Clear' = fewer than CLEAR_THRESHOLD illustration pixels in that half.
    Returns True if the template should be rejected.
    """
    mid = img_height // 2
    for i, line in enumerate(lines):
        lw = line_width(line, font_reg, font_bold, space_w)
        if lw / img_width < LONG_RATIO:
            continue
        region = illus[:mid, :] if i == 0 else illus[mid:, :]
        if region.sum() >= CLEAR_THRESHOLD:
            return True
    return False


def try_template(template_file, segments, font_reg, font_bold, space_w, ascent, descent, line_h, total_h, lines):
    """Load a template, check overlap rule, return (img, zone_cx, first_line_y) or None."""
    img = Image.open(os.path.join(TEMPLATES_DIR, template_file)).convert("RGBA")
    illus = illus_mask(img)

    zone_cx = img.width // 2
    underline = TEMPLATE_UNDERLINE.get(template_file)

    if underline is not None:
        underline_y, underline_line = underline
        first_line_y = underline_y - ascent - 4 - (underline_line - 1) * line_h
    else:
        first_line_y = ZONE_CY - total_h // 2

    if check_overlap(illus, lines, img.width, img.height, font_reg, font_bold, space_w):
        return None

    return img, zone_cx, first_line_y


def generate(title: str, template_num: int = None, out_path: str = None):
    # Build candidate list — requested template first, then others shuffled
    if template_num is not None:
        idx = max(0, min(template_num - 1, len(TEMPLATE_FILES) - 1))
        requested = TEMPLATE_FILES[idx]
        others = [f for f in TEMPLATE_FILES if f != requested]
        random.shuffle(others)
        candidates = [requested] + others
    else:
        candidates = TEMPLATE_FILES[:]
        random.shuffle(candidates)

    segments = parse_segments(title)
    max_width = ZONE_X2 - ZONE_X1

    for font_size in range(32, 10, -1):
        font_reg  = ImageFont.truetype(FONT_REGULAR, font_size)
        font_bold = ImageFont.truetype(FONT_BOLD,    font_size)
        space_w   = font_reg.getlength(" ")
        ascent, descent = font_reg.getmetrics()
        line_h = ascent + descent - 2
        lines = word_wrap(segments, font_reg, font_bold, max_width)
        total_h = len(lines) * line_h - 4
        if total_h <= (ZONE_Y2 - ZONE_Y1) and len(lines) <= 4:
            break

    result = None
    for template_file in candidates:
        result = try_template(template_file, segments, font_reg, font_bold, space_w, ascent, descent, line_h, total_h, lines)
        if result is not None:
            print(f"Using template: {template_file}")
            break

    if result is None:
        # Fallback: use the first candidate regardless
        template_file = candidates[0]
        img = Image.open(os.path.join(TEMPLATES_DIR, template_file)).convert("RGBA")
        zone_cx = img.width // 2
        underline = TEMPLATE_UNDERLINE.get(template_file)
        first_line_y = (ZONE_CY - total_h // 2) if underline is None else (underline[0] - ascent - 4 - (underline[1] - 1) * line_h)
        print(f"Warning: no clean template found, using {template_file}")
    else:
        img, zone_cx, first_line_y = result

    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        lw = line_width(line, font_reg, font_bold, space_w)
        x = zone_cx - lw // 2
        y = first_line_y + i * line_h
        render_line(draw, line, x, y, font_reg, font_bold, space_w)

    if out_path is None:
        safe_name = re.sub(r'[^\w\s-]', '', title.replace('**', '')).strip().replace(' ', '-').lower()
        out_path = os.path.join(TEMPLATES_DIR, f"{safe_name}.png")

    img.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"Saved: {out_path}  (template: {template_file})")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PipeRocket blog cover image.")
    parser.add_argument("title", help='Blog title. Wrap bold words in **double stars**.')
    parser.add_argument("--template", type=int, choices=range(1, 10), metavar="1-9",
                        help="Template number 1–9 (default: random)")
    parser.add_argument("--out", help="Output file path (default: auto-named in templates dir)")
    args = parser.parse_args()

    generate(args.title, template_num=args.template, out_path=args.out)
