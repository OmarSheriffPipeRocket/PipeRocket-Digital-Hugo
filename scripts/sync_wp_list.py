"""
Sync WordPress content into existing content/list/*.md files (listicles).

Walks every content/list/*.md with a wp_id, fetches the matching WP post,
renders new frontmatter + Markdown body using the same logic as
sync_wp_posts.py, then writes back to the SAME path (preserving the /list/
section). Preserves `toc:` and `readingTime:` fields from the original file.

Excludes any slugs listed in SKIP_SLUGS below.

Run from repo root:
  python3 scripts/sync_wp_list.py            # dry-run report
  python3 scripts/sync_wp_list.py --diff     # write per-post diffs to tmp/wp-diff-list/
  python3 scripts/sync_wp_list.py --apply    # write changes (also runs the audit)
"""

import argparse
import base64
import difflib
import json
import os
import re
import ssl
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import html as html_lib
try:
    from markdownify import markdownify as html_to_md
except ImportError:
    sys.exit("Missing dep: pip3 install --user markdownify")

# Reuse helpers from the blog sync script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_wp_posts import (  # noqa: E402
    load_env, wp_get as _wp_get_url, fetch_categories, fetch_users,
    fetch_media_url, scrape_seo_meta, author_slug, extract_internal_links,
    REPO_ROOT, CONTENT_DIR,
)

LIST_DIR = os.path.join(CONTENT_DIR, "list")
SKIP_SLUGS = {"best-affordable-b2b-ppc-agencies"}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def wp_get(env, path):
    auth = base64.b64encode(f"{env['WP_USER']}:{env['WP_APP_PASSWORD']}".encode()).decode()
    req = Request(env["WP_URL"].rstrip("/") + path,
                  headers={"Authorization": f"Basic {auth}",
                           "User-Agent": "PR-wp-list-sync/1.0"})
    return urlopen(req, timeout=30, context=SSL_CTX)


FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def read_fm_and_body(path):
    with open(path) as f:
        text = f.read()
    m = FM_RE.match(text)
    if not m:
        return {}, "", text
    fm_raw = m.group(1)
    fm = {}
    for line in fm_raw.split("\n"):
        mm = re.match(r"(\w+):\s*(.*)$", line)
        if mm:
            k, v = mm.group(1), mm.group(2).strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            fm[k] = v
    return fm, fm_raw, text[m.end():]


def render_new(post, env, categories, users, preserve_toc, preserve_rt):
    title = html_lib.unescape(post["title"]["rendered"])
    excerpt_html = post["excerpt"]["rendered"]
    description = html_lib.unescape(re.sub(r"<[^>]+>", "", excerpt_html)).strip().replace('"', '\\"')

    seo = scrape_seo_meta(post["link"])
    meta_title = html_lib.unescape(seo["meta_title"]).replace('"', '\\"')
    meta_description = html_lib.unescape(seo["meta_description"]).replace('"', '\\"')

    body_md = html_to_md(
        post["content"]["rendered"],
        heading_style="ATX",
        bullets="-",
        strip=["script", "style"],
    ).strip() + "\n"

    cat_ids = post.get("categories", []) or []
    cat_name = categories.get(cat_ids[0], "") if cat_ids else ""
    written_by = author_slug(users.get(post.get("author", 0), ""))
    featured = fetch_media_url(env, post.get("featured_media", 0))

    date = post.get("date_gmt", post.get("date", ""))[:10]
    modified = post.get("modified_gmt", post.get("modified", ""))[:10]

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
    slug = post["slug"]
    fm.append(f'slug: "{slug}"')
    if written_by:
        fm.append(f'writtenBy: "{written_by}"')
    if cat_name:
        fm.append(f'category: "{cat_name}"')
    if featured:
        fm.append(f'featuredImage: "{featured}"')
    fm.append(f"wp_id: {post['id']}")
    fm.append(f'wp_link: "{post["link"].split("piperocket.digital")[-1]}"')
    if preserve_toc:
        fm.append(preserve_toc)
    if preserve_rt:
        fm.append(preserve_rt)
    fm.append("---")
    return "\n".join(fm) + "\n\n" + body_md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--diff", action="store_true")
    args = ap.parse_args()

    env = load_env()

    files = []
    for fn in sorted(os.listdir(LIST_DIR)):
        if not fn.endswith(".md") or fn == "_index.md":
            continue
        fp = os.path.join(LIST_DIR, fn)
        fm, fm_raw, body = read_fm_and_body(fp)
        slug = fm.get("slug", "")
        wp_id = fm.get("wp_id", "")
        if not wp_id:
            continue
        if slug in SKIP_SLUGS:
            continue
        files.append((fp, fm, fm_raw, body, int(wp_id)))

    print(f"Listicle files to consider: {len(files)} (skipping: {', '.join(sorted(SKIP_SLUGS))})")
    print("Fetching categories + users…")
    categories = fetch_categories(env)
    users = fetch_users(env)

    diff_dir = os.path.join(REPO_ROOT, "tmp", "wp-diff-list")
    if args.diff:
        os.makedirs(diff_dir, exist_ok=True)

    written = 0
    link_audit = []
    for fp, fm, fm_raw, body, wp_id in files:
        try:
            with wp_get(env, f"/wp-json/wp/v2/posts/{wp_id}") as r:
                post = json.load(r)
        except Exception as e:
            print(f"  ERROR fetching wp_id={wp_id}: {e}")
            continue

        toc_line = next((l for l in fm_raw.split("\n") if l.startswith("toc:")), None)
        rt_line = next((l for l in fm_raw.split("\n") if l.startswith("readingTime:")), None)

        new_text = render_new(post, env, categories, users, toc_line, rt_line)
        with open(fp) as f:
            old_text = f.read()

        if args.diff:
            diff = list(difflib.unified_diff(
                old_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=f"a/{os.path.relpath(fp, REPO_ROOT)}",
                tofile=f"b/wp/{post['slug']}.md",
            ))
            added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
            removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
            with open(os.path.join(diff_dir, f"{post['slug']}.diff"), "w") as f:
                f.writelines(diff)
            print(f"  +{added:>4}  -{removed:>4}   {post['slug']}")

        if args.apply:
            prev_links = extract_internal_links(old_text)
            with open(fp, "w") as f:
                f.write(new_text)
            written += 1
            new_set = {u for _, u in extract_internal_links(new_text)}
            lost = [(t, u) for (t, u) in prev_links if u not in new_set]
            if prev_links:
                link_audit.append({
                    "slug": post["slug"],
                    "file": os.path.relpath(fp, REPO_ROOT),
                    "previous": len(prev_links),
                    "kept": len(prev_links) - len(lost),
                    "lost": lost,
                })
            print(f"  wrote {os.path.relpath(fp, REPO_ROOT)}")

    if args.apply and link_audit:
        audit_path = os.path.join(REPO_ROOT, "tmp", "wp-link-audit-list.json")
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        with open(audit_path, "w") as f:
            json.dump(link_audit, f, indent=2)
        total_prev = sum(e["previous"] for e in link_audit)
        total_lost = sum(len(e["lost"]) for e in link_audit)
        print()
        print(f"Wrote {written} files.")
        print(f"Internal links before: {total_prev}, lost: {total_lost}")
        print(f"Audit: {os.path.relpath(audit_path, REPO_ROOT)}")

    if not (args.apply or args.diff):
        print("\nDry-run (no diffs, no writes). Pass --diff to preview or --apply to write.")


if __name__ == "__main__":
    main()
