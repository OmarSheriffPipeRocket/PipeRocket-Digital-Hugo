"""
Per-page SEO audit driven by data/content_map.yml.

For every page in the content map, extract the deterministic SEO signals and
write three artifacts under audit/:
  - content_map_audit.json  — full per-page detail (link lists, cannibalization,
                               GSC queries) for downstream tooling / the workflow
  - content_map_audit.csv   — one row per page: counts + flags (open in a sheet)
  - content_map_audit_issues.md — flagged problems only, grouped by dimension

Dimensions (deterministic layer):
  1. internal links   — count + [{anchor, href}]   (editorial body links, markdown)
  2. external links   — count + [{anchor, href}]
  3. anchor check     — internal anchors whose text is MORE/less specific than the
                        destination page's target keyword (e.g. anchor "b2b saas seo"
                        linking to the "saas seo" page)
  4. title            — text + length + flag
  5. description      — text + length + flag
  6. headings         — H1 count (rendered) + H2/H3 outline (markdown)
  7. schema           — JSON-LD @types present (rendered)
  8. primary freq     — exact-phrase + stemmed-family counts of the primary in body
  9. cannibalization  — OTHER pages getting GSC impressions for this page's primary
 10. crawlability     — indexable? canonical (self/cross), robots meta, in sitemap

The subjective calls (confirm anchor mismatches, multiple/doubtful keywords,
cannibalization severity) are layered on top by a workflow that consumes the JSON.

Usage:
  hugo --quiet                 # ensure public/ is fresh
  python3 scripts/audit_content_map.py
"""

import csv
import html
import json
import re
from collections import defaultdict
from pathlib import Path

from build_content_map import iter_pages, normalize
from generate_link_map import read_frontmatter

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
PUBLIC = ROOT / "public"
MAP_FILE = ROOT / "data" / "content_map.yml"
QP_ROWS = ROOT / "credentials" / "gsc_output" / "qp_2026-06-08.json"
SITEMAP = PUBLIC / "sitemap.xml"
REDIRECTS = ROOT / "static" / "_redirects"
AUDIT_DIR = ROOT / "audit"

ARTICLE_SECTIONS = {"blog", "glossary", "list", "compare", "alternative", "case-study"}

# Schema.org @types each page type SHOULD emit (beyond the site-wide Organization).
EXPECTED_SCHEMA = {
    "blog": ["Article", "BreadcrumbList"],
    "list": ["Article", "ItemList", "BreadcrumbList"],
    "glossary": ["DefinedTerm", "Article", "BreadcrumbList"],
    "compare": ["Article", "BreadcrumbList"],
    "alternative": ["Article", "ItemList", "BreadcrumbList"],
    "case-study": ["Article", "BreadcrumbList"],
    "home": ["WebSite"],
}
# A fallback/generic image that signals a weak (non-unique) Article image.
WEAK_IMAGE = "piperocket-logo.svg"


# ---------------- content_map.yml parse ----------------

def parse_content_map():
    """Return {url: {type, keyword_target, primary, secondary[], intent, funnel,
    cluster, gsc{...}}} — a light hand-parse (no PyYAML dep)."""
    txt = MAP_FILE.read_text(encoding="utf-8")
    blocks = re.split(r"(?=^  - url:)", txt, flags=re.M)
    out = {}
    for b in blocks:
        mu = re.search(r'url:\s*"([^"]+)"', b)
        if not mu:
            continue
        url = mu.group(1)
        sec = re.search(r"\n    secondary:\n((?:      - .*\n?)+)", b)
        secondary = re.findall(r'      - "?([^"\n]+?)"?\s*$', sec.group(1), re.M) if sec else []
        gsc = {}
        for k in ("total_impressions", "top_query", "top_query_position",
                  "primary_position", "aligned"):
            m = re.search(rf"\n      {k}:\s*\"?([^\"\n]+?)\"?\s*$", b, re.M)
            if m:
                gsc[k] = m.group(1)
        out[url] = {
            "type": (re.search(r"\n    type:\s*(\S+)", b) or [None, ""])[1],
            "keyword_target": "\n    keyword_target: false" not in b,
            "primary": (re.search(r'\n    primary:\s*"([^"]*)"', b) or [None, ""])[1],
            "secondary": secondary,
            "intent": (re.search(r"\n    intent:\s*(\S+)", b) or [None, ""])[1],
            "funnel": (re.search(r"\n    funnel:\s*(\S+)", b) or [None, ""])[1],
            "cluster": (re.search(r'\n    cluster:\s*"?([^"\n]+?)"?\s*$', b, re.M) or [None, ""])[1],
            "gsc": gsc,
        }
    return out


# ---------------- markdown body ----------------

def md_body(f):
    raw = f.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    return parts[2] if len(parts) >= 3 else raw


# strip markdown links to plain text but KEEP the anchor words; drop code/headings markup
def md_to_text(body):
    t = body
    t = re.sub(r"```.*?```", " ", t, flags=re.S)          # fenced code
    t = re.sub(r"`[^`]*`", " ", t)                         # inline code
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)            # images
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)         # links -> anchor text
    t = re.sub(r"\{\{.*?\}\}", " ", t, flags=re.S)          # shortcodes
    t = re.sub(r"[#>*_~|`-]", " ", t)                       # md punctuation
    return re.sub(r"\s+", " ", t).strip()


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def extract_links(body):
    internal, external = [], []
    for m in LINK_RE.finditer(body):
        anchor = re.sub(r"\s+", " ", m.group(1)).strip()
        href = m.group(2).strip()
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        is_ext = bool(re.match(r"https?://", href)) and "piperocket.digital" not in href
        (external if is_ext else internal).append({"anchor": anchor, "href": href})
    return internal, external


def heading_outline(body):
    out = []
    for m in re.finditer(r"^(#{1,4})\s+(.+?)\s*$", body, flags=re.M):
        # ignore headings inside fenced code is approximated (rare); strip bold
        text = re.sub(r"[*_`]", "", m.group(2)).strip()
        out.append({"level": len(m.group(1)), "text": text})
    return out


# ---------------- keyword frequency ----------------

def stem(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("es"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def stem_tokens(s):
    return [stem(w) for w in normalize(s)]


def phrase_counts(text, phrase):
    """Return (exact_count, family_count). exact = case-insensitive phrase match;
    family = consecutive stemmed-token-sequence matches (catches agency/agencies,
    tool/tools, reordering-free plural/singular variants)."""
    if not phrase:
        return 0, 0
    low = text.lower()
    exact = len(re.findall(r"\b" + re.escape(phrase.lower()) + r"\b", low))
    pt = stem_tokens(phrase)
    if not pt:
        return exact, exact
    bt = stem_tokens(text)
    n = len(pt)
    fam = sum(1 for i in range(len(bt) - n + 1) if bt[i:i + n] == pt)
    return exact, fam


# ---------------- anchor semantic check ----------------

def norm_path(href):
    """Reduce an internal href to a /path/ key comparable to content_map urls."""
    h = re.sub(r"https?://[^/]+", "", href)
    h = h.split("#")[0].split("?")[0]
    if not h.startswith("/"):
        h = "/" + h
    if not h.endswith("/"):
        h += "/"
    return h


def anchor_check(internal_links, cmap):
    """Flag internal links whose anchor text is more/less specific than (or
    unrelated to) the destination page's primary target keyword."""
    flags = []
    for lk in internal_links:
        dest = norm_path(lk["href"])
        d = cmap.get(dest)
        if not d or not d.get("primary"):
            continue
        a = set(normalize(lk["anchor"]))
        p = set(normalize(d["primary"]))
        if not a or not p:
            continue
        if a == p:
            continue
        extra = a - p          # qualifier words in anchor missing from dest target
        missing = p - a        # dest target words missing from anchor
        overlap = a & p
        if extra and p.issubset(a):
            kind = "anchor_more_specific"   # e.g. anchor "b2b saas seo" -> "saas seo"
        elif missing and a.issubset(p):
            kind = "anchor_less_specific"
        elif not overlap:
            kind = "anchor_unrelated"
        elif len(overlap) / len(a | p) < 0.5:
            kind = "anchor_weak_match"
        else:
            continue
        flags.append({
            "anchor": lk["anchor"], "href": lk["href"], "dest_primary": d["primary"],
            "kind": kind, "extra_words": sorted(extra), "missing_words": sorted(missing),
        })
    return flags


# ---------------- GSC: cannibalization + per-page queries ----------------

def load_gsc_rows():
    rows = json.loads(QP_ROWS.read_text())["rows"]
    by_query = {}          # normalized query -> [(path, impr, pos, raw_query)]
    by_page = {}           # path -> [(query, impr, pos)]
    for r in rows:
        path = norm_path(r["page"])
        q = r["query"]
        nq = " ".join(normalize(q))
        by_query.setdefault(nq, []).append((path, r["impressions"], round(r["position"], 1), q))
        by_page.setdefault(path, []).append((q, r["impressions"], round(r["position"], 1)))
    for p in by_page:
        by_page[p].sort(key=lambda x: -x[1])
    return by_query, by_page


def cannibalization(url, primary, by_query):
    """OTHER pages getting impressions for the SAME query as this page's primary."""
    if not primary:
        return []
    nq = " ".join(normalize(primary))
    hits = by_query.get(nq, [])
    others = [{"page": p, "impressions": i, "position": pos}
              for (p, i, pos, _) in hits if p != url]
    others.sort(key=lambda x: -x["impressions"])
    return others


# ---------------- rendered HTML head ----------------

def public_file(url):
    if url == "/":
        return PUBLIC / "index.html"
    return PUBLIC / url.strip("/") / "index.html"


def read_html(url):
    f = public_file(url)
    if not f.exists():
        return False, ""
    return True, f.read_text(encoding="utf-8", errors="ignore")


def rendered_text(html_text):
    """Visible main-content text from rendered HTML, with chrome removed
    (head/script/style/nav/header/footer). Used for keyword frequency so
    template-driven landing pages — which have empty markdown bodies — are
    measured by what's actually on the page."""
    t = html_text
    t = re.sub(r"<head\b.*?</head>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<script\b.*?</script>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<style\b.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<(nav|header|footer)\b.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def heading_texts(html_text, tag):
    """Rendered <h1>/<h2> inner text, chrome stripped. <header> is KEPT because
    the blog/article banner H1 lives inside <header class=...banner>; only nav,
    footer, aside, script, style are removed."""
    t = re.sub(r"<head\b.*?</head>", " ", html_text, flags=re.S | re.I)
    t = re.sub(r"<(script|style|nav|footer|aside)\b.*?</\1>", " ", t, flags=re.S | re.I)
    out = []
    for m in re.findall(rf"<{tag}\b[^>]*>(.*?)</{tag}>", t, flags=re.S | re.I):
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m))).strip()
        if txt:
            out.append(txt)
    return out


# ---------------- redirects ----------------

def load_redirects():
    """Return (active, stray, broken) for exact (non-wildcard) Netlify rules.

    Netlify skips a NON-forced redirect when a static file exists at that path —
    so a `301` rule whose source is a live page does NOT actually redirect (it's
    shadowed by the file). Only `301!` (forced) or rules whose source has no file
    actually fire.
      active : {src: target} — rules that genuinely redirect
      stray  : [(src, target)] — non-forced rules shadowed by a live file (dead config)
      broken : [(src, target)] — ACTIVE redirects whose target 404s
    """
    active, stray, broken = {}, [], []
    if not REDIRECTS.exists():
        return active, stray, broken
    for line in REDIRECTS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2 or not parts[0].startswith("/") or "*" in parts[0]:
            continue
        src = norm_path(parts[0])
        forced = any("!" in p for p in parts[1:])
        tgt = parts[1].rstrip("!")
        tgt = norm_path(tgt) if tgt.startswith("/") else tgt
        src_is_live = public_file(src).exists()
        if forced or not src_is_live:
            active[src] = tgt
            if tgt.startswith("/") and not target_exists(tgt):
                broken.append((src, tgt))
        else:
            stray.append((src, tgt))   # shadowed by the live file → never fires
    return active, stray, broken


def target_exists(tgt):
    """Does a redirect target resolve to a real file? Handles both pretty URLs
    (→ <path>/index.html) and explicit files like /sitemap.xml."""
    raw = tgt.strip("/")
    last = raw.split("/")[-1]
    if "." in last:                       # explicit file (e.g. sitemap.xml)
        return (PUBLIC / raw).exists()
    return public_file(tgt).exists()


def resolve(path, rmap, depth=0):
    """Follow redirects to the final internal path (cap chain depth)."""
    p = norm_path(path)
    seen = set()
    while p in rmap and p not in seen and depth < 6:
        seen.add(p)
        p = rmap[p]
        depth += 1
    return p


# ---------------- deep schema audit ----------------

ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def schema_audit(html_text, ptype):
    """Parse every JSON-LD block; return (types, issues). Validates required
    fields + Google rich-result usability per @type."""
    types, issues, blocks = [], [], {}
    raw_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html_text, re.S)
    for raw in raw_blocks:
        try:
            d = json.loads(raw)
        except Exception as e:
            issues.append(f"JSON-LD parse error: {str(e)[:50]}")
            continue
        for obj in (d if isinstance(d, list) else [d]):
            t = obj.get("@type", "?")
            types.append(t)
            blocks.setdefault(t, obj)
            if obj.get("@context", "").rstrip("/") not in ("https://schema.org", "http://schema.org"):
                issues.append(f"{t}: @context not schema.org")
    types = sorted(set(types))

    a = blocks.get("Article")
    if a:
        hl = a.get("headline", "")
        if not hl:
            issues.append("Article: missing headline")
        elif len(hl) > 110:
            issues.append(f"Article: headline {len(hl)}>110 chars (Google truncates)")
        img = a.get("image", "")
        img = img.get("url", "") if isinstance(img, dict) else img
        if not img:
            issues.append("Article: missing image")
        elif WEAK_IMAGE in img:
            issues.append("Article: image is the fallback logo SVG (not a usable rich-result image)")
        au = a.get("author", {})
        if not (isinstance(au, dict) and au.get("name")):
            issues.append("Article: author missing/invalid")
        elif not au.get("url"):
            issues.append("Article: author has no url (weak E-E-A-T link)")
        pub = a.get("publisher", {})
        if not (isinstance(pub, dict) and pub.get("logo")):
            issues.append("Article: publisher/logo missing")
        for k in ("datePublished", "dateModified"):
            v = a.get(k, "")
            if not v:
                issues.append(f"Article: missing {k}")
            elif not ISO_RE.match(str(v)):
                issues.append(f"Article: {k} not ISO-8601 ({v})")
        if not a.get("mainEntityOfPage"):
            issues.append("Article: missing mainEntityOfPage")

    bl = blocks.get("BreadcrumbList")
    if bl:
        items = bl.get("itemListElement", [])
        if len(items) < 2:
            issues.append("BreadcrumbList: <2 crumbs")
        for it in items:
            if not (it.get("position") and it.get("name") and it.get("item")):
                issues.append("BreadcrumbList: an item missing position/name/item")
                break

    il = blocks.get("ItemList")
    if il:
        items = il.get("itemListElement", [])
        if not items:
            issues.append("ItemList: empty")
        n = il.get("numberOfItems")
        if n is not None and n != len(items):
            issues.append(f"ItemList: numberOfItems {n} != {len(items)} elements")

    faq = blocks.get("FAQPage")
    if faq:
        qs = faq.get("mainEntity", [])
        if not qs:
            issues.append("FAQPage: no questions")
        for q in qs:
            ans = (q.get("acceptedAnswer") or {}).get("text", "")
            if not q.get("name") or not ans:
                issues.append("FAQPage: a Q/A is empty")
                break

    dt = blocks.get("DefinedTerm")
    if ptype == "glossary" and not dt:
        pass  # handled by expected-schema check
    elif dt:
        for k in ("name", "description", "inDefinedTermSet"):
            if not dt.get(k):
                issues.append(f"DefinedTerm: missing {k}")

    # expected-schema presence
    for exp in EXPECTED_SCHEMA.get(ptype, []):
        if exp not in types:
            issues.append(f"missing expected {exp} schema")
    if "Organization" not in types:
        issues.append("missing site-wide Organization schema")

    return types, issues


def parse_head(url, h):
    out = {"exists": bool(h), "title": "", "title_len": 0, "description": "",
           "desc_len": 0, "canonical": "", "robots": "", "schema_types": [],
           "h1_count": 0, "is_alias": False}
    if not h:
        return out
    out["is_alias"] = 'http-equiv="refresh"' in h
    m = re.search(r"<title>(.*?)</title>", h, re.S)
    if m:
        out["title"] = html.unescape(re.sub(r"\s+", " ", m.group(1)).strip())
        out["title_len"] = len(out["title"])
    m = re.search(r'<meta name="description" content="(.*?)">', h, re.S)
    if m:
        out["description"] = html.unescape(m.group(1).strip())
        out["desc_len"] = len(out["description"])
    m = re.search(r'<link rel="canonical" href="(.*?)"', h)
    if m:
        out["canonical"] = m.group(1)
    m = re.search(r'<meta name="robots" content="(.*?)"', h)
    if m:
        out["robots"] = m.group(1)
    out["h1_count"] = len(re.findall(r"<h1[\s>]", h))
    types = set()
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        for t in re.findall(r'"@type"\s*:\s*"([^"]+)"', blk):
            types.add(t)
    out["schema_types"] = sorted(types)
    return out


def load_sitemap():
    if not SITEMAP.exists():
        return set()
    return {norm_path(loc) for loc in re.findall(r"<loc>(.*?)</loc>", SITEMAP.read_text())}


# ---------------- build ----------------

def build():
    cmap = parse_content_map()
    by_query, by_page = load_gsc_rows()
    sitemap = load_sitemap()
    rmap, stray_redirects, broken_redirects = load_redirects()
    map_urls = set(cmap.keys())

    # url -> source markdown file
    url_file = {path: f for (_ctype, path, f) in iter_pages()}

    pages = []
    for url, meta in cmap.items():
        f = url_file.get(url)
        body = md_body(f) if f else ""
        text = md_to_text(body)
        internal, external = extract_links(body)
        exists, html_text = read_html(url)
        head = parse_head(url, html_text)
        schema_types, schema_issues = schema_audit(html_text, meta["type"]) if html_text else ([], [])
        primary = meta["primary"]
        # keyword frequency from the RENDERED page text (counts template-driven
        # landing pages correctly; markdown body is empty for those).
        rtext = rendered_text(html_text) if html_text else text
        rendered_words = len(rtext.split())
        h1_texts = heading_texts(html_text, "h1") if html_text else []
        h2_texts = heading_texts(html_text, "h2") if html_text else []
        exact, fam = phrase_counts(rtext, primary)
        sec_freq = {s: dict(zip(("exact", "family"), phrase_counts(rtext, s)))
                    for s in meta["secondary"]}
        canon_self = (head["canonical"].rstrip("/").endswith(url.rstrip("/"))
                      if head["canonical"] else False)
        redirected = url in rmap
        rec = {
            "url": url,
            "type": meta["type"],
            "keyword_target": meta["keyword_target"],
            "primary": primary,
            "secondary": meta["secondary"],
            "intent": meta["intent"],
            "funnel": meta["funnel"],
            "cluster": meta["cluster"],
            "source_file": str(f.relative_to(ROOT)) if f else None,
            "body_word_count": len(text.split()),
            "rendered_word_count": rendered_words,
            "redirected": redirected,
            "redirect_target": rmap.get(url, ""),
            # 1-2 links
            "internal_links": internal,
            "internal_link_count": len(internal),
            "external_links": external,
            "external_link_count": len(external),
            # 3 anchor check
            "anchor_flags": anchor_check(internal, cmap),
            # 4-5 title/desc
            "title": head["title"], "title_len": head["title_len"],
            "description": head["description"], "desc_len": head["desc_len"],
            # 6 headings (rendered HTML, main content — count matches the text list)
            "h1_count": len(h1_texts),
            "h1_texts": h1_texts,
            "h2_count": len(h2_texts),
            "h2_texts": h2_texts,
            "headings": heading_outline(body),
            # 7 schema (deep)
            "schema_types": schema_types or head["schema_types"],
            "schema_issues": schema_issues,
            # 8 keyword frequency
            "primary_freq_exact": exact,
            "primary_freq_family": fam,
            "secondary_freq": sec_freq,
            # 9 cannibalization (redirect-filtered below)
            "cannibalization": cannibalization(url, primary, by_query),
            "gsc_top_queries": [{"query": q, "impressions": i, "position": p}
                                for (q, i, p) in by_page.get(url, [])[:8]],
            # 10 crawlability
            "canonical": head["canonical"],
            "canonical_self": canon_self,
            "robots": head["robots"],
            "noindex": "noindex" in head["robots"].lower(),
            "in_sitemap": url in sitemap,
            "is_alias": head["is_alias"],
            "rendered": exists,
        }
        rec["indexable"] = (rec["rendered"] and not rec["noindex"]
                            and not rec["is_alias"] and rec["in_sitemap"]
                            and canon_self and not redirected)
        pages.append(rec)

    # ---- redirect-aware cannibalization filter ----
    # Drop a competitor that is a redirect source, or that resolves (through
    # redirects) to the same final URL as the page (legacy/duplicate URLs).
    for p in pages:
        self_final = resolve(p["url"], rmap)
        kept = []
        for o in p["cannibalization"]:
            comp = o["page"]
            if comp in rmap:                      # competitor is a redirect source
                continue
            if resolve(comp, rmap) == self_final:  # both resolve to same page
                continue
            kept.append(o)
        p["cannibalization"] = kept

    # ---- internal link graph (inbound / outbound), redirect-resolved ----
    inbound = defaultdict(set)      # target -> {source urls}
    outbound = defaultdict(set)     # source -> {target urls in map}
    for p in pages:
        src = p["url"]
        to_redirect = []
        for lk in p["internal_links"]:
            tgt = resolve(norm_path(lk["href"]), rmap)
            if norm_path(lk["href"]) in rmap:
                to_redirect.append({"anchor": lk["anchor"], "href": lk["href"], "final": tgt})
            if tgt in map_urls and tgt != src:
                outbound[src].add(tgt)
                inbound[tgt].add(src)
        p["links_to_redirect"] = to_redirect
    for p in pages:
        p["inbound_count"] = len(inbound[p["url"]])
        p["inbound_pages"] = sorted(inbound[p["url"]])
        p["outbound_count"] = len(outbound[p["url"]])
        p["outbound_pages"] = sorted(outbound[p["url"]])

    AUDIT_DIR.mkdir(exist_ok=True)
    (AUDIT_DIR / "content_map_audit.json").write_text(
        json.dumps({"page_count": len(pages), "pages": pages,
                    "redirect_hygiene": {"stray": stray_redirects, "broken": broken_redirects}},
                   indent=2), encoding="utf-8")
    write_csv(pages)
    write_issues(pages, stray_redirects, broken_redirects)
    summarize(pages, stray_redirects, broken_redirects)


def write_csv(pages):
    cols = ["url", "type", "keyword_target", "primary", "funnel", "intent", "cluster",
            "body_word_count", "internal_link_count", "external_link_count",
            "inbound_count", "outbound_count", "anchor_flag_count", "title", "title_len",
            "desc_len", "h1_count", "h2_count", "schema_types", "schema_issue_count",
            "primary_freq_exact", "primary_freq_family", "cannibalization_count",
            "indexable", "redirected", "canonical_self", "noindex", "in_sitemap"]
    with (AUDIT_DIR / "content_map_audit.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for p in pages:
            w.writerow([
                p["url"], p["type"], p["keyword_target"], p["primary"], p["funnel"],
                p["intent"], p["cluster"], p["body_word_count"], p["internal_link_count"],
                p["external_link_count"], p["inbound_count"], p["outbound_count"],
                len(p["anchor_flags"]), p["title"], p["title_len"], p["desc_len"],
                p["h1_count"], p["h2_count"], "|".join(p["schema_types"]),
                len(p["schema_issues"]), p["primary_freq_exact"], p["primary_freq_family"],
                len(p["cannibalization"]), p["indexable"], p["redirected"],
                p["canonical_self"], p["noindex"], p["in_sitemap"],
            ])


def write_issues(pages, stray_redirects=(), broken_redirects=()):
    L = ["# Content-map SEO audit — flagged issues (deterministic layer)\n",
         "_Generated by scripts/audit_content_map.py. Subjective calls are "
         "enriched by the audit workflow on top of this._\n"]

    def section(title, items):
        L.append(f"\n## {title}  ({len(items)})\n")
        L.extend(items if items else ["_none_"])

    kw = [p for p in pages if p["keyword_target"]]

    # title / description
    titles = [f"- `{p['url']}` — title {p['title_len']} chars" for p in pages
              if p["title_len"] > 60 or (p["rendered"] and p["title_len"] < 15)]
    section("Title length (>60 or <15)", titles)
    descs = [f"- `{p['url']}` — desc {p['desc_len']} chars" for p in pages
             if p["desc_len"] > 160 or (p["rendered"] and 0 < p["desc_len"] < 70)
             or (p["rendered"] and p["desc_len"] == 0 and not p["is_alias"])]
    section("Meta description (>160, <70, or missing)", descs)

    # headings / h1
    h1s = [f"- `{p['url']}` — {p['h1_count']} H1" for p in pages
           if p["rendered"] and not p["is_alias"] and p["h1_count"] != 1]
    section("H1 count != 1", h1s)

    # schema for article pages
    sch = [f"- `{p['url']}` — types: {', '.join(p['schema_types']) or 'NONE'}"
           for p in pages if p["type"] in ARTICLE_SECTIONS and "Article" not in p["schema_types"]
           and "DefinedTerm" not in p["schema_types"]]
    section("Article-type pages missing Article/DefinedTerm schema", sch)

    # crawlability
    crawl = [f"- `{p['url']}` — indexable=False (noindex={p['noindex']}, "
             f"in_sitemap={p['in_sitemap']}, canonical_self={p['canonical_self']}, "
             f"alias={p['is_alias']})" for p in pages
             if p["keyword_target"] and not p["indexable"]]
    section("Keyword pages NOT indexable", crawl)

    # internal links thin
    thin = [f"- `{p['url']}` — {p['internal_link_count']} internal links "
            f"({p['body_word_count']}w)" for p in kw
            if p["body_word_count"] > 600 and p["internal_link_count"] < 2]
    section("Thin internal linking (long body, <2 internal links)", thin)

    # anchor mismatches
    anch = []
    for p in pages:
        for fl in p["anchor_flags"]:
            if fl["kind"] in ("anchor_more_specific", "anchor_unrelated"):
                anch.append(f"- `{p['url']}` — anchor \"{fl['anchor']}\" → "
                            f"`{fl['href']}` (target: \"{fl['dest_primary']}\") "
                            f"[{fl['kind']}; extra: {fl['extra_words']}]")
    section("Anchor-text mismatches (more-specific / unrelated)", anch)

    # primary keyword absent from body
    absent = [f"- `{p['url']}` — primary \"{p['primary']}\" appears {p['primary_freq_family']}× "
              f"({p['body_word_count']}w body)" for p in kw
              if p["body_word_count"] > 400 and p["primary_freq_family"] == 0]
    section("Primary keyword absent from body (long pages)", absent)

    # cannibalization
    can = [f"- `{p['url']}` — primary \"{p['primary']}\": "
           + ", ".join(f"{o['page']}({o['impressions']}i,p{o['position']})"
                       for o in p["cannibalization"][:6])
           for p in kw if p["cannibalization"]]
    section("Cannibalization — other pages with impressions for the primary", can)

    # schema issues
    sch = [f"- `{p['url']}` ({p['type']}): " + "; ".join(p["schema_issues"])
           for p in pages if p["schema_issues"]]
    section("Schema issues (correctness / usability)", sch)

    # interlinking
    orphans = [f"- `{p['url']}` ({p['type']})" for p in kw if p["inbound_count"] == 0]
    section("Orphans (0 in-content inbound links)", orphans)
    almost = [f"- `{p['url']}` — 1 inbound (from {p['inbound_pages'][0]})" for p in kw if p["inbound_count"] == 1]
    section("Almost-orphans (1 inbound link)", almost)
    poor_out = [f"- `{p['url']}` — {p['outbound_count']} outbound ({p['body_word_count']}w)"
                for p in kw if p["body_word_count"] > 600 and p["outbound_count"] < 2]
    section("Poor outbound (long body, <2 internal targets)", poor_out)
    redir_links = [f"- `{p['url']}` → links to redirect: " + ", ".join(f"{l['href']}→{l['final']}" for l in p["links_to_redirect"])
                   for p in pages if p.get("links_to_redirect")]
    section("Links pointing to actively-redirected URLs (update to final target)", redir_links)

    # redirect hygiene
    broken = [f"- `{s}` → `{t}` (target 404s — ACTIVE redirect to a dead URL)" for s, t in broken_redirects]
    section("Broken redirects (active rule → 404 target)", broken)
    stray = [f"- `{s}` → `{t}` (non-forced rule shadowed by a live page — dead config, remove)" for s, t in stray_redirects]
    section("Stray redirect rules (live page has a non-firing 301)", stray)

    (AUDIT_DIR / "content_map_audit_issues.md").write_text("\n".join(L), encoding="utf-8")


def summarize(pages, stray_redirects=(), broken_redirects=()):
    kw = [p for p in pages if p["keyword_target"]]
    both = [p for p in kw if p["inbound_count"] <= 2 and p["body_word_count"] > 600 and p["outbound_count"] < 2]
    print(f"\nAudited {len(pages)} pages ({len(kw)} keyword-target)")
    print(f"  audit/content_map_audit.json  (full detail)")
    print(f"  audit/content_map_audit.csv   (per-page metrics)")
    print(f"  audit/content_map_audit_issues.md (flagged)")
    print(f"  schema issues (pages)  : {sum(1 for p in pages if p['schema_issues'])}")
    print(f"  orphans (0 inbound)    : {sum(1 for p in kw if p['inbound_count']==0)}")
    print(f"  almost-orphans (1)     : {sum(1 for p in kw if p['inbound_count']==1)}")
    print(f"  poor inbound (<=2)     : {sum(1 for p in kw if p['inbound_count']<=2)}")
    print(f"  poor outbound          : {sum(1 for p in kw if p['body_word_count']>600 and p['outbound_count']<2)}")
    print(f"  both poor              : {len(both)}")
    print(f"  links to redirects     : {sum(len(p.get('links_to_redirect',[])) for p in pages)}")
    print(f"  pages w/ cannibalization (redirect-filtered): {sum(1 for p in kw if p['cannibalization'])}")
    print(f"  redirected map pages   : {sum(1 for p in pages if p['redirected'])}")
    print(f"  BROKEN redirects (→404): {len(broken_redirects)}  {[s for s,_ in broken_redirects]}")
    print(f"  stray redirect rules   : {len(stray_redirects)}  {[s for s,_ in stray_redirects]}")


if __name__ == "__main__":
    build()
