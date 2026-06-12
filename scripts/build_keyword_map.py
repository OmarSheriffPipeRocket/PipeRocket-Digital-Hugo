"""
Bootstrap data/keyword_map.yml — the page→target-keyword ownership ledger.

Phase-1 scope: blogs + glossary + list (the cannibalization-prone, deliberately
interlinked set).
Phase-2 scope: landing/service pages + compare + alternative + case-study + tools
(the money pages + branded/navigational set). Together these cover the full
indexable corpus minus pure utility/legal/conversion pages (see LANDING_EXCLUDE).

For each in-scope page:
  1. primary candidate from slug/title (reuses generate_link_map.py extractors)
  2. OVERRIDE primary with the page's real GSC top query, when an export exists
     (credentials/gsc_output/qp_rollup_<date>.json). Disagreements between the
     slug guess and GSC reality get a `# REVIEW: slug said "..."` inline comment.
  3. secondary[] seeded from the page's other high-impression GSC queries
  4. cluster + cluster_entity by fuzzy-matching primary against entity_map.yml
  5. intent + funnel pre-filled by heuristic (marked for human review)

Runs OFFLINE if no GSC export is present (slug-only primaries) so the map is
buildable now and re-runnable once gsc_query_page.py has produced a rollup.

Usage:
  python3 scripts/gsc_query_page.py        # optional but recommended first
  python3 scripts/build_keyword_map.py
"""

import re
import sys
from pathlib import Path

from generate_link_map import read_frontmatter, clean_blog_anchor, clean_listicle_anchors

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
ENTITY_MAP = ROOT / "data" / "entity_map.yml"
GSC_DIR = ROOT / "credentials" / "gsc_output"
OUT_FILE = ROOT / "data" / "keyword_map.yml"

# Section-based scopes live under content/<section>/*.md.
# "landing" is special: root-level content/*.md with URL /<slug>/ (no section).
SECTION_SCOPE = ["blogs", "glossary", "list",            # phase 1
                 "compare", "alternative", "case-study", "tools"]  # phase 2

# Root-level content/*.md pages that carry NO keyword target — pure
# utility / legal / conversion / form pages. They are still listed in the map
# (complete page inventory) but as type "utility" with a blank primary and
# keyword_target: false. Everything else at the root (service + industry
# landing pages, pricing, reviews) is a "landing" entry.
UTILITY_PAGES = {
    "about-us", "contact-us", "careers", "partnership",
    "privacy-policy", "terms-and-conditions", "cookies-policy",
    "research-methodology", "schedule-a-demo", "webinar-pritesh",
    "write-for-us", "faqs", "saas-ppc-faqs", "saas-seo-agency-faqs",
}

# Display label per content type (mirrors Phase-1: blogs->blog, list stays list).
TYPE_LABEL = {
    "blogs": "blog", "glossary": "glossary", "list": "list",
    "landing": "landing", "compare": "compare", "alternative": "alternative",
    "case-study": "case-study", "tools": "tool", "utility": "utility",
    "author": "author", "section": "section", "home": "home",
}

# Types that carry NO keyword target (inventory-only). Home is NOT here — the
# user assigns it the head term "saas marketing agency".
NO_KEYWORD_TYPES = {"utility", "author", "section"}

# The home page's assigned head keyword (fixed, not GSC-seeded — GSC top query
# is the bare brand, which the junk filter would drop anyway).
HOME_PRIMARY = "saas marketing agency"

STOPWORDS = {"the", "a", "an", "for", "to", "in", "of", "and", "on", "your", "with",
             "best", "top", "how", "what", "is", "are", "guide", "complete",
             "2024", "2025", "2026"}


# ---------- frontmatter helpers ----------

def read_extra_fm(filepath):
    """Pull category / glossaryCategory / lastmod beyond what read_frontmatter gives."""
    try:
        fm = filepath.read_text(encoding="utf-8").split("---", 2)[1]
    except Exception:
        return {}
    out = {}
    for line in fm.splitlines():
        m = re.match(r'\s*(category|glossaryCategory|date|lastmod):\s*"?([^"]+?)"?\s*$', line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


# ---------- GSC rollup ----------

def load_gsc_rollup():
    """Return {path: rollup_dict} from the newest qp_rollup_*.json, or {} if none."""
    files = sorted(GSC_DIR.glob("qp_rollup_*.json"))
    if not files:
        print("No GSC rollup found — building slug/title-only primaries.", file=sys.stderr)
        return {}, None
    latest = files[-1]
    import json
    data = json.loads(latest.read_text())
    by_path = {}
    for p in data.get("pages", []):
        path = url_to_path(p["page"])
        if path:
            by_path[path] = p
    print(f"Loaded GSC rollup {latest.name} ({len(by_path)} pages)", file=sys.stderr)
    return by_path, latest.name


def is_junk_query(q):
    """A GSC query that is never a real target keyword: the bare brand/domain
    or a `site:` operator. Used so GSC seeding can't pick these as `primary`."""
    ql = (q or "").lower().strip()
    if not ql:
        return True
    if "site:" in ql or ql.startswith("http"):
        return True
    # GSC spam: LLM-scraper prompt strings leak in as "queries". Real target
    # keywords are short — drop anything implausibly long or many-worded.
    if len(ql) > 80 or len(ql.split()) > 10:
        return True
    return ql in {"piperocket", "piperocket digital", "piperocket.digital",
                  "pipe rocket", "www.piperocket.digital"}


def page_url(fm_url, default):
    """The page's real path: frontmatter `url:` override (normalized to a
    leading+trailing slash) when set, else the section/slug-derived default.
    Many pages (case studies, authors, nested FAQs) publish at a custom url."""
    if fm_url:
        u = fm_url.strip()
        if not u.startswith("/"):
            u = "/" + u
        if not u.endswith("/"):
            u += "/"
        return u
    return default


def url_to_path(url):
    """https://piperocket.digital/blogs/x/ -> /blogs/x/ ; pass through if already a path."""
    if not url:
        return None
    m = re.search(r"https?://[^/]+(/.*)$", url)
    path = m.group(1) if m else url
    if not path.startswith("/"):
        path = "/" + path
    return path


# ---------- entity-map cluster matching ----------

def singularize(w):
    # naive: strip a trailing plural 's' (but keep "ss" like "process"). Applied to
    # both the page primary and the entity strings, so "backlinks"≈"backlink".
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def normalize(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return [singularize(w) for w in s.split() if w not in STOPWORDS and len(w) > 1]


def load_entity_clusters():
    """Return {cluster_key: [(entity_string, token_set), ...]} from entity_map.yml.

    Minimal hand-parse (avoids a hard PyYAML dep): top-level `key:` at col 0 opens
    a cluster; `- Entity` list items anywhere under it are collected.
    """
    clusters = {}
    cur = None
    for line in ENTITY_MAP.read_text(encoding="utf-8").splitlines():
        if re.match(r"^[a-z][a-z0-9\-]*:\s*$", line):       # top-level cluster key
            cur = line.split(":")[0]
            clusters[cur] = []
        elif cur and re.match(r"^\s*-\s+\S", line):          # list item (entity)
            ent = line.strip()[1:].strip().strip('"')
            toks = set(normalize(ent))
            if toks:
                clusters[cur].append((ent, toks))
    return clusters


def match_cluster(primary, clusters):
    """Best (cluster_key, entity) by token-Jaccard against primary; None if weak."""
    ptoks = set(normalize(primary))
    if not ptoks:
        return None, None
    best, best_score = (None, None), 0.0
    for ckey, ents in clusters.items():
        for ent, etoks in ents:
            inter = len(ptoks & etoks)
            if not inter:
                continue
            score = inter / len(ptoks | etoks)
            if score > best_score:
                best, best_score = (ckey, ent), score
    return best if best_score >= 0.34 else (None, None)


# ---------- intent / funnel heuristics ----------

def guess_intent_funnel(ctype, title, slug):
    t = (title or "").lower()
    s = (slug or "").lower()
    if ctype == "glossary":
        return "informational", "tofu"
    if ctype == "list":
        return "commercial", "mofu"           # "best X agencies" = vendor research
    if ctype == "landing":
        return "commercial", "bofu"           # service/industry money pages
    if ctype == "compare":
        # PipeRocket-vs-X is branded/navigational; neutral A-vs-B is commercial
        nav = "piperocket" in s or "pipe-rocket" in s
        return ("navigational" if nav else "commercial"), "bofu"
    if ctype == "alternative":
        return "commercial", "bofu"           # "X alternatives" = switching intent
    if ctype == "case-study":
        return "navigational", "bofu"         # branded proof, not keyword-led
    if ctype == "tools":
        return "transactional", "tofu"        # free calculators = tool intent
    if ctype == "utility":
        return "navigational", "none"         # legal/utility/conversion, no funnel
    if ctype == "author":
        return "navigational", "none"         # E-E-A-T byline pages
    if ctype == "section":
        return "navigational", "none"         # directory/index listing pages
    if ctype == "home":
        return "commercial", "bofu"           # head term: saas marketing agency
    # blogs
    if " vs " in t or "-vs-" in s:
        return "commercial", "bofu"
    if re.search(r"\bbest\b.*\b(agenc|tool|software|platform)", t):
        return "commercial", "mofu"
    if t.startswith("how to") or t.startswith("what is") or "guide" in t or "examples" in t:
        return "informational", "tofu"
    return "informational", "tofu"


# ---------- primary derivation ----------

def slug_primary(ctype, title, slug):
    if ctype == "blogs":
        cands = clean_blog_anchor(title)
    elif ctype == "list":
        cands = clean_listicle_anchors(title, slug)
    elif ctype == "glossary":  # strip "what is", "?", trailing clauses
        t = re.sub(r"^what is\s+", "", (title or ""), flags=re.I)
        t = re.split(r"[?:]", t)[0].strip()
        cands = [t] if t else []
    elif ctype == "compare":  # "piperocket-digital-vs-klientboost" -> "... vs ..."
        cands = [(slug or "").replace("-vs-", " vs ").replace("-", " ").strip()]
    elif ctype == "case-study":  # branded: "<company> case study"
        base = (slug or "").replace("-", " ").strip()
        cands = [f"{base} case study"] if base else []
    else:  # landing, alternative ("X alternatives"), tools — slug IS the keyword
        cands = [(slug or "").replace("-", " ").strip()]
    return cands[0] if cands else (slug or "").replace("-", " ")


# ---------- build ----------

def iter_pages():
    """Yield (ctype, path, file) across Phase-1 + Phase-2 scopes.

    Order: root landing pages first within their slot, sections in SECTION_SCOPE
    order — so Phase-1 entries (blogs/glossary/list) keep their positions and the
    diff for a re-run is append-only for the new Phase-2 sections.
    """
    for ctype in SECTION_SCOPE:
        for f in sorted((CONTENT_DIR / ctype).glob("*.md")):
            if f.name == "_index.md":
                continue
            slug, _, url = read_frontmatter(f)
            if not slug:
                continue
            # case-study has a [permalinks] rule /case-study-:slug/ in hugo.toml
            default = (f"/case-study-{slug}/" if ctype == "case-study"
                       else f"/{ctype}/{slug}/")
            yield ctype, page_url(url, default), f
    # author byline pages -> /author/<slug>/  (E-E-A-T, no keyword target)
    for f in sorted((CONTENT_DIR / "author").glob("*.md")):
        if f.name == "_index.md":
            continue
        slug, _, url = read_frontmatter(f)
        if slug:
            yield "author", page_url(url, f"/author/{slug}/"), f
    # home page -> /  (keyword target) and directory index pages -> /<section>/
    for f in sorted(CONTENT_DIR.glob("**/_index.md")):
        rel = f.parent.relative_to(CONTENT_DIR).as_posix()
        if rel == ".":
            yield "home", "/", f
        else:
            yield "section", f"/{rel}/", f
    # root-level pages (no section) -> /<slug>/. Service/industry pages are
    # "landing" (keyword targets); utility/legal/conversion pages are "utility".
    for f in sorted(CONTENT_DIR.glob("*.md")):
        if f.name == "_index.md":
            continue
        slug, _, url = read_frontmatter(f)
        if not slug:
            continue
        ctype = "utility" if slug in UTILITY_PAGES else "landing"
        yield ctype, page_url(url, f"/{slug}/"), f


def build():
    clusters = load_entity_clusters()
    gsc, gsc_src = load_gsc_rollup()
    entries = []

    for ctype, path, f in iter_pages():
        slug, title, _ = read_frontmatter(f)
        no_keyword = ctype in NO_KEYWORD_TYPES   # utility / author / section

        # primary candidate: home gets its fixed head term, no-keyword types get
        # nothing, everything else derives from slug/title.
        if ctype == "home":
            slug_kw = HOME_PRIMARY
        elif no_keyword:
            slug_kw = ""
        else:
            slug_kw = slug_primary(ctype, title, slug)
        primary = slug_kw
        review_note = None
        secondary, gsc_block = [], None

        g = gsc.get(path)
        if g:
            top = g["top_query"]
            # Seed primary from GSC reality, but never let a junk query
            # (bare brand/domain, site: operator) become the target keyword.
            # No-keyword pages never seed a primary; the home keyword is fixed —
            # but the gsc block is still attached as an informational add-on.
            if not no_keyword and ctype != "home" and not is_junk_query(top):
                primary = top
                if normalize(primary) != normalize(slug_kw):
                    review_note = f'slug said "{slug_kw}"'
            if not no_keyword:
                # secondary = next few queries, excluding the primary + junk
                for q in g.get("queries", [])[1:6]:
                    if is_junk_query(q["query"]):
                        continue
                    if normalize(q["query"]) != normalize(primary):
                        secondary.append(q["query"])
            gsc_block = {
                "top_query": g["top_query"],
                "impressions": g["top_query_impressions"],
                "clicks": g["top_query_clicks"],
                "position": g["top_query_position"],
                "total_impressions": g["total_impressions"],
            }

        ckey, centity = (None, None) if no_keyword else match_cluster(primary, clusters)
        intent, funnel = guess_intent_funnel(ctype, title, slug)

        entries.append({
            "url": path, "type": TYPE_LABEL.get(ctype, ctype),
            "keyword_target": not no_keyword,
            "primary": primary, "review_note": review_note,
            "secondary": secondary,
            "intent": intent, "funnel": funnel,
            "cluster": ckey, "cluster_entity": centity,
            "canonical_for": primary,
            "status": "active",
            "gsc": gsc_block,
        })

    write_yaml(entries, gsc_src)
    summarize(entries, gsc_src)


# ---------- YAML emit (hand-rolled for comments + stable ordering) ----------

def yq(s):
    """Quote a scalar for YAML."""
    s = str(s).replace('"', '\\"')
    return f'"{s}"'


def write_yaml(entries, gsc_src):
    L = [
        "# data/keyword_map.yml — page → target-keyword ownership ledger",
        "# Generated by scripts/build_keyword_map.py.",
        "# Phase 1: blogs + glossary + list.  Phase 2: landing + compare + alternative + case-study + tools.",
        "# `primary` is GSC-seeded where data exists (junk brand/site: queries filtered), else slug/title-derived.",
        "# REVIEW the intent/funnel fields and any `# REVIEW:` lines before relying on them.",
        f"# GSC source: {gsc_src or 'none (slug/title-only build)'}",
        "",
        "meta:",
        '  gsc_property: "sc-domain:piperocket.digital"',
        f"  gsc_snapshot: {yq(gsc_src) if gsc_src else 'null'}",
        f"  page_count: {len(entries)}",
        "",
        "pages:",
    ]
    for e in entries:
        head = f"  - url: {yq(e['url'])}"
        if e["review_note"]:
            head += f"          # REVIEW: {e['review_note']}"
        L.append(head)
        L.append(f"    type: {e['type']}")
        # Utility/legal pages are part of the inventory but carry no keyword
        # target — flag them explicitly; keyword pages omit the field (= true).
        if not e.get("keyword_target", True):
            L.append("    keyword_target: false")
        L.append(f"    primary: {yq(e['primary'])}")
        if e["secondary"]:
            L.append("    secondary:")
            for s in e["secondary"]:
                L.append(f"      - {yq(s)}")
        else:
            L.append("    secondary: []")
        # Fixed intent/funnel for utility pages need no human review.
        rev = "        # REVIEW" if e.get("keyword_target", True) else ""
        L.append(f"    intent: {e['intent']}{rev}")
        L.append(f"    funnel: {e['funnel']}{'            # REVIEW' if e.get('keyword_target', True) else ''}")
        L.append(f"    cluster: {e['cluster'] or 'null'}")
        if e["cluster_entity"]:
            L.append(f"    cluster_entity: {yq(e['cluster_entity'])}")
        L.append(f"    canonical_for: {yq(e['canonical_for'])}")
        L.append(f"    status: {e['status']}")
        if e["gsc"]:
            g = e["gsc"]
            L.append("    gsc:")
            L.append(f"      top_query: {yq(g['top_query'])}")
            L.append(f"      impressions: {g['impressions']}")
            L.append(f"      clicks: {g['clicks']}")
            L.append(f"      position: {g['position']}")
            L.append(f"      total_impressions: {g['total_impressions']}")
        L.append("")
    OUT_FILE.write_text("\n".join(L), encoding="utf-8")


def summarize(entries, gsc_src):
    by_type, gsc_seeded, no_cluster, reviews = {}, 0, 0, 0
    for e in entries:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
        if e["gsc"]:
            gsc_seeded += 1
        if not e["cluster"]:
            no_cluster += 1
        if e["review_note"]:
            reviews += 1
    print(f"\nWrote {OUT_FILE}  ({len(entries)} pages)")
    for k, v in sorted(by_type.items()):
        print(f"  {k:10s}: {v}")
    print(f"  GSC-seeded primaries : {gsc_seeded}/{len(entries)}"
          + (f" (from {gsc_src})" if gsc_src else " — run gsc_query_page.py to seed"))
    print(f"  slug↔GSC mismatches  : {reviews}  (marked `# REVIEW:`)")
    print(f"  unmatched to cluster : {no_cluster}  (entity-map gaps or off-topic)")


if __name__ == "__main__":
    build()
