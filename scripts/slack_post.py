#!/usr/bin/env python3
"""
slack_post.py — post a message to the PipeRocket weekly-news-scan Slack channel.

The incoming-webhook URL is kept out of the repo: it's read from the
SLACK_WEBHOOK_URL env var, or from the gitignored file credentials/slack_webhook.txt.
The message text is read from --text or, if omitted, from stdin.

Usage:
    python3 scripts/slack_post.py --text ":newspaper: weekly scan ..."
    echo ":newspaper: ..." | python3 scripts/slack_post.py
"""
import argparse
import json
import os
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEBHOOK_FILE = ROOT / "credentials" / "slack_webhook.txt"


def load_webhook():
    url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if url:
        return url
    if WEBHOOK_FILE.exists():
        return WEBHOOK_FILE.read_text().strip()
    sys.exit(
        "No Slack webhook configured. Set SLACK_WEBHOOK_URL or create "
        f"{WEBHOOK_FILE} (gitignored) with the incoming-webhook URL."
    )


def main():
    WEBHOOK = load_webhook()
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", help="Slack mrkdwn message. If omitted, read from stdin.")
    args = ap.parse_args()

    text = args.text if args.text is not None else sys.stdin.read()
    text = text.strip()
    if not text:
        sys.exit("No message text provided (pass --text or pipe via stdin).")

    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", "replace")
        print(f"HTTP {resp.status}: {body}")
        sys.exit(0 if resp.status == 200 and body.strip() == "ok" else 1)


if __name__ == "__main__":
    main()
