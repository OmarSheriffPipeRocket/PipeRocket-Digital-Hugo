"""Switch 24 OLD-template WP posts to single-test.php via REST API.

Usage:
  # Dry run (default — shows what would change, makes NO writes):
  python3 scripts/switch_template.py

  # Test one post first, e.g., saas-ppc-checklist (id 2504):
  python3 scripts/switch_template.py --execute --only 2504

  # After verifying, apply to all 24:
  python3 scripts/switch_template.py --execute

Auth: reads credentials/wp_app_password.txt
  username: omar@piperocket.digital
  password: xxxx xxxx xxxx xxxx xxxx xxxx
"""

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CREDS = ROOT / "credentials" / "wp_app_password.txt"

BASE = "https://piperocket.digital"
NEW_TEMPLATE = "single-test.php"

# (wp_id, slug, friendly_url)
POSTS = [
    (2463, "b2b-demand-generation-guide", "/blogs/b2b-demand-generation-guide/"),
    (2468, "b2b-inbound-marketing-guide", "/blogs/b2b-inbound-marketing-guide/"),
    (2441, "b2b-lead-generation", "/blogs/b2b-lead-generation/"),
    (2471, "b2b-linkedin-marketing-guide", "/blogs/b2b-linkedin-marketing-guide/"),
    (2438, "b2b-marketing", "/blogs/b2b-marketing/"),
    (2373, "b2b-saas-seo", "/blogs/b2b-saas-seo/"),
    (2476, "fintech-seo-guide", "/blogs/fintech-seo-guide/"),
    (2515, "the-no-nonsense-guide-to-auditing-your-saas-ppc-account", "/blogs/how-to-conduct-a-saas-ppc-audit/"),
    (2794, "how-to-run-a-saas-content-audit-that-actually-moves-rankings", "/blogs/how-to-do-saas-content-audit/"),
    (2593, "how-to-do-saas-seo-competitor-analysis", "/blogs/how-to-do-saas-seo-competitor-analysis/"),
    (2597, "how-to-do-saas-seo-keyword-research", "/blogs/how-to-do-saas-seo-keyword-research/"),
    (2686, "how-to-rank-on-chatgpt-in-2026-strategies-and-tips", "/blogs/how-to-rank-on-chatgpt/"),
    (2555, "how-to-run-google-ads-for-saas", "/blogs/how-to-run-google-ads-for-saas/"),
    (2679, "how-to-run-linkedin-retargeting-ads", "/blogs/how-to-run-linkedin-retargeting-ads/"),
    (2646, "how-to-write-saas-comparison-pages-for-seo", "/blogs/how-to-write-saas-comparison-pages-for-seo/"),
    (2682, "how-to-write-google-ads-copy-for-saas-in-2026", "/blogs/how-to-write-saas-google-ads-copy/"),
    (2630, "how-to-write-saas-seo-content-with-ai-that-actually-ranks", "/blogs/how-to-write-saas-seo-content-with-ai/"),
    (2622, "blogs-optimize-saas-landing-pages-for-seo", "/blogs/optimize-saas-landing-pages-for-seo/"),
    (2458, "saas-content-marketing-guide", "/blogs/saas-content-marketing-guide/"),
    (2785, "the-8-common-saas-google-ads-mistakes-to-avoid-in-2026", "/blogs/saas-google-ads-mistakes-to-avoid/"),
    (2772, "saas-linkedin-ads-mistakes-to-avoid", "/blogs/saas-linkedin-ads-mistakes-to-avoid/"),
    (2504, "saas-ppc-checklist", "/blogs/saas-ppc-checklist/"),
    (2431, "saas-ppc", "/blogs/saas-ppc/"),
    (2578, "saas-seo-checklist", "/blogs/saas-seo-checklist/"),
]


def load_creds():
    if not CREDS.exists():
        sys.exit(f"ERROR: credentials file not found at {CREDS}")
    user = pw = None
    for line in CREDS.read_text().splitlines():
        if line.startswith("username:"):
            user = line.split(":", 1)[1].strip()
        elif line.startswith("password:"):
            pw = line.split(":", 1)[1].strip()
    if not user or not pw:
        sys.exit("ERROR: credentials file must have 'username:' and 'password:' lines")
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return f"Basic {token}"


def get_post(post_id, auth):
    req = urllib.request.Request(
        f"{BASE}/wp-json/wp/v2/posts/{post_id}?_fields=id,slug,link,template,status",
        headers={"Authorization": auth, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def update_template(post_id, template, auth):
    body = json.dumps({"template": template}).encode()
    req = urllib.request.Request(
        f"{BASE}/wp-json/wp/v2/posts/{post_id}",
        data=body,
        method="POST",
        headers={
            "Authorization": auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="Apply changes (default is dry run)")
    ap.add_argument("--only", type=int, default=None, help="Operate on a single wp_id")
    ap.add_argument("--target", default=NEW_TEMPLATE, help=f"Target template (default {NEW_TEMPLATE})")
    args = ap.parse_args()

    auth = load_creds()
    posts = [p for p in POSTS if (args.only is None or p[0] == args.only)]
    if not posts:
        sys.exit(f"No matching posts for --only {args.only}")

    print(f"Mode:    {'EXECUTE' if args.execute else 'DRY RUN'}")
    print(f"Target:  {args.target}")
    print(f"Posts:   {len(posts)}\n")

    ok = fail = skipped = 0
    for wp_id, slug, url in posts:
        try:
            before = get_post(wp_id, auth)
        except urllib.error.HTTPError as e:
            print(f"  ✗ {wp_id:<5}  GET failed: HTTP {e.code} — {url}")
            fail += 1
            continue
        current = before.get("template", "")
        if current == args.target:
            print(f"  ⊙ {wp_id:<5}  already on {args.target}, skip — {url}")
            skipped += 1
            continue

        if not args.execute:
            print(f"  ◌ {wp_id:<5}  would change '{current or '(default)'}' → '{args.target}' — {url}")
            ok += 1
            continue

        try:
            after = update_template(wp_id, args.target, auth)
            new = after.get("template", "")
            mark = "✓" if new == args.target else "?"
            print(f"  {mark} {wp_id:<5}  '{current or '(default)'}' → '{new}' — {url}")
            if new == args.target:
                ok += 1
            else:
                fail += 1
            time.sleep(0.3)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")[:300]
            print(f"  ✗ {wp_id:<5}  POST failed HTTP {e.code}: {body} — {url}")
            fail += 1

    print(f"\n=== {'EXECUTE' if args.execute else 'DRY RUN'} done ===")
    print(f"  OK:      {ok}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {fail}")


if __name__ == "__main__":
    main()
