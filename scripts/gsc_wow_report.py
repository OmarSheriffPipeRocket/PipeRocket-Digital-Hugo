"""
GSC Week-over-Week report for piperocket.digital.

Finished week vs previous week, broken down by:
  - Overall (clicks/traffic, impressions, CTR, avg position)
  - Intent (Brand, ToFu+MoFu, BoFu)
  - Region (Global, US)

GSC has no "Leads" metric — that lives in analytics/CRM, reported separately.

Usage: python3 scripts/gsc_wow_report.py
"""

from datetime import date, timedelta

from gsc_analysis import get_service, pick_site, query, sum_metrics, pct_delta

# Most recent finished week, Sunday → Saturday.
_today = date.today()
CUR_END = _today - timedelta(days=(_today.weekday() - 5) % 7)  # last Saturday
CUR_START = CUR_END - timedelta(days=6)                        # its Sunday
PREV_END = CUR_START - timedelta(days=1)
PREV_START = PREV_END - timedelta(days=6)

BRAND = ("piperocket", "pipe rocket", "piperrocket", "pipe rockets")
BOFU = ("agency", "agencies", "services", "service", "company", "companies",
        "consultant", "consultancy", "firm", "firms", "pricing", "price", "cost",
        "hire", "best ", "top ", "alternative", " vs ", "vs.", "review", "compare")


def classify(q):
    ql = q.lower()
    if any(b in ql for b in BRAND):
        return "Brand"
    if any(b in ql for b in BOFU):
        return "BoFu"
    return "ToFu+MoFu"


def fmt(m):
    return (m["clicks"], m["impressions"], m["ctr"] * 100, m["position"])


def short_page(page):
    return page.replace("https://piperocket.digital", "") or "/"


def page_intent_clicks(svc, site, start, end, country=None):
    """{page: {intent: clicks}}, intent assigned per (page, query) row."""
    dims = ["page", "query", "country"] if country else ["page", "query"]
    rows = query(svc, site, dims, start, end)
    if country:
        rows = [r for r in rows if r["keys"][2] == country]
    out = {}
    for r in rows:
        page, q = r["keys"][0], r["keys"][1]
        out.setdefault(page, {}).setdefault(classify(q), 0)
        out[page][classify(q)] += r.get("clicks", 0)
    return out


def line(label, cur, prev):
    cc, ci, cr, cp = fmt(cur)
    pc, pi, pr, pp = fmt(prev)
    print(f"{label:<14} "
          f"clicks {cc:>5} vs {pc:<5} ({pct_delta(cc, pc):+6.1f}%)  "
          f"impr {ci:>7} vs {pi:<7} ({pct_delta(ci, pi):+6.1f}%)  "
          f"ctr {cr:>5.2f}% vs {pr:<5.2f}% ({pct_delta(cr, pr):+6.1f}%)  "
          f"pos {cp:>5.2f} vs {pp:<5.2f} (Δ{cp - pp:+.2f})")


def main():
    svc = get_service()
    site = pick_site(svc)
    print(f"\nSite: {site}")
    print(f"Finished week: {CUR_START} → {CUR_END}")
    print(f"Prev week:     {PREV_START} → {PREV_END}\n")

    # --- Overall (by date) ---
    cur_overall = sum_metrics(query(svc, site, ["date"], CUR_START, CUR_END))
    prev_overall = sum_metrics(query(svc, site, ["date"], PREV_START, PREV_END))

    print("=== OVERALL ===")
    line("Total", cur_overall, prev_overall)
    print("Leads:         not available in GSC (pull from GA4/CRM)\n")

    # --- Intent (by query), optionally region-filtered ---
    def by_intent(start, end, country=None):
        dims = ["query", "country"] if country else ["query"]
        rows = query(svc, site, dims, start, end)
        if country:
            rows = [r for r in rows if r["keys"][1] == country]
        buckets = {"Brand": [], "ToFu+MoFu": [], "BoFu": []}
        for r in rows:
            buckets[classify(r["keys"][0])].append(r)
        return {k: sum_metrics(v) for k, v in buckets.items()}

    def movers(country=None):
        dims = ["query", "country"] if country else ["query"]
        cur = query(svc, site, dims, CUR_START, CUR_END)
        prev = query(svc, site, dims, PREV_START, PREV_END)
        if country:
            cur = [r for r in cur if r["keys"][1] == country]
            prev = [r for r in prev if r["keys"][1] == country]
        cmap = {r["keys"][0]: r for r in cur}
        pmap = {r["keys"][0]: r for r in prev}
        bucket = {"Brand": [], "ToFu+MoFu": [], "BoFu": []}
        for q in set(cmap) | set(pmap):
            a = cmap.get(q, {}); b = pmap.get(q, {})
            bucket[classify(q)].append({
                "q": q,
                "cd": a.get("clicks", 0) - b.get("clicks", 0),
                "cn": a.get("clicks", 0), "cp": b.get("clicks", 0),
                "id": a.get("impressions", 0) - b.get("impressions", 0),
                "in": a.get("impressions", 0), "ip": b.get("impressions", 0),
            })
        return bucket

    for label, country in (("INTENT — GLOBAL", None), ("INTENT — US", "usa")):
        cur_i, prev_i = by_intent(CUR_START, CUR_END, country), by_intent(PREV_START, PREV_END, country)
        mv = movers(country)
        print(f"=== {label} ===")
        for k in ("Brand", "ToFu+MoFu", "BoFu"):
            line(k, cur_i[k], prev_i[k])
            rows = mv[k]
            cm = sorted([r for r in rows if r["cd"]], key=lambda x: -abs(x["cd"]))[:4]
            im = sorted([r for r in rows if r["id"]], key=lambda x: -abs(x["id"]))[:4]
            print("   clicks movers: " + (", ".join(f"{r['q']!r} {r['cp']}->{r['cn']} ({r['cd']:+d})" for r in cm) or "none"))
            print("   impr   movers: " + (", ".join(f"{r['q']!r} {r['ip']}->{r['in']} ({r['id']:+d})" for r in im) or "none"))
        print()

    # --- Region (by country) ---
    def region(start, end, country=None):
        rows = query(svc, site, ["date", "country"], start, end)
        if country:
            rows = [r for r in rows if r["keys"][1] == country]
        return sum_metrics(rows)

    print("=== REGION ===")
    line("Global", region(CUR_START, CUR_END), region(PREV_START, PREV_END))
    line("US", region(CUR_START, CUR_END, "usa"), region(PREV_START, PREV_END, "usa"))
    print()

    # --- Page-level click movers, per intent (finished vs prev week) ---
    def page_movers(label, country):
        cur = page_intent_clicks(svc, site, CUR_START, CUR_END, country)
        prev = page_intent_clicks(svc, site, PREV_START, PREV_END, country)
        print(f"=== PAGE-LEVEL CLICK MOVERS — {label} ===")
        for intent in ("Brand", "ToFu+MoFu", "BoFu"):
            deltas = []
            for p in set(cur) | set(prev):
                cn = cur.get(p, {}).get(intent, 0)
                cp = prev.get(p, {}).get(intent, 0)
                if (cn or cp) and cn != cp:
                    deltas.append((short_page(p), cn, cp, cn - cp))
            gainers = sorted([d for d in deltas if d[3] > 0], key=lambda x: -x[3])
            losers = sorted([d for d in deltas if d[3] < 0], key=lambda x: x[3])
            cur_tot = sum(cur.get(p, {}).get(intent, 0) for p in cur)
            prev_tot = sum(prev.get(p, {}).get(intent, 0) for p in prev)
            print(f"  {intent}  (clicks {cur_tot} vs {prev_tot})")
            print("    gained: " + (", ".join(f"{p} {cp}->{cn} ({d:+d})" for p, cn, cp, d in gainers[:6]) or "none"))
            print("    lost:   " + (", ".join(f"{p} {cp}->{cn} ({d:+d})" for p, cn, cp, d in losers[:6]) or "none"))
        print()

    page_movers("GLOBAL", None)
    page_movers("US", "usa")


if __name__ == "__main__":
    main()
