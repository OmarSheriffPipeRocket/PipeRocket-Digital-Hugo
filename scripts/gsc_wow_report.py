"""
GSC Week-over-Week report for piperocket.digital.

Finished week vs previous week, broken down by:
  - Overall (clicks/traffic, impressions)
  - Intent (Brand, ToFu+MoFu, BoFu)
  - Region (Global, US)

Intent classification differs by metric:
  - CLICKS: Brand = query contains a brand term (piperocket, etc). Non-brand clicks
    are split BoFu vs ToFu+MoFu by the PAGE they landed on (a /list/ or agency-landing
    page is BoFu regardless of the search term used to find it).
  - IMPRESSIONS: all three buckets are assigned purely by query text (keyword match),
    since impressions describe search demand, not a specific page visit.

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

BRAND_QUERY = ("piperocket", "pipe rocket", "piperrocket", "pipe rockets")
BOFU_QUERY = ("agency", "agencies", "services", "service", "company", "companies",
              "consultant", "consultancy", "firm", "firms", "pricing", "price", "cost",
              "hire", "best ", "top ", "alternative", " vs ", "vs.", "review", "compare")

# Page-path buckets, used only for splitting non-brand CLICKS into BoFu vs ToFu+MoFu.
BRAND_SLUGS = {"about-us", "careers", "contact-us", "reviews", "partnership", "faqs",
               "privacy-policy", "terms-and-conditions", "cookies-policy", "research-methodology"}
TOFU_DIRS = {"blogs", "glossary", "tools", "checklists", "author", "research"}
BOFU_DIRS = {"list", "alternative", "compare", "vs", "case-study"}
BOFU_SLUGS = {"pricing", "schedule-a-demo"}


def classify_query(q):
    """Keyword classification of a query — used for ALL impressions bucketing."""
    ql = q.lower()
    if any(b in ql for b in BRAND_QUERY):
        return "Brand"
    if any(b in ql for b in BOFU_QUERY):
        return "BoFu"
    return "ToFu+MoFu"


def classify_page(page_path):
    """Classify a page path (e.g. '/list/best-x/', '/linkedin-marketing-agency/') by funnel stage."""
    segments = [s for s in page_path.strip("/").split("/") if s]
    if not segments:
        return "Brand"  # homepage
    first = segments[0]
    if first in BRAND_SLUGS:
        return "Brand"
    if first in TOFU_DIRS:
        return "ToFu+MoFu"
    if first in BOFU_DIRS or first in BOFU_SLUGS:
        return "BoFu"
    # Remaining root-level single-segment pages are PipeRocket's own service/landing
    # pages (e.g. /saas-seo-agency/, /linkedin-marketing-agency/, /enterprise-ppc-agency/) — BoFu.
    return "BoFu"


def classify_click(page_path, q):
    """CLICKS bucket: brand queries win regardless of page; otherwise split by page."""
    if any(b in q.lower() for b in BRAND_QUERY):
        return "Brand"
    return classify_page(page_path)


def short_page(page):
    return page.replace("https://piperocket.digital", "") or "/"


def pct(label, cur, prev):
    print(f"  {label:<10} {cur:>7} vs {prev:<7} ({pct_delta(cur, prev):+6.1f}%)")


def fetch_rows(svc, site, start, end, country=None):
    dims = ["page", "query", "country"] if country else ["page", "query"]
    rows = query(svc, site, dims, start, end)
    if country:
        rows = [r for r in rows if r["keys"][2] == country]
    return rows


def bucket_totals(rows):
    """Returns (click_totals, impr_totals), each {Brand/ToFu+MoFu/BoFu: int}."""
    clicks = {"Brand": 0, "ToFu+MoFu": 0, "BoFu": 0}
    impressions = {"Brand": 0, "ToFu+MoFu": 0, "BoFu": 0}
    for r in rows:
        page, q = short_page(r["keys"][0]), r["keys"][1]
        clicks[classify_click(page, q)] += r.get("clicks", 0)
        impressions[classify_query(q)] += r.get("impressions", 0)
    return clicks, impressions


def query_movers(rows_cur, rows_prev):
    """Per-bucket query movers for both clicks (page+query based) and impressions (query based)."""
    def agg(rows):
        click_agg, impr_agg = {}, {}
        for r in rows:
            page, q = short_page(r["keys"][0]), r["keys"][1]
            cb, ib = classify_click(page, q), classify_query(q)
            click_agg.setdefault((cb, q), 0)
            click_agg[(cb, q)] += r.get("clicks", 0)
            impr_agg.setdefault((ib, q), 0)
            impr_agg[(ib, q)] += r.get("impressions", 0)
        return click_agg, impr_agg

    ccur, icur = agg(rows_cur)
    cprev, iprev = agg(rows_prev)

    def deltas(cur_map, prev_map):
        out = {"Brand": [], "ToFu+MoFu": [], "BoFu": []}
        for (b, q) in set(cur_map) | set(prev_map):
            n, p = cur_map.get((b, q), 0), prev_map.get((b, q), 0)
            if n != p:
                out[b].append((q, p, n, n - p))
        return out

    return deltas(ccur, cprev), deltas(icur, iprev)


def page_click_totals(rows):
    """{page: {bucket: clicks}} using the CLICKS classifier (brand-by-query, else by-page)."""
    out = {}
    for r in rows:
        page, q = r["keys"][0], r["keys"][1]
        bucket = classify_click(short_page(page), q)
        out.setdefault(page, {}).setdefault(bucket, 0)
        out[page][bucket] += r.get("clicks", 0)
    return out


def true_totals(svc, site, start, end, country=None):
    """Accurate site-wide totals from a low-dimension query (page+query+country
    combos get anonymized below a threshold, undercounting the bucketed sums)."""
    dims = ["date", "country"] if country else ["date"]
    rows = query(svc, site, dims, start, end)
    if country:
        rows = [r for r in rows if r["keys"][1] == country]
    m = sum_metrics(rows)
    return m["clicks"], m["impressions"]


def report_region(label, svc, site, country):
    cur_rows = fetch_rows(svc, site, CUR_START, CUR_END, country)
    prev_rows = fetch_rows(svc, site, PREV_START, PREV_END, country)
    cur_c, cur_i = bucket_totals(cur_rows)
    prev_c, prev_i = bucket_totals(prev_rows)
    tot_c_cur, tot_i_cur = true_totals(svc, site, CUR_START, CUR_END, country)
    tot_c_prev, tot_i_prev = true_totals(svc, site, PREV_START, PREV_END, country)

    print(f"=== OVERALL — {label} ===")
    pct("Traffic", tot_c_cur, tot_c_prev)
    pct("Impressions", tot_i_cur, tot_i_prev)
    print("  (bucket sums below may not add up to the totals above — GSC anonymizes")
    print("   some low-volume page+query+country combinations)")
    print()
    print("  Traffic (clicks):")
    for k in ("Brand", "BoFu", "ToFu+MoFu"):
        arrow = "Increased" if cur_c[k] > prev_c[k] else "Decreased" if cur_c[k] < prev_c[k] else "Flat"
        print(f"    {k}: {arrow} from {prev_c[k]} to {cur_c[k]}" if arrow != "Flat" else f"    {k}: Flat at {cur_c[k]}")
    print("  Impressions:")
    for k in ("Brand", "BoFu", "ToFu+MoFu"):
        arrow = "Increased" if cur_i[k] > prev_i[k] else "Decreased" if cur_i[k] < prev_i[k] else "Flat"
        print(f"    {k}: {arrow} from {prev_i[k]} to {cur_i[k]}" if arrow != "Flat" else f"    {k}: Flat at {cur_i[k]}")
    print()

    click_mv, impr_mv = query_movers(cur_rows, prev_rows)
    print(f"  --- movers ({label}) ---")
    for k in ("Brand", "BoFu", "ToFu+MoFu"):
        cm = sorted(click_mv[k], key=lambda x: -abs(x[3]))[:4]
        im = sorted(impr_mv[k], key=lambda x: -abs(x[3]))[:4]
        print(f"  {k}:")
        print("    clicks movers: " + (", ".join(f"{q!r} {p}->{n} ({d:+d})" for q, p, n, d in cm) or "none"))
        print("    impr   movers: " + (", ".join(f"{q!r} {p}->{n} ({d:+d})" for q, p, n, d in im) or "none"))
    print()

    cur_pages = page_click_totals(cur_rows)
    prev_pages = page_click_totals(prev_rows)
    print(f"  --- page-level click movers ({label}) ---")
    for k in ("Brand", "BoFu", "ToFu+MoFu"):
        deltas = []
        for p in set(cur_pages) | set(prev_pages):
            cn = cur_pages.get(p, {}).get(k, 0)
            cp = prev_pages.get(p, {}).get(k, 0)
            if cn != cp:
                deltas.append((short_page(p), cn, cp, cn - cp))
        gainers = sorted([d for d in deltas if d[3] > 0], key=lambda x: -x[3])[:6]
        losers = sorted([d for d in deltas if d[3] < 0], key=lambda x: x[3])[:6]
        print(f"  {k}:")
        print("    gained: " + (", ".join(f"{p} {cp}->{cn} ({d:+d})" for p, cn, cp, d in gainers) or "none"))
        print("    lost:   " + (", ".join(f"{p} {cp}->{cn} ({d:+d})" for p, cn, cp, d in losers) or "none"))
    print()


def main():
    svc = get_service()
    site = pick_site(svc)
    print(f"\nSite: {site}")
    print(f"Finished week: {CUR_START} → {CUR_END}")
    print(f"Prev week:     {PREV_START} → {PREV_END}\n")
    print("Leads: not available in GSC (pull from GA4/CRM)\n")

    report_region("GLOBAL", svc, site, None)
    report_region("US", svc, site, "usa")


if __name__ == "__main__":
    main()
