"""
GSC query x page export for the keyword map.

Pulls the ["page", "query"] dimension pair over the standard ~6-week window —
the join the WoW report in gsc_analysis.py never does — so we can see, per URL,
which queries it actually ranks for, and per query, how many of our own URLs
compete for it.

Reuses auth/query helpers from gsc_analysis.py (same token, same site pick).
First run may trigger the OAuth copy-URL flow if credentials/token.json is stale.

Writes two artifacts to credentials/gsc_output/:
  qp_<end>.json        — full page→query rows (impr/clicks/position/ctr)
  qp_rollup_<end>.json — per-URL rollup: top query + metrics (the primary seed
                         for build_content_map.py) + every query the URL ranks for

Usage:
  python3 scripts/gsc_query_page.py
"""

import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

# Reuse the wired-up auth + paginated query from the WoW script.
from gsc_analysis import get_service, pick_site, query, OUT_DIR

# Same reporting-delay-aware window as gsc_analysis.py (GSC lags ~2-3 days).
END_DATE = date.today() - timedelta(days=3)
START_DATE = END_DATE - timedelta(days=41)  # ~6 weeks


def main():
    svc = get_service()
    site = pick_site(svc)
    print(f"\nUsing site: {site}")
    print(f"Date range: {START_DATE} → {END_DATE}\n")

    rows = query(svc, site, ["page", "query"], START_DATE, END_DATE)
    print(f"Pulled {len(rows)} page×query rows")

    # Flatten into plain dicts.
    flat = []
    for r in rows:
        page, q = r["keys"]
        flat.append({
            "page": page,
            "query": q,
            "clicks": r.get("clicks", 0),
            "impressions": r.get("impressions", 0),
            "ctr": r.get("ctr", 0.0),
            "position": r.get("position", 0.0),
        })

    full_file = OUT_DIR / f"qp_{END_DATE.isoformat()}.json"
    full_file.write_text(json.dumps(
        {"site": site,
         "date_range": {"start": START_DATE.isoformat(), "end": END_DATE.isoformat()},
         "rows": flat},
        indent=2, default=str))
    print(f"Wrote {full_file}  ({len(flat)} rows)")

    # Per-page rollup: rank each page's queries by impressions; top one seeds `primary`.
    by_page = defaultdict(list)
    for row in flat:
        by_page[row["page"]].append(row)

    rollup = []
    for page, qrows in by_page.items():
        qrows_sorted = sorted(qrows, key=lambda x: -x["impressions"])
        top = qrows_sorted[0]
        rollup.append({
            "page": page,
            "top_query": top["query"],
            "top_query_impressions": top["impressions"],
            "top_query_clicks": top["clicks"],
            "top_query_position": round(top["position"], 1),
            "top_query_ctr": round(top["ctr"], 4),
            "total_impressions": sum(q["impressions"] for q in qrows),
            "total_clicks": sum(q["clicks"] for q in qrows),
            "query_count": len(qrows),
            # keep the top 25 queries per page for secondary-keyword seeding
            "queries": [
                {"query": q["query"], "impressions": q["impressions"],
                 "clicks": q["clicks"], "position": round(q["position"], 1)}
                for q in qrows_sorted[:25]
            ],
        })
    rollup.sort(key=lambda x: -x["total_impressions"])

    rollup_file = OUT_DIR / f"qp_rollup_{END_DATE.isoformat()}.json"
    rollup_file.write_text(json.dumps(
        {"site": site,
         "date_range": {"start": START_DATE.isoformat(), "end": END_DATE.isoformat()},
         "pages": rollup},
        indent=2, default=str))
    print(f"Wrote {rollup_file}  ({len(rollup)} pages)")

    print("\n=== Top 15 pages by impressions (page → top query) ===")
    for p in rollup[:15]:
        print(f"  {p['total_impressions']:>7} impr | pos {p['top_query_position']:>5} | "
              f"{p['page']}  →  \"{p['top_query']}\"")


if __name__ == "__main__":
    main()
