"""
Create "GSC Content Decline Report — 28d vs prior 28d" Google Sheet.

Pulls fresh page-level GSC data for the trailing 28-day window vs the prior
28-day window (same windows as scripts/gsc_28d_page_declines.py), classifies
every page by content type (Homepage / Listicles / Blogs / Glossary / Tools /
Compare / Alternative / VS / Case Studies / Checklists / Research / Service-
Landing / Static-Brand / Other), and writes:

  - "Overall" tab: site-wide totals, a per-page-type summary table, and the
    top 20 clicks-decliners across the whole site
  - one tab per page type present in the data: every tracked page in that
    type with clicks/impressions/CTR/position now vs prior, sorted worst
    decliners first

Usage: python3 scripts/create_gsc_decline_sheet.py
"""

import sys
from datetime import date, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gsc_analysis import get_service, pick_site, query, pct_delta, OUT_DIR

ROOT = Path(__file__).resolve().parent.parent
SHEETS_TOKEN = ROOT / "credentials" / "token_backlinks.json"

END_DATE = date.today() - timedelta(days=3)
CUR_START, CUR_END = END_DATE - timedelta(days=27), END_DATE
PREV_END = CUR_START - timedelta(days=1)
PREV_START = PREV_END - timedelta(days=27)

TYPE_DIR_MAP = {
    "blogs": "Blogs",
    "list": "Listicles",
    "glossary": "Glossary",
    "tools": "Tools",
    "compare": "Compare Pages",
    "alternative": "Alternative Pages",
    "vs": "VS Pages",
    "case-study": "Case Studies",
    "checklists": "Checklists",
    "research": "Research",
    "author": "Author Pages",
}
STATIC_SLUGS = {
    "about-us", "careers", "contact-us", "reviews", "partnership", "faqs",
    "privacy-policy", "terms-and-conditions", "cookies-policy",
    "research-methodology", "write-for-us-digital-marketing-seo-ppc",
    "schedule-a-demo", "pricing",
}
TYPE_ORDER = [
    "Homepage", "Listicles", "Blogs", "Glossary", "Tools", "Compare Pages",
    "Alternative Pages", "VS Pages", "Case Studies", "Checklists", "Research",
    "Service/Landing Pages", "Static/Brand Pages", "Author Pages", "Other",
]

# min prior-window volume to keep a page out of the noise floor
MIN_PREV_CLICKS = 3
MIN_PREV_IMPR = 50


def short_page(page):
    return page.replace("https://piperocket.digital", "") or "/"


def page_type(page_path):
    segments = [s for s in page_path.strip("/").split("/") if s]
    if not segments:
        return "Homepage"
    first = segments[0]
    if first in TYPE_DIR_MAP:
        return TYPE_DIR_MAP[first]
    if first in STATIC_SLUGS:
        return "Static/Brand Pages"
    if len(segments) == 1:
        return "Service/Landing Pages"
    return "Other"


def rows_to_map(rows):
    return {r["keys"][0]: r for r in rows}


def build_page_rows(map_cur, map_prev):
    out = []
    for k in set(map_cur) | set(map_prev):
        a = map_cur.get(k, {"clicks": 0, "impressions": 0, "position": 0, "ctr": 0})
        b = map_prev.get(k, {"clicks": 0, "impressions": 0, "position": 0, "ctr": 0})
        out.append({
            "page": short_page(k),
            "type": page_type(short_page(k)),
            "clicks_now": a["clicks"], "clicks_prev": b["clicks"],
            "clicks_delta": a["clicks"] - b["clicks"],
            "clicks_pct": pct_delta(a["clicks"], b["clicks"]),
            "impr_now": a["impressions"], "impr_prev": b["impressions"],
            "impr_delta": a["impressions"] - b["impressions"],
            "impr_pct": pct_delta(a["impressions"], b["impressions"]),
            "ctr_now": a["ctr"], "ctr_prev": b["ctr"],
            "ctr_delta": a["ctr"] - b["ctr"],
            "pos_now": round(a["position"], 2) if a["impressions"] else 0.0,
            "pos_prev": round(b["position"], 2) if b["impressions"] else 0.0,
            "pos_delta": round((a["position"] - b["position"]), 2) if (a["impressions"] and b["impressions"]) else 0.0,
        })
    return out


def type_summary(rows):
    """Per-type aggregate totals, impression-weighted position."""
    agg = {}
    for r in rows:
        t = agg.setdefault(r["type"], {
            "pages": 0, "clicks_now": 0, "clicks_prev": 0,
            "impr_now": 0, "impr_prev": 0,
            "pos_now_weighted": 0.0, "pos_prev_weighted": 0.0,
            "declining_pages": 0,
        })
        t["pages"] += 1
        t["clicks_now"] += r["clicks_now"]
        t["clicks_prev"] += r["clicks_prev"]
        t["impr_now"] += r["impr_now"]
        t["impr_prev"] += r["impr_prev"]
        t["pos_now_weighted"] += r["pos_now"] * r["impr_now"]
        t["pos_prev_weighted"] += r["pos_prev"] * r["impr_prev"]
        if r["clicks_delta"] < 0 or r["impr_delta"] < 0:
            t["declining_pages"] += 1
    for t in agg.values():
        t["pos_now"] = (t["pos_now_weighted"] / t["impr_now"]) if t["impr_now"] else 0.0
        t["pos_prev"] = (t["pos_prev_weighted"] / t["impr_prev"]) if t["impr_prev"] else 0.0
    return agg


PAGE_HEADER = [
    "Page", "Clicks Prev", "Clicks Now", "Clicks Δ", "Clicks Δ%",
    "Impr Prev", "Impr Now", "Impr Δ", "Impr Δ%",
    "CTR Prev %", "CTR Now %", "CTR Δ pts",
    "Pos Prev", "Pos Now", "Pos Δ",
]


def page_row_values(r):
    return [
        r["page"], r["clicks_prev"], r["clicks_now"], r["clicks_delta"],
        "" if r["clicks_pct"] == float("inf") else round(r["clicks_pct"], 1),
        r["impr_prev"], r["impr_now"], r["impr_delta"],
        "" if r["impr_pct"] == float("inf") else round(r["impr_pct"], 1),
        round(r["ctr_prev"] * 100, 2), round(r["ctr_now"] * 100, 2), round(r["ctr_delta"] * 100, 2),
        r["pos_prev"], r["pos_now"], r["pos_delta"],
    ]


def main():
    svc = get_service()
    site = pick_site(svc)
    print(f"Site: {site}")
    print(f"Current 28d:  {CUR_START} -> {CUR_END}")
    print(f"Previous 28d: {PREV_START} -> {PREV_END}\n")

    p_cur = query(svc, site, ["page"], CUR_START, CUR_END)
    p_prev = query(svc, site, ["page"], PREV_START, PREV_END)
    all_rows = build_page_rows(rows_to_map(p_cur), rows_to_map(p_prev))

    d_cur = query(svc, site, ["date"], CUR_START, CUR_END)
    d_prev = query(svc, site, ["date"], PREV_START, PREV_END)
    site_cur_clicks = sum(r.get("clicks", 0) for r in d_cur)
    site_cur_impr = sum(r.get("impressions", 0) for r in d_cur)
    site_cur_pos = (sum(r.get("position", 0) * r.get("impressions", 0) for r in d_cur) / site_cur_impr) if site_cur_impr else 0
    site_prev_clicks = sum(r.get("clicks", 0) for r in d_prev)
    site_prev_impr = sum(r.get("impressions", 0) for r in d_prev)
    site_prev_pos = (sum(r.get("position", 0) * r.get("impressions", 0) for r in d_prev) / site_prev_impr) if site_prev_impr else 0

    live_rows = [r for r in all_rows if r["clicks_prev"] >= MIN_PREV_CLICKS or r["impr_prev"] >= MIN_PREV_IMPR]
    summary = type_summary(live_rows)

    by_type = {}
    for r in live_rows:
        by_type.setdefault(r["type"], []).append(r)
    for t in by_type:
        by_type[t].sort(key=lambda x: (x["clicks_delta"], x["impr_delta"]))

    top20 = sorted(live_rows, key=lambda x: x["clicks_delta"])[:20]

    # === Create spreadsheet ===
    creds = Credentials.from_authorized_user_file(str(SHEETS_TOKEN))
    sheets = build("sheets", "v4", credentials=creds)

    present_types = [t for t in TYPE_ORDER if t in by_type]
    sheet_props = [{"properties": {"title": "Overall"}}]
    sheet_props += [{"properties": {"title": t}} for t in present_types]

    spreadsheet = sheets.spreadsheets().create(body={
        "properties": {"title": f"GSC Content Decline Report — {END_DATE.isoformat()}"},
        "sheets": sheet_props,
    }).execute()
    sid = spreadsheet["spreadsheetId"]
    url = spreadsheet["spreadsheetUrl"]
    print(f"Created spreadsheet: {url}")

    # === Overall tab ===
    overall_values = [
        [f"GSC Content Decline Report — {site}"],
        [f"Current 28d: {CUR_START} to {CUR_END}   |   Previous 28d: {PREV_START} to {PREV_END}"],
        [],
        ["SITE-WIDE TOTALS", "Current 28d", "Previous 28d", "Delta"],
        ["Clicks", site_cur_clicks, site_prev_clicks, f"{pct_delta(site_cur_clicks, site_prev_clicks):+.1f}%"],
        ["Impressions", site_cur_impr, site_prev_impr, f"{pct_delta(site_cur_impr, site_prev_impr):+.1f}%"],
        ["Avg Position", round(site_cur_pos, 2), round(site_prev_pos, 2), round(site_cur_pos - site_prev_pos, 2)],
        [],
        ["BY PAGE TYPE", "Pages Tracked", "Clicks Prev", "Clicks Now", "Clicks Δ",
         "Impr Prev", "Impr Now", "Impr Δ", "Pos Prev", "Pos Now", "Pos Δ", "# Declining Pages"],
    ]
    for t in present_types:
        s = summary[t]
        overall_values.append([
            t, s["pages"], s["clicks_prev"], s["clicks_now"], s["clicks_now"] - s["clicks_prev"],
            s["impr_prev"], s["impr_now"], s["impr_now"] - s["impr_prev"],
            round(s["pos_prev"], 2), round(s["pos_now"], 2), round(s["pos_now"] - s["pos_prev"], 2),
            s["declining_pages"],
        ])
    overall_values.append([])
    overall_values.append(["TOP 20 CLICKS DECLINERS (site-wide)", "Page Type"] + PAGE_HEADER[1:])
    for r in top20:
        overall_values.append([r["page"], r["type"]] + page_row_values(r)[1:])

    sheets.spreadsheets().values().update(
        spreadsheetId=sid, range="Overall!A1",
        valueInputOption="RAW", body={"values": overall_values},
    ).execute()

    # === Per-type tabs ===
    for t in present_types:
        rows = by_type[t]
        values = [PAGE_HEADER] + [page_row_values(r) for r in rows]
        sheets.spreadsheets().values().update(
            spreadsheetId=sid, range=f"'{t}'!A1",
            valueInputOption="RAW", body={"values": values},
        ).execute()
        print(f"  {t}: {len(rows)} pages")

    # === Formatting: freeze header rows, bold headers ===
    requests = []
    sheet_ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in spreadsheet["sheets"]}
    for t in present_types:
        requests.append({
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_ids[t], "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        })
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet_ids[t], "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }
        })
    requests.append({
        "updateSheetProperties": {
            "properties": {"sheetId": sheet_ids["Overall"], "gridProperties": {"frozenRowCount": 3}},
            "fields": "gridProperties.frozenRowCount",
        }
    })
    sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": requests}).execute()

    print(f"\nDone. Spreadsheet ID: {sid}")
    print(f"URL: {url}")


if __name__ == "__main__":
    main()
