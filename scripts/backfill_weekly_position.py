#!/usr/bin/env python3
"""
backfill_weekly_position.py — pull WEEKLY GSC position history for each
listicle's PRIMARY KEYWORD (not just whatever query has the most impressions),
bucketed relative to that listicle's own first-refresh date (week 1 =
first_refresh_date .. +6 days, week 2 = next 7 days, etc.) rather than
calendar weeks, since every listicle started its refresh cadence on a
different date.

Primary keyword is derived from the slug per site convention (slug == primary
keyword, hyphenated — see feedback_slug_as_primary_keyword memory).

For listicles with no refresh yet, falls back to the Published date as the
start point and flags start_basis="published" so it's visually distinguishable
from a real refresh-anchored series.

Queries GSC per-page-per-query (dimensions=["date"], filtered to that exact
page URL AND that exact query string) so we get one row per calendar day for
just the primary keyword, then rolls those up into weekly buckets with an
impression-weighted average position (a plain average would let a
low-impression day skew the week as much as a high-impression day).

Writes/replaces the "Weekly Position" tab in the Listicle Position Tracker
sheet: Slug | Primary Keyword | Week # | Week Start | Week End | Position |
Impressions | Clicks | Start Basis.

Usage:
  python3 scripts/backfill_weekly_position.py
"""
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build as gbuild

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_listicle_position_tracker import (
    ROOT, TOKEN, get_title, get_history_entries, parse_date, primary_keyword_for,
)
from gsc_analysis import get_service, pick_site

import json

SID = "1aZl5Yq2G4CuDSYLWa7NkpnivjVfO3nDAdaexIVqZxPk"
END_DATE = date.today() - timedelta(days=3)  # GSC reporting lag


def query_page_daily(svc, site, page_url, query_str, start, end):
    """Per-page daily clicks/impressions/position, filtered to the exact page
    URL and, if query_str is given, ALSO the exact query string (AND — both
    filters in one filterGroup, GSC's default groupType). query_str=None
    aggregates across every query the page ranks for (use for content that
    targets a spread of queries rather than one exact head keyword)."""
    filters = [{"dimension": "page", "operator": "equals", "expression": page_url}]
    if query_str:
        filters.append({"dimension": "query", "operator": "equals", "expression": query_str})
    rows, start_row = [], 0
    while True:
        body = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["date"],
            "dimensionFilterGroups": [{"filters": filters}],
            "rowLimit": 25000,
            "startRow": start_row,
            "dataState": "all",
        }
        resp = svc.searchanalytics().query(siteUrl=site, body=body).execute()
        batch = resp.get("rows", [])
        rows.extend(batch)
        if len(batch) < 25000:
            break
        start_row += 25000
    return rows


def bucket_into_weeks(daily_rows, start):
    """daily_rows: list of {keys:[date_str], clicks, impressions, position}."""
    by_date = {r["keys"][0]: r for r in daily_rows}
    weeks = []
    cursor = start
    week_no = 1
    while cursor <= END_DATE:
        wk_end = min(cursor + timedelta(days=6), END_DATE)
        d = cursor
        clicks = impressions = 0
        pos_weighted = 0.0
        while d <= wk_end:
            r = by_date.get(d.isoformat())
            if r:
                clicks += r.get("clicks", 0)
                impressions += r.get("impressions", 0)
                pos_weighted += r.get("position", 0) * r.get("impressions", 0)
            d += timedelta(days=1)
        position = round(pos_weighted / impressions, 1) if impressions else ""
        weeks.append({
            "week_no": week_no, "start": cursor.isoformat(), "end": wk_end.isoformat(),
            "position": position, "impressions": impressions, "clicks": clicks,
        })
        cursor = wk_end + timedelta(days=1)
        week_no += 1
    return weeks


def main():
    state = json.loads((ROOT / "data" / "refresh-state.json").read_text())
    svc = get_service()
    site = pick_site(svc)

    out_rows = []
    for slug in state["publish_order"]:
        path = ROOT / "content" / "list" / f"{slug}.md"
        if not path.exists():
            print(f"WARNING: missing file for {slug}", file=sys.stderr)
            continue
        text = path.read_text()
        entries = get_history_entries(text)

        published = None
        refresh_dates = []
        for date_str, desc in entries:
            if "publish" in desc.lower():
                published = parse_date(date_str)
            else:
                d = parse_date(date_str)
                if d:
                    refresh_dates.append(d)
        refresh_dates.sort()

        if refresh_dates:
            start = refresh_dates[0].date()
            basis = "refresh"
        elif published:
            start = published.date()
            basis = "published"
        else:
            print(f"WARNING: no date info for {slug}, skipping", file=sys.stderr)
            continue

        if start > END_DATE:
            print(f"SKIP {slug}: start date {start} is after GSC window end {END_DATE}", file=sys.stderr)
            continue

        page_url = f"https://piperocket.digital/list/{slug}/"
        primary_keyword = primary_keyword_for(slug)
        print(f"Querying {slug} ({primary_keyword!r}) from {start} ({basis})...")
        daily = query_page_daily(svc, site, page_url, primary_keyword, start, END_DATE)
        weeks = bucket_into_weeks(daily, start)
        for w in weeks:
            out_rows.append([
                slug, primary_keyword, w["week_no"], w["start"], w["end"],
                w["position"], w["impressions"], w["clicks"], basis,
            ])
        time.sleep(0.3)  # be polite to the GSC quota

    creds = Credentials.from_authorized_user_file(str(TOKEN))
    sheets = gbuild("sheets", "v4", credentials=creds)

    # (Re)create the Weekly Position tab so reruns don't duplicate/stack rows.
    meta = sheets.spreadsheets().get(spreadsheetId=SID).execute()
    existing = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    if "Weekly Position" in existing:
        sheets.spreadsheets().batchUpdate(spreadsheetId=SID, body={
            "requests": [{"deleteSheet": {"sheetId": existing["Weekly Position"]}}]
        }).execute()
    sheets.spreadsheets().batchUpdate(spreadsheetId=SID, body={
        "requests": [{"addSheet": {"properties": {"title": "Weekly Position"}}}]
    }).execute()

    header = [["Slug", "Primary Keyword", "Week #", "Week Start", "Week End",
               "Position", "Impressions", "Clicks", "Start Basis"]]
    sheets.spreadsheets().values().update(
        spreadsheetId=SID, range="Weekly Position!A1",
        valueInputOption="RAW", body={"values": header + out_rows},
    ).execute()

    print(f"\nWrote {len(out_rows)} weekly rows across {len(state['publish_order'])} listicles to 'Weekly Position' tab.")


if __name__ == "__main__":
    main()
