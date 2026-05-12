"""
GSC WoW analysis for piperocket.digital.

First run: opens browser for OAuth consent. Saves token to credentials/token.json.
Subsequent runs: reuses the token.

Usage:
  python3 scripts/gsc_analysis.py
"""

import json
import os
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
CREDS_FILE = ROOT / "credentials" / "Google Creds.json"
TOKEN_FILE = ROOT / "credentials" / "token.json"
OUT_DIR = ROOT / "credentials" / "gsc_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# Site can be either URL-prefix or domain property. Script auto-detects.
CANDIDATE_SITES = [
    "sc-domain:piperocket.digital",
    "https://piperocket.digital/",
]

# Pull ~6 weeks so we have 4 prior weeks + last 10 days context. GSC has ~2-3 day reporting delay.
END_DATE = date.today() - timedelta(days=3)
START_DATE = END_DATE - timedelta(days=41)  # 6 weeks-ish


def get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(
                port=0,
                login_hint="omar@piperocket.digital",
                open_browser=False,
                authorization_prompt_message=(
                    "\n\n========================================\n"
                    "COPY THIS URL into your browser (omar@piperocket.digital):\n\n"
                    "{url}\n"
                    "========================================\n"
                ),
                success_message="Auth complete. You can close this tab.",
            )
        TOKEN_FILE.write_text(creds.to_json())
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def pick_site(svc):
    sites = svc.sites().list().execute().get("siteEntry", [])
    available = [s["siteUrl"] for s in sites]
    print(f"GSC sites on this account: {available}")
    for candidate in CANDIDATE_SITES:
        if candidate in available:
            return candidate
    if available:
        print(f"No exact match; using first available: {available[0]}")
        return available[0]
    raise RuntimeError("No GSC sites accessible with this credential.")


def query(svc, site, dimensions, start, end, row_limit=25000):
    rows, start_row = [], 0
    while True:
        body = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": dimensions,
            "rowLimit": row_limit,
            "startRow": start_row,
            "dataState": "all",
        }
        resp = svc.searchanalytics().query(siteUrl=site, body=body).execute()
        batch = resp.get("rows", [])
        rows.extend(batch)
        if len(batch) < row_limit:
            break
        start_row += row_limit
    return rows


def bucket_weeks(end):
    """Returns list of (label, start, end) for the trailing 4 weeks + last-10-days bucket."""
    weeks = []
    cursor = end
    for i in range(4):
        wk_end = cursor
        wk_start = cursor - timedelta(days=6)
        weeks.append((f"W-{i}", wk_start, wk_end))
        cursor = wk_start - timedelta(days=1)
    weeks.reverse()  # oldest first
    # last 10 days separate
    last10 = ("LAST_10", end - timedelta(days=9), end)
    prior10 = ("PRIOR_10", end - timedelta(days=19), end - timedelta(days=10))
    return weeks, last10, prior10


def sum_metrics(rows):
    c = sum(r.get("clicks", 0) for r in rows)
    i = sum(r.get("impressions", 0) for r in rows)
    pos_weighted = sum(r.get("position", 0) * r.get("impressions", 0) for r in rows)
    avg_pos = (pos_weighted / i) if i else 0
    ctr = (c / i) if i else 0
    return {"clicks": c, "impressions": i, "ctr": ctr, "position": avg_pos}


def pct_delta(now, prev):
    if prev == 0:
        return float("inf") if now > 0 else 0.0
    return (now - prev) / prev * 100


def main():
    svc = get_service()
    site = pick_site(svc)
    print(f"\nUsing site: {site}")
    print(f"Date range: {START_DATE} → {END_DATE}\n")

    weeks, last10, prior10 = bucket_weeks(END_DATE)

    # === 1. Daily totals for the full window ===
    daily = query(svc, site, ["date"], START_DATE, END_DATE)
    daily_map = {r["keys"][0]: r for r in daily}

    weekly_summary = []
    for label, ws, we in weeks:
        rows = [daily_map[d.isoformat()] for d in (ws + timedelta(days=i) for i in range(7)) if d.isoformat() in daily_map]
        weekly_summary.append({"label": label, "start": ws.isoformat(), "end": we.isoformat(), **sum_metrics(rows)})

    # Last 10 vs prior 10 days
    def metrics_for_range(s, e):
        rows = [daily_map[d.isoformat()] for d in (s + timedelta(days=i) for i in range((e - s).days + 1)) if d.isoformat() in daily_map]
        return sum_metrics(rows)

    last10_m = metrics_for_range(last10[1], last10[2])
    prior10_m = metrics_for_range(prior10[1], prior10[2])

    # === 2. Top queries last 10 days vs prior 10 ===
    q_last = query(svc, site, ["query"], last10[1], last10[2])
    q_prior = query(svc, site, ["query"], prior10[1], prior10[2])
    qmap_last = {r["keys"][0]: r for r in q_last}
    qmap_prior = {r["keys"][0]: r for r in q_prior}

    # === 3. Top pages last 10 vs prior 10 ===
    p_last = query(svc, site, ["page"], last10[1], last10[2])
    p_prior = query(svc, site, ["page"], prior10[1], prior10[2])
    pmap_last = {r["keys"][0]: r for r in p_last}
    pmap_prior = {r["keys"][0]: r for r in p_prior}

    # === Build query movers ===
    all_q = set(qmap_last) | set(qmap_prior)
    query_deltas = []
    for q in all_q:
        a = qmap_last.get(q, {"clicks": 0, "impressions": 0, "position": 0, "ctr": 0})
        b = qmap_prior.get(q, {"clicks": 0, "impressions": 0, "position": 0, "ctr": 0})
        query_deltas.append({
            "query": q,
            "clicks_now": a["clicks"], "clicks_prev": b["clicks"],
            "clicks_delta": a["clicks"] - b["clicks"],
            "impr_now": a["impressions"], "impr_prev": b["impressions"],
            "impr_delta": a["impressions"] - b["impressions"],
            "pos_now": a["position"], "pos_prev": b["position"],
            "pos_delta": a["position"] - b["position"] if b["position"] else 0,
        })

    page_deltas = []
    all_p = set(pmap_last) | set(pmap_prior)
    for p in all_p:
        a = pmap_last.get(p, {"clicks": 0, "impressions": 0, "position": 0, "ctr": 0})
        b = pmap_prior.get(p, {"clicks": 0, "impressions": 0, "position": 0, "ctr": 0})
        page_deltas.append({
            "page": p,
            "clicks_now": a["clicks"], "clicks_prev": b["clicks"],
            "clicks_delta": a["clicks"] - b["clicks"],
            "impr_now": a["impressions"], "impr_prev": b["impressions"],
            "impr_delta": a["impressions"] - b["impressions"],
            "pos_now": a["position"], "pos_prev": b["position"],
            "pos_delta": a["position"] - b["position"] if b["position"] else 0,
        })

    # === Output ===
    report = {
        "site": site,
        "date_range": {"start": START_DATE.isoformat(), "end": END_DATE.isoformat()},
        "weekly_summary": weekly_summary,
        "last_10_vs_prior_10": {
            "last_10": {"window": [last10[1].isoformat(), last10[2].isoformat()], **last10_m},
            "prior_10": {"window": [prior10[1].isoformat(), prior10[2].isoformat()], **prior10_m},
            "delta_pct": {
                "clicks": pct_delta(last10_m["clicks"], prior10_m["clicks"]),
                "impressions": pct_delta(last10_m["impressions"], prior10_m["impressions"]),
                "ctr": pct_delta(last10_m["ctr"], prior10_m["ctr"]),
                "position": last10_m["position"] - prior10_m["position"],
            },
        },
        "top_query_gainers": sorted(query_deltas, key=lambda x: -x["clicks_delta"])[:20],
        "top_query_losers": sorted(query_deltas, key=lambda x: x["clicks_delta"])[:20],
        "top_impression_gainers": sorted(query_deltas, key=lambda x: -x["impr_delta"])[:20],
        "top_impression_losers": sorted(query_deltas, key=lambda x: x["impr_delta"])[:20],
        "top_page_gainers": sorted(page_deltas, key=lambda x: -x["clicks_delta"])[:20],
        "top_page_losers": sorted(page_deltas, key=lambda x: x["clicks_delta"])[:20],
        "top_pages_now": sorted(page_deltas, key=lambda x: -x["clicks_now"])[:30],
        "top_queries_now": sorted(query_deltas, key=lambda x: -x["clicks_now"])[:30],
    }

    out_file = OUT_DIR / f"report_{END_DATE.isoformat()}.json"
    out_file.write_text(json.dumps(report, indent=2, default=str))
    print(f"Wrote {out_file}")

    # === Console summary ===
    print("\n=== Weekly WoW (oldest → newest) ===")
    print(f"{'week':<8}{'start':<12}{'end':<12}{'clicks':>8}{'impr':>10}{'ctr':>8}{'pos':>8}")
    for w in weekly_summary:
        print(f"{w['label']:<8}{w['start']:<12}{w['end']:<12}{w['clicks']:>8}{w['impressions']:>10}{w['ctr']*100:>7.2f}%{w['position']:>8.2f}")

    print("\n=== Last 10 vs prior 10 days ===")
    d = report["last_10_vs_prior_10"]["delta_pct"]
    print(f"Clicks:      {last10_m['clicks']} vs {prior10_m['clicks']}  ({d['clicks']:+.1f}%)")
    print(f"Impressions: {last10_m['impressions']} vs {prior10_m['impressions']}  ({d['impressions']:+.1f}%)")
    print(f"CTR:         {last10_m['ctr']*100:.2f}% vs {prior10_m['ctr']*100:.2f}%  ({d['ctr']:+.1f}%)")
    print(f"Avg pos:     {last10_m['position']:.2f} vs {prior10_m['position']:.2f}  (Δ {d['position']:+.2f})")


if __name__ == "__main__":
    main()
