"""
Download missing featuredImage thumbnails referenced from content/*.md files.

For every Markdown file with a `featuredImage: "/images/wp-import/X.ext"` field
whose local file is missing, fetch the post via WP REST API by wp_id, resolve
the featured_media → source_url, and download the bytes to static/images/wp-import/.

Run from repo root:
  python3 scripts/download_wp_thumbs.py            # dry-run
  python3 scripts/download_wp_thumbs.py --apply    # actually download
"""

import argparse
import base64
import json
import os
import re
import ssl
from urllib.request import urlopen, Request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONTENT_DIR = os.path.join(REPO_ROOT, "content")
STATIC_DIR = os.path.join(REPO_ROOT, "static")
ENV_PATH = os.path.join(REPO_ROOT, "credentials", ".env")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

FM_KEY = re.compile(r'^(\w+):\s*(.*)$')


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                env[k] = v
    return env


def auth_header(env):
    return base64.b64encode(f"{env['WP_USER']}:{env['WP_APP_PASSWORD']}".encode()).decode()


def wp_get(env, path, auth):
    url = env["WP_URL"].rstrip("/") + path
    req = Request(url, headers={"Authorization": f"Basic {auth}"})
    return urlopen(req, timeout=30, context=SSL_CTX)


def read_frontmatter(path):
    with open(path) as f:
        text = f.read()
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    fm = {}
    for line in text[4:end].split("\n"):
        m = FM_KEY.match(line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            fm[k] = v
    return fm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    env = load_env()
    auth = auth_header(env)

    todo = []  # (md_path, wp_id, expected_local_path)
    for sec in ("blogs", "research", "list"):
        d = os.path.join(CONTENT_DIR, sec)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".md"):
                continue
            fp = os.path.join(d, fn)
            fm = read_frontmatter(fp)
            img = fm.get("featuredImage", "")
            wp_id = fm.get("wp_id", "")
            if not img or not img.startswith("/images/wp-import/") or not wp_id:
                continue
            local = os.path.join(STATIC_DIR, img.lstrip("/"))
            if os.path.exists(local):
                continue
            todo.append((fp, wp_id, local))

    print(f"Missing thumbnails: {len(todo)}")
    if not todo:
        return

    out_dir = os.path.join(STATIC_DIR, "images", "wp-import")
    os.makedirs(out_dir, exist_ok=True)

    downloaded = 0
    failed = []
    for md_path, wp_id, expected_local in todo:
        try:
            with wp_get(env, f"/wp-json/wp/v2/posts/{wp_id}?_fields=featured_media", auth) as r:
                post = json.load(r)
            mid = post.get("featured_media", 0)
            if not mid:
                failed.append((md_path, "no featured_media"))
                continue
            with wp_get(env, f"/wp-json/wp/v2/media/{mid}?_fields=source_url", auth) as r:
                media = json.load(r)
            src = media.get("source_url", "")
            if not src:
                failed.append((md_path, "no source_url"))
                continue
            print(f"  {wp_id}: {src.split('/')[-1]}")
            if args.apply:
                req = Request(src, headers={"User-Agent": "PR-wp-thumb-dl/1.0"})
                with urlopen(req, timeout=60, context=SSL_CTX) as r:
                    data = r.read()
                with open(expected_local, "wb") as f:
                    f.write(data)
            downloaded += 1
        except Exception as e:
            failed.append((md_path, str(e)))

    print()
    print(f"Downloaded: {downloaded}")
    if failed:
        print(f"Failed: {len(failed)}")
        for mp, why in failed[:20]:
            print(f"  {os.path.relpath(mp, REPO_ROOT)}: {why}")
    if not args.apply:
        print("\nDry-run only. Re-run with --apply to actually download.")


if __name__ == "__main__":
    main()
