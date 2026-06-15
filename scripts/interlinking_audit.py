"""
Interlinking audit — editorial in-content link graph from the RENDERED site.

Unlike the markdown-based pass, this reads public/*.html so template-driven
landing pages are measured correctly. Scope:
  - links inside <main> only (header/footer/site-nav are outside it)
  - chrome stripped (CTA, TOC rail, author card, breadcrumb, related, subscribe,
    logo marquee, directory/blog-list grids, modals, nav/aside)
  - SOURCES exclude section-index / home / author / utility pages (their links
    are template listings/nav, not editorial equity) and redirected pages
  - targets resolved through redirects; only live content_map pages counted

Writes audit/interlinking_audit.md and prints a summary.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

from audit_content_map import load_redirects, resolve, norm_path, parse_content_map

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
AUDIT = ROOT / "audit"
RMAP, _stray, _broken = load_redirects()

CHROME = re.compile(r"(cta|__rail|author-card|breadcrumb|subscribe|related|sticky|"
                    r"marquee|modal|logo|trust-|__nav|directory|blogcats|bloglist|"
                    r"pr-footer|funnel-audit|section-search)", re.I)
# page types that are NOT editorial link sources (template/nav-driven)
NONSOURCE_TYPES = {"section", "home", "author", "utility"}
CONTENT_TYPES = {"blog", "list", "glossary", "compare", "alternative", "case-study", "landing", "tool"}


def public_file(url):
    return PUBLIC / "index.html" if url == "/" else PUBLIC / url.strip("/") / "index.html"


def incontent_targets(html):
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup
    drop = []
    for el in main.find_all(True):
        if el.name in ("nav", "aside", "header", "footer", "script", "style", "form"):
            drop.append(el); continue
        cls = " ".join(el.get("class") or [])
        if cls and CHROME.search(cls):
            drop.append(el)
    for el in drop:
        el.decompose()
    out = []
    for a in main.find_all("a", href=True):
        h = a["href"].strip()
        if h.startswith("#") or h.startswith("mailto:") or h.startswith("tel:"):
            continue
        if h.startswith("/") or "piperocket.digital" in h:
            p = norm_path(re.sub(r"https?://[^/]+", "", h).split("#")[0].split("?")[0])
            out.append(p)
    return out


def main():
    cmap = parse_content_map()
    typ = {u: m["type"] for u, m in cmap.items()}
    live = set(cmap.keys())
    redirected = {u for u in cmap if u in RMAP}

    inbound = defaultdict(set)
    outbound = defaultdict(set)
    for url, m in cmap.items():
        if m["type"] in NONSOURCE_TYPES or url in redirected:
            continue
        f = public_file(url)
        if not f.exists():
            continue
        for tgt in incontent_targets(f.read_text(encoding="utf-8", errors="ignore")):
            t = resolve(tgt, RMAP)
            if t in live and t != url and typ.get(t) not in NONSOURCE_TYPES:
                outbound[url].add(t)
                inbound[t].add(url)

    # classify content (keyword-target-ish) pages
    pages = [u for u, m in cmap.items() if m["type"] in CONTENT_TYPES and u not in redirected]
    def ind(u): return len(inbound[u])
    def outd(u): return len(outbound[u])

    orphans = sorted([u for u in pages if ind(u) == 0], key=lambda u: typ[u])
    almost = sorted([u for u in pages if ind(u) == 1], key=lambda u: typ[u])
    poor_in = sorted([u for u in pages if ind(u) == 2], key=lambda u: typ[u])
    poor_out = sorted([u for u in pages if outd(u) < 3], key=lambda u: (typ[u], outd(u)))
    both = [u for u in pages if ind(u) <= 2 and outd(u) < 3]
    hubs_in = sorted(pages, key=lambda u: -ind(u))[:15]
    hubs_out = sorted(pages, key=lambda u: -outd(u))[:15]

    # by type
    bytype = defaultdict(lambda: [0, 0, 0])  # type -> [pages, orphans, total_inbound]
    for u in pages:
        bytype[typ[u]][0] += 1
        bytype[typ[u]][1] += 1 if ind(u) == 0 else 0
        bytype[typ[u]][2] += ind(u)

    L = ["# Interlinking audit — editorial in-content link graph (rendered HTML)\n",
         f"_Scope: links inside `<main>`, chrome stripped, redirect-resolved. "
         f"Source pages exclude section-index/home/author/utility (template nav). "
         f"{len(pages)} content pages analyzed._\n",
         "\n## Summary\n",
         f"| Bucket | Pages |", "|---|---|",
         f"| Orphans (0 editorial inbound) | {len(orphans)} |",
         f"| Almost-orphans (1 inbound) | {len(almost)} |",
         f"| Poor inbound (exactly 2) | {len(poor_in)} |",
         f"| Poor outbound (<3 in-content links) | {len(poor_out)} |",
         f"| Both poor | {len(both)} |",
         "\n## By type (pages · orphans · avg inbound)\n",
         "| Type | Pages | Orphans | Avg inbound |", "|---|---|---|---|"]
    for t, (p, o, ti) in sorted(bytype.items(), key=lambda x: -x[1][0]):
        L.append(f"| {t} | {p} | {o} | {ti/p:.1f} |")

    def tbl(title, urls, cols=True):
        L.append(f"\n## {title} ({len(urls)})\n")
        if not urls:
            L.append("_none_"); return
        L.append("| Page | Type | In | Out |"); L.append("|---|---|---|---|")
        for u in urls:
            L.append(f"| {u} | {typ[u]} | {ind(u)} | {outd(u)} |")

    tbl("Orphans — 0 editorial inbound links", orphans)
    tbl("Almost-orphans — 1 inbound link", almost)
    tbl("Poor outbound — <3 in-content internal links", poor_out)
    L.append("\n## Top inbound hubs\n"); L.append("| Page | In |"); L.append("|---|---|")
    for u in hubs_in:
        L.append(f"| {u} | {ind(u)} |")

    (AUDIT / "interlinking_audit.md").write_text("\n".join(L), encoding="utf-8")
    print(f"Wrote audit/interlinking_audit.md  ({len(pages)} content pages)")
    print(f"  orphans (0 inbound)   : {len(orphans)}")
    print(f"  almost-orphans (1)    : {len(almost)}")
    print(f"  poor inbound (2)      : {len(poor_in)}")
    print(f"  poor outbound (<3)    : {len(poor_out)}")
    print(f"  both poor             : {len(both)}")
    print("  orphans by type       :", dict((t, v[1]) for t, v in bytype.items() if v[1]))


if __name__ == "__main__":
    main()
