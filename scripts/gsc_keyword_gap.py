"""
Classify GSC window queries into keyword-gap buckets.

Inputs:
  - credentials/gsc_output/qp_window_qroll_<start>_<end>.json  (query rollup)
  - data/content_map.yml  (page → primary keyword ownership ledger)

Buckets (per query, above MIN_IMPR, brand excluded):
  TARGETED        — query ≈ the primary of the page that ranks for it (already owned)
  B1_SECONDARY    — the ranking page is the right home (strong topical overlap with its
                    primary) but the query ISN'T the primary → an un-incorporated
                    secondary keyword to add to that page
  OWNED_ELSEWHERE — query weakly matches its ranking page, but another page's primary
                    is a strong match → a dedicated page exists (routing, not a gap)
  B2_NO_PAGE      — query weakly matches its ranking page AND no page's primary is a
                    strong match → no dedicated page; new-content opportunity

Usage:
  python3 scripts/gsc_keyword_gap.py 2026-06-22 2026-06-28
"""

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "credentials" / "gsc_output"
MIN_IMPR = 25

STOP = {"the", "a", "an", "for", "of", "to", "in", "and", "or", "best", "top",
        "agency", "agencies", "company", "companies", "firm", "firms", "service",
        "services", "near", "me", "vs", "is", "are", "what", "how", "list"}
# Note: agency/company/firm variants are stopped so "enterprise seo agency" and
# "enterprise seo firms" collapse to the same core {enterprise, seo}.


def singular(w):
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("ses") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def core(text):
    toks = re.findall(r"[a-z0-9]+", text.lower())
    return frozenset(singular(t) for t in toks if t not in STOP and len(t) > 1)


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def relation(q_core, p_core):
    """Return one of: equal | variant | weak between a query core and a primary core."""
    if not q_core or not p_core:
        return "weak"
    if q_core == p_core:
        return "equal"
    if q_core <= p_core or p_core <= q_core:
        return "variant"
    if jaccard(q_core, p_core) >= 0.5:
        return "variant"
    return "weak"


def main():
    start, end = sys.argv[1], sys.argv[2]
    qroll = json.loads((OUT_DIR / f"qp_window_qroll_{start}_{end}.json").read_text())["queries"]
    cmap = yaml.safe_load((ROOT / "data" / "content_map.yml").read_text())

    # Build url → primary, and a list of (primary_core, url, primary) for global match.
    page_primary = {}
    primaries = []
    for p in cmap["pages"]:
        url = p["url"]
        prim = (p.get("primary") or "").strip()
        page_primary[url] = prim
        if prim:
            primaries.append((core(prim), url, prim))

    def url_path(u):
        # normalize full url to path for content_map lookup
        m = re.sub(r"^https?://[^/]+", "", u)
        return m if m.endswith("/") else m + "/"

    buckets = {"TARGETED": [], "B1_SECONDARY": [], "OWNED_ELSEWHERE": [], "B2_NO_PAGE": []}

    for x in qroll:
        q = x["query"]
        if x["total_impressions"] < MIN_IMPR:
            continue
        if "piperocket" in q or "pipe rocket" in q:
            continue
        qc = core(q)
        path = url_path(x["top_page"])
        pp = page_primary.get(path, "")
        ppc = core(pp)
        rel = relation(qc, ppc)

        rec = {
            "query": q,
            "impressions": x["total_impressions"],
            "clicks": x["total_clicks"],
            "position": x["top_page_position"],
            "ranking_page": path,
            "page_primary": pp,
        }

        if rel == "equal":
            buckets["TARGETED"].append(rec)
        elif rel == "variant":
            buckets["B1_SECONDARY"].append(rec)
        else:
            # weak vs its own ranking page — is there a dedicated page anywhere?
            best = None
            for pc, url, prim in primaries:
                r = relation(qc, pc)
                if r in ("equal", "variant"):
                    score = jaccard(qc, pc) + (0.5 if r == "equal" else 0)
                    if best is None or score > best[0]:
                        best = (score, url, prim, r)
            if best:
                rec["owner_page"] = best[1]
                rec["owner_primary"] = best[2]
                rec["match"] = best[3]
                buckets["OWNED_ELSEWHERE"].append(rec)
            else:
                buckets["B2_NO_PAGE"].append(rec)

    for k in buckets:
        buckets[k].sort(key=lambda r: -r["impressions"])

    out = OUT_DIR / f"keyword_gap_{start}_{end}.json"
    out.write_text(json.dumps(buckets, indent=2))
    print(f"Wrote {out}\n")
    for k, v in buckets.items():
        tot = sum(r["impressions"] for r in v)
        print(f"{k:<16} {len(v):>4} queries   {tot:>7} impressions")


if __name__ == "__main__":
    main()
