"""
GSC query x page export, last 28 days — for content-gap analysis.

Same join as gsc_query_page.py but with a 28-day window (GSC ~3-day lag aware).
Writes credentials/gsc_output/qp_28d_<end>.json and qp_28d_rollup_<end>.json.
"""

import json
from collections import defaultdict
from datetime import date, timedelta

from gsc_analysis import get_service, pick_site, query, OUT_DIR

END_DATE = date.today() - timedelta(days=3)
START_DATE = END_DATE - timedelta(days=27)  # 28-day window inclusive


def main():
    svc = get_service()
    site = pick_site(svc)
    print(f"\nUsing site: {site}")
    print(f"Date range: {START_DATE} -> {END_DATE}\n")

    rows = query(svc, site, ["page", "query"], START_DATE, END_DATE)
    print(f"Pulled {len(rows)} page x query rows")

    flat = []
    for r in rows:
        page, q = r["keys"]
        flat.append({
            "page": page, "query": q,
            "clicks": r.get("clicks", 0),
            "impressions": r.get("impressions", 0),
            "ctr": r.get("ctr", 0.0),
            "position": r.get("position", 0.0),
        })

    full_file = OUT_DIR / f"qp_28d_{END_DATE.isoformat()}.json"
    full_file.write_text(json.dumps(
        {"site": site,
         "date_range": {"start": START_DATE.isoformat(), "end": END_DATE.isoformat()},
         "rows": flat}, indent=2, default=str))
    print(f"Wrote {full_file}  ({len(flat)} rows)")

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
            "total_impressions": sum(q["impressions"] for q in qrows),
            "total_clicks": sum(q["clicks"] for q in qrows),
            "query_count": len(qrows),
            "queries": [
                {"query": q["query"], "impressions": q["impressions"],
                 "clicks": q["clicks"], "position": round(q["position"], 1)}
                for q in qrows_sorted
            ],
        })
    rollup.sort(key=lambda x: -x["total_impressions"])

    rollup_file = OUT_DIR / f"qp_28d_rollup_{END_DATE.isoformat()}.json"
    rollup_file.write_text(json.dumps(
        {"site": site,
         "date_range": {"start": START_DATE.isoformat(), "end": END_DATE.isoformat()},
         "pages": rollup}, indent=2, default=str))
    print(f"Wrote {rollup_file}  ({len(rollup)} pages)")


if __name__ == "__main__":
    main()
