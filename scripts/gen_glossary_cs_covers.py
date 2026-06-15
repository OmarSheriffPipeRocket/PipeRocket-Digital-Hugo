"""
Option C — give glossary terms + case studies a real Article/OG image.

- og-default cover (site-wide fallback raster)
- glossary: featuredImage = existing infographic-1 (2400x1260) where present,
  else a generated 1200x630-class cover
- case studies: generated cover
Sets `featuredImage` in each page's frontmatter (only if absent).

Usage: python3 scripts/gen_glossary_cs_covers.py
"""

import re
from pathlib import Path

import generate_blog_cover as gbc

ROOT = Path(__file__).resolve().parent.parent
GLOSS = ROOT / "content" / "glossary"
CS = ROOT / "content" / "case-study"
IG_DIR = ROOT / "static" / "images" / "glossary-infographics"
GCOV = ROOT / "static" / "images" / "glossary-covers"
CCOV = ROOT / "static" / "images" / "case-study-covers"
GCOV.mkdir(parents=True, exist_ok=True)
CCOV.mkdir(parents=True, exist_ok=True)


def fm_get(text, key):
    m = re.search(rf'(?m)^{key}:\s*"?([^"\n]+?)"?\s*$', text)
    return m.group(1) if m else None


def fm_set_featured(path, value):
    """Insert featuredImage right after the opening --- if not already present."""
    t = path.read_text(encoding="utf-8")
    if re.search(r"(?m)^featuredImage:", t):
        return False
    t2 = t.replace("---\n", f'---\nfeaturedImage: "{value}"\n', 1)
    path.write_text(t2, encoding="utf-8")
    return True


def cover_title(title, term_style=True):
    """Short, bold-keyed cover title from a glossary/CS title."""
    base = re.split(r"[?:|]", title)[0].strip()
    if term_style:
        m = re.match(r"(?i)^(What (?:Is|Are)(?: an?| the)?)\s+(.+)$", base)
        if m:
            return f"{m.group(1)} **{m.group(2)}**"
    return base


def gen_cover(title, out):
    try:
        gbc.generate(title, out_path=str(out))
        return True
    except Exception as e:
        print(f"   ! cover gen failed for {out.name}: {str(e)[:60]}")
        return False


def main():
    # 1) og-default fallback raster
    og = ROOT / "static" / "images" / "og-default.webp"
    if not og.exists():
        gen_cover("PipeRocket **Digital** — B2B SaaS Marketing", og)
    print(f"og-default: {'ok' if og.exists() else 'MISSING'}")

    # 2) glossary
    used_ig = made = skipped = 0
    for f in sorted(GLOSS.glob("*.md")):
        if f.name == "_index.md":
            continue
        slug = f.stem
        t = f.read_text(encoding="utf-8")
        title = fm_get(t, "title") or slug
        ig = IG_DIR / f"{slug}-infographic-1.webp"
        if ig.exists():
            val = f"/images/glossary-infographics/{slug}-infographic-1.webp"; used_ig += 1
        else:
            out = GCOV / f"{slug}.webp"
            if not out.exists():
                gen_cover(cover_title(title), out)
            val = f"/images/glossary-covers/{slug}.webp"; made += 1
        if not fm_set_featured(f, val):
            skipped += 1
    print(f"glossary: {used_ig} via infographic, {made} via generated cover, {skipped} already had featuredImage")

    # 3) case studies
    cs_made = cs_skip = 0
    for f in sorted(CS.glob("*.md")):
        if f.name == "_index.md":
            continue
        slug = f.stem
        t = f.read_text(encoding="utf-8")
        title = fm_get(t, "metaTitle") or fm_get(t, "title") or slug
        out = CCOV / f"{slug}.webp"
        if not out.exists():
            gen_cover(cover_title(title, term_style=False), out)
        if fm_set_featured(f, f"/images/case-study-covers/{slug}.webp"):
            cs_made += 1
        else:
            cs_skip += 1
    print(f"case studies: {cs_made} set, {cs_skip} already had featuredImage")


if __name__ == "__main__":
    main()
