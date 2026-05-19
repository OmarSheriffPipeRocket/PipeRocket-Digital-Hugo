#!/usr/bin/env python3
"""
Audit + optimize static images.

Stages
------
1.  Walk every static/images/**/*.{png,jpg,jpeg} (>= 50 KB).
2.  For each, grep across the source tree (assets/, content/, layouts/,
    data/, hugo.toml, static/) for any reference to the filename. We
    match both bare filename ("car-bg.png") and the full URL form
    ("/images/.../car-bg.png").
3.  Classify each file:
       USED  → has at least one reference, will be converted to WebP and
               every reference rewritten to .webp.
       DEAD  → zero references, listed for the user to delete.
4.  Convert in-place: PNG/JPG → .webp via cwebp (q=82, sharp YUV).
5.  Walk every source file and replace .png → .webp / .jpg → .webp on
    the converted set.
6.  Delete the original PNG/JPG only when its WebP exists.

Safety
------
- Only converts files that ARE referenced. Dead files are reported but
  not touched. The user can review and delete manually.
- Skips icons, favicons, og:image source PNGs (we keep PNG for those).
- Refuses to overwrite an existing .webp if the source is older.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "static" / "images"
SEARCH_DIRS = [
    ROOT / "assets",
    ROOT / "content",
    ROOT / "layouts",
    ROOT / "data",
    ROOT / "static",  # SVGs may reference PNG fallbacks
]
EXTRA_FILES = [ROOT / "hugo.toml"]
SOURCE_EXTS = (".html", ".md", ".css", ".scss", ".toml", ".json", ".yaml", ".yml", ".svg", ".js")

# Files we deliberately keep as PNG (favicons, social cards, etc.)
KEEP_PNG = {
    "favicon-16.png",
    "favicon-32.png",
    "apple-touch-icon.png",
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
    "mstile-150x150.png",
    "piperocket-logo@800.png",
}

# Minimum file size to consider (bytes). Tiny icons + sprites stay as-is.
MIN_SIZE = 50 * 1024

# WebP quality (82 = visually lossless for screenshots/photos)
WEBP_QUALITY = 82


def all_source_files():
    """Yield every source file we should grep through."""
    seen = set()
    for d in SEARCH_DIRS:
        if not d.is_dir():
            continue
        for p in d.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in SOURCE_EXTS:
                continue
            if p in seen:
                continue
            seen.add(p)
            yield p
    for f in EXTRA_FILES:
        if f.is_file() and f not in seen:
            seen.add(f)
            yield f


def build_search_index():
    """Read every source file into memory once for fast grepping."""
    return {p: p.read_text(encoding="utf-8", errors="ignore") for p in all_source_files()}


def find_refs(filename, full_url, index):
    """Return list of (file, snippet) where filename or full_url appears."""
    hits = []
    for p, text in index.items():
        if filename in text or full_url in text:
            hits.append(p)
    return hits


def convert_to_webp(src: Path) -> bool:
    """Run cwebp. Returns True on success."""
    dst = src.with_suffix(".webp")
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return True  # already converted
    try:
        # -m 6 = highest compression effort
        # -sharp_yuv = better edges on screenshots / logos
        subprocess.check_call([
            "cwebp", "-quiet", "-m", "6", "-sharp_yuv",
            "-q", str(WEBP_QUALITY),
            str(src), "-o", str(dst),
        ])
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  cwebp failed for {src}: {e}", file=sys.stderr)
        return False


def rewrite_refs(filename_png, filename_webp, full_url_png, full_url_webp, index):
    """Replace every .png ref with .webp ref. Persists changes to disk."""
    touched = 0
    for p, text in index.items():
        new_text = text
        if filename_png in new_text:
            new_text = new_text.replace(filename_png, filename_webp)
        if full_url_png != filename_png and full_url_png in new_text:
            new_text = new_text.replace(full_url_png, full_url_webp)
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            index[p] = new_text
            touched += 1
    return touched


def main():
    if not IMAGES.is_dir():
        sys.exit(f"static/images/ not found at {IMAGES}")

    print("Building source-file index for grep…")
    index = build_search_index()
    print(f"  indexed {len(index)} files")

    used = []  # (path, refs)
    dead = []  # path
    saved_total = 0

    for img in sorted(IMAGES.rglob("*")):
        if not img.is_file():
            continue
        if img.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        if img.name in KEEP_PNG:
            continue
        if img.stat().st_size < MIN_SIZE:
            continue

        rel = img.relative_to(ROOT)
        filename = img.name
        # URL form: /images/<relative under static/images>
        url_rel = "/images/" + str(img.relative_to(IMAGES)).replace(os.sep, "/")
        refs = find_refs(filename, url_rel, index)

        if not refs:
            dead.append(img)
            continue
        used.append((img, refs, url_rel))

    print(f"\nFound {len(used)} used images >= 50KB and {len(dead)} dead images.")

    # ----- Convert USED images -----
    if used:
        print(f"\nConverting {len(used)} used images to WebP…")
        for img, refs, url_rel in used:
            before = img.stat().st_size
            if not convert_to_webp(img):
                continue
            webp = img.with_suffix(".webp")
            after = webp.stat().st_size
            saved = before - after
            saved_total += saved
            # Update every reference
            new_filename = webp.name
            new_url = "/images/" + str(webp.relative_to(IMAGES)).replace(os.sep, "/")
            touched = rewrite_refs(img.name, new_filename, url_rel, new_url, index)
            # Remove the original PNG
            img.unlink()
            print(
                f"  ✓ {url_rel}  "
                f"{before//1024}KB → {after//1024}KB  "
                f"(saved {saved//1024}KB, {touched} files updated)"
            )

    # ----- Report dead images -----
    if dead:
        dead_total = sum(p.stat().st_size for p in dead)
        print(f"\n{len(dead)} images appear unused — totalling {dead_total//(1024*1024)} MB.")
        for p in sorted(dead, key=lambda x: -x.stat().st_size)[:30]:
            print(f"  · {p.relative_to(ROOT)}  ({p.stat().st_size//1024}KB)")
        if len(dead) > 30:
            print(f"  … and {len(dead) - 30} more")
        # Write list to a file so the user can rm them later
        dead_list = ROOT / "scripts" / "dead-images.txt"
        with open(dead_list, "w") as fh:
            for p in dead:
                fh.write(str(p.relative_to(ROOT)) + "\n")
        print(f"\nFull list written to {dead_list.relative_to(ROOT)}")
        print("Review and remove with:  xargs -I {} rm {} < scripts/dead-images.txt")

    print(f"\nDone. Saved {saved_total // (1024*1024)} MB on converted images.")


if __name__ == "__main__":
    main()
