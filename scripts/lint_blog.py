#!/usr/bin/env python3
"""
Deterministic phrasing gate for PipeRocket blogs (tofu-mofu-writer output).

Usage:
    python3 scripts/lint_blog.py content/blogs/<slug>.md [more.md ...]
    python3 scripts/lint_blog.py --all        # lint every content/blogs/*.md

Hard-fails (exit 1) on the two AI tells that keep slipping past LLM writers:
  1. Em/en dashes anywhere.
  2. The "setup-reframe" construction, in every form:
       - period-chopped:  "... isn't the keywords. It's the pages."
       - comma reframe:   "... not A, it's B" / "not A, but B"
       - contrastive "X, not Y" in HEADINGS and BOLD-LEAD bullets (the TL;DR /
         H2 / bullet zone where it actually slipped). In body prose it is a
         WARNING only, because legitimate example copy in quotes lives there.
Also flags banned words / openers as hard-fails (reuses the house list).

The infographic LOGO is NOT verified here (a .webp can't be grepped) — that
gate lives in scripts/build_infographic.sh, which runs at rasterize time.

Exit 0 = clean; 1 = one or more FAILs. WARNINGs never fail the build.
"""
import sys
import re
import glob
import os

BANNED_WORDS = [
    "delve", "tapestry", "underscore", "unpack", "pivotal", "paramount",
    "transformative", "holistic", "synergy", "paradigm", "groundbreaking",
    "utilize", "streamline", "comprehensive", "empower", "foster",
    "facilitate", "harness", "elevate", "actionable", "world-class",
    "industry-leading", "mission-critical", "value-add",
]
BANNED_OPENERS = [
    "Certainly,", "Absolutely,", "It's worth noting", "It is important to note",
    "As we can see", "At the end of the day", "Furthermore,", "Moreover,",
    "Additionally,", "In conclusion", "In today's landscape",
    "The answer lies in", "Let's explore", "But here's the thing",
]

# setup-reframe: period-chopped ("The gap isn't the keywords. It's the pages.")
# Only the negated COPULA (isn't/aren't/wasn't/weren't) counts — action-verb
# negations (don't/can't/doesn't) are not the reframe. Both halves must be
# short, which is what makes it the punchy "obvious X. deeper Y." tell and what
# keeps ordinary prose ("...a link that isn't there. That's a hypothesis...")
# from tripping it.
RE_CHOPPED = re.compile(
    r"\b(isn't|aren't|wasn't|weren't|ain't|"
    r"(?:it'?s|that'?s|there'?s|this is|is|are|was|were)\s+not)\b"
    r"[^.!?]{0,28}[.!?]\s+"
    r"(It'?s|They'?re|That'?s|It is|They are)\b[^.!?]{0,35}[.!?]",
    re.I,
)
# setup-reframe: comma copula reframe ("not the page, it's the site around it")
RE_COMMA_REFRAME = re.compile(
    r"\bnot\b[^.!?,]{0,30},\s+(it'?s|they'?re|that'?s)\b", re.I
)
# contrastive "X, not Y" — only banned in headings / bold-lead bullets
RE_CONTRASTIVE = re.compile(r",\s+not\s+[a-z]")


def is_heading_or_bold_lead(line):
    s = line.strip()
    if s.startswith("#"):
        return True
    # bold-lead bullet: "- **Label:** ..." or "- **Label** ..."
    if re.match(r"^-\s+\*\*", s):
        return True
    return False


def strip_quoted(text):
    """Remove "double-quoted" spans so example copy doesn't trip the linter."""
    return re.sub(r'"[^"]*"', '""', text)


def lint(path):
    fails, warns = [], []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    in_frontmatter = False
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")

        if line.strip() == "---" and i <= 2:
            in_frontmatter = True
            continue
        if in_frontmatter and line.strip() == "---":
            in_frontmatter = False

        # dashes: hard fail everywhere
        if "—" in line or "–" in line:
            fails.append(f"L{i}: em/en-dash — rewrite with comma/period/parens/colon")

        unquoted = strip_quoted(line)

        # setup-reframe: hard fail everywhere (chopped + comma form)
        if RE_CHOPPED.search(unquoted):
            fails.append(f"L{i}: setup-reframe (period-chopped 'isn't X. It's Y') — state it directly")
        if RE_COMMA_REFRAME.search(unquoted):
            fails.append(f"L{i}: setup-reframe (comma 'not A, it's/but B') — state it directly")

        # contrastive "X, not Y": hard fail in headings/bold leads, warn in body
        if RE_CONTRASTIVE.search(unquoted):
            if is_heading_or_bold_lead(line):
                fails.append(f"L{i}: contrastive 'X, not Y' in heading/bold lead — rephrase positively")
            else:
                warns.append(f"L{i}: contrastive 'X, not Y' in body — check it isn't a reframe tell")

        # banned words / openers (skip frontmatter; skip quoted example copy)
        if not in_frontmatter and i > 2:
            low = unquoted.lower()
            for w in BANNED_WORDS:
                if re.search(r"\b" + re.escape(w) + r"\b", low):
                    fails.append(f"L{i}: banned word '{w}'")
            for o in BANNED_OPENERS:
                if line.strip().startswith(o):
                    fails.append(f"L{i}: banned opener '{o}'")

    return fails, warns


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    if args == ["--all"]:
        paths = sorted(glob.glob("content/blogs/*.md"))
    else:
        paths = args

    any_fail = False
    for p in paths:
        if not os.path.exists(p):
            print(f"SKIP (missing): {p}")
            continue
        fails, warns = lint(p)
        slug = os.path.basename(p)
        if fails:
            any_fail = True
            print(f"FAIL  {slug}")
            for m in fails:
                print(f"      {m}")
        else:
            print(f"PASS  {slug}")
        for m in warns:
            print(f"      warn: {m}")
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
