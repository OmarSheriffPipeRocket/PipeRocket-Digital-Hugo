"""
Bootstrap data/keyword_map.yml — the page→target-keyword ownership ledger.

Phase-1 scope: blogs + glossary + list (the cannibalization-prone, deliberately
interlinked set). compare/alternative are deferred (branded/navigational).

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

IN_SCOPE = ["blogs", "glossary", "list"]  # phase 1
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
    else:  # glossary: strip "what is", "?", trailing clauses
        t = re.sub(r"^what is\s+", "", (title or ""), flags=re.I)
        t = re.split(r"[?:]", t)[0].strip()
        cands = [t] if t else []
    return cands[0] if cands else (slug or "").replace("-", " ")


# ---------- build ----------

def build():
    clusters = load_entity_clusters()
    gsc, gsc_src = load_gsc_rollup()
    entries = []

    for ctype in IN_SCOPE:
        for f in sorted((CONTENT_DIR / ctype).glob("*.md")):
            if f.name == "_index.md":
                continue
            slug, title, _ = read_frontmatter(f)
            if not slug:
                continue
            path = f"/{ctype}/{slug}/"
            extra = read_extra_fm(f)

            slug_kw = slug_primary(ctype, title, slug)
            primary = slug_kw
            review_note = None
            secondary, gsc_block = [], None

            g = gsc.get(path)
            if g:
                primary = g["top_query"]
                # flag when GSC reality diverges from the slug guess
                if normalize(primary) != normalize(slug_kw):
                    review_note = f'slug said "{slug_kw}"'
                # secondary = next few queries, excluding the primary
                for q in g.get("queries", [])[1:6]:
                    if normalize(q["query"]) != normalize(primary):
                        secondary.append(q["query"])
                gsc_block = {
                    "top_query": g["top_query"],
                    "impressions": g["top_query_impressions"],
                    "clicks": g["top_query_clicks"],
                    "position": g["top_query_position"],
                    "total_impressions": g["total_impressions"],
                }

            ckey, centity = match_cluster(primary, clusters)
            intent, funnel = guess_intent_funnel(ctype, title, slug)

            entries.append({
                "url": path, "type": ctype.rstrip("s") if ctype != "list" else "list",
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
        "# Generated by scripts/build_keyword_map.py. Phase 1: blogs + glossary + list.",
        "# `primary` is GSC-seeded where data exists, else slug/title-derived.",
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
        L.append(f"    primary: {yq(e['primary'])}")
        if e["secondary"]:
            L.append("    secondary:")
            for s in e["secondary"]:
                L.append(f"      - {yq(s)}")
        else:
            L.append("    secondary: []")
        L.append(f"    intent: {e['intent']}        # REVIEW")
        L.append(f"    funnel: {e['funnel']}            # REVIEW")
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
