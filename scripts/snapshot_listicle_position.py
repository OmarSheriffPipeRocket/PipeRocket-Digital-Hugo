#!/usr/bin/env python3
"""
snapshot_listicle_position.py — append a new GSC-position snapshot to the
Listicle Position Tracker sheet (run periodically after gsc_query_page.py).

Updates Sheet1's GSC Position / Primary Keyword / Impressions / Clicks /
Snapshot Date columns in place, and appends one row per listicle to Position
Log — so Position Log becomes a time series you can chart per slug.

Usage:
  python3 scripts/gsc_query_page.py   # refresh GSC data first
  python3 scripts/snapshot_listicle_position.py --snapshot-date 2026-08-06
"""
import argparse

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from create_listicle_position_tracker import TOKEN, build_rows

SID = "1aZl5Yq2G4CuDSYLWa7NkpnivjVfO3nDAdaexIVqZxPk"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-date", required=True, help="YYYY-MM-DD")
    a = ap.parse_args()

    rows = build_rows(a.snapshot_date)

    creds = Credentials.from_authorized_user_file(str(TOKEN))
    sheets = build("sheets", "v4", credentials=creds)

    sheet1_rows = [
        [r["title"], r["slug"], r["published"], r["first_refresh"],
         r["position"], r["primary_keyword"], r["impressions"], r["clicks"],
         a.snapshot_date]
        for r in rows
    ]
    sheets.spreadsheets().values().update(
        spreadsheetId=SID, range="Sheet1!A2",
        valueInputOption="RAW", body={"values": sheet1_rows},
    ).execute()

    log_rows = [
        [a.snapshot_date, r["slug"], r["position"], r["primary_keyword"],
         r["impressions"], r["clicks"]]
        for r in rows
    ]
    sheets.spreadsheets().values().append(
        spreadsheetId=SID, range="Position Log!A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": log_rows},
    ).execute()

    print(f"Snapshotted {len(rows)} listicles @ {a.snapshot_date}.")


if __name__ == "__main__":
    main()
