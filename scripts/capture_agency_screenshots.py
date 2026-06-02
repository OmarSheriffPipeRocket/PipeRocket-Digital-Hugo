#!/usr/bin/env python3
"""
Capture each agency's homepage, dismiss cookie banners, save as WebP,
and insert into a listicle with a descriptive alt tag.

Workflow:
  1. Parse a listicle's markdown to find each `### N. <Brand>` H3.
  2. For every brand, auto-detect its official URL from the first
     external markdown link in that section (skipping our own brand
     and review-site URLs like clutch.co / g2.com). Normalizes paths
     like /contact/ or /blog/foo back to the brand's root domain.
  3. Capture each brand's homepage with Playwright (1280x800):
     navigate → wait → dismiss cookie/consent banner → screenshot to PNG.
  4. Convert the PNG to WebP via Pillow (quality 82, method 6) for
     ~60–80% smaller files than raw PNG, ~25% smaller than pngquant.
  5. Save to static/images/agencies/<slug>-home.webp and remove the
     intermediate PNG.
  6. Insert ![<Brand> homepage screenshot — B2B marketing agency](
     /images/agencies/<slug>-home.webp) into the listicle right after
     the "Best for:" subline (fallback: right after the H3 line).

Idempotent — re-runs skip sections whose image is already inserted.

Dependencies:
  pip install playwright pillow
  python -m playwright install chromium

Usage:
  python3 scripts/capture_agency_screenshots.py \
      content/list/best-affordable-b2b-ppc-agencies.md

  # All listicles:
  for f in content/list/*.md; do
    [ "$(basename $f)" = "_index.md" ] && continue
    python3 scripts/capture_agency_screenshots.py "$f"
  done

  # Just regenerate existing screenshots (force re-capture):
  python3 scripts/capture_agency_screenshots.py --force <files>
"""

import os
import re
import sys
import argparse

# Playwright + Pillow are the heavy deps — import lazily so --help works
# even without them installed.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None  # type: ignore
try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

# ───────────────────── Config ────────────────────────────────────────────

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENCIES_DIR = os.path.join(SITE_ROOT, "static", "images", "agencies")

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 800
NAV_TIMEOUT_MS = 30_000
SETTLE_MS = 2_500  # let lazy-loaded heroes paint

# Common cookie/consent banner accept-button text patterns.
# Playwright matches case-insensitively when using these via locator(text=…).
ACCEPT_BUTTON_TEXTS = [
    "Accept All",
    "Accept all",
    "Accept",
    "I Accept",
    "Allow All",
    "Allow all",
    "I Agree",
    "Agree",
    "Got it",
    "OK",
    "Continue",
    "Okay",
]

# Hard-coded URL overrides for brands whose listicle section doesn't
# directly link their homepage (e.g., our own brand only links /contact-us/).
# Match by lowercased brand name.
#
# Agency URLs sourced from each agency's verified Clutch profile.
URL_OVERRIDES = {
    "piperocket digital": "https://piperocket.digital",
    "piperocket": "https://piperocket.digital",
    # Sourced from each agency's verified Clutch profile.
    "amsive": "https://www.amsive.com/",
    "grow and convert": "https://www.growandconvert.com/",
    "lyfe marketing": "https://www.lyfemarketing.com/",
    "linkflow": "https://www.linkflow.ai",
    "ninjapromo": "https://ninjapromo.io",
    "properexpression": "https://www.properexpression.com",
    "revenuezen": "https://revenuezen.com/",
    "serpsculpt": "https://serpsculpt.com/",
    "straight north": "https://www.straightnorth.com/",
    "stratabeat": "https://stratabeat.com",
    "mvpgrow": "https://mvpgrow.com/",
    # Sourced via WebSearch (no Clutch profile linked in listicle text).
    "sureoak": "https://sureoak.com/",
    "cstmr": "https://cstmr.com/",
    "inbound fintech": "https://www.inboundfintech.com",
    "high voltage": "https://hvseo.co/",
    "omnius": "https://www.omnius.so/",
    "mint studios": "https://www.mintcopywritingstudios.com/",
    "bamboo": "https://growwithbamboo.com/",
    "fintech digital": "https://www.fintechdigital.com/",
    "fox agency": "https://fox.agency/us/",
    "campfire labs": "https://www.campfirelabs.co/",
    "clearvoice": "https://www.clearvoice.com/",
    "codeless": "https://codeless.io/",
    "contentvisit": "https://www.contentvisit.com/",
    "megawatt": "https://megawattcontent.com/",
    "optimist": "https://www.yesoptimist.com/",
    "quoleady": "https://www.quoleady.com/",
    "the social shepherd": "https://thesocialshepherd.com/",
    "thrive digital": "https://www.thrivedigital.com/",
    "new north": "https://newnorth.com/",
    # Round 3 — agencies with no existing capture (added 2026-05-17).
    "skale": "https://skale.so/",
    "jeenam": "https://jeenaminfotech.com/",
    "inturact": "https://www.inturact.com/",
    "embarque": "https://www.embarque.io/",
    "tripledart": "https://www.tripledart.com/",
    "cyberwhyze": "https://www.whyzelabs.com/",
    "magnetude consulting": "https://www.magnetudeconsulting.com/",
    "jumpfactor": "https://www.jumpfactor.net/",
    "draft.dev": "https://draft.dev/",
    "perceptric": "https://perceptric.com/",
    "everydeveloper": "https://everydeveloper.com/",
    "clarity": "https://clarity.global/",
    "prop tech marketing": "https://www.proptechmarketing.com/",
}

# Review-site URLs to ignore when auto-detecting the brand homepage.
# Our own domain stays out so other listicle sections that link to a
# competitor's site (which happens to mention piperocket in metadata)
# aren't confused. Auto-detection falls through to the override map.
SKIP_URL_HOSTS = (
    "clutch.co",
    "g2.com",
    "trustpilot.com",
    "capterra.com",
    "/contact-us/",  # internal contact link
)

# Tolerate bold wrappers around the heading rank, brand, or whole thing:
#   ### 1. Brand Name
#   ### **1. Brand Name**
#   ### **1.** Brand Name
#   ### 1. **Brand Name**
H3_PATTERN = re.compile(r"^###\s+\**\d+\.\**\s*\**(.+?)\**\s*$", re.MULTILINE)


def clean_brand_name(raw: str) -> str:
    """Strip markdown link wrappers and "Best for:" suffixes from a raw
    heading capture so we get just the brand name.

        "[Kalungi](/blogs/best-saas-seo-agencies/#kalungi) – Best for: ..."
            → "Kalungi"
        "PipeRocket Digital"
            → "PipeRocket Digital"
        "**Beacon Digital**"
            → "Beacon Digital"
    """
    s = raw.strip()
    # Strip leading/trailing bold markers
    s = re.sub(r"^\*+\s*|\s*\*+$", "", s)
    # If it's a markdown link, grab the link text
    m = re.match(r"\[([^\]]+)\]\([^)]+\)(.*)$", s)
    if m:
        s = m.group(1).strip()
    # Drop anything after a separator (em-dash, en-dash, colon, " - Best", " – Best")
    s = re.split(r"\s*[–—:]\s*|\s+-\s+", s, maxsplit=1)[0]
    # Final cleanup
    return s.strip(" *")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


# ───────────────────── Helpers ──────────────────────────────────────────


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def should_skip_url(url: str) -> bool:
    low = url.lower()
    return any(host in low for host in SKIP_URL_HOSTS)


def normalize_homepage(url: str) -> str:
    """Strip /contact/, /blog/post, /about path segments and keep root."""
    m = re.match(r"(https?://[^/]+)", url)
    if not m:
        return url
    return m.group(1) + "/"


def detect_brand_url(section_text: str, brand_name: str):
    """1) Try the override map (handles brands whose listicle section
       links only to internal pages, like our own /contact-us/).
       2) Otherwise, scan markdown links: prefer one whose link text
          matches the brand name, fall back to first non-review URL.
       3) Normalize to the root domain so we land on the actual
          homepage, not /contact/ or /blog/foo.
    """
    low_name = brand_name.lower().strip()
    if low_name in URL_OVERRIDES:
        return URL_OVERRIDES[low_name]

    candidates_named = []
    candidates_any = []
    for text_part, url in LINK_PATTERN.findall(section_text):
        if should_skip_url(url):
            continue
        if "/blog/" in url and low_name not in url.lower():
            continue
        candidates_any.append(url)
        if low_name.split()[0] in text_part.lower():
            candidates_named.append(url)
    chosen = candidates_named or candidates_any
    if not chosen:
        return None
    return normalize_homepage(chosen[0])


def dismiss_cookie_banner(page) -> bool:
    """Try clicking common consent-banner accept buttons.

    Returns True if any button was clicked. We swallow per-button errors
    because most sites surface only one accept button so the rest will
    fail-fast and that's expected."""
    clicked = False
    for txt in ACCEPT_BUTTON_TEXTS:
        try:
            # Match buttons, links, and inputs by their visible text.
            locator = page.get_by_role("button", name=re.compile(rf"^{re.escape(txt)}\s*$", re.IGNORECASE))
            if locator.count() > 0 and locator.first.is_visible():
                locator.first.click(timeout=2_000)
                clicked = True
                page.wait_for_timeout(800)
                break
        except Exception:
            pass
    # Fallback: also try matching <a> and generic clickable elements.
    if not clicked:
        for txt in ACCEPT_BUTTON_TEXTS:
            try:
                locator = page.locator(f'text=/^{re.escape(txt)}\\s*$/i')
                if locator.count() > 0 and locator.first.is_visible():
                    locator.first.click(timeout=2_000)
                    clicked = True
                    page.wait_for_timeout(800)
                    break
            except Exception:
                pass
    return clicked


def convert_png_to_webp(png_path: str, webp_path: str, quality: int = 82) -> int:
    """Convert a PNG to WebP via Pillow. Removes the source PNG on success.
    Returns the size of the resulting WebP file."""
    if Image is None:
        # Can't convert — leave the PNG in place and return its size.
        return os.path.getsize(png_path)
    try:
        im = Image.open(png_path)
        im.save(webp_path, format="WEBP", quality=quality, method=6)
    except Exception as e:
        print(f"    ✗ WebP conversion failed: {e}")
        return os.path.getsize(png_path)
    if os.path.exists(webp_path) and os.path.getsize(webp_path) > 1000:
        os.remove(png_path)
    return os.path.getsize(webp_path)


def alt_text_for(name: str) -> str:
    """Descriptive alt for SEO + accessibility."""
    return f"{name} homepage screenshot — B2B marketing agency"


def capture_screenshot(page, url: str, out_path: str) -> bool:
    """Navigate, dismiss consent banner, take screenshot. Returns success."""
    try:
        page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
    except Exception as e:
        print(f"    ✗ navigation failed: {e}")
        return False
    page.wait_for_timeout(SETTLE_MS)
    dismissed = dismiss_cookie_banner(page)
    if dismissed:
        page.wait_for_timeout(800)  # let banner animate out
    try:
        page.screenshot(path=out_path, full_page=False, type="png")
    except Exception as e:
        print(f"    ✗ screenshot failed: {e}")
        return False
    return os.path.exists(out_path) and os.path.getsize(out_path) > 1000


# ───────────────────── Main ─────────────────────────────────────────────


def process_listicle(md_path: str, browser_context, force: bool = False, inject: bool = True) -> None:
    if not os.path.exists(md_path):
        print(f"  ! {md_path} not found", file=sys.stderr)
        return

    with open(md_path, "r") as f:
        original = f.read()
    content = original

    os.makedirs(AGENCIES_DIR, exist_ok=True)

    h3_matches = list(H3_PATTERN.finditer(content))
    if not h3_matches:
        print(f"  - {md_path}: no ### N. headings found, skipping")
        return

    sections = []
    for i, m in enumerate(h3_matches):
        name = clean_brand_name(m.group(1))
        body_start = m.end()
        body_end = h3_matches[i + 1].start() if i + 1 < len(h3_matches) else len(content)
        sections.append(
            {"name": name, "body": content[body_start:body_end], "h3": m.group(0)}
        )

    captured = 0
    inserted = 0
    skipped = 0

    for sec in sections:
        name = sec["name"]
        url = detect_brand_url(sec["body"], name)
        if not url:
            print(f"  - skipping {name}: no external URL detected")
            skipped += 1
            continue

        slug = slugify(name)
        webp_file = f"{slug}-home.webp"
        png_temp = os.path.join(AGENCIES_DIR, f"{slug}-home.png")
        webp_path = os.path.join(AGENCIES_DIR, webp_file)
        alt = alt_text_for(name)
        img_md = f"![{alt}](/images/agencies/{webp_file})"

        # Idempotency — skip if the alt+webp reference is already in the file.
        # Also tolerate the older PNG / older alt-text format we may have
        # injected on previous runs.
        legacy_png_md = f"![{name} homepage](/images/agencies/{slug}-home.png)"
        if (img_md in content or legacy_png_md in content) and not force:
            skipped += 1
            continue

        if not os.path.exists(webp_path) or force:
            page = browser_context.new_page()
            try:
                print(f"  · capturing {name} ({url})")
                ok = capture_screenshot(page, url, png_temp)
            finally:
                page.close()
            if not ok:
                skipped += 1
                continue
            png_kb = os.path.getsize(png_temp) // 1024
            webp_bytes = convert_png_to_webp(png_temp, webp_path)
            webp_kb = webp_bytes // 1024
            print(f"    ✓ {webp_file}: {png_kb} KB PNG → {webp_kb} KB WebP")
            captured += 1

        if not inject:
            continue

        # Insertion strategy
        anchors = [
            re.compile(re.escape(sec["h3"]) + r"\n\n(Best for:[^\n]*\n)", re.MULTILINE),
            re.compile(re.escape(sec["h3"]) + r"\n", re.MULTILINE),
        ]
        matched = None
        for pat in anchors:
            matched = pat.search(content)
            if matched:
                break
        if not matched:
            continue
        if img_md in content:
            continue
        idx = matched.end()
        content = content[:idx] + f"\n{img_md}\n\n" + content[idx:]
        inserted += 1

    if content != original:
        with open(md_path, "w") as f:
            f.write(content)

    print(
        f"  ✓ {os.path.basename(md_path)}: "
        f"{captured} captured, {inserted} inserted, {skipped} skipped"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Capture agency homepages, dismiss cookie banners, compress, "
            "and inject into a listicle."
        ),
    )
    parser.add_argument("files", nargs="+", help="Listicle .md paths")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-capture & re-compress even if the image file already exists.",
    )
    parser.add_argument(
        "--no-inject",
        action="store_true",
        help="Capture screenshots only; don't modify the markdown file. "
        "Useful when the listicle already has legacy wp-import images that "
        "will be swapped via a separate find-replace step.",
    )
    args = parser.parse_args()

    if sync_playwright is None:
        print(
            "✗ Playwright not installed. Run:\n"
            "    pip install playwright && python -m playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)

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
        for fp in args.files:
            process_listicle(fp, context, force=args.force, inject=not args.no_inject)
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
