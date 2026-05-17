#!/usr/bin/env python3
"""Capture multiple pages per agency from data/agencies.toml.

For each agency entry, captures the homepage, pricing (if present), and
contact page. Saves to:
  static/images/agencies/<slug>-home.webp
  static/images/agencies/<slug>-pricing.webp
  static/images/agencies/<slug>-contact.webp

Workflow per URL:
  1. Navigate via Playwright (1280x800 viewport, real desktop UA).
  2. Wait for the hero/content to paint.
  3. Dismiss cookie/consent banner if present.
  4. Screenshot to PNG, then convert to WebP (quality 82, method 6).

Idempotent — re-runs skip any output file that already exists unless
--force is passed.

Dependencies:
  pip install playwright pillow tomli
  python -m playwright install chromium

Usage:
  python3 scripts/capture_agency_pages.py                    # all agencies
  python3 scripts/capture_agency_pages.py --only piperocket-digital
  python3 scripts/capture_agency_pages.py --pages pricing,contact
  python3 scripts/capture_agency_pages.py --force            # re-capture
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        print("✗ Need tomllib (Python 3.11+) or tomli. `pip install tomli`")
        sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("✗ playwright not installed. Run: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "agencies.toml"
OUT_DIR = ROOT / "static" / "images" / "agencies"

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 800
NAV_TIMEOUT_MS = 30_000
SETTLE_MS = 2_500

PAGE_TYPES = ("homepage", "pricing", "contact")
PAGE_SUFFIX = {"homepage": "home", "pricing": "pricing", "contact": "contact"}

ACCEPT_BUTTON_TEXTS = [
    "Accept All", "Accept all", "Accept", "I Accept",
    "Allow All", "Allow all", "I Agree", "Agree",
    "Got it", "OK", "Continue", "Okay",
]


def load_agencies() -> dict:
    with open(DATA_FILE, "rb") as fh:
        return tomllib.load(fh)


def dismiss_cookie_banner(page) -> bool:
    import re
    for txt in ACCEPT_BUTTON_TEXTS:
        try:
            locator = page.get_by_role(
                "button",
                name=re.compile(rf"^{re.escape(txt)}\s*$", re.IGNORECASE),
            )
            if locator.count() > 0 and locator.first.is_visible():
                locator.first.click(timeout=2000)
                page.wait_for_timeout(800)
                return True
        except Exception:
            pass
    for txt in ACCEPT_BUTTON_TEXTS:
        try:
            locator = page.locator(f'text=/^{re.escape(txt)}\\s*$/i')
            if locator.count() > 0 and locator.first.is_visible():
                locator.first.click(timeout=2000)
                page.wait_for_timeout(800)
                return True
        except Exception:
            pass
    return False


def convert_png_to_webp(png_path: Path, webp_path: Path, quality: int = 82) -> int:
    if Image is None:
        return png_path.stat().st_size
    try:
        im = Image.open(png_path)
        im.save(webp_path, format="WEBP", quality=quality, method=6)
    except Exception as e:
        print(f"      ✗ WebP conversion failed: {e}")
        return png_path.stat().st_size
    if webp_path.exists() and webp_path.stat().st_size > 1000:
        png_path.unlink(missing_ok=True)
    return webp_path.stat().st_size


def capture_url(context, url: str, out_webp: Path) -> bool:
    page = context.new_page()
    try:
        try:
            page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
        except Exception as e:
            print(f"      ✗ navigation failed: {e}")
            return False
        page.wait_for_timeout(SETTLE_MS)
        dismissed = dismiss_cookie_banner(page)
        if dismissed:
            page.wait_for_timeout(800)
        png_temp = out_webp.with_suffix(".png")
        try:
            page.screenshot(path=str(png_temp), full_page=False, type="png")
        except Exception as e:
            print(f"      ✗ screenshot failed: {e}")
            return False
        if not (png_temp.exists() and png_temp.stat().st_size > 1000):
            return False
        png_kb = png_temp.stat().st_size // 1024
        webp_bytes = convert_png_to_webp(png_temp, out_webp)
        webp_kb = webp_bytes // 1024
        print(f"      ✓ {out_webp.name}: {png_kb} KB PNG → {webp_kb} KB WebP")
        return True
    finally:
        page.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="Process a single agency slug")
    ap.add_argument(
        "--pages",
        default="homepage,pricing,contact",
        help="Comma-separated subset of: homepage,pricing,contact",
    )
    ap.add_argument("--force", action="store_true", help="Re-capture even if file exists")
    args = ap.parse_args()

    wanted = {p.strip() for p in args.pages.split(",")}
    invalid = wanted - set(PAGE_TYPES)
    if invalid:
        print(f"✗ Unknown page types: {sorted(invalid)}. Valid: {PAGE_TYPES}")
        sys.exit(2)

    agencies = load_agencies()
    if args.only:
        if args.only not in agencies:
            print(f"✗ slug not in data/agencies.toml: {args.only}")
            sys.exit(2)
        agencies = {args.only: agencies[args.only]}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    captured = 0
    skipped = 0
    missing_urls = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        for slug, agency in agencies.items():
            print(f"\n[{slug}] {agency.get('name', slug)}")
            for ptype in PAGE_TYPES:
                if ptype not in wanted:
                    continue
                # 'homepage' lives under the 'homepage' key in TOML;
                # other types use the same key name.
                url = agency.get(ptype)
                if not url:
                    if ptype in ("pricing",):
                        # pricing is optional, silent skip
                        continue
                    print(f"    - {ptype}: missing URL in data file")
                    missing_urls += 1
                    continue
                out_webp = OUT_DIR / f"{slug}-{PAGE_SUFFIX[ptype]}.webp"
                if out_webp.exists() and not args.force:
                    skipped += 1
                    continue
                print(f"    · capturing {ptype} ({url})")
                ok = capture_url(context, url, out_webp)
                if ok:
                    captured += 1
        context.close()
        browser.close()

    print(f"\n=== Summary ===")
    print(f"Captured:     {captured}")
    print(f"Skipped (existed): {skipped}")
    print(f"Missing URLs: {missing_urls}")


if __name__ == "__main__":
    main()
