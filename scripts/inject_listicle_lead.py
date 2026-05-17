#!/usr/bin/env python3
"""Insert a one-line "Comparing the top N best X agencies of 2026 includes
1. A, 2. B, ..., and N. Z." sentence as the FIRST paragraph after the
front matter of each listicle.

This is the lead sentence used on best-affordable-b2b-ppc-agencies.md —
great for AEO/GEO (AI engines pull lists like this into answer cards)
and for skim-reading.

Algorithm per listicle:
  1. Read the title from front matter.
  2. Parse every `### N. <Brand>` H3, in order, deriving the brand name
     after stripping bold markers, markdown link wrappers, and any
     "– Best for: …" suffix.
  3. Build the noun phrase from the title — strip leading filler verbs
     ("I Ranked", "My Picks for", "We Ranked", "Ranking", "The"), the
     leading agency count ("11", "Top 10"), and lowercase the rest. If
     the phrase doesn't already mention a year, append "of 2026".
  4. Skip if the file already contains a "Comparing the top" sentence
     in its first 800 bytes after the front matter.
  5. Otherwise insert the new sentence + a blank line as the first body
     paragraph.

Usage:
  python3 scripts/inject_listicle_lead.py --dry-run
  python3 scripts/inject_listicle_lead.py
  python3 scripts/inject_listicle_lead.py --only best-saas-seo-agencies.md
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST_DIR = ROOT / "content" / "list"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

# Matches headings like:
#   ### 1. Agency
#   ### **1. Agency**
#   ### **1. [Agency](url) – Best for: …**
#   ### 1. [Agency](url)
H3_RE = re.compile(
    r"^###\s+\**\s*(?P<rank>\d+)\.\s*\**\s*(?P<rest>.+?)\s*$",
    re.MULTILINE,
)

LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def clean_brand_name(raw: str) -> str:
    s = raw.strip().strip("*").strip()
    # If wrapped in a markdown link, take the link text
    m = LINK_RE.match(s)
    if m:
        s = m.group(1).strip()
        # capture any trailing text after the link
        tail = s
    # Drop suffix after em-dash, en-dash, hyphen-separator, or colon
    s = re.split(r"\s+[–—‐\-:]\s+", s, maxsplit=1)[0]
    # Also drop trailing "– Best for: ..." that survived split
    s = re.sub(r"\s*[–—]\s*Best for.*$", "", s, flags=re.IGNORECASE)
    # Strip any inline trailing bold markers / brackets / parens left over
    s = s.strip(" *_[]()")
    return s


# False-positive H3s that look like rankings but are actually FAQ questions
# (the FAQ section in some listicles uses "### 1. What is …").
def looks_like_faq_question(raw_after_rank: str) -> bool:
    txt = raw_after_rank.lower()
    return txt.startswith(("what ", "what's", "how ", "should ", "is ",
                           "why ", "do ", "does ", "can ", "where ",
                           "ask ", "verify ", "treat ", "check "))


def parse_agencies(md_text: str) -> list[str]:
    out = []
    seen_ranks = set()
    for m in H3_RE.finditer(md_text):
        rank = int(m.group("rank"))
        raw = m.group("rest")
        # An agency H3 starts a numbered list at 1, 2, 3... in order. The
        # FAQ section may restart numbering — detect by ranks repeating
        # (e.g. agency ranks 1..11 then FAQ ranks 1..8) AND by FAQ-shaped
        # text.
        if rank in seen_ranks:
            break
        if looks_like_faq_question(raw):
            break
        name = clean_brand_name(raw)
        if name:
            out.append(name)
            seen_ranks.add(rank)
    return out


def noun_phrase_from_title(title: str, n: int) -> str:
    """Build the comparison-sentence's noun phrase from the listicle title.
    Examples:
      "Best Affordable B2B PPC Agencies"
          → "best affordable B2B PPC agencies of 2026"
      "11 Best Martech Marketing Agencies in 2026"
          → "best Martech marketing agencies in 2026"
      "I Ranked The 11 Best SaaS SEO Agencies in 2026"
          → "best SaaS SEO agencies in 2026"
      "The Top 10 B2B PPC Agencies You Need to Consider in 2026"
          → "B2B PPC agencies in 2026"
      "The Best B2B Advertising Agencies (2026 Rankings)"
          → "best B2B advertising agencies of 2026"
    """
    t = title.strip()
    # Strip surrounding quotes
    t = t.strip('"').strip("'")
    # Drop common filler at the start. Iterate so chained prefixes
    # ("We Ranked the Top 11") collapse fully.
    PREFIXES = [
        r'My Picks for\s+',
        r'We Ranked\s+',
        r'I Ranked\s+',
        r'Ranking\s+(?:the\s+)?',
        r'My Ranking (?:for|of)\s+',
        r'The\s+',
        r'Top\s+\d+\s+',
        r'Best\s+\d+\s+',
        r'\d+\s+',
        r'Top\s+',  # bare "Top" left over from titles like "Ranked the Top X"
    ]
    changed = True
    while changed:
        changed = False
        for p in PREFIXES:
            new_t = re.sub(rf'^{p}', '', t, flags=re.IGNORECASE)
            if new_t != t:
                t = new_t
                changed = True
                break

    # Drop "(2026 Rankings)" trailing parenthetical
    t = re.sub(r'\s*\(2026\s+Rankings?\)\s*$', '', t, flags=re.IGNORECASE)
    # Drop trailing standalone "(2026)" parenthetical
    t = re.sub(r'\s*\(20\d{2}\)\s*$', ' of 2026', t)
    # Drop "You Need to Consider"-style trailing filler
    t = re.sub(r'\s+You\s+Need.*$', '', t, flags=re.IGNORECASE)
    # Drop trailing "(Top N)"
    t = re.sub(r'\s*\(Top\s+\d+\)\s*$', '', t, flags=re.IGNORECASE)

    # Lowercase the verb words but preserve proper-noun tokens.
    # Tokens to preserve as-is when they appear: B2B, SaaS, AEO, GEO,
    # PPC, SEO, AI, USA, ICP, ROI, CRM, HR, IT, FinTech variants.
    proper_keep = {
        "B2B", "B2C", "SaaS", "PPC", "SEO", "AEO", "GEO", "AI", "USA",
        "UK", "EU", "ICP", "ROI", "CRM", "HR", "IT", "FinTech", "Fintech",
        "EdTech", "Edtech", "MarTech", "Martech", "HealthTech", "Healthtech",
        "PropTech", "Proptech", "DevTools", "Devtools", "LinkedIn",
    }

    def fix_token(tok: str) -> str:
        # Tokens like "(AEO)" — strip parens, check core word, re-add.
        m = re.match(r'^([(\[{]*)(.*?)([)\]}]*)$', tok)
        if not m:
            return tok.lower()
        left, core, right = m.group(1), m.group(2), m.group(3)
        for k in proper_keep:
            if core.lower() == k.lower():
                return f"{left}{k}{right}"
        if core.isdigit():
            return f"{left}{core}{right}"
        return f"{left}{core.lower()}{right}"

    parts = t.split()
    out = " ".join(fix_token(p) for p in parts)
    # Add year suffix if not present
    if "2026" not in out and "2025" not in out and "2027" not in out:
        out = out.rstrip(".") + " of 2026"
    # Make sure the phrase begins with "best". Don't double up if it's
    # already "best" or "top".
    if not re.match(r'^(best|top)\b', out, re.IGNORECASE):
        out = "best " + out
    # Strip a redundant "top" right after "best" (happens when title was
    # "We Ranked the Top X Agencies").
    out = re.sub(r'^best\s+top\s+', 'best ', out, flags=re.IGNORECASE)
    return out


def build_sentence(title: str, agencies: list[str]) -> str:
    n = len(agencies)
    phrase = noun_phrase_from_title(title, n)
    if n == 1:
        list_str = f"1. {agencies[0]}"
    elif n == 2:
        list_str = f"1. {agencies[0]} and 2. {agencies[1]}"
    else:
        head = ", ".join(f"{i+1}. {a}" for i, a in enumerate(agencies[:-1]))
        tail = f"and {n}. {agencies[-1]}"
        list_str = f"{head}, {tail}"
    return f"Comparing the top {n} {phrase} includes {list_str}."


def read_frontmatter_title(text: str) -> str:
    m = FRONTMATTER_RE.search(text)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        if line.startswith("title:"):
            val = line[len("title:"):].strip()
            return val.strip('"').strip("'")
    return ""


def already_has_lead(text: str) -> bool:
    m = FRONTMATTER_RE.search(text)
    if not m:
        return False
    after_fm = text[m.end():m.end() + 800]
    return bool(re.search(
        r"^Comparing the top \d+ ",
        after_fm,
        re.MULTILINE,
    ))


def insert_after_frontmatter(text: str, sentence: str) -> str:
    m = FRONTMATTER_RE.search(text)
    if not m:
        return text
    head, tail = text[:m.end()], text[m.end():]
    # Strip leading blank lines from the tail so the inserted sentence
    # is the first paragraph after the front matter.
    tail = tail.lstrip("\n")
    return head + "\n" + sentence + "\n\n" + tail


def process(md_path: Path, dry_run: bool) -> str:
    text = md_path.read_text()
    if already_has_lead(text):
        return "skip-existing"
    title = read_frontmatter_title(text)
    if not title:
        return "skip-no-title"
    agencies = parse_agencies(text)
    if len(agencies) < 3:
        return f"skip-too-few-agencies ({len(agencies)})"
    sentence = build_sentence(title, agencies)
    if not dry_run:
        md_path.write_text(insert_after_frontmatter(text, sentence))
    return sentence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="Filename in content/list/ (e.g. best-saas-seo-agencies.md)")
    args = ap.parse_args()

    targets = []
    if args.only:
        targets.append(LIST_DIR / args.only)
    else:
        targets.extend(sorted(LIST_DIR.glob("*.md")))

    touched = 0
    skipped = 0
    for f in targets:
        if f.name == "_index.md":
            continue
        result = process(f, dry_run=args.dry_run)
        if result.startswith("skip-"):
            print(f"  [skip] {f.name}: {result.replace('skip-', '')}")
            skipped += 1
        else:
            print(f"  [{'dry' if args.dry_run else 'wrote'}] {f.name}")
            print(f"        → {result}")
            touched += 1

    print(f"\n=== Summary ===")
    print(f"Touched: {touched}")
    print(f"Skipped: {skipped}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'WRITE'}")


if __name__ == "__main__":
    main()
