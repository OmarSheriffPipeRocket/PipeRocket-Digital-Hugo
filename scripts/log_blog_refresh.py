#!/usr/bin/env python3
"""
log_blog_refresh.py — record a blog refresh in the Blog Refresh Tracker sheet.

Does two things in one call:
  1. Appends a row to the "Change Log" tab (append-only history, one row per refresh).
  2. Updates that blog's "Last Refresh Date" in "Sheet1" (current-state tracker).

Sheet: https://docs.google.com/spreadsheets/d/1tUoYuEvwVxbjJdcEoYyjCwZ-7GuLc-gT2sq1eF7cTQw
Auth: credentials/token_backlinks.json (spreadsheets scope).

Usage:
  python3 scripts/log_blog_refresh.py \
      --slug enterprise-seo-strategy-and-framework \
      --date 2026-06-30 \
      --summary "Refreshed stats + added June spam-update note" \
      --stats "aio-coverage-2026; towcenter-ai-citation-60pct-wrong" \
      --news "june-2026-spam-update" \
      --other "fixed 1 dead link; reframed intro" \
      --commit abc1234
"""
import argparse
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SID = "1tUoYuEvwVxbjJdcEoYyjCwZ-7GuLc-gT2sq1eF7cTQw"
TOKEN = "credentials/token_backlinks.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--date", required=True, help="Refresh date YYYY-MM-DD")
    ap.add_argument("--summary", required=True)
    ap.add_argument("--stats", default="", help="stat_bank ids applied")
    ap.add_argument("--news", default="", help="news_bank ids applied")
    ap.add_argument("--other", default="", help="links / reframes / dead-links")
    ap.add_argument("--commit", default="")
    a = ap.parse_args()

    c = Credentials.from_authorized_user_file(TOKEN)
    s = build("sheets", "v4", credentials=c)

    # 1) resolve the blog title from Sheet1 (nice-to-have for the log row)
    rows = s.spreadsheets().values().get(
        spreadsheetId=SID, range="Sheet1!A2:C").execute().get("values", [])
    title, row_idx = "", None
    for i, r in enumerate(rows, start=2):
        if len(r) >= 2 and r[1] == a.slug:
            title = r[0]
            row_idx = i
            break
    if row_idx is None:
        sys.exit(f"Slug '{a.slug}' not found in Sheet1 — add it there first.")

    # 2) append to Change Log
    s.spreadsheets().values().append(
        spreadsheetId=SID, range="Change Log!A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": [[a.date, a.slug, title, a.summary,
                          a.stats, a.news, a.other, a.commit]]}).execute()

    # 3) update Last Refresh Date in Sheet1
    s.spreadsheets().values().update(
        spreadsheetId=SID, range=f"Sheet1!C{row_idx}",
        valueInputOption="RAW", body={"values": [[a.date]]}).execute()

    print(f"Logged refresh: {a.slug} @ {a.date} (Sheet1 row {row_idx} + Change Log).")


if __name__ == "__main__":
    main()
