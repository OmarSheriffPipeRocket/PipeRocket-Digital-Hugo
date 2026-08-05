"""
GSC page-level decline report: last 28 days vs previous 28 days.

For every page, compares clicks, impressions, CTR, and avg position across two
trailing 28-day windows (GSC ~3-day reporting lag aware) and surfaces the pages
that got WORSE — not just clicks losers, but also:
  - CTR decliners (clicks fell even though impressions/position held — usually
    a SERP feature, snippet change, or a new/better-ranking competitor)
  - Position-only decliners (impressions/clicks still fine now, but position is
    sliding — an early warning before clicks actually drop)
  - Pages that went to zero clicks (fully dropped out of the money queries)
  - Device split (mobile vs desktop) for the top clicks-decliners, to catch
    device-specific regressions (e.g. a mobile UX/CWV issue) that a blended
    number would hide
  - Query-level drill-down for the top N clicks-decliners, so you can see
    WHICH queries dropped on that page (single query cratering vs broad decay)

Usage: python3 scripts/gsc_28d_page_declines.py
"""

import json
from datetime import date, timedelta

from gsc_analysis import get_service, pick_site, query, sum_metrics, pct_delta, OUT_DIR

END_DATE = date.today() - timedelta(days=3)
CUR_START, CUR_END = END_DATE - timedelta(days=27), END_DATE
PREV_END = CUR_START - timedelta(days=1)
PREV_START = PREV_END - timedelta(days=27)

TOP_N_DRILLDOWN = 12


def short_page(page):
    return page.replace("https://piperocket.digital", "") or "/"


def rows_to_map(rows):
    return {r["keys"][0]: r for r in rows}


def build_deltas(map_cur, map_prev, keyname="page"):
    out = []
    for k in set(map_cur) | set(map_prev):
        a = map_cur.get(k, {"clicks": 0, "impressions": 0, "position": 0, "ctr": 0})
        b = map_prev.get(k, {"clicks": 0, "impressions": 0, "position": 0, "ctr": 0})
        out.append({
            keyname: k,
            "clicks_now": a["clicks"], "clicks_prev": b["clicks"],
            "clicks_delta": a["clicks"] - b["clicks"],
            "clicks_pct": pct_delta(a["clicks"], b["clicks"]),
            "impr_now": a["impressions"], "impr_prev": b["impressions"],
            "impr_delta": a["impressions"] - b["impressions"],
            "impr_pct": pct_delta(a["impressions"], b["impressions"]),
            "ctr_now": a["ctr"], "ctr_prev": b["ctr"],
            "ctr_delta": a["ctr"] - b["ctr"],
            "pos_now": round(a["position"], 2), "pos_prev": round(b["position"], 2),
            # positive pos_delta = WORSE (number went up)
            "pos_delta": round(a["position"] - b["position"], 2) if b["position"] else 0.0,
        })
    return out


def main():
    svc = get_service()
    site = pick_site(svc)
    print(f"\nSite: {site}")
    print(f"Current 28d:  {CUR_START} -> {CUR_END}")
    print(f"Previous 28d: {PREV_START} -> {PREV_END}\n")

    # === Page-level ===
    p_cur = query(svc, site, ["page"], CUR_START, CUR_END)
    p_prev = query(svc, site, ["page"], PREV_START, PREV_END)
    page_deltas = build_deltas(rows_to_map(p_cur), rows_to_map(p_prev), "page")
    for d in page_deltas:
        d["page"] = short_page(d["page"])

    # Only pages with meaningful prior volume, to avoid noise from 1-click pages
    live = [d for d in page_deltas if d["clicks_prev"] >= 3 or d["impr_prev"] >= 50]

    clicks_losers = sorted([d for d in live if d["clicks_delta"] < 0], key=lambda x: x["clicks_delta"])
    impr_losers = sorted([d for d in live if d["impr_delta"] < 0], key=lambda x: x["impr_delta"])
    zeroed_out = sorted([d for d in live if d["clicks_now"] == 0 and d["clicks_prev"] > 0],
                         key=lambda x: -x["clicks_prev"])
    position_only_losers = sorted(
        [d for d in live if d["pos_delta"] > 1.0 and d["clicks_delta"] >= 0],
        key=lambda x: -x["pos_delta"])
    ctr_losers = sorted(
        [d for d in live if d["ctr_delta"] < -0.01 and d["impr_delta"] >= -5 and d["pos_delta"] <= 0.5],
        key=lambda x: x["ctr_delta"])

    # === Query-level: overall movers (for context) ===
    q_cur = query(svc, site, ["query"], CUR_START, CUR_END)
    q_prev = query(svc, site, ["query"], PREV_START, PREV_END)
    query_deltas = build_deltas(rows_to_map(q_cur), rows_to_map(q_prev), "query")
    query_losers = sorted([d for d in query_deltas if d["clicks_prev"] >= 3],
                           key=lambda x: x["clicks_delta"])[:20]

    # === Device split for top clicks-decliners ===
    dev_cur = query(svc, site, ["page", "device"], CUR_START, CUR_END)
    dev_prev = query(svc, site, ["page", "device"], PREV_START, PREV_END)

    def device_map(rows):
        m = {}
        for r in rows:
            page, dev = r["keys"]
            m.setdefault(short_page(page), {})[dev] = r
        return m

    dmap_cur, dmap_prev = device_map(dev_cur), device_map(dev_prev)

    top_decliners = clicks_losers[:TOP_N_DRILLDOWN]
    device_breakdown = {}
    for d in top_decliners:
        page = d["page"]
        row = {}
        for dev in ("MOBILE", "DESKTOP", "TABLET"):
            a = dmap_cur.get(page, {}).get(dev, {"clicks": 0, "impressions": 0, "position": 0})
            b = dmap_prev.get(page, {}).get(dev, {"clicks": 0, "impressions": 0, "position": 0})
            if a["clicks"] or b["clicks"]:
                row[dev] = {"clicks_now": a["clicks"], "clicks_prev": b["clicks"],
                            "clicks_delta": a["clicks"] - b["clicks"]}
        device_breakdown[page] = row

    # === Query drill-down per top page decliner ===
    qp_cur = query(svc, site, ["page", "query"], CUR_START, CUR_END)
    qp_prev = query(svc, site, ["page", "query"], PREV_START, PREV_END)

    def qp_map(rows):
        m = {}
        for r in rows:
            page, q = r["keys"]
            m.setdefault(short_page(page), {})[q] = r
        return m

    qpmap_cur, qpmap_prev = qp_map(qp_cur), qp_map(qp_prev)

    page_query_drilldown = {}
    for d in top_decliners:
        page = d["page"]
        qcur = qpmap_cur.get(page, {})
        qprev = qpmap_prev.get(page, {})
        qdeltas = build_deltas(qcur, qprev, "query")
        qdeltas = sorted(qdeltas, key=lambda x: x["clicks_delta"])[:8]
        page_query_drilldown[page] = qdeltas

    # === Output JSON ===
    report = {
        "site": site,
        "current_window": {"start": CUR_START.isoformat(), "end": CUR_END.isoformat()},
        "previous_window": {"start": PREV_START.isoformat(), "end": PREV_END.isoformat()},
        "clicks_losers": clicks_losers[:40],
        "impression_losers": impr_losers[:40],
        "zeroed_out_pages": zeroed_out[:40],
        "position_only_losers": position_only_losers[:40],
        "ctr_losers": ctr_losers[:40],
        "query_losers": query_losers,
        "top_decliner_device_breakdown": device_breakdown,
        "top_decliner_query_drilldown": page_query_drilldown,
    }
    out_file = OUT_DIR / f"page_declines_28d_{END_DATE.isoformat()}.json"
    out_file.write_text(json.dumps(report, indent=2, default=str))
    print(f"Wrote {out_file}\n")

    # === Console summary ===
    print(f"=== TOP {TOP_N_DRILLDOWN} PAGE CLICKS LOSERS (28d vs prior 28d) ===")
    print(f"{'page':<55}{'clicks':>16}{'impr':>16}{'pos':>14}{'ctr':>16}")
    for d in top_decliners:
        clk = f"{d['clicks_prev']}->{d['clicks_now']} ({d['clicks_delta']:+d})"
        imp = f"{d['impr_prev']}->{d['impr_now']} ({d['impr_delta']:+d})"
        pos = f"{d['pos_prev']}->{d['pos_now']} ({d['pos_delta']:+.1f})"
        ctr = f"{d['ctr_prev']*100:.1f}%->{d['ctr_now']*100:.1f}%"
        print(f"{d['page']:<55}{clk:>16}{imp:>16}{pos:>14}{ctr:>16}")

    print(f"\n=== FULLY ZEROED OUT (had clicks, now 0) ===")
    for d in zeroed_out[:15]:
        print(f"  {d['page']:<55} {d['clicks_prev']} -> 0  (impr {d['impr_prev']}->{d['impr_now']}, pos {d['pos_prev']}->{d['pos_now']})")

    print(f"\n=== POSITION SLIDING (clicks/impr flat or up, position worse — early warning) ===")
    for d in position_only_losers[:15]:
        print(f"  {d['page']:<55} pos {d['pos_prev']}->{d['pos_now']} ({d['pos_delta']:+.1f}), clicks {d['clicks_prev']}->{d['clicks_now']}, impr {d['impr_prev']}->{d['impr_now']}")

    print(f"\n=== CTR DROPPING (impr/pos steady, CTR fell — snippet/SERP-feature risk) ===")
    for d in ctr_losers[:15]:
        print(f"  {d['page']:<55} CTR {d['ctr_prev']*100:.1f}%->{d['ctr_now']*100:.1f}%, impr {d['impr_prev']}->{d['impr_now']}, pos {d['pos_prev']}->{d['pos_now']}")

    print(f"\n=== TOP QUERY LOSERS (site-wide) ===")
    for d in query_losers[:15]:
        print(f"  {d['query']!r:<45} clicks {d['clicks_prev']}->{d['clicks_now']} ({d['clicks_delta']:+d}), pos {d['pos_prev']}->{d['pos_now']}")

    print(f"\n=== DEVICE BREAKDOWN for top clicks losers ===")
    for page, row in device_breakdown.items():
        parts = ", ".join(f"{dev}: {v['clicks_prev']}->{v['clicks_now']} ({v['clicks_delta']:+d})" for dev, v in row.items())
        print(f"  {page:<55} {parts}")

    print(f"\n=== QUERY DRILLDOWN for top clicks losers ===")
    for page, qdeltas in page_query_drilldown.items():
        print(f"  {page}")
        for q in qdeltas:
            if q["clicks_delta"] < 0 or q["impr_delta"] < 0:
                print(f"      {q['query']!r:<40} clicks {q['clicks_prev']}->{q['clicks_now']} ({q['clicks_delta']:+d}), impr {q['impr_prev']}->{q['impr_now']}, pos {q['pos_prev']}->{q['pos_now']}")


if __name__ == "__main__":
    main()
