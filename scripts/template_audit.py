"""Cross-reference template (old vs new) against GSC losers/winners."""
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path("/Users/omarsheriff/Desktop/piperocket-site")
REPORT = ROOT / "credentials" / "gsc_output" / "report_2026-05-09.json"
OUT = ROOT / "credentials" / "gsc_output" / "template_audit.json"

BASE = "https://piperocket.digital"

# Fingerprint detection rules
def classify(html: str) -> dict:
    has_toc = bool(re.search(r"table.of.contents|toc-|class=.toc", html, re.I))
    has_sidebar = bool(re.search(r"sidebar|aside class", html, re.I))
    bp_count = html.count("blog-page")
    rel_count = html.count("related-articles")
    auth_card = bool(re.search(r"author-card|written-by", html, re.I))
    is_new = has_toc and has_sidebar and bp_count >= 8
    is_old = (not has_toc or not has_sidebar) and bp_count <= 6
    template = "NEW" if is_new else ("OLD" if is_old else "MIXED")
    return {
        "template": template,
        "size": len(html),
        "has_toc": has_toc,
        "has_sidebar": has_sidebar,
        "blog_page_count": bp_count,
        "related_count": rel_count,
        "author_card": auth_card,
    }


def fetch(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "audit/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode(errors="ignore")
    except Exception:
        return ""


def main():
    report = json.loads(REPORT.read_text())

    # Pages to inspect: top losers + top gainers + top current
    pages = set()
    for key in ["top_page_losers", "top_page_gainers", "top_pages_now"]:
        for p in report.get(key, []):
            pages.add(p["page"])

    # Filter to only blog/list type URLs (template-relevant)
    pages = [p for p in pages if "/blogs/" in p or "/list/" in p]
    print(f"Scanning {len(pages)} blog/list pages for template fingerprint...\n")

    # Build lookup for GSC perf
    perf = {}
    for key in ["top_page_losers", "top_page_gainers", "top_pages_now"]:
        for p in report.get(key, []):
            if p["page"] not in perf:
                perf[p["page"]] = p

    rows = []
    for url in pages:
        html = fetch(url)
        if not html:
            print(f"  ✗ failed: {url}")
            continue
        cls = classify(html)
        gsc = perf.get(url, {})
        rows.append({"url": url, **cls, "clicks_now": gsc.get("clicks_now", 0), "clicks_prev": gsc.get("clicks_prev", 0), "clicks_delta": gsc.get("clicks_delta", 0), "impr_now": gsc.get("impr_now", 0), "impr_delta": gsc.get("impr_delta", 0), "pos_now": gsc.get("pos_now", 0), "pos_delta": gsc.get("pos_delta", 0)})
        time.sleep(0.1)

    OUT.write_text(json.dumps(rows, indent=2, default=str))

    # Sort: OLD losers first, then NEW losers
    rows.sort(key=lambda r: (r["template"], r["clicks_delta"]))

    print(f"{'template':<8}{'clicks Δ':>10}{'pos Δ':>8}{'impr Δ':>10}  url")
    for r in rows:
        d_clicks = r["clicks_delta"]
        d_pos = r["pos_delta"]
        d_impr = r["impr_delta"]
        short = r["url"].replace("https://piperocket.digital", "")
        print(f"{r['template']:<8}{d_clicks:>+10}{d_pos:>+8.1f}{d_impr:>+10}  {short}")

    # Tally
    print(f"\n=== Tally ===")
    old = [r for r in rows if r["template"] == "OLD"]
    new = [r for r in rows if r["template"] == "NEW"]
    mixed = [r for r in rows if r["template"] == "MIXED"]
    print(f"  OLD template: {len(old)} pages, total clicks delta: {sum(r['clicks_delta'] for r in old):+}")
    print(f"  NEW template: {len(new)} pages, total clicks delta: {sum(r['clicks_delta'] for r in new):+}")
    print(f"  MIXED: {len(mixed)} pages")
    print(f"\n  OLD impressions delta: {sum(r['impr_delta'] for r in old):+}")
    print(f"  NEW impressions delta: {sum(r['impr_delta'] for r in new):+}")


if __name__ == "__main__":
    main()
