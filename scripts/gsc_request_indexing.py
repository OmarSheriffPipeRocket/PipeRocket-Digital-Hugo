"""
GSC indexing requester for piperocket.digital.

Detects URLs that changed in the most recent commit(s) under `content/list/`,
then nudges Google + Bing/Yandex to re-crawl them.

Strategies (run in order, all best-effort):
  1. Ping the public sitemap so Google sees updated `lastmod` dates.
  2. POST to IndexNow (Bing/Yandex/Seznam/Naver).
  3. Submit each URL to Google's Indexing API if a service-account key is
     present at credentials/gsc-service-account.json. (See note below.)
  4. Always print a Google Search Console "URL Inspection" deep-link per
     URL so a human can click "Request Indexing" manually if needed.

ToS note on the Indexing API: Google's published spec lists JobPosting and
BroadcastEvent as the officially supported types. Submitting general content
URLs is widely done in practice (it's how every SEO indexing service works)
and does cause Google to re-crawl, but it isn't formally sanctioned. Use
at your discretion. To skip the API call, simply omit the service-account
file - the rest of the script still runs.

Usage:
  # Auto-detect from the most recent commit (default after a batch commit)
  python3 scripts/gsc_request_indexing.py

  # Specify a commit range
  python3 scripts/gsc_request_indexing.py --range HEAD~2..HEAD

  # Pass URLs directly
  python3 scripts/gsc_request_indexing.py \\
      --url https://piperocket.digital/list/best-saas-seo-agencies/ \\
      --url https://piperocket.digital/list/top-fintech-seo-agencies/
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_BASE = "https://piperocket.digital"
SITEMAP_URL = f"{SITE_BASE}/sitemap.xml"

SERVICE_ACCOUNT_FILE = ROOT / "credentials" / "gsc-service-account.json"
INDEXNOW_KEY_FILE = ROOT / "credentials" / "indexnow.key"


def changed_listicle_urls(rev_range: str) -> list[str]:
    """Return public URLs for listicle .md files changed in the given revision range."""
    cmd = ["git", "diff", "--name-only", rev_range, "--", "content/list/"]
    out = subprocess.check_output(cmd, cwd=ROOT, text=True).strip()
    urls: list[str] = []
    for path in out.splitlines():
        if not path.endswith(".md") or path.endswith("_index.md"):
            continue
        slug = Path(path).stem
        urls.append(f"{SITE_BASE}/list/{slug}/")
    return sorted(set(urls))


def ping_sitemap() -> None:
    """Google retired the sitemap ping endpoint in June 2023 and now relies on
    `lastmod` dates in the sitemap itself plus discovery via crawl. We already
    set `lastmod` on every rewrite, so this function only prints a confirmation
    that the sitemap will be re-read on Google's next scheduled crawl."""
    print(f"  Sitemap at {SITEMAP_URL} carries fresh lastmod; Google re-reads on next crawl.")
    print("  (Google retired the manual ping endpoint in June 2023.)")


def indexnow_submit(urls: list[str]) -> None:
    """POST a batch to api.indexnow.org. Requires a key file hosted at
    https://piperocket.digital/<KEY>.txt so the search engine can validate
    ownership. The local file at credentials/indexnow.key holds that key."""
    if not INDEXNOW_KEY_FILE.exists():
        print("  IndexNow skipped: credentials/indexnow.key not found")
        return
    key = INDEXNOW_KEY_FILE.read_text().strip()
    payload = {
        "host": "piperocket.digital",
        "key": key,
        "keyLocation": f"{SITE_BASE}/{key}.txt",
        "urlList": urls,
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.indexnow.org/IndexNow",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"  IndexNow: HTTP {resp.status} ({len(urls)} URLs)")
    except Exception as e:
        print(f"  IndexNow failed: {e}")


def google_indexing_api(urls: list[str]) -> None:
    """Call the Indexing API per URL using a service-account credential.
    See ToS note in the module docstring."""
    if not SERVICE_ACCOUNT_FILE.exists():
        print("  Indexing API skipped: credentials/gsc-service-account.json not found")
        return
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("  Indexing API skipped: install with `pip install google-api-python-client google-auth`")
        return

    creds = service_account.Credentials.from_service_account_file(
        str(SERVICE_ACCOUNT_FILE),
        scopes=["https://www.googleapis.com/auth/indexing"],
    )
    service = build("indexing", "v3", credentials=creds, cache_discovery=False)
    ok, failed = 0, 0
    for url in urls:
        try:
            service.urlNotifications().publish(
                body={"url": url, "type": "URL_UPDATED"}
            ).execute()
            ok += 1
        except Exception as e:
            failed += 1
            print(f"    failed {url}: {e}")
    print(f"  Indexing API: {ok} ok, {failed} failed")


def gsc_inspection_links(urls: list[str]) -> list[str]:
    """Deep-links into the GSC URL Inspection tool. Click 'Request Indexing'
    after the page loads to formally request a re-crawl."""
    site = urllib.parse.quote(f"{SITE_BASE}/", safe="")
    return [
        f"https://search.google.com/search-console/inspect?resource_id={site}&id={urllib.parse.quote(u, safe='')}"
        for u in urls
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--range",
        default="HEAD~1..HEAD",
        help="Git revision range to inspect (default: HEAD~1..HEAD)",
    )
    parser.add_argument(
        "--url",
        action="append",
        default=[],
        help="URL to submit (repeatable). Overrides --range when provided.",
    )
    parser.add_argument(
        "--no-sitemap",
        action="store_true",
        help="Skip sitemap ping",
    )
    parser.add_argument(
        "--no-indexnow",
        action="store_true",
        help="Skip IndexNow submission",
    )
    parser.add_argument(
        "--no-google",
        action="store_true",
        help="Skip Google Indexing API submission",
    )
    args = parser.parse_args()

    urls = args.url or changed_listicle_urls(args.range)
    if not urls:
        print(f"No listicle URLs to submit in {args.range}.")
        return 0

    print(f"Submitting {len(urls)} URL(s) for re-indexing:")
    for u in urls:
        print(f"  - {u}")
    print()

    if not args.no_sitemap:
        print("Sitemap ping:")
        ping_sitemap()
        print()

    if not args.no_indexnow:
        print("IndexNow (Bing/Yandex/Seznam/Naver):")
        indexnow_submit(urls)
        print()

    if not args.no_google:
        print("Google Indexing API:")
        google_indexing_api(urls)
        print()

    print("Google Search Console deep-links (click 'Request Indexing' after page loads):")
    for link in gsc_inspection_links(urls):
        print(f"  {link}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
