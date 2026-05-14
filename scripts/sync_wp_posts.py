"""
Sync /blogs/ and /research/ posts from WordPress into Hugo content files.

Reads credentials from credentials/.env (WP_URL, WP_USER, WP_APP_PASSWORD).

Default (no flags): dry-run report — lists every WP post and shows whether the
matching Hugo file is NEW (no local file), IN-SYNC (Hugo lastmod >= WP modified),
or OUT-OF-DATE (WP newer).

Run from repo root:
  python3 scripts/sync_wp_posts.py                  # dry-run report
  python3 scripts/sync_wp_posts.py --apply          # write NEW + OUT-OF-DATE files
  python3 scripts/sync_wp_posts.py --apply --only-new
  python3 scripts/sync_wp_posts.py --apply --only-stale
  python3 scripts/sync_wp_posts.py --apply --ids 1234,5678
"""

import argparse
import base64
import difflib
import html
import json
import os
import re
import ssl
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError

try:
    from markdownify import markdownify as html_to_md
except ImportError:
    sys.exit("Missing dep: pip3 install --user markdownify")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONTENT_DIR = os.path.join(REPO_ROOT, "content")
ENV_PATH = os.path.join(REPO_ROOT, "credentials", ".env")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# Map WP user slug → local data/authors.toml slug. WP slugs that match exactly
# don't need an entry. Add overrides here when the WP slug differs.
AUTHOR_SLUG_OVERRIDES = {
    "kamaraj-mathiarasan": "kamaraj",
}


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k] = v
    return env


def wp_get(env, path):
    url = env["WP_URL"].rstrip("/") + path
    auth = base64.b64encode(f"{env['WP_USER']}:{env['WP_APP_PASSWORD']}".encode()).decode()
    req = Request(url, headers={
        "Authorization": f"Basic {auth}",
        "User-Agent": "PR-wp-sync/1.0",
    })
    return urlopen(req, timeout=30, context=SSL_CTX)


def fetch_all_posts(env):
    out = []
    page = 1
    while True:
        try:
            with wp_get(env, f"/wp-json/wp/v2/posts?per_page=100&page={page}&status=publish") as r:
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


def fetch_categories(env):
    with wp_get(env, "/wp-json/wp/v2/categories?per_page=100") as r:
        return {c["id"]: c["name"] for c in json.load(r)}


def fetch_users(env):
    with wp_get(env, "/wp-json/wp/v2/users?per_page=100") as r:
        return {u["id"]: u["slug"] for u in json.load(r)}


def fetch_media_url(env, media_id):
    if not media_id:
        return ""
    try:
        with wp_get(env, f"/wp-json/wp/v2/media/{media_id}") as r:
            m = json.load(r)
        src = m.get("source_url", "")
        # Convert absolute WP URL to a Hugo /images/... path matching prior convention
        if src and "/wp-content/uploads/" in src:
            return "/images/wp-import/" + src.split("/wp-content/uploads/")[-1].split("/")[-1]
        return src
    except Exception:
        return ""


def scrape_seo_meta(url):
    """Pull <title>, meta description, og:image, JSON-LD from the live page."""
    out = {"meta_title": "", "meta_description": "", "og_image": "", "schema": []}
    try:
        req = Request(url, headers={"User-Agent": "PR-wp-sync/1.0"})
        html = urlopen(req, timeout=20, context=SSL_CTX).read().decode("utf-8", errors="ignore")
    except Exception:
        return out
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    if m:
        out["meta_title"] = m.group(1).strip()
    m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if m:
        out["meta_description"] = m.group(1).strip()
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if m:
        out["og_image"] = m.group(1).strip()
    for sm in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
        try:
            out["schema"].append(json.loads(sm.group(1).strip()))
        except Exception:
            pass
    return out


def author_slug(wp_user_slug):
    return AUTHOR_SLUG_OVERRIDES.get(wp_user_slug, wp_user_slug)


def target_path(link, slug):
    """Decide content/blogs/ or content/research/ from the live URL path."""
    parts = link.split("piperocket.digital/")[-1].strip("/").split("/")
    section = parts[0] if parts else ""
    if section not in ("blogs", "research"):
        return None
    return os.path.join(CONTENT_DIR, section, f"{slug}.md")


def find_existing_by_wpid(wp_id):
    """Scan content/ for the .md whose frontmatter has wp_id == wp_id."""
    needle = re.compile(rf'^wp_id:\s*{wp_id}\s*$', re.M)
    for section in ("blogs", "research"):
        d = os.path.join(CONTENT_DIR, section)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".md"):
                continue
            fp = os.path.join(d, fn)
            with open(fp) as f:
                head = f.read(4000)
            if needle.search(head):
                return fp
    return None


INTERNAL_LINK_RE = re.compile(r'\[([^\]]+)\]\((/[^)]+)\)')


def extract_internal_links(md_text):
    """Return list of (text, url) for every relative-link Markdown anchor."""
    return [(m.group(1), m.group(2)) for m in INTERNAL_LINK_RE.finditer(md_text)]


def hugo_lastmod(path):
    if not path or not os.path.exists(path):
        return None
    with open(path) as f:
        head = f.read(4000)
    m = re.search(r'^lastmod:\s*(\S+)', head, re.M) or re.search(r'^date:\s*(\S+)', head, re.M)
    if not m:
        return None
    val = m.group(1).strip().strip('"').strip("'")
    try:
        return datetime.fromisoformat(val.split("T")[0])
    except Exception:
        return None


def render_frontmatter(post, env, categories, users):
    """Return (yaml_frontmatter_str, body_md, target_filepath) or (None, None, None) to skip."""
    link = post["link"]
    slug = post["slug"]
    target = target_path(link, slug)
    if not target:
        return None, None, None

    title = html.unescape(post["title"]["rendered"])
    excerpt_html = post["excerpt"]["rendered"]
    description = html.unescape(re.sub(r"<[^>]+>", "", excerpt_html)).strip().replace('"', '\\"')

    seo = scrape_seo_meta(link)
    meta_title = html.unescape(seo["meta_title"]).replace('"', '\\"')
    meta_description = html.unescape(seo["meta_description"]).replace('"', '\\"')

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

    fm_lines = [
        "---",
        f'title: "{title.replace(chr(34), chr(92)+chr(34))}"',
        f'description: "{description}"',
    ]
    if meta_title and meta_title != title:
        fm_lines.append(f'meta_title: "{meta_title}"')
    if meta_description and meta_description != description:
        fm_lines.append(f'meta_description: "{meta_description}"')
    fm_lines.append(f"date: {date}")
    if modified and modified != date:
        fm_lines.append(f"lastmod: {modified}")
    fm_lines.append(f'slug: "{slug}"')
    if written_by:
        fm_lines.append(f'writtenBy: "{written_by}"')
    if cat_name:
        fm_lines.append(f'category: "{cat_name}"')
    if featured:
        fm_lines.append(f'featuredImage: "{featured}"')
    fm_lines.append(f"wp_id: {post['id']}")
    fm_lines.append(f'wp_link: "{link}"')
    # NOTE: WP JSON-LD schema is intentionally NOT written to YAML frontmatter.
    # It breaks Hugo's YAML parser, and head-meta.html already builds schema
    # from title/description/author/date front-matter fields.
    fm_lines.append("---")
    return "\n".join(fm_lines) + "\n\n", body_md, target


def classify(post, target):
    existing = find_existing_by_wpid(post["id"])
    wp_mod = datetime.fromisoformat(post["modified_gmt"][:10]) if post.get("modified_gmt") else None
    if not existing:
        return "NEW", existing
    lm = hugo_lastmod(existing)
    if wp_mod and lm and wp_mod.date() > lm.date():
        return "OUT-OF-DATE", existing
    return "IN-SYNC", existing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Actually write files (default: dry-run)")
    ap.add_argument("--diff", action="store_true", help="Write per-post unified diffs for OUT-OF-DATE posts to tmp/wp-diff/")
    ap.add_argument("--only-new", action="store_true")
    ap.add_argument("--only-stale", action="store_true")
    ap.add_argument("--ids", default="", help="Comma-separated WP IDs to limit to")
    args = ap.parse_args()

    env = load_env()
    only_ids = {int(x) for x in args.ids.split(",") if x.strip()}

    print("Fetching WP posts, categories, users…")
    posts = fetch_all_posts(env)
    categories = fetch_categories(env)
    users = fetch_users(env)

    print(f"Total posts: {len(posts)}")

    in_scope = []
    for p in posts:
        link = p.get("link", "")
        seg = link.split("piperocket.digital/")[-1].strip("/").split("/")[0] if link else ""
        if seg in ("blogs", "research"):
            in_scope.append(p)
    print(f"In scope (/blogs/ + /research/): {len(in_scope)}")
    print()

    counts = {"NEW": 0, "OUT-OF-DATE": 0, "IN-SYNC": 0, "SKIP": 0, "WRITTEN": 0}
    rows = []
    diff_dir = os.path.join(REPO_ROOT, "tmp", "wp-diff")
    diff_summary = []  # (slug, +lines, -lines, diff_path)
    link_audit = []  # {slug, file, lost: [(text,url)], kept: int}
    if args.diff:
        os.makedirs(diff_dir, exist_ok=True)
    for p in in_scope:
        if only_ids and p["id"] not in only_ids:
            counts["SKIP"] += 1
            continue
        link = p["link"]
        slug = p["slug"]
        target = target_path(link, slug)
        status, existing = classify(p, target)
        counts[status] += 1
        rows.append((status, p["id"], slug, link, existing or target))

        if args.diff and status == "OUT-OF-DATE" and existing:
            fm, body, _ = render_frontmatter(p, env, categories, users)
            if fm:
                new_text = fm + body
                with open(existing) as f:
                    old_text = f.read()
                diff = list(difflib.unified_diff(
                    old_text.splitlines(keepends=True),
                    new_text.splitlines(keepends=True),
                    fromfile=f"a/{os.path.relpath(existing, REPO_ROOT)}",
                    tofile=f"b/wp/{p['slug']}.md",
                ))
                added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
                removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
                diff_path = os.path.join(diff_dir, f"{p['slug']}.diff")
                with open(diff_path, "w") as f:
                    f.writelines(diff)
                diff_summary.append((p["slug"], added, removed, diff_path))

        if args.apply and status != "IN-SYNC":
            if args.only_new and status != "NEW":
                continue
            if args.only_stale and status != "OUT-OF-DATE":
                continue
            fm, body, tgt = render_frontmatter(p, env, categories, users)
            if not fm:
                continue
            out_path = existing or tgt
            prev_links = []
            if existing and os.path.exists(existing):
                with open(existing) as f:
                    prev_links = extract_internal_links(f.read())
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            new_text = fm + body
            with open(out_path, "w") as f:
                f.write(new_text)
            counts["WRITTEN"] += 1
            # Audit internal-link survival
            if prev_links:
                new_set = {u for _, u in extract_internal_links(new_text)}
                lost = [(t, u) for (t, u) in prev_links if u not in new_set]
                link_audit.append({
                    "slug": p["slug"],
                    "file": os.path.relpath(out_path, REPO_ROOT),
                    "previous": len(prev_links),
                    "kept": len(prev_links) - len(lost),
                    "lost": lost,
                })
            print(f"  wrote {os.path.relpath(out_path, REPO_ROOT)}")

    print()
    print("REPORT")
    print("------")
    for status, wpid, slug, link, path in sorted(rows, key=lambda r: (r[0], r[2])):
        rel = os.path.relpath(path, REPO_ROOT) if path and os.path.exists(path) else "(would create)"
        print(f"  {status:<12} wp_id={wpid:<5} {slug:<55}  {rel}")
    print()
    for k, v in counts.items():
        if v:
            print(f"  {k}: {v}")
    if args.diff and diff_summary:
        print()
        print("DIFF SUMMARY (OUT-OF-DATE)")
        print("--------------------------")
        for slug, added, removed, path in sorted(diff_summary, key=lambda r: -(r[1]+r[2])):
            print(f"  +{added:>5}  -{removed:>5}   {slug}")
        print(f"\nPer-post diffs written to: {os.path.relpath(diff_dir, REPO_ROOT)}/")

    if link_audit:
        audit_path = os.path.join(REPO_ROOT, "tmp", "wp-link-audit.json")
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        with open(audit_path, "w") as f:
            json.dump(link_audit, f, indent=2)
        print()
        print("INTERNAL LINK AUDIT (post-overwrite)")
        print("------------------------------------")
        total_prev = sum(e["previous"] for e in link_audit)
        total_lost = sum(len(e["lost"]) for e in link_audit)
        print(f"  Files audited: {len(link_audit)}   Links before: {total_prev}   Links lost: {total_lost}")
        for e in sorted(link_audit, key=lambda x: -len(x["lost"])):
            if not e["lost"]:
                continue
            print(f"\n  {e['file']}  ({len(e['lost'])} lost of {e['previous']})")
            for t, u in e["lost"][:8]:
                print(f"    - [{t}]({u})")
            if len(e["lost"]) > 8:
                print(f"    … and {len(e['lost']) - 8} more")
        print(f"\nFull audit: {os.path.relpath(audit_path, REPO_ROOT)}")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to write files.")


if __name__ == "__main__":
    main()
