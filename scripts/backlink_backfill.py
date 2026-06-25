"""
Brand-mentions / backlink outreach backfill — Phase 1 (one-time batch).

Reads December 2025 Gmail (inbox + sent), keeps threads that look like
backlink / brand-mention / link-outreach conversations, then writes one
row per thread to a fresh Google Sheet.

Two modes (classification is done by Claude in the chat session, not by
an API call — so no Anthropic key is needed):

  python3 scripts/backlink_backfill.py fetch
    Gmail search (Dec 2025, inbox+sent) -> group by thread
    -> cheap keyword pre-filter
    -> dump survivors to credentials/backlink_candidates.json

  python3 scripts/backlink_backfill.py write
    Read credentials/backlink_classified.json (produced by Claude)
    -> create Google Sheet, write one row per backlink thread

Reuses the existing OAuth desktop client at credentials/Google Creds.json.
New scopes (gmail.readonly + spreadsheets) trigger a ONE-TIME re-consent,
stored separately in credentials/token_backlinks.json so the GSC token
(credentials/token.json) is untouched.
"""

import base64
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
CREDS_FILE = ROOT / "credentials" / "Google Creds.json"
TOKEN_FILE = ROOT / "credentials" / "token_backlinks.json"
CANDIDATES_FILE = ROOT / "credentials" / "backlink_candidates.json"
CLASSIFIED_FILE = ROOT / "credentials" / "backlink_classified.json"
CACHE_FILE = ROOT / "credentials" / "_all_threads_cache.json"
ENV_FILE = ROOT / "credentials" / ".env"

# --- live watcher (Phase 2) state ---
SEEN_FILE = ROOT / "credentials" / "_seen_threads.json"      # thread ids already processed
WATCH_NEW_FILE = ROOT / "credentials" / "_watch_new.json"    # new candidates for Claude to classify
SLACK_QUEUE_FILE = ROOT / "credentials" / "_slack_queue.json"  # messages Claude wants posted
META_FILE = ROOT / "credentials" / "_watch_meta.json"        # {last_run_epoch} for gap-aware catch-up

# Incoming requests only (someone asking us). Includes Spam because legit
# cold outreach is often mis-flagged; the keyword + noise filters cut the junk.
WATCH_INBOX = "(in:inbox OR in:spam)"
# Lookback on the very first run (no recorded last-run yet).
DEFAULT_LOOKBACK = "newer_than:7d"
GAP_BUFFER = 3600          # re-scan 1h before last run so nothing on the boundary slips
GAP_MAX = 60 * 86400       # cap the catch-up window at 60 days, even after a long closure


def _load_meta():
    return json.loads(META_FILE.read_text()) if META_FILE.exists() else {}


def _save_meta(d):
    META_FILE.write_text(json.dumps(d))


def build_watch_query():
    """Gmail query covering everything since the last successful run.

    No last_run (first run) -> 7-day window. Otherwise query from last_run minus
    a 1h buffer, so however long the Mac was closed, the next run catches up the
    whole gap (capped at 60 days). Returns (query, gap_seconds_or_None).
    """
    last = _load_meta().get("last_run")
    if not last:
        return f"{DEFAULT_LOOKBACK} {WATCH_INBOX}", None
    now = int(time.time())
    gap = now - int(last)
    after = now - min(gap + GAP_BUFFER, GAP_MAX)
    return f"after:{after} {WATCH_INBOX}", gap

# Automated/bulk senders that are never a real brand-mention request — dropped
# before Claude classifies, to keep the hourly run clean.
NOISE_SENDERS = (
    "no-reply@slack.com", "notification@slack.com", "slack.com",
    "substack.com", "neilpatel.com", "builtin.com", "quora.com",
    "fathom.video", "gemini-notes@google.com", "otter.ai", "ambitionbox.com",
    "glassdoor.com", "canva.com", "engage.canva", "elementor.com",
    "clutch.co", "ahrefs.com", "github.com", "zamzar.com", "plumhq.com",
    "sc-noreply@google.com", "g2.com", "semrush.com", "mailchimp", "mailchi.mp",
    "searchenginejournal.com", "rankmath.com", "indeed.com", "notion.so",
    "calendly.com", "zoom.us", "hubspot", "stripe.com", "paypal", "medium.com",
    "producthunt", "googlealerts-noreply@google.com", "drive-shares-dm-noreply",
    "ads-account-noreply@google.com", "gartner.com", "conductor.com",
    "freepik.com", "microsoftadvertising.com", "crunchbase.com", "netlify.com",
    "redditmail.com", "minuteslink.com", "designrush.co", "openai.com",
    "growresolve.com", "conductor.com", "gartner.com",
)


def _is_noise_sender(addr):
    a = addr.lower()
    return any(n in a for n in NOISE_SENDERS)


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Dec 2025 -> current date. Gmail `after:` is inclusive of the following day onward.
GMAIL_QUERY = "after:2025/11/30 before:2026/06/20 (in:inbox OR in:sent)"

# Cheap pre-filter. A thread survives if ANY message text matches.
# Deliberately HIGH-RECALL (favours false positives) — Claude classifies the
# survivors afterwards, so missing a real thread is worse than over-including.
KEYWORD_RE = re.compile(
    r"("
    # --- links ---
    r"\bbacklink|\bback link|link\s*insertion|link\s*exchange|link\s*building|"
    r"link\s*swap|link\s*placement|editorial\s*link|do\s*follow|dofollow|"
    r"add\s*(?:a\s*)?link|insert\s*(?:a\s*)?link|include\s*(?:a\s*)?link|"
    r"link\s*to|linking\s*to|link\s*back|anchor\s*text|\bhyperlink|"
    # --- mentions ---
    r"brand\s*mention|unlinked\s*mention|mention\s*(?:you|your|us|our|piperocket)|"
    r"feature\s*(?:you|your|us|our|piperocket)|get\s*featured|shout\s*out|shoutout|"
    # --- guest posts / contributions ---
    r"guest\s*post|guest\s*blog|guest\s*contribut|guest\s*article|"
    r"write\s*for\s*us|contribut(?:e|or|ion)|publish\s*(?:on|your|an article)|"
    r"sponsored\s*post|sponsored\s*content|paid\s*post|paid\s*placement|placement\b|"
    # --- listicles / roundups / swaps ---
    r"round\s*-?up|listicle|list\s*exchange|\bswap\b|mutual\s*(?:mention|feature)|"
    r"add\s*(?:you|your|us|our)\b|include\s*(?:you|your|us|our)\b|reciprocal|"
    r"add\s*(?:you|us)\s*to\s*(?:your|our|the)\s*list|featured?\s*in\s*(?:your|our|the)\s*list|"
    # --- partnership / collab / outreach ---
    r"collaborat|collaboration|\bcollab\b|work\s*together|"
    r"partnership|partner\s*with|co-?marketing|cross\s*-?promot|outreach|"
    # --- SEO authority signals ---
    r"domain\s*authority|domain\s*rating|\bDA\s*\d|\bDR\s*\d|high\s*-?authority|"
    r"digital\s*pr\b|\bHARO\b|\bqwoted\b"
    r")",
    re.IGNORECASE,
)

SHEET_HEADER = [
    "Thread date", "From / counterpart", "Direction",
    "Our article (hosts them)", "→ links to their page",
    "Their article (hosts us)", "→ links to our page",
    "Anchor / type", "Ask summary", "Status",
    "Last message snippet", "Gmail link",
]


# ----------------------------------------------------------------------------- auth

def get_creds():
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
    return creds


# ----------------------------------------------------------------------------- gmail

def header(msg, name):
    for h in msg.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def decode_part(data):
    if not data:
        return ""
    return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", "replace")


def extract_body(payload):
    """Walk MIME parts; prefer text/plain, fall back to stripped text/html."""
    plain, html = [], []

    def walk(part):
        mime = part.get("mimeType", "")
        body = part.get("body", {})
        if mime == "text/plain":
            plain.append(decode_part(body.get("data", "")))
        elif mime == "text/html":
            html.append(decode_part(body.get("data", "")))
        for sub in part.get("parts", []):
            walk(sub)

    walk(payload)
    if plain:
        text = "\n".join(plain)
    elif html:
        text = re.sub(r"<[^>]+>", " ", "\n".join(html))
        text = unescape(text)
    else:
        text = ""
    # collapse quoted-reply noise lightly + whitespace
    text = re.sub(r"\n\s*>.*", "", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def fetch_threads(svc, query=GMAIL_QUERY, cache=True):
    """Return list of threads, each a dict with id + ordered messages."""
    threads = []
    page_token = None
    thread_ids = []
    while True:
        resp = svc.users().messages().list(
            userId="me", q=query, maxResults=500, pageToken=page_token
        ).execute()
        for m in resp.get("messages", []):
            thread_ids.append(m["threadId"])
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    seen = set()
    unique = [t for t in thread_ids if not (t in seen or seen.add(t))]
    print(f"  {len(thread_ids)} matching messages across {len(unique)} threads")

    for tid in unique:
        t = svc.users().threads().get(userId="me", id=tid, format="full").execute()
        msgs = []
        for m in t.get("messages", []):
            msgs.append({
                "id": m.get("id"),
                "from": header(m, "From"),
                "to": header(m, "To"),
                "subject": header(m, "Subject"),
                "date": header(m, "Date"),
                "labels": m.get("labelIds", []),
                "body": extract_body(m.get("payload", {})),
            })
        threads.append({"id": tid, "messages": msgs})
    if cache:
        # Cache the full download so we can re-filter (e.g. new keywords) for free.
        CACHE_FILE.write_text(json.dumps(threads, ensure_ascii=False))
        print(f"  cached {len(threads)} full threads -> {CACHE_FILE.name}")
    return threads


def thread_text(thread):
    return "\n".join(
        f"{m['subject']} {m['from']} {m['body']}" for m in thread["messages"]
    )


# ----------------------------------------------------------------------------- sheet

def write_sheet(creds, rows):
    sheets = build("sheets", "v4", credentials=creds, cache_discovery=False)
    ss = sheets.spreadsheets().create(body={
        "properties": {"title": "Backlink & Brand-Mention Tracker — Dec 2025"},
        "sheets": [{"properties": {"title": "Threads"}}],
    }).execute()
    sid = ss["spreadsheetId"]
    url = ss["spreadsheetUrl"]
    values = [SHEET_HEADER] + rows
    sheets.spreadsheets().values().update(
        spreadsheetId=sid, range="Threads!A1",
        valueInputOption="RAW", body={"values": values},
    ).execute()
    # bold header
    sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": [{
        "repeatCell": {
            "range": {"sheetId": ss["sheets"][0]["properties"]["sheetId"],
                      "startRowIndex": 0, "endRowIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
            "fields": "userEnteredFormat.textFormat.bold",
        }}, {"updateSheetProperties": {
            "properties": {"sheetId": ss["sheets"][0]["properties"]["sheetId"],
                           "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount"}}]}).execute()
    return url


# ----------------------------------------------------------------------------- main

def run_fetch():
    creds = get_creds()
    gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
    print("Fetching December threads...")
    threads = fetch_threads(gmail)
    candidates = [t for t in threads if KEYWORD_RE.search(thread_text(t))]
    print(f"Keyword pre-filter: {len(candidates)}/{len(threads)} threads survive")
    CANDIDATES_FILE.write_text(json.dumps(candidates, indent=2, ensure_ascii=False))
    print(f"\nWrote {CANDIDATES_FILE}  ({len(candidates)} candidate threads)")
    print("Next: Claude classifies these, then run `write`.")


def run_refilter():
    """Re-apply the keyword filter to the cached threads (no Gmail calls).

    Use after broadening KEYWORD_RE. Writes the new candidate set and reports
    how many threads are NEW vs the previous candidates file.
    """
    if not CACHE_FILE.exists():
        sys.exit(f"ERROR: {CACHE_FILE} not found. Run `fetch` once to build the cache.")
    threads = json.loads(CACHE_FILE.read_text())
    prev_ids = set()
    if CANDIDATES_FILE.exists():
        prev_ids = {t["id"] for t in json.loads(CANDIDATES_FILE.read_text())}
    candidates = [t for t in threads if KEYWORD_RE.search(thread_text(t))]
    new_ids = [t["id"] for t in candidates if t["id"] not in prev_ids]
    CANDIDATES_FILE.write_text(json.dumps(candidates, indent=2, ensure_ascii=False))
    print(f"Cache: {len(threads)} threads")
    print(f"Keyword survivors: {len(candidates)} (was {len(prev_ids)})")
    print(f"NEW threads not in previous candidates: {len(new_ids)}")
    if new_ids:
        (ROOT / "credentials" / "_new_ids.json").write_text(json.dumps(new_ids))
        print("  wrote credentials/_new_ids.json")


def _load_seen():
    """Return {thread_id: message_count_seen}. Migrates the old list format."""
    if not SEEN_FILE.exists():
        return {}
    data = json.loads(SEEN_FILE.read_text())
    if isinstance(data, list):  # legacy: list of thread ids -> count unknown (0)
        return {tid: 0 for tid in data}
    return data


def _save_seen(d):
    SEEN_FILE.write_text(json.dumps(d, sort_keys=True))


def run_seed_seen():
    """Record every cached thread at its current message count.

    Run ONCE before going live so the watcher doesn't re-alert on the mail we
    already backfilled — but a NEW reply to any of those threads (count goes up)
    will still surface. Needs the cache from a prior `fetch`.
    """
    if not CACHE_FILE.exists():
        sys.exit(f"ERROR: {CACHE_FILE} not found. Run `fetch` first.")
    seen = _load_seen()
    cached = json.loads(CACHE_FILE.read_text())
    for t in cached:
        seen[t["id"]] = max(seen.get(t["id"], 0), len(t["messages"]))
    _save_seen(seen)
    print(f"Seeded seen-state from {len(cached)} cached threads (total tracked: {len(seen)}).")


def run_watch():
    """Incremental check for new inbound requests AND new replies (hourly).

    A thread is 'fresh' if we've never seen it, OR it now has more messages than
    when last processed (i.e. a new reply arrived). Keyword + noise filters apply.
    Writes fresh threads to _watch_new.json (tagged new vs reply) for Claude.
    Does NOT mark seen — `mark-seen` does that after Slack posting.
    """
    creds = get_creds()
    gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
    query, gap = build_watch_query()
    if gap is not None and gap > 6 * 3600:
        days = gap / 86400
        print(f"⏳ Gap since last run: {days:.1f} days — catching up the whole window.")
        # leave a breadcrumb so Claude can mention the catch-up in Slack if it wants
        (ROOT / "credentials" / "_watch_gap.txt").write_text(f"{days:.1f}")
    else:
        (ROOT / "credentials" / "_watch_gap.txt").write_text("")
    print(f"Watch query: {query}")
    threads = fetch_threads(gmail, query=query, cache=False)
    seen = _load_seen()
    fresh = []
    for t in threads:
        prev = seen.get(t["id"])  # None if never seen
        if prev is not None and len(t["messages"]) <= prev:
            continue  # already processed, no new reply
        # If WE sent the latest message, the ball is in their court — nothing to alert.
        if "piperocket.digital" in t["messages"][-1]["from"].lower():
            continue
        if all(_is_noise_sender(m["from"]) for m in t["messages"]):
            continue
        if KEYWORD_RE.search(thread_text(t)):
            t["_kind"] = "new thread" if prev is None else "new reply"
            t["_new_messages"] = len(t["messages"]) - (prev or 0)
            fresh.append(t)
    WATCH_NEW_FILE.write_text(json.dumps(fresh, indent=2, ensure_ascii=False))
    n_new = sum(1 for t in fresh if t["_kind"] == "new thread")
    n_reply = len(fresh) - n_new
    print(f"Fresh: {len(fresh)} ({n_new} new threads, {n_reply} new replies) "
          f"of {len(threads)} recent inbox threads")
    if not fresh:
        print("Nothing new. Done.")


def run_mark_seen():
    """Record current message count for every thread in _watch_new.json."""
    if not WATCH_NEW_FILE.exists():
        print("No _watch_new.json; nothing to mark.")
        return
    seen = _load_seen()
    fresh = json.loads(WATCH_NEW_FILE.read_text())
    for t in fresh:
        seen[t["id"]] = len(t["messages"])
    _save_seen(seen)
    # Stamp last successful run so the next watch covers exactly the gap since now.
    meta = _load_meta()
    meta["last_run"] = int(time.time())
    meta["last_run_iso"] = datetime.now(timezone.utc).isoformat()
    _save_meta(meta)
    print(f"Marked {len(fresh)} threads at current message count (total tracked: {len(seen)}).")


def run_notify():
    """Post each message in _slack_queue.json to the Slack incoming webhook.

    _slack_queue.json is a JSON list of strings (Slack mrkdwn). Claude composes
    it during the watch run.
    """
    load_env()
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        sys.exit("ERROR: SLACK_WEBHOOK_URL not set in credentials/.env")
    if not SLACK_QUEUE_FILE.exists():
        print("No _slack_queue.json; nothing to post.")
        return
    msgs = json.loads(SLACK_QUEUE_FILE.read_text())
    for m in msgs:
        text = m if isinstance(m, str) else m.get("text", "")
        body = json.dumps({"text": text}).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            resp.read()
    print(f"Posted {len(msgs)} Slack message(s).")
    SLACK_QUEUE_FILE.write_text("[]")  # clear queue after posting


def run_write():
    """Read classified threads and push to a new Google Sheet.

    Expected JSON: a list of objects, each with keys:
      thread_date, counterpart, direction,
      our_article (our page hosting their mention),
      their_link (their page the link points to),
      their_article (their page hosting our mention),
      our_link (our page the link points to),
      anchor_text, ask_summary, status, last_message, gmail_link
    Only rows the classifier marked as backlink-related should be present.
    """
    if not CLASSIFIED_FILE.exists():
        sys.exit(f"ERROR: {CLASSIFIED_FILE} not found. Claude must produce it first.")
    data = json.loads(CLASSIFIED_FILE.read_text())
    rows = [[
        r.get("thread_date", ""), r.get("counterpart", ""), r.get("direction", ""),
        r.get("our_article", ""), r.get("their_link", ""),
        r.get("their_article", ""), r.get("our_link", ""),
        r.get("anchor_text", ""), r.get("ask_summary", ""), r.get("status", ""),
        r.get("last_message", ""), r.get("gmail_link", ""),
    ] for r in data]
    if not rows:
        print("No classified rows to write. Done.")
        return
    creds = get_creds()
    url = write_sheet(creds, rows)
    print(f"\n✅ Sheet created with {len(rows)} rows:\n{url}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "fetch":
        run_fetch()
    elif mode == "refilter":
        run_refilter()
    elif mode == "write":
        run_write()
    elif mode == "seed-seen":
        run_seed_seen()
    elif mode == "watch":
        run_watch()
    elif mode == "mark-seen":
        run_mark_seen()
    elif mode == "notify":
        run_notify()
    else:
        sys.exit("Usage: python3 scripts/backlink_backfill.py "
                 "[fetch|refilter|write|seed-seen|watch|mark-seen|notify]")


if __name__ == "__main__":
    main()
