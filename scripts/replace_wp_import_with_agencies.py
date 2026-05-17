#!/usr/bin/env python3
"""Replace legacy `/images/wp-import/` agency homepage refs with the canonical
`/images/agencies/{slug}-home.webp` refs across content/list/*.md.

Listicle BANNER images (featured image, top hero banners) are left untouched —
they map to no agency homepage.

Idempotent: re-running has no effect.

Run from repo root: python3 scripts/replace_wp_import_with_agencies.py [--dry-run]
"""
import argparse
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST_DIR = os.path.join(ROOT, "content/list")
STATIC_DIR = os.path.join(ROOT, "static/images/agencies")

WP_RE = re.compile(r'/images/wp-import/[A-Za-z0-9_\-\.]+\.(?:webp|png|jpg|jpeg)', re.IGNORECASE)

# Manual slug overrides — keyed by the auto-derived slug after stripping
# leading "NN_" and trailing "-Homepage-NNNxNNN".
OVERRIDES = {
    "piperocket": "piperocket-digital",
    "disruptive": "disruptive-advertising",
    "directive": "directive-consulting",
    "siege": "siege-media",
    "loopex": "loopex-digital",
    "madx": "madx-digital",
    "poweredbysearch": "powered-by-search",
    "growandconvert": None,  # no /images/agencies/ exists yet → capture
    "grow-and-convert": None,
    "tinuity": "tinuiti",  # legacy typo
    "firstpagesage": "first-page-sage",  # consolidate to one slug
    "theseoworks": None,  # need capture
    "the-seo-works-geo-page": None,
    "thesocialshepard": None,
    "thrive-digital": None,  # ambiguous → capture
    "stratabeat": None,
    "serpsculpt": None,
    "leadium": "leadium",
    "amsive": None,
    "linkflow": None,
    "seer-hompage": None,
    "lyfemarketing": None,
    "campfire-labs": None,
    "clearvoice": None,
    "codeless": None,
    "contentvisit": None,
    "fintech-digtial": None,  # legacy typo
    "fox-agency": None,
    "high-voltage": None,
    "inbound-fintech": None,
    "megawatt": None,
    "mint-studios": None,
    "ninjapromo": None,
    "omnius": None,
    "optimist": None,
    "properexpression": None,
    "quoleady": None,
    "straight-north": None,
    "bamboo": None,
    "cstmr": None,
    "mvpgrow": None,
    "revenuezen": None,
    "therubiconagency": "the-rubicon-agency",
}

# Listicle banner filenames (NOT agency homepages). Anything matching
# "-Homepage" or "-Home" is always an agency homepage, never a banner.
BANNER_HINTS = re.compile(
    r'(banner|agencies[-_]?\d?|^3\.png$|^aeo-geo-agencies)',
    re.IGNORECASE,
)


def derive_slug(filename: str) -> str:
    """Derive an agency slug from a wp-import filename."""
    fn = re.sub(r'\.(webp|png|jpg|jpeg)$', '', filename, flags=re.IGNORECASE)
    fn = re.sub(r'^\d+_', '', fn)
    fn = re.sub(r'-Homepage.*$', '', fn, flags=re.IGNORECASE)
    fn = re.sub(r'-Home.*$', '', fn, flags=re.IGNORECASE)
    fn = re.sub(r'-Image-.*$', '', fn, flags=re.IGNORECASE)
    fn = re.sub(r'-\d+x\d+$', '', fn)
    return re.sub(r'[^a-zA-Z0-9]+', '-', fn).lower().strip('-')


def is_banner(filename: str) -> bool:
    # Explicit banner exceptions even when filename contains "Homepage".
    # These are composite/themed listicle heroes, not single-agency homepages.
    if re.search(
        r'^Fintech-Marketing-Agencies-Homepage|^B2B-.*-Homepage',
        filename, re.IGNORECASE,
    ):
        return True
    # Otherwise: any "-Homepage" / "-Home" / "-GEO-Page" filename is an
    # agency asset, never a banner.
    if re.search(r'-Homepage|-Home-|-GEO-Page', filename, re.IGNORECASE):
        return False
    return bool(BANNER_HINTS.search(filename))


def resolve(wp_path: str, available: set) -> str | None:
    fn = os.path.basename(wp_path)
    if is_banner(fn):
        return None
    slug = derive_slug(fn)

    # Check overrides FIRST (overrides may map to None to force "needs capture")
    if slug in OVERRIDES:
        target = OVERRIDES[slug]
        if target is None:
            return None
        return f"/images/agencies/{target}-home.webp"

    if slug in available:
        return f"/images/agencies/{slug}-home.webp"
    concat = slug.replace("-", "")
    if concat in available:
        return f"/images/agencies/{concat}-home.webp"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    available = {f.replace("-home.webp", "")
                 for f in os.listdir(STATIC_DIR)
                 if f.endswith("-home.webp")}

    total_replacements = 0
    files_touched = 0
    unresolved_paths = set()
    banner_paths = set()

    for fname in sorted(os.listdir(LIST_DIR)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(LIST_DIR, fname)
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()

        wp_refs = set(WP_RE.findall(text))
        if not wp_refs:
            continue

        new_text = text
        file_replacements = 0
        for wp in wp_refs:
            target = resolve(wp, available)
            if target is None:
                if is_banner(os.path.basename(wp)):
                    banner_paths.add(wp)
                else:
                    unresolved_paths.add(wp)
                continue
            # do the replacement
            count = new_text.count(wp)
            new_text = new_text.replace(wp, target)
            file_replacements += count

        if file_replacements > 0:
            print(f"[{fname}] {file_replacements} replacement(s)")
            if not args.dry_run:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new_text)
            files_touched += 1
            total_replacements += file_replacements

    print(f"\n=== Summary ===")
    print(f"Files touched:        {files_touched}")
    print(f"Total replacements:   {total_replacements}")
    print(f"Mode:                 {'DRY RUN' if args.dry_run else 'WRITE'}")
    print(f"\nBanner paths kept (no agency mapping):    {len(banner_paths)}")
    for b in sorted(banner_paths):
        print(f"  {b}")
    print(f"\nUnresolved agency paths (need capture):   {len(unresolved_paths)}")
    for u in sorted(unresolved_paths):
        print(f"  {u}")


if __name__ == "__main__":
    main()
