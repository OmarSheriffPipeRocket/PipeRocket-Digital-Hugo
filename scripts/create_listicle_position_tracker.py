#!/usr/bin/env python3
"""
create_listicle_position_tracker.py — one-time setup for the Listicle Position
Tracker Google Sheet.

For each of the 41 agency listicles in data/refresh-state.json's publish_order:
  - Reads title + Published date + first non-"Published" Update History entry
    (the actual first refresh date) straight from the markdown file.
  - Derives the listicle's primary keyword from its slug (site convention:
    slug == primary keyword, hyphenated — see feedback_slug_as_primary_keyword
    memory), and pulls GSC position/impressions/clicks for that EXACT query
    string (not just whatever query happens to have the most impressions)
    from the latest credentials/gsc_output/qp_<date>.json full export (run
    scripts/gsc_query_page.py first to refresh that file).

Creates a new spreadsheet with two tabs:
  - Sheet1: current-state snapshot (Slug | Title | Published | First Refresh
    Date | GSC Position | Primary Keyword | 6wk Impressions | 6wk Clicks |
    Snapshot Date)
  - Position Log: append-only history (Snapshot Date | Slug | Position |
    Primary Keyword | Impressions | Clicks), seeded with one baseline row
    per listicle.

Usage:
  python3 scripts/gsc_query_page.py   # refresh GSC data first
  python3 scripts/create_listicle_position_tracker.py --snapshot-date 2026-07-30
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
TOKEN = ROOT / "credentials" / "token_backlinks.json"
GSC_OUT = ROOT / "credentials" / "gsc_output"


def get_title(text):
    m = re.search(r'^title:\s*"?(.+?)"?\s*$', text, re.M)
    return m.group(1) if m else ""


def get_history_entries(text):
    m = re.search(r'## Update History\n(.*?)(?:\n## |\Z)', text, re.S)
    if not m:
        return []
    return re.findall(r'-\s*\*\*(.+?):\*\*\s*(.+)', m.group(1))


def parse_date(d):
    try:
        return datetime.strptime(d.strip(), "%B %d, %Y")
    except ValueError:
        return None


def primary_keyword_for(slug):
    """Site convention: slug == primary keyword, hyphenated. De-hyphenate it."""
    return slug.replace("-", " ")


def latest_full_query_export():
    """The full (non-rollup) page×query export — rollup only keeps the top 25
    queries per page by impressions, which can omit the primary keyword if
    it's not the highest-impression query for that page."""
    files = sorted(f for f in GSC_OUT.glob("qp_*.json")
                    if re.fullmatch(r"qp_\d{4}-\d{2}-\d{2}\.json", f.name))
    if not files:
        sys.exit("No qp_<date>.json found — run scripts/gsc_query_page.py first.")
    return json.loads(files[-1].read_text())


def build_rows(snapshot_date):
    state = json.loads((ROOT / "data" / "refresh-state.json").read_text())
    full = latest_full_query_export()
    by_page = {}
    for r in full["rows"]:
        by_page.setdefault(r["page"], []).append(r)

    rows = []
    for slug in state["publish_order"]:
        path = ROOT / "content" / "list" / f"{slug}.md"
        if not path.exists():
            print(f"WARNING: missing file for slug {slug}", file=sys.stderr)
            continue
        text = path.read_text()
        title = get_title(text)
        entries = get_history_entries(text)

        published = ""
        refresh_dates = []
        for date_str, desc in entries:
            if "publish" in desc.lower():
                published = date_str.strip()
            else:
                refresh_dates.append(date_str.strip())

        parsed = sorted(
            [(parse_date(d), d) for d in refresh_dates if parse_date(d)],
            key=lambda x: x[0],
        )
        first_refresh = parsed[0][1] if parsed else ""

        primary_keyword = primary_keyword_for(slug)
        page_url = f"https://piperocket.digital/list/{slug}/"
        page_rows = by_page.get(page_url, [])
        match = next((r for r in page_rows
                      if r["query"].strip().lower() == primary_keyword.lower()), None)
        position = round(match["position"], 1) if match else ""
        impressions = match["impressions"] if match else 0
        clicks = match["clicks"] if match else 0

        rows.append({
            "slug": slug, "title": title, "published": published,
            "first_refresh": first_refresh, "position": position,
            "primary_keyword": primary_keyword, "impressions": impressions,
            "clicks": clicks,
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-date", required=True, help="YYYY-MM-DD, stamped as the baseline snapshot date")
    a = ap.parse_args()

    rows = build_rows(a.snapshot_date)

    creds = Credentials.from_authorized_user_file(str(TOKEN))
    sheets = build("sheets", "v4", credentials=creds)

    spreadsheet = sheets.spreadsheets().create(body={
        "properties": {"title": "Listicle Position Tracker"},
        "sheets": [
            {"properties": {"title": "Sheet1"}},
            {"properties": {"title": "Position Log"}},
        ],
    }).execute()
    sid = spreadsheet["spreadsheetId"]
    url = spreadsheet["spreadsheetUrl"]
    print(f"Created spreadsheet: {url}")

    sheet1_header = [["Title", "Slug", "Published Date", "First Refresh Date",
                       "GSC Position", "Primary Keyword", "6wk Impressions", "6wk Clicks",
                       "Snapshot Date"]]
    sheet1_rows = [
        [r["title"], r["slug"], r["published"], r["first_refresh"],
         r["position"], r["primary_keyword"], r["impressions"], r["clicks"],
         a.snapshot_date]
        for r in rows
    ]
    sheets.spreadsheets().values().update(
        spreadsheetId=sid, range="Sheet1!A1",
        valueInputOption="RAW", body={"values": sheet1_header + sheet1_rows},
    ).execute()

    log_header = [["Snapshot Date", "Slug", "GSC Position", "Primary Keyword",
                    "Impressions", "Clicks"]]
    log_rows = [
        [a.snapshot_date, r["slug"], r["position"], r["primary_keyword"],
         r["impressions"], r["clicks"]]
        for r in rows
    ]
    sheets.spreadsheets().values().update(
        spreadsheetId=sid, range="Position Log!A1",
        valueInputOption="RAW", body={"values": log_header + log_rows},
    ).execute()

    print(f"Wrote {len(rows)} rows to Sheet1 and Position Log.")
    print(f"\nSpreadsheet ID: {sid}")
    print(f"URL: {url}")


if __name__ == "__main__":
    main()
