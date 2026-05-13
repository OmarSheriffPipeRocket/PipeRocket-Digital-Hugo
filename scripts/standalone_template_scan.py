"""Classify standalone (non-blog/non-listicle/non-glossary) pages: v2 vs default."""
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path("/Users/omarsheriff/Desktop/piperocket-site")
CONTENT = ROOT / "content"
BASE = "https://piperocket.digital"

# Pages that aren't really content (skip)
SKIP = {"_index", "privacy-policy", "terms-and-conditions"}


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "audit/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode(errors="ignore")
    except Exception:
        return ""


def classify(html):
    """v2 has stat-band + principles + heavy accordion + scrollTrigger animations."""
    stat_band = html.count("stat-band")
    principles = html.count("principles-section") + html.count("principles_")
    accordion = html.count("accordion")
    hero = html.count("hero-section") + html.count("hero__")
    tech_stack = html.count("tech-stack")
    # v2 has lots of these; default has very few/none
    score = (
        (1 if stat_band >= 8 else 0)
        + (1 if principles >= 3 else 0)
        + (1 if accordion >= 30 else 0)
        + (1 if hero >= 5 else 0)
        + (1 if tech_stack >= 2 else 0)
    )
    if score >= 3:
        return "V2"
    if score <= 1:
        return "DEFAULT"
    return "PARTIAL"


def main():
    pages = []
    for md in sorted(CONTENT.glob("*.md")):
        if md.stem in SKIP or md.stem == "_index":
            continue
        pages.append(md)

    rows = []
    for md in pages:
        slug = md.stem
        url = f"{BASE}/{slug}/"
        html = fetch(url)
        if not html:
            rows.append((md, url, "?", 0))
            continue
        t = classify(html)
        rows.append((md, url, t, len(html)))
        time.sleep(0.08)

    rows.sort(key=lambda r: (r[2], r[1]))
    print(f"\n{'template':<10}{'size':>8}  {'url'}")
    print("-" * 110)
    for md, url, t, sz in rows:
        print(f"{t:<10}{sz:>8}  {url}")

    from collections import Counter
    c = Counter(r[2] for r in rows)
    print(f"\n--- Counts ---")
    for k, v in sorted(c.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
