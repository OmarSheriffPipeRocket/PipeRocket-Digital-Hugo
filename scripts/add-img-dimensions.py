#!/usr/bin/env python3
"""
Add explicit width/height attributes to all <img> tags in homepage
templates, reading the actual dimensions from each image file.

Why: CLS prevention. Without width/height, browsers reserve no space for
images until they download — content below shifts when each one paints.
With dimensions, browsers reserve the correct aspect ratio upfront.

Skips images that already have width/height. Skips template syntax srcs.

Usage:
  python3 scripts/add-img-dimensions.py
  python3 scripts/add-img-dimensions.py --dry-run
"""
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
IDENTIFY = "/opt/homebrew/bin/identify"

# Templates to process. Add more as needed.
TARGET_FILES = [
    "layouts/index.html",
    "layouts/partials/logo-marquee.html",
    "layouts/partials/stat-band.html",
    "layouts/partials/working-tv.html",
    "layouts/partials/header.html",
    "layouts/partials/footer.html",
]

# Cache to avoid re-running identify on the same file
_dim_cache: dict[str, tuple[int, int] | None] = {}


def get_dimensions(src: str) -> tuple[int, int] | None:
    """Return (width, height) for an image src like /images/foo.webp.

    Returns None if the file doesn't exist or identify fails.
    """
    if src in _dim_cache:
        return _dim_cache[src]

    rel = src.lstrip("/")
    file_path = STATIC_DIR / rel
    if not file_path.exists():
        _dim_cache[src] = None
        return None

    try:
        result = subprocess.run(
            [IDENTIFY, "-format", "%w %h", str(file_path) + "[0]"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            if len(parts) >= 2:
                w, h = int(parts[0]), int(parts[1])
                _dim_cache[src] = (w, h)
                return (w, h)
    except Exception as e:
        print(f"  ! identify failed for {src}: {e}", file=sys.stderr)

    # Fallback: parse SVG width/height or viewBox directly when identify
    # fails (e.g. crashes on huge embedded base64 PNG paths)
    if file_path.suffix.lower() == ".svg":
        try:
            head = file_path.read_text(errors="ignore")[:4096]
            # Try explicit width/height first
            m_w = re.search(r'<svg[^>]*\bwidth="(\d+)"', head)
            m_h = re.search(r'<svg[^>]*\bheight="(\d+)"', head)
            if m_w and m_h:
                w, h = int(m_w.group(1)), int(m_h.group(1))
                _dim_cache[src] = (w, h)
                return (w, h)
            # Fall back to viewBox
            m_vb = re.search(r'viewBox="\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)"', head)
            if m_vb:
                w, h = int(float(m_vb.group(1))), int(float(m_vb.group(2)))
                _dim_cache[src] = (w, h)
                return (w, h)
        except Exception as e:
            print(f"  ! SVG fallback failed for {src}: {e}", file=sys.stderr)

    _dim_cache[src] = None
    return None


def process_file(template_path: Path, dry_run: bool) -> tuple[int, int, int]:
    """Add width/height to <img> tags missing them.

    Returns (added, skipped_already_sized, skipped_no_dims).
    """
    content = template_path.read_text()
    added = 0
    skipped_sized = 0
    skipped_no_dims = 0

    def replace_img(match: re.Match[str]) -> str:
        nonlocal added, skipped_sized, skipped_no_dims
        tag = match.group(0)

        # Skip if width or height already present
        if re.search(r"\bwidth\s*=", tag) or re.search(r"\bheight\s*=", tag):
            skipped_sized += 1
            return tag

        # Extract src
        src_match = re.search(r'src="([^"]+)"', tag)
        if not src_match:
            return tag
        src = src_match.group(1)

        # Skip Hugo template syntax in src
        if "{{" in src or "}}" in src:
            return tag

        dims = get_dimensions(src)
        if not dims:
            skipped_no_dims += 1
            return tag

        w, h = dims
        # Insert width and height before the closing > or />
        if tag.endswith("/>"):
            new_tag = tag[:-2].rstrip() + f' width="{w}" height="{h}" />'
        else:
            new_tag = tag[:-1].rstrip() + f' width="{w}" height="{h}">'
        added += 1
        return new_tag

    new_content = re.sub(r"<img\b[^>]*>", replace_img, content)

    if new_content != content and not dry_run:
        template_path.write_text(new_content)

    return added, skipped_sized, skipped_no_dims


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be modified\n")

    total_added = 0
    total_sized = 0
    total_missing = 0

    for rel in TARGET_FILES:
        path = PROJECT_ROOT / rel
        if not path.exists():
            print(f"SKIP  {rel} (not found)")
            continue
        added, sized, missing = process_file(path, dry_run)
        total_added += added
        total_sized += sized
        total_missing += missing
        action = "Would add" if dry_run else "Added"
        print(f"  {rel}: {action} {added}, already-sized {sized}, no-dims {missing}")

    print()
    print(f"Total images updated: {total_added}")
    print(f"Already had dimensions: {total_sized}")
    print(f"Could not find file or read dims: {total_missing}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
