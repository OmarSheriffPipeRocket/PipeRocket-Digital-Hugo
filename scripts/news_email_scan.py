#!/usr/bin/env python3
"""
news_email_scan.py — pull the past N days of SEO/PPC/AI-search newsletters from Gmail.

Reads omar@piperocket.digital via the gmail.readonly scope on
credentials/token_backlinks.json and prints each newsletter's date, sender,
subject, a cleaned text body, and the outbound links it contains.

Consumed by the weekly-news-scan scheduled task as the EMAIL half of the scan
(the WEB half hits the four publishers' sites directly). Output is plain text
meant to be read by a Claude session that then applies the news_bank
significance gate.

Usage:
    python3 scripts/news_email_scan.py [--days 7] [--max 30]
"""
import argparse
import base64
import html
import os
import re
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.path.join(ROOT, "credentials", "token_backlinks.json")

# The four sources Omar is subscribed to. Match on sender domain/handle.
SOURCES = [
    "searchengineland.com",
    "thirddoormedia.com",        # SEL parent (Danny Goodwin)
    "searchenginejournal.com",
    "seroundtable.com",
    "ahrefs.com",
]

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t]*\n[ \t]*")
MULTINL_RE = re.compile(r"\n{3,}")
LINK_RE = re.compile(r'https?://[^\s"\'<>)\]]+')

# Newsletter chrome we don't need the model to read.
JUNK_LINK = re.compile(
    r"(unsubscribe|list-manage|/preferences|utm_|mailchi|sendgrid|"
    r"beehiiv|substackcdn|pixel|/open|/click\?|facebook\.com|twitter\.com|"
    r"linkedin\.com/shareArticle|instagram\.com)",
    re.I,
)


def _b64(data):
    return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", "replace")


def _walk_parts(payload):
    """Yield (mimeType, decoded_text) for every text part."""
    stack = [payload]
    while stack:
        p = stack.pop()
        mt = p.get("mimeType", "")
        body = p.get("body", {})
        data = body.get("data")
        if data and mt in ("text/plain", "text/html"):
            yield mt, _b64(data)
        for sub in p.get("parts", []) or []:
            stack.append(sub)


def _clean(text, is_html):
    if is_html:
        text = re.sub(r"(?is)<style.*?</style>", " ", text)
        text = re.sub(r"(?is)<script.*?</script>", " ", text)
        text = re.sub(r"(?i)<br\s*/?>", "\n", text)
        text = re.sub(r"(?i)</p>", "\n\n", text)
        text = TAG_RE.sub(" ", text)
        text = html.unescape(text)
    text = WS_RE.sub("\n", text)
    text = MULTINL_RE.sub("\n\n", text)
    return text.strip()


def _body_and_links(payload):
    plain = htmlbody = None
    for mt, txt in _walk_parts(payload):
        if mt == "text/plain" and plain is None:
            plain = txt
        elif mt == "text/html" and htmlbody is None:
            htmlbody = txt
    raw_for_links = htmlbody or plain or ""
    links = []
    seen = set()
    for m in LINK_RE.findall(raw_for_links):
        m = m.rstrip(".,);")
        if JUNK_LINK.search(m) or m in seen:
            continue
        seen.add(m)
        links.append(m)
    body = _clean(plain, False) if plain else _clean(htmlbody or "", True)
    return body, links


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--max", type=int, default=30)
    ap.add_argument("--body-chars", type=int, default=4000)
    ap.add_argument("--max-links", type=int, default=25)
    args = ap.parse_args()

    if not os.path.exists(TOKEN):
        sys.exit(f"Missing Gmail token: {TOKEN}")

    creds = Credentials.from_authorized_user_file(TOKEN)
    svc = build("gmail", "v1", credentials=creds)

    from_q = " OR ".join(f"from:{d}" for d in SOURCES)
    q = f"newer_than:{args.days}d ({from_q})"
    resp = (
        svc.users()
        .messages()
        .list(userId="me", q=q, maxResults=args.max)
        .execute()
    )
    msgs = resp.get("messages", [])
    print(f"=== EMAIL SCAN: {len(msgs)} newsletters in last {args.days}d ===\n")
    if not msgs:
        print("(no matching newsletters in window)")
        return

    for i, ref in enumerate(msgs, 1):
        m = (
            svc.users()
            .messages()
            .get(userId="me", id=ref["id"], format="full")
            .execute()
        )
        hdr = {h["name"].lower(): h["value"] for h in m["payload"]["headers"]}
        body, links = _body_and_links(m["payload"])
        print(f"----- [{i}] -----")
        print(f"Date:    {hdr.get('date','?')}")
        print(f"From:    {hdr.get('from','?')}")
        print(f"Subject: {hdr.get('subject','(no subject)')}")
        print(f"\nBODY:\n{body[:args.body_chars]}")
        if links:
            print(f"\nLINKS ({min(len(links), args.max_links)} of {len(links)}):")
            for url in links[: args.max_links]:
                print(f"  {url}")
        print()


if __name__ == "__main__":
    main()
