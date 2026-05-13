"""
Sync original WordPress publish/modified dates back onto migrated Hugo content.

Fetches every WP post + page from piperocket.digital/wp-json/wp/v2/, builds a
{wp_id: (date_gmt, modified_gmt)} map, then walks every Hugo content file with
a `wp_id:` frontmatter field and rewrites:
  - `date:`   →  WP date_gmt (date only, YYYY-MM-DD)
  - `lastmod:` →  WP modified_gmt (only if Modified differs from Published)

Run from repo root:
  python3 scripts/sync_wp_dates.py            # dry-run preview
  python3 scripts/sync_wp_dates.py --apply    # actually write changes
"""

import argparse
import json
import os
import re
import ssl
import sys
import time
from urllib.request import urlopen, Request

# This Python install can't find the system root CAs. Since the WP REST API
# we're hitting is public data on a domain we own (piperocket.digital), it's
# safe to skip verification for this one-off date-sync run.
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

WP_BASE = "https://piperocket.digital/wp-json/wp/v2"
ENDPOINTS = ["posts", "pages", "glossary", "faq", "vs_page", "alt_page"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "content"))


def fetch_all(endpoint):
    """Page through the WP REST API and return every entry."""
    out = []
    page = 1
    while True:
        url = f"{WP_BASE}/{endpoint}?per_page=100&page={page}&_fields=id,date_gmt,modified_gmt,slug,link,status"
        req = Request(url, headers={"User-Agent": "PR-date-sync/1.0"})
        try:
            with urlopen(req, timeout=30, context=SSL_CTX) as r:
                batch = json.loads(r.read())
        except Exception as e:
            if page > 1 and "rest_post_invalid_page_number" in str(e):
                break
            print(f"  Error on {endpoint} page {page}: {e}", file=sys.stderr)
            break
        if not batch:
            break
        out.extend(batch)
        print(f"  {endpoint} page {page}: +{len(batch)} entries (total {len(out)})")
        page += 1
        time.sleep(0.3)
    return out


def parse_frontmatter(text):
    """Split a Hugo markdown file into (frontmatter_lines, body)."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    fm = text[3:end].strip("\n").split("\n")
    body = text[end + 4:].lstrip("\n")
    return fm, body


def parse_wp_id(fm_lines):
    """Pull wp_id from a list of frontmatter lines."""
    for ln in fm_lines:
        m = re.match(r"^wp_id:\s*(\d+)", ln)
        if m:
            return int(m.group(1))
    return None


def rewrite_frontmatter(fm_lines, new_date, new_lastmod):
    """Replace `date:` and ensure `lastmod:` line is present (or absent if same)."""
    out = []
    saw_date = False
    saw_lastmod = False
    for ln in fm_lines:
        if re.match(r"^date:\s*", ln):
            out.append(f"date: {new_date}")
            saw_date = True
        elif re.match(r"^lastmod:\s*", ln):
            if new_lastmod:
                out.append(f"lastmod: {new_lastmod}")
            saw_lastmod = True
        else:
            out.append(ln)
    if not saw_date:
        out.insert(0, f"date: {new_date}")
    if new_lastmod and not saw_lastmod:
        # Add lastmod right after date
        for i, ln in enumerate(out):
            if ln.startswith("date:"):
                out.insert(i + 1, f"lastmod: {new_lastmod}")
                break
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually write changes (otherwise dry-run preview)")
    args = parser.parse_args()

    # 1) Fetch all WP entries
    print("Fetching WP entries...")
    wp_by_id = {}
    for ep in ENDPOINTS:
        for entry in fetch_all(ep):
            if entry.get("status") != "publish":
                continue
            wp_by_id[entry["id"]] = {
                "date_gmt": entry["date_gmt"],
                "modified_gmt": entry["modified_gmt"],
                "slug": entry.get("slug", ""),
                "link": entry.get("link", ""),
                "endpoint": ep,
            }
    print(f"Total WP entries indexed: {len(wp_by_id)}")
    print()

    # 2) Walk Hugo content
    matched = []
    unmatched_wp = []
    unmatched_hugo = []
    files_walked = 0
    files_with_wp_id = 0

    for root, _, files in os.walk(CONTENT_DIR):
        for f in files:
            if not f.endswith(".md") or f == "_index.md":
                continue
            files_walked += 1
            path = os.path.join(root, f)
            with open(path) as fh:
                text = fh.read()
            fm_lines, _ = parse_frontmatter(text)
            if not fm_lines:
                continue
            wp_id = parse_wp_id(fm_lines)
            if wp_id is None:
                continue
            files_with_wp_id += 1
            wp_entry = wp_by_id.get(wp_id)
            if wp_entry is None:
                unmatched_hugo.append((path, wp_id))
                continue
            current_date = next(
                (re.sub(r"^date:\s*", "", ln) for ln in fm_lines if ln.startswith("date:")),
                "",
            )
            new_date = wp_entry["date_gmt"][:10]   # YYYY-MM-DD
            new_lastmod = (
                wp_entry["modified_gmt"][:10]
                if wp_entry["modified_gmt"][:10] != new_date
                else None
            )
            matched.append({
                "path": path.replace(CONTENT_DIR + "/", ""),
                "wp_id": wp_id,
                "old_date": current_date,
                "new_date": new_date,
                "new_lastmod": new_lastmod,
                "wp_link": wp_entry["link"],
            })

    # 3) Report
    print(f"Hugo content files walked: {files_walked}")
    print(f"Hugo files with wp_id: {files_with_wp_id}")
    print(f"Matched against WP: {len(matched)}")
    print(f"Hugo wp_id not found in WP API: {len(unmatched_hugo)}")
    print()

    changed = [m for m in matched if m["old_date"].strip() != m["new_date"]]
    same    = [m for m in matched if m["old_date"].strip() == m["new_date"]]

    print(f"Already correct: {len(same)}")
    print(f"Will change: {len(changed)}")
    print()

    if changed:
        print("Sample of changes (first 10):")
        for m in changed[:10]:
            extra = f"  lastmod={m['new_lastmod']}" if m["new_lastmod"] else ""
            print(f"  {m['path']}: {m['old_date']} → {m['new_date']}{extra}")
        if len(changed) > 10:
            print(f"  ... and {len(changed) - 10} more")
        print()

    if unmatched_hugo:
        print(f"Hugo files with wp_id missing from WP API (first 10):")
        for p, wid in unmatched_hugo[:10]:
            print(f"  {p}: wp_id={wid}")
        if len(unmatched_hugo) > 10:
            print(f"  ... and {len(unmatched_hugo) - 10} more")
        print()

    if not args.apply:
        print("DRY RUN — no changes written. Re-run with --apply to update files.")
        return

    # 4) Apply changes
    for m in changed:
        full_path = os.path.join(CONTENT_DIR, m["path"])
        with open(full_path) as fh:
            text = fh.read()
        fm_lines, body = parse_frontmatter(text)
        if not fm_lines:
            continue
        new_fm = rewrite_frontmatter(fm_lines, m["new_date"], m["new_lastmod"])
        with open(full_path, "w") as fh:
            fh.write("---\n")
            fh.write("\n".join(new_fm))
            fh.write("\n---\n\n")
            fh.write(body)
        print(f"  Wrote {m['path']}: {m['new_date']}")

    print()
    print(f"Updated {len(changed)} files.")


if __name__ == "__main__":
    main()
