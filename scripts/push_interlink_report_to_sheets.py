#!/usr/bin/env python3
"""
Push the full-site interlink report (scripts/interlink_full_report.py output)
into a new Google Sheet with 4 tabs: By Page, All Links (Edges), Summary by
Type, Unresolved Links.

Usage:
  python3 scripts/interlink_full_report.py      # regenerate the CSVs first
  python3 scripts/push_interlink_report_to_sheets.py
"""
import csv
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = ROOT / "audit"
TOKEN_FILE = ROOT / "credentials" / "token_backlinks.json"
CREDS_FILE = ROOT / "credentials" / "Google Creds.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

NAVY, ACCENT, WHITE, LIGHT, GOLD, RED_LIGHT = (
    "0B2440", "0BA6E2", "FFFFFF", "E8F4FB", "FFF3CD", "FBE4E4",
)


def get_creds():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
            TOKEN_FILE.write_text(creds.to_json())
    return creds


def rgb(hex6):
    r, g, b = int(hex6[0:2], 16), int(hex6[2:4], 16), int(hex6[4:6], 16)
    return {"red": r / 255, "green": g / 255, "blue": b / 255}


def read_csv(name):
    with open(AUDIT_DIR / name, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    return rows


def header_fmt_request(sheet_id, ncols):
    return {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1,
                  "startColumnIndex": 0, "endColumnIndex": ncols},
        "cell": {"userEnteredFormat": {
            "backgroundColor": rgb(NAVY),
            "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": rgb(WHITE)},
            "verticalAlignment": "MIDDLE",
        }},
        "fields": "userEnteredFormat",
    }}


def freeze_request(sheet_id, rows=1, cols=1):
    return {"updateSheetProperties": {
        "properties": {"sheetId": sheet_id,
                       "gridProperties": {"frozenRowCount": rows, "frozenColumnCount": cols}},
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
    }}


def col_width_request(sheet_id, idx, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": idx, "endIndex": idx + 1},
        "properties": {"pixelSize": px},
        "fields": "pixelSize",
    }}


def wrap_request(sheet_id, start_row, end_row, start_col, end_col):
    return {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row,
                  "startColumnIndex": start_col, "endColumnIndex": end_col},
        "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}},
        "fields": "userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment",
    }}


def banding_request(sheet_id, nrows, ncols):
    return {"addBanding": {"bandedRange": {
        "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": nrows,
                  "startColumnIndex": 0, "endColumnIndex": ncols},
        "rowProperties": {"headerColorStyle": {"rgbColor": rgb(NAVY)},
                          "firstBandColorStyle": {"rgbColor": rgb(WHITE)},
                          "secondBandColorStyle": {"rgbColor": rgb(LIGHT)}},
    }}}


def main():
    creds = get_creds()
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    by_page = read_csv("interlink_full_report_by_page.csv")
    edges = read_csv("interlink_full_report_edges.csv")
    summary = read_csv("interlink_full_report_summary.csv")
    unresolved = [edges[0]] + [r for r in edges[1:] if r[8].startswith("No")]

    ss = service.spreadsheets().create(body={
        "properties": {"title": "PipeRocket — Full-Site Interlinking Report (2026-07-01)"},
        "sheets": [
            {"properties": {"title": "By Page", "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 1}}},
            {"properties": {"title": "All Links (Edges)", "gridProperties": {"frozenRowCount": 1}}},
            {"properties": {"title": "Summary by Type", "gridProperties": {"frozenRowCount": 1}}},
            {"properties": {"title": "Unresolved Links", "gridProperties": {"frozenRowCount": 1}}},
        ],
    }).execute()
    sid = ss["spreadsheetId"]
    url = ss["spreadsheetUrl"]
    sheet_ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in ss["sheets"]}

    data_updates = [
        {"range": "By Page!A1", "values": by_page},
        {"range": "All Links (Edges)!A1", "values": edges},
        {"range": "Summary by Type!A1", "values": summary},
        {"range": "Unresolved Links!A1", "values": unresolved},
    ]
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sid,
        body={"valueInputOption": "RAW", "data": data_updates},
    ).execute()

    requests = []

    # By Page (8 cols: A Page URL, B Type, C Title, D In Count, E Out Count, F Orphan, G Inbound, H Outbound)
    bp_id = sheet_ids["By Page"]
    requests += [
        header_fmt_request(bp_id, 8),
        col_width_request(bp_id, 0, 260), col_width_request(bp_id, 1, 90),
        col_width_request(bp_id, 2, 280), col_width_request(bp_id, 3, 80),
        col_width_request(bp_id, 4, 80), col_width_request(bp_id, 5, 90),
        col_width_request(bp_id, 6, 420), col_width_request(bp_id, 7, 420),
        wrap_request(bp_id, 1, len(by_page), 6, 8),
        {"addConditionalFormatRule": {"rule": {
            "ranges": [{"sheetId": bp_id, "startRowIndex": 1, "endRowIndex": len(by_page),
                       "startColumnIndex": 0, "endColumnIndex": 8}],
            "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "YES"}]},
                           "format": {"backgroundColor": rgb(GOLD)}},
        }, "index": 0}},
    ]

    # All Links (Edges) — 9 cols: Source URL, Source Type, Source Title, Anchor Text,
    # Anchor Text Context, Target URL, Target Type, Target Title, Resolved
    ae_id = sheet_ids["All Links (Edges)"]
    requests += [
        header_fmt_request(ae_id, 9),
        col_width_request(ae_id, 0, 220), col_width_request(ae_id, 1, 80),
        col_width_request(ae_id, 2, 240), col_width_request(ae_id, 3, 200),
        col_width_request(ae_id, 4, 380), col_width_request(ae_id, 5, 220),
        col_width_request(ae_id, 6, 90), col_width_request(ae_id, 7, 240),
        col_width_request(ae_id, 8, 130),
        wrap_request(ae_id, 1, len(edges), 4, 5),
        banding_request(ae_id, len(edges), 9),
    ]

    # Summary by Type (7 cols)
    sm_id = sheet_ids["Summary by Type"]
    requests += [
        header_fmt_request(sm_id, 7),
        col_width_request(sm_id, 0, 110),
    ]

    # Unresolved Links (same 9-col shape as All Links)
    ur_id = sheet_ids["Unresolved Links"]
    requests += [
        header_fmt_request(ur_id, 9),
        col_width_request(ur_id, 0, 220), col_width_request(ur_id, 2, 240),
        col_width_request(ur_id, 4, 380), col_width_request(ur_id, 5, 220),
        col_width_request(ur_id, 7, 130),
        wrap_request(ur_id, 1, len(unresolved), 4, 5),
        {"repeatCell": {
            "range": {"sheetId": ur_id, "startRowIndex": 1, "endRowIndex": len(unresolved),
                      "startColumnIndex": 0, "endColumnIndex": 9},
            "cell": {"userEnteredFormat": {"backgroundColor": rgb(RED_LIGHT)}},
            "fields": "userEnteredFormat.backgroundColor",
        }},
    ]

    service.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": requests}).execute()

    print(f"\nSheet created: {url}")
    print(f"  By Page          : {len(by_page)-1} pages")
    print(f"  All Links        : {len(edges)-1} edges")
    print(f"  Summary by Type  : {len(summary)-1} types")
    print(f"  Unresolved Links : {len(unresolved)-1} broken internal targets")


if __name__ == "__main__":
    main()
