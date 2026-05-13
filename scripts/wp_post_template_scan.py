"""Scan all WP `post` type entries; filter to non-listicles; classify template."""
import json
import re
import time
import urllib.request

BASE = "https://piperocket.digital"


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "audit/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode(errors="ignore")
    except Exception as e:
        return f"__ERR__{e}"


def all_posts():
    all_p, page = [], 1
    while True:
        body = fetch(f"{BASE}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=id,slug,title,link,template,modified,status,categories")
        if body.startswith("__ERR__") or not body.startswith("["):
            break
        batch = json.loads(body)
        if not batch:
            break
        all_p.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        time.sleep(0.05)
    return all_p


def is_listicle(slug, title):
    t = (title or "").lower()
    s = (slug or "").lower()
    if s.startswith("best-") or s.startswith("top-") or s.startswith("my-picks-") or s.startswith("the-best") or s.startswith("the-10-") or s.startswith("the-11-") or s.startswith("the-12-") or s.startswith("12-") or s.startswith("11-") or s.startswith("10-"):
        return True
    return bool(re.search(r"\b(best|top)\b.+\bagenc", t))


def classify_template(html):
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


def main():
    posts = all_posts()
    print(f"Total WP posts: {len(posts)}\n")

    non_listicle = [p for p in posts if not is_listicle(p.get("slug"), p.get("title", {}).get("rendered"))]
    print(f"Non-listicle posts: {len(non_listicle)}\n")

    rows = []
    for p in non_listicle:
        url = p["link"]
        html = fetch(url)
        if html.startswith("__ERR__"):
            tmpl = "ERR"
        else:
            tmpl = classify_template(html)
        rows.append({
            "id": p["id"],
            "slug": p["slug"],
            "title": p.get("title", {}).get("rendered", ""),
            "url": url,
            "wp_template_field": p.get("template", ""),
            "fingerprint": tmpl,
            "modified": p.get("modified"),
        })
        time.sleep(0.08)

    rows.sort(key=lambda r: (r["fingerprint"], r["url"]))
    print(f"{'fp':<6}  {'wp_template':<25}  {'modified':<20}  url")
    print("-" * 150)
    for r in rows:
        short = r["url"].replace(BASE, "")
        tmpl_field = r["wp_template_field"] or "(default)"
        print(f"{r['fingerprint']:<6}  {tmpl_field:<25}  {r['modified'] or '':<20}  {short}")

    from collections import Counter
    c = Counter(r["fingerprint"] for r in rows)
    print(f"\n--- Fingerprint counts ---")
    for k, v in sorted(c.items()):
        print(f"  {k}: {v}")

    c2 = Counter((r["wp_template_field"] or "(default)") for r in rows)
    print(f"\n--- WP template field counts ---")
    for k, v in sorted(c2.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
