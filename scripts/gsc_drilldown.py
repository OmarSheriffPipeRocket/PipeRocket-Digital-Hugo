"""Daily drill-down for specific pages/queries that collapsed."""
import json
from datetime import date, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / "credentials" / "token.json"
OUT_DIR = ROOT / "credentials" / "gsc_output"

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SITE = "https://piperocket.digital/"

END = date.today() - timedelta(days=3)
START = END - timedelta(days=41)

TARGET_PAGES = [
    "https://piperocket.digital/blogs/best-saas-ppc-agencies/",
    "https://piperocket.digital/glossary/what-is-schema-markup/",
    "https://piperocket.digital/glossary/what-is-a-301-redirect/",
    "https://piperocket.digital/list/best-affordable-b2b-ppc-agencies/",
    "https://piperocket.digital/blogs/best-enterprise-seo-agencies/",
]

TARGET_QUERIES = [
    "seo for saas companies",
    "technical seo agency",
    "enterprise seo",
    "schema markup",
    "301 redirect",
    "saas ppc agency",
]


def svc():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def daily_for_page(s, page):
    body = {
        "startDate": START.isoformat(),
        "endDate": END.isoformat(),
        "dimensions": ["date"],
        "rowLimit": 25000,
        "dimensionFilterGroups": [{"filters": [{"dimension": "page", "operator": "equals", "expression": page}]}],
        "dataState": "all",
    }
    return s.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])


def daily_for_query(s, q):
    body = {
        "startDate": START.isoformat(),
        "endDate": END.isoformat(),
        "dimensions": ["date"],
        "rowLimit": 25000,
        "dimensionFilterGroups": [{"filters": [{"dimension": "query", "operator": "equals", "expression": q}]}],
        "dataState": "all",
    }
    return s.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])


def top_queries_for_page(s, page, start, end):
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["query"],
        "rowLimit": 50,
        "dimensionFilterGroups": [{"filters": [{"dimension": "page", "operator": "equals", "expression": page}]}],
        "dataState": "all",
    }
    return s.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])


def main():
    s = svc()
    out = {"date_range": [START.isoformat(), END.isoformat()], "pages": {}, "queries": {}, "ppc_top_queries": {}}

    print(f"=== DAILY IMPR/CLICKS FOR TARGET PAGES ({START} -> {END}) ===")
    for p in TARGET_PAGES:
        rows = daily_for_page(s, p)
        out["pages"][p] = rows
        print(f"\n{p}")
        print(f"  {'date':<12}{'clicks':>8}{'impr':>8}{'pos':>8}")
        for r in rows[-30:]:
            d = r["keys"][0]
            print(f"  {d:<12}{r.get('clicks',0):>8}{r.get('impressions',0):>8}{r.get('position',0):>8.1f}")

    print(f"\n\n=== DAILY IMPR FOR COLLAPSED QUERIES ===")
    for q in TARGET_QUERIES:
        rows = daily_for_query(s, q)
        out["queries"][q] = rows
        print(f"\nquery: {q}")
        print(f"  {'date':<12}{'clicks':>8}{'impr':>8}{'pos':>8}")
        for r in rows[-30:]:
            d = r["keys"][0]
            print(f"  {d:<12}{r.get('clicks',0):>8}{r.get('impressions',0):>8}{r.get('position',0):>8.1f}")

    # Top queries for ppc page now vs earlier
    ppc = TARGET_PAGES[0]
    early = (date.fromisoformat("2026-04-12"), date.fromisoformat("2026-04-25"))
    recent = (END - timedelta(days=13), END)
    eq = top_queries_for_page(s, ppc, *early)
    rq = top_queries_for_page(s, ppc, *recent)
    out["ppc_top_queries"] = {"early_window": [d.isoformat() for d in early], "recent_window": [d.isoformat() for d in recent], "early": eq, "recent": rq}

    print(f"\n=== PPC PAGE: top queries early {early} ===")
    for r in eq[:15]:
        print(f"  clicks {r.get('clicks',0):>3}  impr {r.get('impressions',0):>5}  pos {r.get('position',0):>5.1f}  | {r['keys'][0]}")
    print(f"\n=== PPC PAGE: top queries recent {recent} ===")
    for r in rq[:15]:
        print(f"  clicks {r.get('clicks',0):>3}  impr {r.get('impressions',0):>5}  pos {r.get('position',0):>5.1f}  | {r['keys'][0]}")

    (OUT_DIR / f"drilldown_{END.isoformat()}.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved drilldown JSON.")


if __name__ == "__main__":
    main()
