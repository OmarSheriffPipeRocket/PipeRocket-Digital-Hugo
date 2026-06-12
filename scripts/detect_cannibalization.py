"""
Keyword cannibalization detector for the PipeRocket site.

Two independent layers, then cross-referenced (the design's payoff):

  Layer A — DECLARATIVE (no GSC): collisions between pages' normalized
            primary / canonical_for / secondary in data/content_map.yml.
            Auto-cleared when the colliding pages declare DIFFERENT intent
            (the blog's "intent, not vocabulary" rule).

  Layer B — EMPIRICAL (GSC query×page): for each near-duplicate query, the
            set of our own URLs ranking for it. 2+ content URLs in contention
            = real on-SERP cannibalization, regardless of what the map declared.

Cross-reference:
  CONFIRMED  = pair in BOTH layers      (declared overlap that IS splitting rankings)
  UNDECLARED = Layer B only             (ranking overlap the map didn't predict)
  LATENT     = Layer A only             (declared same target, not yet both ranking)

Per pair, recommends the blog's move (merge / canonical / delete) from GSC equity,
and flags the "wrong page type ranks" case (informational blog outranking the
commercial page that should own a buyer query).

REPORTS ONLY — never mutates content_map.yml. Writes:
  data/keyword_cannibalization_report.md

Usage:
  python3 scripts/detect_cannibalization.py
"""

import json
import re
from collections import defaultdict
from pathlib import Path

from build_content_map import normalize  # shared tokenizer (lowercase+stopword+singularize)

ROOT = Path(__file__).resolve().parent.parent
MAP_FILE = ROOT / "data" / "content_map.yml"
GSC_DIR = ROOT / "credentials" / "gsc_output"
# NOTE: must NOT live under data/ — Hugo treats data/* as data files and fails
# to unmarshal a markdown report ("unmarshal of format ... not supported").
OUT_FILE = ROOT / "keyword_cannibalization_report.md"

# --- tunables ---
POS_CONTENTION = 30.0     # a URL is "in contention" for a query at/above this position
POS_PAGE1 = 20.0          # both URLs here = HIGH severity (genuinely competing up top)
MIN_URL_IMPR = 10         # a URL needs this many impressions to count as a real competitor
                          # (position on a handful of impressions is statistical noise)
MIN_GROUP_IMPR = 20       # ignore query groups below this combined impression floor
DELETE_IMPR_CEIL = 50     # a losing URL under this (and ~0 clicks) = nothing to save → delete
COMMERCIAL_RX = re.compile(
    r"\b(agenc|compan|firm|service|tool|software|platform|pricing|vs|best|top|cost)\b", re.I)


def nkey(s):
    """Normalized near-duplicate key for a keyword/query: sorted token tuple."""
    if not s:
        return ()
    return tuple(sorted(normalize(s)))


# ---------- parse content_map.yml (hand-rolled; no PyYAML in this env) ----------

def load_map():
    text = MAP_FILE.read_text(encoding="utf-8")
    blocks = re.split(r"\n(?=  - url:)", text)
    pages = []
    for b in blocks:
        m = re.search(r'  - url: "([^"]+)"', b)
        if not m:
            continue
        p = {"url": m.group(1), "secondary": []}
        for field in ("type", "primary", "intent", "funnel", "cluster", "canonical_for"):
            fm = re.search(rf'^    {field}: "?([^"\n]+?)"?\s*(?:#.*)?$', b, re.M)
            p[field] = fm.group(1).strip() if fm else None
        # secondary list
        sec = re.search(r"^    secondary:\n((?:      - .*\n?)+)", b, re.M)
        if sec:
            p["secondary"] = re.findall(r'      - "?([^"\n]+?)"?\s*$', sec.group(1), re.M)
        pages.append(p)
    return pages


# ---------- GSC load ----------

def url_path(u):
    # GSC reports #anchor and ?query variants as separate "pages" — strip them so a
    # single page's scroll-to-text / sitelink fragments collapse into one URL.
    p = re.sub(r"https?://[^/]+", "", u) or "/"
    p = p.split("#")[0].split("?")[0]
    return p or "/"


def load_gsc():
    files = sorted(GSC_DIR.glob("qp_2*.json"))  # the full page×query export (not rollup)
    files = [f for f in files if "rollup" not in f.name]
    if not files:
        return None, None
    latest = files[-1]
    data = json.loads(latest.read_text())
    return data["rows"], latest.name


# ---------- Layer A: declarative collisions ----------

def layer_a(pages):
    """Return {nkey: [page,...]} for primary/canonical_for collisions across 2+ pages."""
    by_key = defaultdict(list)
    for p in pages:
        keys = {nkey(p["primary"]), nkey(p["canonical_for"])}
        keys.discard(())
        for k in keys:
            by_key[k].append(p)
    # also note secondary↔primary overlaps as a softer signal
    sec_index = defaultdict(set)
    for p in pages:
        for s in p["secondary"]:
            sec_index[nkey(s)].add(p["url"])
    collisions = {k: v for k, v in by_key.items() if len({x["url"] for x in v}) >= 2}
    return collisions, sec_index


# ---------- Layer B: empirical GSC overlap ----------

def layer_b(rows):
    """Group rows by near-duplicate query; aggregate per-path; keep groups with 2+ URLs."""
    # group rawquery×page → aggregate per normalized-query per path
    grp = defaultdict(lambda: defaultdict(lambda: {"impr": 0, "clk": 0, "pos_w": 0.0}))
    raw_examples = defaultdict(set)
    for r in rows:
        path = url_path(r["page"])
        # homepage + brand queries are not cannibalization. Catch brand spelled with
        # spaces/hyphens too ("pipe rocket", "pipe-rocket" → "piperocket").
        if path == "/" or "piperocket" in re.sub(r"[^a-z]", "", r["query"].lower()):
            continue
        k = nkey(r["query"])
        if not k:
            continue
        raw_examples[k].add(r["query"])
        cell = grp[k][path]
        cell["impr"] += r["impressions"]
        cell["clk"] += r["clicks"]
        cell["pos_w"] += r["position"] * r["impressions"]

    groups = {}
    for k, paths in grp.items():
        if len(paths) < 2:
            continue
        urls = []
        for path, m in paths.items():
            impr = m["impr"]
            pos = (m["pos_w"] / impr) if impr else 999
            urls.append({"path": path, "impr": impr, "clk": m["clk"], "pos": round(pos, 1)})
        total_impr = sum(u["impr"] for u in urls)
        if total_impr < MIN_GROUP_IMPR:
            continue
        # a "real competitor" must be both in contention AND have non-trivial impressions
        real = [u for u in urls if u["pos"] <= POS_CONTENTION and u["impr"] >= MIN_URL_IMPR]
        if len(real) < 2:
            continue  # only one URL genuinely competes → not cannibalization
        real.sort(key=lambda u: -u["impr"])      # de-facto owner = most impressions
        urls.sort(key=lambda u: -u["impr"])      # display by impact
        groups[k] = {"urls": urls, "real": real, "total_impr": total_impr,
                     "examples": sorted(raw_examples[k], key=len)[:3]}
    return groups


def severity(group):
    page1 = [u for u in group["real"] if u["pos"] <= POS_PAGE1]
    return "HIGH" if len(page1) >= 2 else "MEDIUM"


# ---------- recommendation engine (the blog's merge/canonical/delete) ----------

def recommend(group, page_by_path, example_query):
    real = group["real"]
    winner = real[0]                       # de-facto owner = most impressions
    moves = []
    commercial = bool(COMMERCIAL_RX.search(example_query))
    w_page = page_by_path.get(winner["path"])
    w_type = w_page["type"] if w_page else "?"
    # If the most-trafficked URL isn't in the map (legacy/redirect/service), the
    # canonical direction is ambiguous — don't prescribe folding live pages into it.
    owner_unknown = w_page is None

    for loser in real[1:]:                 # only the genuine competitors, not noise URLs
        l_page = page_by_path.get(loser["path"])
        l_type = l_page["type"] if l_page else "?"
        # URLs not in content_map are service/legacy/redirect pages — never auto-recommend
        # deleting or merging them; flag for a human to classify.
        if l_page is None or owner_unknown:
            moves.append((loser["path"], "INVESTIGATE",
                          "a competing URL is not in content_map (legacy/redirect or service "
                          "page) — confirm which URL is canonical before consolidating"))
            continue
        # intent differentiation → auto-soften (blog: intent, not vocabulary)
        if w_page and l_page and w_page["intent"] and l_page["intent"] \
                and w_page["intent"] != l_page["intent"]:
            moves.append((loser["path"], "VERIFY",
                          f"different declared intent ({w_type}:{w_page['intent']} vs "
                          f"{l_type}:{l_page['intent']}) — may be legitimately distinct"))
            continue
        if loser["clk"] == 0 and loser["impr"] < DELETE_IMPR_CEIL:
            moves.append((loser["path"], "DELETE", "no clicks, minimal impressions → 301 to winner"))
        elif l_type == w_type:
            moves.append((loser["path"], "MERGE/CANONICAL",
                          f"both {l_type}; fold value into winner + 301, or canonical if near-duplicate"))
        else:
            moves.append((loser["path"], "MERGE",
                          "has equity; pull unique value into winner, then 301"))

    # wrong-page-type: informational blog winning a commercial query over a commercial page
    note = None
    if commercial and w_type == "blog":
        commercial_losers = [u for u in real[1:]
                             if (page_by_path.get(u["path"]) or {}).get("type") in ("list",)]
        if commercial_losers:
            note = ("WRONG PAGE TYPE — an informational blog is outranking the commercial "
                    "list page for a buyer query; consider intent realignment so the "
                    "conversion page owns it")
    return winner, moves, note


# ---------- report ----------

def md_table(rows, headers):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def build_report():
    pages = load_map()
    page_by_path = {p["url"]: p for p in pages}
    map_keys = set()
    for p in pages:
        map_keys.add(nkey(p["primary"]))
        map_keys.add(nkey(p["canonical_for"]))

    rows, gsc_src = load_gsc()
    a_collisions, sec_index = layer_a(pages)

    if rows is None:
        b_groups = {}
        gsc_note = "**No GSC export found** — Layer B (empirical) skipped; declarative only."
    else:
        b_groups = layer_b(rows)
        gsc_note = f"GSC source: `{gsc_src}`"

    # classify
    confirmed, undeclared, latent = [], [], []
    b_keys = set(b_groups)
    for k, g in b_groups.items():
        (confirmed if k in map_keys else undeclared).append((k, g))
    for k, plist in a_collisions.items():
        if k not in b_keys:
            latent.append((k, plist))

    # severity sort
    confirmed.sort(key=lambda kg: (-{"HIGH": 3, "MEDIUM": 2, "LOW": 1}[severity(kg[1])],
                                   -kg[1]["total_impr"]))
    undeclared.sort(key=lambda kg: (-{"HIGH": 3, "MEDIUM": 2, "LOW": 1}[severity(kg[1])],
                                    -kg[1]["total_impr"]))

    L = [
        "# Keyword Cannibalization Report",
        "",
        f"_Generated by `scripts/detect_cannibalization.py`. {gsc_note}_",
        "",
        "Two-layer detection: **declarative** (content_map.yml collisions) × "
        "**empirical** (GSC query→multiple URLs). See "
        "`/blogs/how-to-fix-keyword-cannibalization/` for the merge/canonical/delete method.",
        "",
        "## Summary",
        "",
        md_table([
            ["CONFIRMED (both layers)", len(confirmed), "Declared overlap that IS splitting rankings — fix first"],
            ["UNDECLARED (GSC only)", len(undeclared), "On-SERP overlap the map didn't predict — verify + declare"],
            ["LATENT (map only)", len(latent), "Same target declared, not yet both ranking — prevent"],
        ], ["Class", "Count", "Meaning"]),
        "",
    ]

    def render_group(k, g, idx):
        sev = severity(g)
        ex = g["examples"][0] if g["examples"] else " ".join(k)
        winner, moves, note = recommend(g, page_by_path, ex)
        lines = [f"### {idx}. `{ex}` — {sev}  ·  {g['total_impr']} impr",
                 ""]
        if len(g["examples"]) > 1:
            lines.append("_Also: " + ", ".join(f"`{e}`" for e in g["examples"][1:]) + "_\n")
        urls_tbl = []
        for u in g["urls"][:8]:
            tag = " 🏆 most impr" if u["path"] == winner["path"] else ""
            t = (page_by_path.get(u["path"]) or {}).get("type", "—")
            urls_tbl.append([f"`{u['path']}`", t, u["pos"], u["impr"], u["clk"], tag])
        lines.append(md_table(urls_tbl, ["URL", "type", "pos", "impr", "clk", ""]))
        lines.append("")
        for path, move, why in moves:
            lines.append(f"- **{move}** `{path}` — {why}")
        if note:
            lines.append(f"- ⚠️ {note}")
        lines.append("")
        return "\n".join(lines)

    L.append("## CONFIRMED — declared overlap splitting rankings\n")
    if confirmed:
        for i, (k, g) in enumerate(confirmed, 1):
            L.append(render_group(k, g, i))
    else:
        L.append("_None._\n")

    L.append("## UNDECLARED — GSC shows 2+ URLs, map didn't predict it\n")
    CAP = 40
    shown = undeclared[:CAP]
    for i, (k, g) in enumerate(shown, 1):
        L.append(render_group(k, g, i))
    if len(undeclared) > CAP:
        L.append(f"_…and {len(undeclared) - CAP} more lower-severity groups (raised the "
                 f"`MIN_GROUP_IMPR`/`POS_CONTENTION` floors to see fewer)._\n")
    if not undeclared:
        L.append("_None._\n")

    L.append("## LATENT — same target declared, not yet both ranking\n")
    if latent:
        rows_l = []
        for k, plist in latent:
            urls = sorted({p["url"] for p in plist})
            intents = {p["intent"] for p in plist}
            flag = "intent-differentiated?" if len(intents) > 1 else ""
            rows_l.append([f"`{' '.join(k)}`", "<br>".join(f"`{u}`" for u in urls), flag])
        L.append(md_table(rows_l, ["target key", "pages declaring it", "note"]))
        L.append("")
    else:
        L.append("_None._\n")

    OUT_FILE.write_text("\n".join(L), encoding="utf-8")

    print(f"Wrote {OUT_FILE}")
    print(f"  CONFIRMED : {len(confirmed)}")
    print(f"  UNDECLARED: {len(undeclared)} (showing {min(len(undeclared), CAP)})")
    print(f"  LATENT    : {len(latent)}")
    if confirmed:
        print("\n  Top confirmed:")
        for k, g in confirmed[:5]:
            ex = g["examples"][0] if g["examples"] else " ".join(k)
            print(f"    [{severity(g)}] \"{ex}\"  ({len(g['urls'])} URLs, {g['total_impr']} impr)")


if __name__ == "__main__":
    build_report()
