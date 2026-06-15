"""
Interlink SUGGESTIONS (does NOT add any links).

For each orphan / near-orphan target, find existing pages whose in-content text
already contains a natural anchor phrase for that target — so a link would be
contextual, not forced. Output a ready-to-action plan: target -> suggested
anchor -> candidate source pages (where the phrase already appears).

Writes audit/interlink_suggestions.md.
"""

import re
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup
from audit_content_map import load_redirects, resolve, norm_path, parse_content_map

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
AUDIT = ROOT / "audit"
RMAP, _s, _b = load_redirects()
CHROME = re.compile(r"(cta|__rail|author-card|breadcrumb|subscribe|related|sticky|"
                    r"marquee|logo|trust-|__nav|directory|blogcats|bloglist|pr-footer|"
                    r"funnel-audit|section-search|modal)", re.I)
NONSOURCE = {"section", "home", "author", "utility"}
CONTENT = {"blog", "list", "glossary", "compare", "alternative", "case-study", "landing", "tool"}
# scoping (per Omar):
EXCLUDE_TARGET_TYPES = {"tool"}          # tools pending redesign — skip
EXCLUDE_SOURCES = {"/blogs/saas-seo/"}   # being rewritten — don't propose as a link source


def pf(u):
    return PUBLIC / "index.html" if u == "/" else PUBLIC / u.strip("/") / "index.html"


def main_text_and_links(html):
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
    links = set()
    for a in main.find_all("a", href=True):
        h = a["href"]
        if h.startswith("/") or "piperocket.digital" in h:
            links.add(resolve(norm_path(re.sub(r"https?://[^/]+", "", h).split("#")[0].split("?")[0]), RMAP))
    text = re.sub(r"\s+", " ", main.get_text(" ")).lower()
    return text, links


def anchor_candidates(url, primary, ptype):
    """Most-specific-first natural anchor phrases for linking TO this target."""
    p = (primary or "").lower().strip()
    c = []
    if ptype == "list":
        c += [p]                                  # best technical seo agencies
        c += [re.sub(r"^best\s+|^top\s+", "", p)]  # technical seo agencies
        c += [re.sub(r"agencies$", "agency", re.sub(r"^best\s+|^top\s+", "", p))]
        if "tools" in p:
            c += [re.sub(r"^best\s+", "", p)]
    elif ptype == "landing":
        c += [p, p.replace(" agency", " marketing"), p.replace(" agency", "")]
    elif ptype == "tool":
        slug = url.strip("/").split("/")[-1].replace("-", " ")
        c += [slug, slug.replace("free ", ""), "roi calculator" if "roi" in slug else "roas calculator"]
    else:  # blog, glossary, compare, alternative
        c += [p]
        if ptype == "glossary":
            c += [re.sub(r"^what is (a |an |the )?", "", p)]
    # clean
    seen, out = set(), []
    for x in c:
        x = re.sub(r"\s+", " ", x or "").strip()
        if x and len(x) > 4 and x not in seen:
            seen.add(x); out.append(x)
    return out


def main():
    cmap = parse_content_map()
    typ = {u: m["type"] for u, m in cmap.items()}
    prim = {u: m["primary"] for u, m in cmap.items()}
    clus = {u: (m["cluster"] or "") for u, m in cmap.items()}
    live = set(cmap.keys())
    redirected = {u for u in cmap if u in RMAP}

    # build text + outbound-link set per source page
    text, outl = {}, {}
    inbound = defaultdict(set)
    for u, m in cmap.items():
        f = pf(u)
        if not f.exists():
            continue
        t, links = main_text_and_links(f.read_text(encoding="utf-8", errors="ignore"))
        text[u] = t
        outl[u] = links
        if m["type"] not in NONSOURCE and u not in redirected:
            for tg in links:
                if tg in live and tg != u:
                    inbound[tg].add(u)

    orphans = [u for u, m in cmap.items()
               if m["type"] in CONTENT and m["type"] not in EXCLUDE_TARGET_TYPES
               and u not in redirected and len(inbound[u]) <= 1]
    order = {"list": 0, "landing": 1, "blog": 2, "compare": 3, "alternative": 4, "glossary": 5}
    orphans.sort(key=lambda u: (order.get(typ[u], 9), u))

    def best_sources(u):
        for phrase in anchor_candidates(u, prim[u], typ[u]):
            srcs = []
            for s, t in text.items():
                if s == u or typ[s] in NONSOURCE or s in redirected or s in EXCLUDE_SOURCES:
                    continue
                if u in outl.get(s, set()):
                    continue
                if phrase in t:
                    srcs.append((s, clus[s] == clus[u] and bool(clus[u])))
            if srcs:
                srcs.sort(key=lambda x: (not x[1], x[0]))
                return phrase, srcs
        return None

    phase1, phase2 = [], []
    for u in orphans:
        b = best_sources(u)
        (phase1 if b else phase2).append((u, b))

    L = ["# Interlink suggestions (plan only — no links added)\n",
         "_Scope: tools excluded (redesign pending); `/blogs/saas-seo/` excluded as a source "
         "(being rewritten); glossary included. For each target, candidate SOURCE pages already "
         "contain the anchor phrase, so a link is natural. Respect the 450-word rule._\n",
         f"\n**Phase 1 — ready now ({len(phase1)} targets, have a natural source).** "
         f"**Phase 2 — need a contextual mention added first ({len(phase2)} targets).**\n",
         "\n## PHASE 1 — ready to interlink\n"]
    for u, b in phase1:
        phrase, srcs = b
        L.append(f"\n### `{u}`  [{typ[u]}]  (inbound {len(inbound[u])})")
        L.append(f"- anchor: \"{phrase}\"  · link FROM (✦ same cluster):")
        for s, sc in srcs[:6]:
            L.append(f"    - {'✦ ' if sc else ''}{s}  [{typ[s]}]")
    L.append("\n## PHASE 2 — no natural source yet (add a mention or hub link)\n")
    for u, _ in phase2:
        L.append(f"- `{u}`  [{typ[u]}]  — anchor \"{(anchor_candidates(u, prim[u], typ[u]) or [prim[u]])[0]}\"")

    (AUDIT / "interlink_suggestions.md").write_text("\n".join(L), encoding="utf-8")
    print(f"Wrote audit/interlink_suggestions.md")
    print(f"  Phase 1 (ready): {len(phase1)}   Phase 2 (need mention): {len(phase2)}")
    from collections import Counter
    print("  Phase 1 by type:", dict(Counter(typ[u] for u, _ in phase1)))


if __name__ == "__main__":
    main()
