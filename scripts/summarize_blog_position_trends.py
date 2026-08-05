#!/usr/bin/env python3
"""
summarize_blog_position_trends.py — turn the raw "Weekly Position" tab (one
row per blog per week) into a plain-English verdict per blog, written to a
new "Position Analysis Summary" tab on the Blog Refresh Tracker sheet.

Verdict is based on KEYWORD POSITION — the blog's verified primary keyword
(from the TAM Dashboard's Page -> Keyword Map, not a proxy) — not the
page-wide aggregate. Weeks with fewer than MIN_IMPR impressions are excluded
before computing a trend — a week with 1-5 impressions produces a
meaningless average position, and comparing a noise week against a real week
produces false "crashes" or "wins" (this is exactly what happened on earlier
passes of this analysis, first with a slug-derived keyword, then with a
GSC-top-query proxy — both were replaced once the real verified keyword map
was found).

Verdict:
  Improving:          delta >= +5   (position number went down = better ranking)
  Declining:          delta <= -5
  Flat:               -5 < delta < +5, with >=2 trustworthy weeks
  No real visibility: fewer than 2 trustworthy weeks for the primary keyword
                       (the page barely/never gets impressions on the exact
                       term it's supposed to be targeting — a different and
                       usually more urgent problem than "flat" or "declining")

Usage:
  python3 scripts/backfill_weekly_position_blogs.py   # refresh Weekly Position first
  python3 scripts/summarize_blog_position_trends.py
"""
from collections import defaultdict

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from create_listicle_position_tracker import TOKEN

BLOG_SID = "1tUoYuEvwVxbjJdcEoYyjCwZ-7GuLc-gT2sq1eF7cTQw"
MIN_IMPR = 20


def to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    creds = Credentials.from_authorized_user_file(str(TOKEN))
    sheets = build("sheets", "v4", credentials=creds)

    rows = sheets.spreadsheets().values().get(
        spreadsheetId=BLOG_SID, range="Weekly Position!A1:K2000").execute().get("values", [])
    header, data = rows[0], rows[1:]

    by_slug = defaultdict(list)
    titles, keywords, volumes = {}, {}, {}
    for r in data:
        r = r + [""] * (len(header) - len(r))
        d = dict(zip(header, r))
        by_slug[d["Slug"]].append(d)
        titles[d["Slug"]] = d["Title"]
        keywords[d["Slug"]] = d["Primary Keyword"]
        volumes[d["Slug"]] = d["Search Volume"]

    out_rows = []
    for slug, wks in by_slug.items():
        wks.sort(key=lambda x: int(x["Week #"]))
        series = [(to_float(w["Keyword Position"]), int(w["Keyword Impressions"] or 0)) for w in wks]
        trustworthy = [(p, i) for p, i in series if p is not None and i >= MIN_IMPR]
        total_impr = sum(i for _, i in series)
        n_weeks = len(series)
        n_trust = len(trustworthy)

        if n_trust >= 2:
            first_pos, last_pos = trustworthy[0][0], trustworthy[-1][0]
            delta = round(first_pos - last_pos, 1)
            if delta >= 5:
                verdict = "Improving"
            elif delta <= -5:
                verdict = "Declining"
            else:
                verdict = "Flat"
            note = f"{n_trust} of {n_weeks} weeks had enough impressions on its own primary keyword to trust"
        elif n_trust == 1:
            first_pos = last_pos = trustworthy[0][0]
            delta = ""
            verdict = "No real visibility"
            note = "Only 1 week ever had enough impressions on its primary keyword — can't tell a trend"
        else:
            first_pos = last_pos = delta = ""
            verdict = "No real visibility"
            note = "Never had enough impressions in any week for its own primary keyword"

        out_rows.append([
            slug, titles.get(slug, ""), keywords.get(slug, ""), volumes.get(slug, ""),
            verdict, first_pos if first_pos != "" else "", last_pos if last_pos != "" else "",
            delta, n_trust, n_weeks, total_impr, note,
        ])

    # Sort: Declining first (needs attention), then Improving, then Flat, then No real visibility
    order = {"Declining": 0, "Improving": 1, "Flat": 2, "No real visibility": 3}
    out_rows.sort(key=lambda r: (order[r[4]], -(r[7] if isinstance(r[7], (int, float)) else 0)))

    header_out = [["Slug", "Title", "Primary Keyword", "Search Volume", "Verdict",
                   "First Trustworthy Position", "Last Trustworthy Position",
                   "Position Change", "Trustworthy Weeks", "Total Weeks Tracked",
                   "Total Keyword Impressions", "Note"]]

    meta = sheets.spreadsheets().get(spreadsheetId=BLOG_SID).execute()
    existing = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    if "Position Analysis Summary" in existing:
        sheets.spreadsheets().batchUpdate(spreadsheetId=BLOG_SID, body={
            "requests": [{"deleteSheet": {"sheetId": existing["Position Analysis Summary"]}}]
        }).execute()
    sheets.spreadsheets().batchUpdate(spreadsheetId=BLOG_SID, body={
        "requests": [{"addSheet": {"properties": {"title": "Position Analysis Summary"}}}]
    }).execute()

    sheets.spreadsheets().values().update(
        spreadsheetId=BLOG_SID, range="Position Analysis Summary!A1",
        valueInputOption="RAW", body={"values": header_out + out_rows},
    ).execute()

    counts = defaultdict(int)
    for r in out_rows:
        counts[r[4]] += 1
    print(f"Wrote {len(out_rows)} blogs to 'Position Analysis Summary'.")
    for v, c in counts.items():
        print(f"  {v}: {c}")


if __name__ == "__main__":
    main()
