#!/usr/bin/env python3
"""Fetch avg monthly search volume (Keyword Planner) for a list of keywords.

Uses the Google Ads API via credentials/google-ads.yaml.

    # keywords as args
    python3 scripts/keyword_volume.py "saas seo" "b2b ppc agency"

    # keywords from a file (one per line) -> CSV on stdout
    python3 scripts/keyword_volume.py --file kw.txt --csv

Defaults to US (geo 2840) + English (lang 1000); override with --geo / --lang.
Importable: from keyword_volume import get_volumes -> {kw: {'sv':int,'competition':str}}
"""
import argparse
import pathlib
import sys
import time

from google.ads.googleads.client import GoogleAdsClient
from google.api_core.exceptions import ResourceExhausted

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "credentials" / "google-ads.yaml"
CUSTOMER_ID = "8831598164"  # PipeRocket Digital
CHUNK = 20  # API allows up to 20 keywords per historical-metrics request


def get_volumes(keywords, geo="2840", lang="1000"):
    client = GoogleAdsClient.load_from_storage(str(CONFIG))
    svc = client.get_service("KeywordPlanIdeaService")
    out = {}
    uniq = list(dict.fromkeys(k.strip() for k in keywords if k.strip()))
    for i in range(0, len(uniq), CHUNK):
        batch = uniq[i : i + CHUNK]
        req = client.get_type("GenerateKeywordHistoricalMetricsRequest")
        req.customer_id = CUSTOMER_ID
        req.keywords.extend(batch)
        req.language = f"languageConstants/{lang}"
        req.geo_target_constants.append(f"geoTargetConstants/{geo}")
        req.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
        # Throttle + retry: the API caps requests-per-method (~4/s).
        for attempt in range(6):
            try:
                resp = svc.generate_keyword_historical_metrics(request=req)
                break
            except ResourceExhausted:
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError("Rate limit: exhausted retries")
        time.sleep(0.4)  # stay under the per-method rate cap between batches
        for r in resp.results:
            m = r.keyword_metrics
            out[r.text.lower()] = {
                "sv": m.avg_monthly_searches,
                "competition": m.competition.name,
            }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keywords", nargs="*")
    ap.add_argument("--file", help="file with one keyword per line")
    ap.add_argument("--geo", default="2840")
    ap.add_argument("--lang", default="1000")
    ap.add_argument("--csv", action="store_true")
    args = ap.parse_args()

    kws = list(args.keywords)
    if args.file:
        kws += pathlib.Path(args.file).read_text().splitlines()
    if not kws:
        print("No keywords given.", file=sys.stderr)
        sys.exit(1)

    res = get_volumes(kws, geo=args.geo, lang=args.lang)
    if args.csv:
        print("keyword,avg_monthly_searches,competition")
        for k in kws:
            k = k.strip()
            if not k:
                continue
            d = res.get(k.lower(), {})
            print(f'"{k}",{d.get("sv","")},{d.get("competition","")}')
    else:
        for k in kws:
            k = k.strip()
            if not k:
                continue
            d = res.get(k.lower())
            print(f"{k:40s} {d['sv'] if d else 'n/a':>8} {d['competition'] if d else ''}")


if __name__ == "__main__":
    main()
