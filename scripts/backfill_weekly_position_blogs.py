#!/usr/bin/env python3
"""
backfill_weekly_position_blogs.py — same idea as backfill_weekly_position.py
(listicles) but for blogs, reading refresh history from the Blog Refresh
Tracker's "Change Log" tab instead of an in-file Update History section.

For each blog slug that has at least one Change Log entry, first-refresh
date = the EARLIEST Change Log date for that slug (a blog can be refreshed
more than once; we want the first one, to match "since the point of refresh").
Blogs with zero Change Log entries have never been refreshed under this
system (their Sheet1 "Last Refresh Date" is just a seeded lastmod baseline,
not a real refresh event) — they're skipped.

UNLIKE LISTICLES, there's no slug-derived "primary keyword" here. Listicle
slugs are short commercial phrases that usually equal the literal target query
("best-enterprise-seo-agencies" -> "best enterprise seo agencies"). Blog slugs
are full title phrases ("how-to-do-saas-content-audit") that rarely match the
actual head query verbatim, and there's no "primary keyword" column for blogs
in the 2026 Content Tracker sheet either. The real, verified primary keyword
per page (with search volume) lives in the separate "PipeRocket TAM Dashboard"
sheet's "Page -> Keyword Map" tab (spreadsheet
1VPqR0b162Pz8nx3q5S5BGAkUeyM5sxuT2l-z7z6nmig) — that's what this script reads.
48 of the 49 refreshed blogs are mapped there; the one that isn't
(research-ai-seo-statistics) also has zero GSC impressions at all, so it's
skipped for the keyword-specific series (still gets a page-wide series).

Tracks BOTH signals side by side per week, since they answer different
questions:
  - Keyword Position / Keyword Impressions: position for that ONE identified
    keyword specifically (same method as the listicle tracker).
  - Page Position / Page Impressions: page-wide impression-weighted average
    across EVERY query the page ranks for (dilutes any single keyword's
    signal, but shows overall visibility — useful since blog content often
    intentionally targets a spread of informational queries, not one head
    term).

Writes/replaces a "Weekly Position" tab on the Blog Refresh Tracker sheet:
Slug | Title | Primary Keyword | Search Volume | Week # | Week Start | Week
End | Keyword Position | Keyword Impressions | Page Position | Page
Impressions.

Usage:
  python3 scripts/gsc_query_page.py   # refresh GSC data first
  python3 scripts/backfill_weekly_position_blogs.py
"""
import json
import re
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build as gbuild

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_listicle_position_tracker import ROOT, TOKEN, GSC_OUT
from backfill_weekly_position import query_page_daily, bucket_into_weeks
from gsc_analysis import get_service, pick_site

BLOG_SID = "1tUoYuEvwVxbjJdcEoYyjCwZ-7GuLc-gT2sq1eF7cTQw"
TAM_SID = "1VPqR0b162Pz8nx3q5S5BGAkUeyM5sxuT2l-z7z6nmig"
END_DATE = date.today() - timedelta(days=3)


def verified_primary_keywords(sheets):
    """slug -> (primary keyword, search volume) from the TAM Dashboard's
    'Page -> Keyword Map' tab — the real, human-verified target keyword per
    page, not a GSC-derived proxy."""
    rows = sheets.spreadsheets().values().get(
        spreadsheetId=TAM_SID, range="'Page -> Keyword Map'!A2:F2000").execute().get("values", [])
    out = {}
    for r in rows:
        if not r or "/blogs/" not in r[0]:
            continue
        m = re.search(r'/blogs/([^/]+)/', r[0])
        if not m:
            continue
        primary_kw = r[4] if len(r) > 4 else ""
        vol = r[5] if len(r) > 5 else ""
        out[m.group(1)] = (primary_kw, vol)
    return out


def main():
    creds = Credentials.from_authorized_user_file(str(TOKEN))
    sheets = gbuild("sheets", "v4", credentials=creds)

    sheet1 = sheets.spreadsheets().values().get(
        spreadsheetId=BLOG_SID, range="Sheet1!A2:C1000").execute().get("values", [])
    log = sheets.spreadsheets().values().get(
        spreadsheetId=BLOG_SID, range="Change Log!A2:H1000").execute().get("values", [])

    titles = {r[1]: r[0] for r in sheet1 if len(r) > 1}

    by_slug_dates = defaultdict(list)
    for r in log:
        if len(r) < 2:
            continue
        try:
            d = datetime.strptime(r[0], "%Y-%m-%d").date()
        except ValueError:
            continue
        by_slug_dates[r[1]].append(d)

    first_refresh = {slug: min(dates) for slug, dates in by_slug_dates.items()}
    print(f"{len(first_refresh)} blogs have >=1 refresh event.")

    svc = get_service()
    site = pick_site(svc)
    verified_kw = verified_primary_keywords(sheets)

    out_rows = []
    for slug, start in sorted(first_refresh.items(), key=lambda x: x[1]):
        if start > END_DATE:
            print(f"SKIP {slug}: start {start} after window end {END_DATE}", file=sys.stderr)
            continue
        page_url = f"https://piperocket.digital/blogs/{slug}/"
        title = titles.get(slug, "")
        primary_keyword, vol = verified_kw.get(slug, ("", ""))
        if not primary_keyword:
            print(f"NOTE: {slug} has no verified primary keyword in the TAM map", file=sys.stderr)

        print(f"Querying {slug} — page-wide from {start}...")
        daily_page = query_page_daily(svc, site, page_url, None, start, END_DATE)
        weeks_page = {w["week_no"]: w for w in bucket_into_weeks(daily_page, start)}
        time.sleep(0.3)

        if primary_keyword:
            print(f"Querying {slug} — keyword {primary_keyword!r} from {start}...")
            daily_kw = query_page_daily(svc, site, page_url, primary_keyword, start, END_DATE)
            weeks_kw = {w["week_no"]: w for w in bucket_into_weeks(daily_kw, start)}
            time.sleep(0.3)
        else:
            weeks_kw = {}

        for wn in sorted(weeks_page):
            wp = weeks_page[wn]
            wk = weeks_kw.get(wn, {})
            out_rows.append([
                slug, title, primary_keyword, vol, wn, wp["start"], wp["end"],
                wk.get("position", ""), wk.get("impressions", 0),
                wp["position"], wp["impressions"],
            ])

    meta = sheets.spreadsheets().get(spreadsheetId=BLOG_SID).execute()
    existing = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    if "Weekly Position" in existing:
        sheets.spreadsheets().batchUpdate(spreadsheetId=BLOG_SID, body={
            "requests": [{"deleteSheet": {"sheetId": existing["Weekly Position"]}}]
        }).execute()
    sheets.spreadsheets().batchUpdate(spreadsheetId=BLOG_SID, body={
        "requests": [{"addSheet": {"properties": {"title": "Weekly Position"}}}]
    }).execute()

    header = [["Slug", "Title", "Primary Keyword", "Search Volume", "Week #",
               "Week Start", "Week End", "Keyword Position", "Keyword Impressions",
               "Page Position", "Page Impressions"]]
    sheets.spreadsheets().values().update(
        spreadsheetId=BLOG_SID, range="Weekly Position!A1",
        valueInputOption="RAW", body={"values": header + out_rows},
    ).execute()

    print(f"\nWrote {len(out_rows)} weekly rows across {len(first_refresh)} blogs to 'Weekly Position' tab.")


if __name__ == "__main__":
    main()
