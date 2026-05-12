"""Scan all non-listicle blogs and classify template."""
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path("/Users/omarsheriff/Desktop/piperocket-site")
CONTENT = ROOT / "content"
BASE = "https://piperocket.digital"


def classify(html: str) -> str:
    has_toc = bool(re.search(r"table.of.contents|toc-|class=.toc", html, re.I))
    has_sidebar = bool(re.search(r"sidebar|aside class", html, re.I))
    bp = html.count("blog-page")
    if not has_sidebar and bp <= 4:
        return "OLD"
    if has_sidebar and bp == 0:
        return "NEW"
    if has_toc and has_sidebar and bp >= 8:
        return "NEW"
    return "MIXED"


def fetch_url_from_md(md):
    text = md.read_text(errors="ignore")
    m = re.search(r'^url:\s*"([^"]+)"', text, re.M)
    if m:
        return m.group(1)
    m = re.search(r'^slug:\s*"([^"]+)"', text, re.M)
    folder = md.parent.name
    slug = m.group(1) if m else md.stem
    return f"/{folder}/{slug}/"


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "audit/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode(errors="ignore")
    except Exception:
        return ""


def is_listicle(name):
    return (
        name.startswith("best-")
        or name.startswith("top-")
        or name.startswith("my-picks-")
        or "agencies-for-" in name
        or "agencies-in-" in name
    )


def main():
    targets = []
    for f in (CONTENT / "blogs").glob("*.md"):
        if f.name == "_index.md":
            continue
        if is_listicle(f.stem):
            continue
        targets.append(f)

    rows = []
    for md in sorted(targets):
        path = fetch_url_from_md(md)
        url = f"{BASE}{path}"
        html = get(url)
        if not html:
            rows.append((md, path, "?"))
            continue
        rows.append((md, path, classify(html)))
        time.sleep(0.08)

    rows.sort(key=lambda r: (r[2], r[1]))

    print(f"\n{'template':<8}  {'url':<70}  {'source file'}")
    print("-" * 130)
    for md, path, t in rows:
        rel = md.relative_to(CONTENT)
        print(f"{t:<8}  {path:<70}  {rel}")

    from collections import Counter
    c = Counter(r[2] for r in rows)
    print(f"\n--- Counts ---")
    for k, v in sorted(c.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
