"""
Post-WP-sync cleanup:

  Step 1 — Rewrite absolute piperocket.digital URLs to relative paths inside
  every .md file under content/ (e.g. https://piperocket.digital/blogs/x/ -> /blogs/x/).

  Step 2 — Restore /glossary/ links that were lost when the WP sync overwrote
  existing Hugo files. Reads tmp/wp-link-audit.json (produced by sync_wp_posts.py
  --apply) and re-wraps the FIRST occurrence of each lost link's text in the
  current body, skipping cases where the text already lives inside a link or
  inside code/headings.

Run from repo root:
  python3 scripts/restore_internal_links.py            # dry-run summary
  python3 scripts/restore_internal_links.py --apply    # actually write changes
"""

import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONTENT_DIR = os.path.join(REPO_ROOT, "content")
AUDIT_PATHS = [
    os.path.join(REPO_ROOT, "tmp", "wp-link-audit.json"),
    os.path.join(REPO_ROOT, "tmp", "wp-link-audit-list.json"),
    os.path.join(REPO_ROOT, "tmp", "wp-link-audit-cpt.json"),
]

ABS_URL_RE = re.compile(r'(https?://(?:www\.)?piperocket\.digital)(/[^)"\s]*)?')


def split_frontmatter(text):
    """Return (frontmatter_with_fences, body). If no frontmatter, frontmatter = ''."""
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end < 0:
        return "", text
    return text[: end + 5], text[end + 5 :]


def rewrite_absolute_urls(text):
    """Replace https://piperocket.digital/... with the relative path. Body only."""
    fm, body = split_frontmatter(text)
    count = len(ABS_URL_RE.findall(body))
    def repl(m):
        path = m.group(2) or "/"
        return path
    new_body = ABS_URL_RE.sub(repl, body)
    return fm + new_body, count


def already_linked(text, idx, length):
    """Heuristic: is the substring at [idx:idx+length] already inside a markdown link or code span?"""
    head = text[max(0, idx - 80):idx]
    if head.rfind("[") > head.rfind("]"):
        return True
    if head.rfind("](") > head.rfind(")"):
        return True
    # In a code span if odd number of backticks since start of line
    line_start = text.rfind("\n", 0, idx) + 1
    if text.count("`", line_start, idx) % 2 == 1:
        return True
    # In a fenced code block
    fences_before = text.count("\n```", 0, idx)
    if fences_before % 2 == 1:
        return True
    return False


def restore_link(text, link_text, link_url):
    """Wrap the first plain occurrence of link_text as a markdown link to link_url.
       Returns (new_text, did_replace, reason_if_skipped)."""
    if link_url.startswith("/images/"):
        return text, False, "skipped: image asset, not a content link"
    # Build a word-boundary, case-insensitive matcher
    pattern = re.compile(r'\b' + re.escape(link_text) + r'\b', re.I)
    for m in pattern.finditer(text):
        if already_linked(text, m.start(), m.end() - m.start()):
            continue
        # Replace only this occurrence preserving original casing
        original = m.group(0)
        return text[:m.start()] + f"[{original}]({link_url})" + text[m.end():], True, ""
    return text, False, f"no unlinked occurrence of '{link_text}'"


def iter_content_md():
    for root, _, files in os.walk(CONTENT_DIR):
        for fn in files:
            if fn.endswith(".md"):
                yield os.path.join(root, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Actually write files (default: dry-run)")
    args = ap.parse_args()

    # ---- Step 1: absolute -> relative across all content/ ----
    step1_total = 0
    step1_files = 0
    for fp in iter_content_md():
        with open(fp) as f:
            text = f.read()
        new_text, count = rewrite_absolute_urls(text)
        if count:
            step1_files += 1
            step1_total += count
            if args.apply and new_text != text:
                with open(fp, "w") as f:
                    f.write(new_text)
    print(f"Step 1 — absolute→relative URL rewrite")
    print(f"  Files touched: {step1_files}")
    print(f"  Links rewritten: {step1_total}")
    print()

    # ---- Step 2: restore lost glossary links from audit ----
    audit = []
    for p in AUDIT_PATHS:
        if os.path.exists(p):
            audit.extend(json.load(open(p)))
    if not audit:
        print("Step 2 skipped — no audit files found.")
        return

    restored_per_file = []
    skipped_log = []
    total_restored = 0
    total_lost = 0
    for entry in audit:
        fp = os.path.join(REPO_ROOT, entry["file"])
        if not os.path.exists(fp):
            continue
        with open(fp) as f:
            full = f.read()
        fm, body = split_frontmatter(full)
        before_body = body
        restored = 0
        for link_text, link_url in entry["lost"]:
            total_lost += 1
            body, ok, reason = restore_link(body, link_text, link_url)
            if ok:
                restored += 1
                total_restored += 1
            else:
                skipped_log.append((entry["file"], link_text, link_url, reason))
        restored_per_file.append((entry["file"], restored, len(entry["lost"])))
        if args.apply and body != before_body:
            with open(fp, "w") as f:
                f.write(fm + body)

    print(f"Step 2 — restore lost internal links")
    print(f"  Total lost links: {total_lost}")
    print(f"  Auto-restored:    {total_restored}")
    print(f"  Skipped:          {total_lost - total_restored}")
    print()
    print(f"{'File':<70} {'restored':>8} {'of':>3} {'lost':>5}")
    print("-" * 90)
    for fp, r, l in sorted(restored_per_file, key=lambda x: -(x[1])):
        print(f"  {fp:<68} {r:>8}     {l:>5}")
    if skipped_log:
        log_path = os.path.join(REPO_ROOT, "tmp", "link-restore-skipped.json")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w") as f:
            json.dump([{"file": f1, "text": t, "url": u, "reason": r} for (f1, t, u, r) in skipped_log], f, indent=2)
        print(f"\nSkipped entries logged to {os.path.relpath(log_path, REPO_ROOT)}")
    if not args.apply:
        print("\nDry-run only. Re-run with --apply to write files.")


if __name__ == "__main__":
    main()
