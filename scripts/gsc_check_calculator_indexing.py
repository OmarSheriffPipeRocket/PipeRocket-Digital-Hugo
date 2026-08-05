"""
Check Google indexing status for all /tools/*-calculator/ pages via the GSC
URL Inspection API.

Reuses the same OAuth token as gsc_analysis.py (webmasters.readonly scope
is sufficient for urlInspection.index.inspect, a read-only call).

Usage:
  python3 scripts/gsc_check_calculator_indexing.py
"""

import re
import sys
import time
from pathlib import Path

from gsc_analysis import get_service, pick_site, ROOT

SITE_BASE = "https://piperocket.digital"
TOOLS_DIR = ROOT / "content" / "tools"


def calculator_urls() -> list[str]:
    urls = []
    for f in sorted(TOOLS_DIR.glob("*-calculator.md")):
        urls.append(f"{SITE_BASE}/tools/{f.stem}/")
    return urls


def inspect_url(svc, site: str, url: str) -> dict:
    resp = svc.urlInspection().index().inspect(
        body={"inspectionUrl": url, "siteUrl": site}
    ).execute()
    result = resp.get("inspectionResult", {})
    idx = result.get("indexStatusResult", {})
    return {
        "url": url,
        "verdict": idx.get("verdict", "UNKNOWN"),
        "coverageState": idx.get("coverageState", ""),
        "lastCrawlTime": idx.get("lastCrawlTime", ""),
        "indexingState": idx.get("indexingState", ""),
        "googleCanonical": idx.get("googleCanonical", ""),
        "userCanonical": idx.get("userCanonical", ""),
        "pageFetchState": idx.get("pageFetchState", ""),
        "robotsTxtState": idx.get("robotsTxtState", ""),
    }


def main():
    svc = get_service()
    site = pick_site(svc)
    urls = calculator_urls()
    print(f"\nChecking {len(urls)} calculator pages against {site}\n")

    indexed, not_indexed, errors = [], [], []

    for url in urls:
        try:
            r = inspect_url(svc, site, url)
        except Exception as e:
            errors.append((url, str(e)))
            print(f"  ERROR  {url}  ({e})")
            continue

        verdict = r["verdict"]
        if verdict == "PASS":
            indexed.append(r)
            print(f"  OK     {url}  [{r['coverageState']}]")
        else:
            not_indexed.append(r)
            print(f"  MISS   {url}  verdict={verdict} state={r['coverageState']} fetch={r['pageFetchState']} robots={r['robotsTxtState']}")

        time.sleep(1)  # be gentle with quota

    print(f"\n=== Summary ===")
    print(f"Indexed:      {len(indexed)}/{len(urls)}")
    print(f"Not indexed:  {len(not_indexed)}/{len(urls)}")
    print(f"Errors:       {len(errors)}/{len(urls)}")

    if not_indexed:
        print("\nNot indexed / issues:")
        for r in not_indexed:
            print(f"  - {r['url']}")
            print(f"      verdict={r['verdict']}  coverageState={r['coverageState']!r}  "
                  f"lastCrawl={r['lastCrawlTime'] or 'never'}  pageFetch={r['pageFetchState']}  robots={r['robotsTxtState']}")

    if errors:
        print("\nErrors:")
        for url, e in errors:
            print(f"  - {url}: {e}")


if __name__ == "__main__":
    sys.exit(main() or 0)
