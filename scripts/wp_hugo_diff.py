"""Audit drift between Hugo source and live WordPress.

Read-only. For each Hugo file with `wp_id`, fetch the matching WP post via
REST API and compare:
  - title
  - slug
  - modified date (vs Hugo `date`)
  - rough body length (HTML chars vs markdown chars; just a sanity check)

Outputs a report so you can decide which pages to sync.
"""

import json
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path("/Users/omarsheriff/Desktop/piperocket-site")
CONTENT = ROOT / "content"
OUT = ROOT / "credentials" / "gsc_output" / "wp_hugo_diff.json"

# Hugo content folder -> WP REST endpoint base
TYPE_MAP = {
    "blogs": "wp/v2/posts",
    "list": "wp/v2/posts",
    "glossary": "wp/v2/glossary",
    "compare": "wp/v2/vs_page",
    "alternative": "wp/v2/alt_page",
    "vs": "wp/v2/vs_page",
}
BASE = "https://piperocket.digital/"


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_raw = parts[1]
    body = parts[2].lstrip("\n")
    fm = {}
    for line in fm_raw.splitlines():
        m = re.match(r'^([a-zA-Z_]+):\s*"?([^"]*?)"?\s*$', line)
        if m:
            fm[m.group(1)] = m.group(2)
    return fm, body


def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"&[a-z]+;|&#\d+;", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fetch_wp(post_type_base: str, wp_id: str):
    url = f"{BASE}wp-json/{post_type_base}/{wp_id}?_fields=id,slug,title,modified,date,status,content,excerpt"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "hugo-sync-audit/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)}


def main():
    md_files = sorted(CONTENT.rglob("*.md"))
    results = []
    seen = 0
    errors = 0
    drift_count = 0

    for md in md_files:
        rel = str(md.relative_to(CONTENT))
        folder = rel.split("/")[0]
        if folder not in TYPE_MAP:
            continue
        text = md.read_text(errors="ignore")
        fm, body = parse_frontmatter(text)
        wp_id = fm.get("wp_id")
        if not wp_id:
            continue
        seen += 1
        base = TYPE_MAP[folder]
        wp = fetch_wp(base, wp_id)
        time.sleep(0.05)
        if "_error" in wp:
            errors += 1
            results.append({"file": rel, "wp_id": wp_id, "error": wp["_error"]})
            print(f"  ✗ {rel}  wp_id={wp_id}  {wp['_error']}")
            continue

        wp_title = wp.get("title", {}).get("rendered", "")
        hugo_title = fm.get("title", "").strip().strip('"')
        wp_slug = wp.get("slug", "")
        hugo_slug = fm.get("slug", md.stem)
        wp_body = strip_html(wp.get("content", {}).get("rendered", ""))
        hugo_body_len = len(body.strip())
        wp_body_len = len(wp_body)
        len_delta_pct = abs(wp_body_len - hugo_body_len) / max(hugo_body_len, 1) * 100

        diffs = []
        if wp_title and hugo_title and wp_title != hugo_title:
            diffs.append("title")
        if wp_slug and hugo_slug and wp_slug != hugo_slug:
            diffs.append("slug")
        if len_delta_pct > 25:
            diffs.append(f"body_len({hugo_body_len}->{wp_body_len},Δ{len_delta_pct:.0f}%)")

        row = {
            "file": rel,
            "wp_id": wp_id,
            "wp_modified": wp.get("modified"),
            "hugo_title": hugo_title,
            "wp_title": wp_title,
            "hugo_slug": hugo_slug,
            "wp_slug": wp_slug,
            "hugo_body_len": hugo_body_len,
            "wp_body_len": wp_body_len,
            "diffs": diffs,
        }
        results.append(row)

        if diffs:
            drift_count += 1
            print(f"  Δ {rel}")
            for d in diffs:
                if d == "title":
                    print(f"      title:  hugo='{hugo_title}'\n              wp='  {wp_title}'")
                elif d == "slug":
                    print(f"      slug:   hugo='{hugo_slug}'  wp='{wp_slug}'")
                else:
                    print(f"      {d}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n=== Summary ===")
    print(f"Scanned: {seen}   With drift: {drift_count}   Errors: {errors}")
    print(f"Full report: {OUT}")


if __name__ == "__main__":
    main()
