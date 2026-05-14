"""
Sync WordPress custom post types (CPTs) into Hugo content folders.

Currently configured:
  WP CPT 'glossary'  -> content/glossary/
  WP CPT 'vs_page'   -> content/compare/   (vs_page lives at /compare/{slug}/ in WP)

For each WP entry, fetches the post, renders new front-matter + Markdown body
using the same logic as sync_wp_posts.py, then writes to the matching local
file (matched by wp_id, falling back to slug). Preserves toc: and readingTime:
fields from the existing file.

Run from repo root:
  python3 scripts/sync_wp_cpt.py             # dry-run report
  python3 scripts/sync_wp_cpt.py --diff      # write per-CPT per-post diffs
  python3 scripts/sync_wp_cpt.py --apply     # write changes
"""

import argparse
import base64
import difflib
import json
import os
import re
import ssl
import sys
from urllib.request import urlopen, Request

import html as html_lib
try:
    from markdownify import markdownify as html_to_md
except ImportError:
    sys.exit("Missing dep: pip3 install --user markdownify")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_wp_posts import (  # noqa: E402
    load_env, fetch_categories, fetch_users, fetch_media_url, scrape_seo_meta,
    author_slug, extract_internal_links, REPO_ROOT, CONTENT_DIR,
)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# WP CPT rest_base  ->  local content folder
CPT_MAP = {
    "glossary": "glossary",
    # vs_page intentionally NOT synced — local /compare/ pages have rich Hugo-specific
    # frontmatter (product_a/b, decision_matrix, etc.) that WP doesn't expose.
    # "vs_page": "compare",
}

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def wp_get(env, path):
    auth = base64.b64encode(f"{env['WP_USER']}:{env['WP_APP_PASSWORD']}".encode()).decode()
    req = Request(env["WP_URL"].rstrip("/") + path,
                  headers={"Authorization": f"Basic {auth}",
                           "User-Agent": "PR-wp-cpt-sync/1.0"})
    return urlopen(req, timeout=30, context=SSL_CTX)


def fetch_all(env, cpt):
    from urllib.error import HTTPError
    out, page = [], 1
    while True:
        try:
            with wp_get(env, f"/wp-json/wp/v2/{cpt}?per_page=100&page={page}") as r:
                batch = json.load(r)
        except HTTPError as e:
            if e.code == 400 and page > 1:
                break
            raise
        if not batch:
            break
        out.extend(batch)
        page += 1
    return out


def read_fm(path):
    with open(path) as f:
        text = f.read()
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).split("\n"):
        mm = re.match(r"(\w+):\s*(.*)$", line)
        if mm:
            k, v = mm.group(1), mm.group(2).strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            fm[k] = v
    return fm, text


def find_local_file(folder, wp_id, slug):
    d = os.path.join(CONTENT_DIR, folder)
    if not os.path.isdir(d):
        return None
    target_by_slug = os.path.join(d, f"{slug}.md")
    # Match by wp_id first
    for fn in os.listdir(d):
        if not fn.endswith(".md") or fn == "_index.md":
            continue
        fp = os.path.join(d, fn)
        fm, _ = read_fm(fp)
        if fm.get("wp_id") and int(fm["wp_id"]) == wp_id:
            return fp
    # Fallback: match by slug
    if os.path.exists(target_by_slug):
        return target_by_slug
    return None


def render_new(post, env, categories, users, preserve_lines):
    title = html_lib.unescape(post["title"]["rendered"])
    excerpt_html = (post.get("excerpt") or {}).get("rendered", "") or ""
    description = html_lib.unescape(re.sub(r"<[^>]+>", "", excerpt_html)).strip().replace('"', '\\"')
    seo = scrape_seo_meta(post["link"])
    meta_title = html_lib.unescape(seo["meta_title"]).replace('"', '\\"')
    meta_description = html_lib.unescape(seo["meta_description"]).replace('"', '\\"')
    body_md = html_to_md(
        post["content"]["rendered"],
        heading_style="ATX", bullets="-", strip=["script", "style"],
    ).strip() + "\n"

    cat_ids = post.get("categories", []) or []
    cat_name = categories.get(cat_ids[0], "") if cat_ids else ""
    written_by = author_slug(users.get(post.get("author", 0), ""))
    featured = fetch_media_url(env, post.get("featured_media", 0))
    date = post.get("date_gmt", post.get("date", ""))[:10]
    modified = post.get("modified_gmt", post.get("modified", ""))[:10]
    slug = post["slug"]

    fm = [
        "---",
        f'title: "{title.replace(chr(34), chr(92)+chr(34))}"',
        f'description: "{description}"',
    ]
    if meta_title and meta_title != title:
        fm.append(f'meta_title: "{meta_title}"')
    if meta_description and meta_description != description:
        fm.append(f'meta_description: "{meta_description}"')
    fm.append(f"date: {date}")
    if modified and modified != date:
        fm.append(f"lastmod: {modified}")
    fm.append(f'slug: "{slug}"')
    if written_by:
        fm.append(f'writtenBy: "{written_by}"')
    if cat_name:
        fm.append(f'category: "{cat_name}"')
    if featured:
        fm.append(f'featuredImage: "{featured}"')
    fm.append(f"wp_id: {post['id']}")
    fm.append(f'wp_link: "{post["link"].split("piperocket.digital")[-1]}"')
    fm.extend(preserve_lines)
    fm.append("---")
    return "\n".join(fm) + "\n\n" + body_md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--diff", action="store_true")
    args = ap.parse_args()

    env = load_env()
    categories = fetch_categories(env)
    users = fetch_users(env)

    overall_audit = []
    for cpt, folder in CPT_MAP.items():
        posts = fetch_all(env, cpt)
        print(f"\n=== CPT '{cpt}' -> content/{folder}/  ({len(posts)} entries) ===")

        diff_dir = os.path.join(REPO_ROOT, "tmp", f"wp-diff-{cpt}")
        if args.diff:
            os.makedirs(diff_dir, exist_ok=True)

        for post in posts:
            # The URL slug (from the link field) often differs from post.slug
            # for vs_page (e.g. WP slug "piperocket-vs-x-2" vs URL "piperocket-digital-vs-x").
            url_slug = post["link"].rstrip("/").split("/")[-1]
            local = find_local_file(folder, post["id"], url_slug) \
                or find_local_file(folder, post["id"], post["slug"])
            if not local:
                # Create a new file at content/{folder}/{url_slug}.md
                local = os.path.join(CONTENT_DIR, folder, f"{url_slug}.md")
                preserve_lines = []
                old_text = ""
            else:
                fm, old_text = read_fm(local)
                preserve_lines = []
                for key in ("toc", "readingTime"):
                    for line in old_text.split("\n"):
                        if line.startswith(f"{key}:"):
                            preserve_lines.append(line)
                            break

            new_text = render_new(post, env, categories, users, preserve_lines)

            if args.diff and old_text:
                diff = list(difflib.unified_diff(
                    old_text.splitlines(keepends=True),
                    new_text.splitlines(keepends=True),
                    fromfile=f"a/{os.path.relpath(local, REPO_ROOT)}",
                    tofile=f"b/wp/{post['slug']}.md",
                ))
                added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
                removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
                with open(os.path.join(diff_dir, f"{post['slug']}.diff"), "w") as f:
                    f.writelines(diff)
                print(f"  +{added:>4}  -{removed:>4}   {post['slug']}")

            if args.apply:
                prev_links = extract_internal_links(old_text) if old_text else []
                os.makedirs(os.path.dirname(local), exist_ok=True)
                with open(local, "w") as f:
                    f.write(new_text)
                new_set = {u for _, u in extract_internal_links(new_text)}
                lost = [(t, u) for (t, u) in prev_links if u not in new_set]
                if prev_links:
                    overall_audit.append({
                        "slug": post["slug"],
                        "file": os.path.relpath(local, REPO_ROOT),
                        "previous": len(prev_links),
                        "kept": len(prev_links) - len(lost),
                        "lost": lost,
                    })
                print(f"  wrote {os.path.relpath(local, REPO_ROOT)}")

    if args.apply and overall_audit:
        audit_path = os.path.join(REPO_ROOT, "tmp", "wp-link-audit-cpt.json")
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        with open(audit_path, "w") as f:
            json.dump(overall_audit, f, indent=2)
        total_prev = sum(e["previous"] for e in overall_audit)
        total_lost = sum(len(e["lost"]) for e in overall_audit)
        print()
        print(f"Internal links before: {total_prev}, lost: {total_lost}")
        print(f"Audit: {os.path.relpath(audit_path, REPO_ROOT)}")

    if not (args.apply or args.diff):
        print("\nDry-run only. --diff to preview, --apply to write.")


if __name__ == "__main__":
    main()
