"""
Ad-hoc GSC page×query pull for an arbitrary window (default Jun 22–28 2026).

Reuses auth/query helpers from gsc_analysis.py. Writes a flat page×query JSON
plus a query-rollup (each query → the pages that received its impressions).

Usage:
  python3 scripts/gsc_window_qp.py 2026-06-22 2026-06-28
"""

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from gsc_analysis import get_service, pick_site, query, OUT_DIR


def main():
    start = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date(2026, 6, 22)
    end = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date(2026, 6, 28)

    svc = get_service()
    site = pick_site(svc)
    print(f"\nUsing site: {site}")
    print(f"Date range: {start} → {end}\n")

    rows = query(svc, site, ["query", "page"], start, end)
    print(f"Pulled {len(rows)} query×page rows")

    flat = []
    for r in rows:
        q, page = r["keys"]
        flat.append({
            "query": q,
            "page": page,
            "clicks": r.get("clicks", 0),
            "impressions": r.get("impressions", 0),
            "ctr": round(r.get("ctr", 0.0), 4),
            "position": round(r.get("position", 0.0), 1),
        })

    tag = f"{start.isoformat()}_{end.isoformat()}"
    full_file = OUT_DIR / f"qp_window_{tag}.json"
    full_file.write_text(json.dumps(
        {"site": site, "date_range": {"start": start.isoformat(), "end": end.isoformat()},
         "rows": flat}, indent=2, default=str))
    print(f"Wrote {full_file}  ({len(flat)} rows)")

    # Query rollup: each query → total impr + the page that got the most impr for it.
    by_q = defaultdict(list)
    for row in flat:
        by_q[row["query"]].append(row)

    qroll = []
    for q, prows in by_q.items():
        prows_sorted = sorted(prows, key=lambda x: -x["impressions"])
        top = prows_sorted[0]
        qroll.append({
            "query": q,
            "total_impressions": sum(p["impressions"] for p in prows),
            "total_clicks": sum(p["clicks"] for p in prows),
            "top_page": top["page"],
            "top_page_impressions": top["impressions"],
            "top_page_position": top["position"],
            "page_count": len(prows),
        })
    qroll.sort(key=lambda x: -x["total_impressions"])

    qfile = OUT_DIR / f"qp_window_qroll_{tag}.json"
    qfile.write_text(json.dumps(
        {"site": site, "date_range": {"start": start.isoformat(), "end": end.isoformat()},
         "queries": qroll}, indent=2, default=str))
    print(f"Wrote {qfile}  ({len(qroll)} unique queries)")

    print("\n=== Top 30 queries by impressions ===")
    for x in qroll[:30]:
        print(f"  {x['total_impressions']:>6} impr | {x['total_clicks']:>3} clk | pos {x['top_page_position']:>5} | "
              f"{x['query'][:50]:<50} → {x['top_page']}")


if __name__ == "__main__":
    main()
