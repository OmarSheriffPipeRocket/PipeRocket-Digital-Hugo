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
               if m["type"] in CONTENT and u not in redirected and len(inbound[u]) <= 1]
    order = {"list": 0, "landing": 1, "tool": 2, "blog": 3, "compare": 4, "alternative": 5, "glossary": 6}
    orphans.sort(key=lambda u: (order.get(typ[u], 9), u))

    L = ["# Interlink suggestions (plan only — no links added)\n",
         "_For each orphan / near-orphan, candidate SOURCE pages already contain the "
         "anchor phrase in-content, so a link would be natural. Pick 2-3 per target; "
         "respect the 450-word rule (no link before ~word 450) and don't link from the "
         "page's own cluster hub if already saturated._\n",
         f"\n{len(orphans)} targets with ≤1 inbound. Ordered: listicles → landing → tools → blogs → compare → glossary.\n"]

    for u in orphans:
        cands = anchor_candidates(u, prim[u], typ[u])
        # find the most-specific candidate phrase that has source matches
        best = None
        for phrase in cands:
            srcs = []
            for s, t in text.items():
                if s == u or typ[s] in NONSOURCE or s in redirected:
                    continue
                if u in outl.get(s, set()):     # already links to target
                    continue
                if phrase in t:
                    same_clus = (clus[s] == clus[u] and clus[u])
                    srcs.append((s, same_clus))
            if srcs:
                best = (phrase, srcs); break
        L.append(f"\n### `{u}`  [{typ[u]}]  (inbound {len(inbound[u])})")
        L.append(f"- target primary: \"{prim[u]}\"")
        if not best:
            L.append(f"- suggested anchor: \"{cands[0] if cands else prim[u]}\"")
            L.append("- **no existing page contains this phrase** → add a contextual mention first, "
                     "or link from the topical hub / cluster siblings manually.")
            continue
        phrase, srcs = best
        srcs.sort(key=lambda x: (not x[1], x[0]))   # same-cluster first
        L.append(f"- suggested anchor: \"{phrase}\"  ({len(srcs)} pages already use it)")
        L.append("- link FROM (✦ = same cluster):")
        for s, sc in srcs[:6]:
            L.append(f"    - {'✦ ' if sc else ''}{s}  [{typ[s]}]")

    (AUDIT / "interlink_suggestions.md").write_text("\n".join(L), encoding="utf-8")
    print(f"Wrote audit/interlink_suggestions.md  ({len(orphans)} targets)")
    # quick coverage stat
    havesrc = 0
    for u in orphans:
        cands = anchor_candidates(u, prim[u], typ[u])
        for phrase in cands:
            if any(phrase in text.get(s, "") for s in text if s != u and typ[s] not in NONSOURCE):
                havesrc += 1; break
    print(f"  targets with at least one natural source: {havesrc}/{len(orphans)}")


if __name__ == "__main__":
    main()
