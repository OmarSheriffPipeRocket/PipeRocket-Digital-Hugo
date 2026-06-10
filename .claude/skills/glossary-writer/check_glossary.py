#!/usr/bin/env python3
"""
Glossary rule checker for PipeRocket glossary entries.

Usage:
    python3 check_glossary.py /path/to/content/glossary/<slug>.md

Mechanically verifies the deterministic rules in SKILL.md and prints a
PASS/FAIL report with line references. Rules that can't be checked
mechanically (setup-reframe, aphoristic closers, parallel-clause triads,
voice match) are surfaced as a manual-review reminder, not auto-failed.

Exit code 0 = all hard checks passed; 1 = one or more FAILs.
"""

import sys
import re
import os

# ----------------------------------------------------------------------
# Rule data (kept in sync with SKILL.md)
# ----------------------------------------------------------------------

REQUIRED_FRONTMATTER = [
    "title", "description", "metaTitle", "metaDescription", "date",
    "slug", "categorySlug", "writtenBy", "glossaryCategory",
    "toc", "readingTime",
]

BANNED_WORDS = [
    "delve", "tapestry", "underscore", "unpack", "pivotal", "paramount",
    "transformative", "holistic", "synergy", "paradigm", "groundbreaking",
    "leverage", "utilize", "robust", "streamline", "scalable",
    "comprehensive", "empower", "foster", "facilitate", "harness",
    "elevate", "actionable", "ecosystem", "landscape", "pain points",
    "thought leader", "thought leadership", "deep dive", "world-class",
    "industry-leading", "end-to-end", "mission-critical", "value-add",
    "content architecture",
]

BANNED_OPENERS = [
    "Certainly", "Absolutely", "It's worth noting", "It is important to note",
    "As we can see", "In order to", "At the end of the day", "Furthermore",
    "Moreover", "Additionally", "In conclusion", "In today's landscape",
    "The answer lies in", "Let's explore", "Here's why that matters",
    "But here's the thing",
]

BANNED_TRANSITIONS = [
    "Furthermore", "Moreover", "Additionally", "In conclusion",
    "To summarize", "In today's world", "It is important to note",
    "This is where X comes in", "And that's not all",
]

VALID_CATEGORY_SLUGS = ["seo", "content-marketing", "b2b-marketing"]

# H2 titles allowed to NOT be questions
H2_NON_QUESTION_ALLOWED = [
    "tl;dr", "frequently asked questions", "the bottom line",
]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def split_frontmatter(text):
    """Return (frontmatter_str, body_str, body_start_line)."""
    if not text.startswith("---"):
        return "", text, 1
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text, 1
    fm = parts[1]
    body = parts[2]
    body_start_line = fm.count("\n") + 2  # lines consumed by fm + delimiters
    return fm, body, body_start_line


def iter_paragraphs(body, line_offset=1):
    """Yield (text, start_line) for prose paragraphs (skip headings,
    bullets, blockquotes, images, code). line_offset aligns reported
    line numbers with the source file."""
    lines = body.split("\n")
    buf, buf_start = [], None
    for i, line in enumerate(lines, start=line_offset):
        stripped = line.strip()
        is_special = (
            stripped == "" or stripped.startswith("#") or
            stripped.startswith("-") or stripped.startswith("*") or
            stripped.startswith(">") or stripped.startswith("!") or
            stripped.startswith("|") or stripped.startswith("```") or
            re.match(r"^\d+\.\s", stripped)
        )
        if is_special:
            if buf:
                yield " ".join(buf), buf_start
                buf, buf_start = [], None
        else:
            if not buf:
                buf_start = i
            buf.append(stripped)
    if buf:
        yield " ".join(buf), buf_start


def word_count_body(body):
    """Count words in prose + bullets, excluding headings/frontmatter/images."""
    words = 0
    for line in body.split("\n"):
        s = line.strip()
        if s == "" or s.startswith("#") or s.startswith("!") or \
           s.startswith("```") or s.startswith("|"):
            continue
        # strip markdown link syntax to count visible words
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        s = re.sub(r"[*>`-]", " ", s)
        words += len(s.split())
    return words


# ----------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------

class Report:
    def __init__(self):
        self.fails = []
        self.warns = []
        self.passes = []

    def fail(self, msg):
        self.fails.append(msg)

    def warn(self, msg):
        self.warns.append(msg)

    def ok(self, msg):
        self.passes.append(msg)


def check(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    fm, body, body_start = split_frontmatter(text)
    body_lines = body.split("\n")
    r = Report()

    # --- Frontmatter fields ---
    for field in REQUIRED_FRONTMATTER:
        if not re.search(rf"^{re.escape(field)}\s*:", fm, re.MULTILINE):
            r.fail(f"Frontmatter missing required field: `{field}`")
    if not r.fails:
        r.ok("All frontmatter fields present")

    # metaTitle / metaDescription length
    m = re.search(r"^metaTitle:\s*\"?(.*?)\"?\s*$", fm, re.MULTILINE)
    if m and len(m.group(1)) > 60:
        r.warn(f"metaTitle is {len(m.group(1))} chars (target ≤ 60)")
    m = re.search(r"^metaDescription:\s*\"?(.*?)\"?\s*$", fm, re.MULTILINE)
    if m and len(m.group(1)) > 155:
        r.fail(f"metaDescription is {len(m.group(1))} chars (max 155)")

    # categorySlug valid
    m = re.search(r"^categorySlug:\s*\"?([\w-]+)\"?", fm, re.MULTILINE)
    if m and m.group(1) not in VALID_CATEGORY_SLUGS:
        r.fail(f"categorySlug `{m.group(1)}` not in {VALID_CATEGORY_SLUGS}")

    # no wp_id / wp_link (new entries)
    if re.search(r"^wp_(id|link):", fm, re.MULTILINE):
        r.warn("Frontmatter has wp_id/wp_link — new entries shouldn't")

    # --- Em/en dashes in body (Fast Fact boilerplate is exempt) ---
    for i, line in enumerate(body_lines, start=body_start):
        if line.strip().startswith("> **Fast Fact:**"):
            continue  # pre-approved stat lines may contain dashes
        if "—" in line or "–" in line:
            r.fail(f"Line {i}: em/en-dash found — rewrite with comma/period/parens")

    # --- [[markers]] ---
    for i, line in enumerate(body_lines, start=body_start):
        if "[[" in line:
            r.fail(f"Line {i}: [[marker]] found — use native markdown links")

    # --- Horizontal rules in body ---
    for i, line in enumerate(body_lines, start=body_start):
        if line.strip() == "---":
            r.fail(f"Line {i}: horizontal rule (---) not allowed in body")

    # --- Banned words ---
    low = body.lower()
    for w in BANNED_WORDS:
        for mt in re.finditer(rf"\b{re.escape(w.lower())}\b", low):
            ln = body[:mt.start()].count("\n") + body_start
            r.fail(f"Line {ln}: banned word `{w}`")
            break  # one report per word is enough

    # --- "not just/only X but also Y" ---
    for mt in re.finditer(r"not (just|only)\b.{0,60}?\bbut also\b", low):
        ln = body[:mt.start()].count("\n") + body_start
        r.fail(f"Line {ln}: banned 'not just/only X but also Y' framing")

    # --- Banned openers / transitions (sentence-start) ---
    for para, start in iter_paragraphs(body, body_start):
        # split into sentences crudely
        for sent in re.split(r"(?<=[.!?])\s+", para):
            sent = sent.strip()
            for opener in set(BANNED_OPENERS + BANNED_TRANSITIONS):
                if sent.lower().startswith(opener.lower()):
                    r.fail(f"~Line {start}: banned opener/transition "
                           f"'{opener}' starts a sentence")

    # --- Paragraph length ≤ 50 words (FAQ answers exempt: they're 3-5 sentences) ---
    faq_start_ln = None
    faq_end_ln = None
    for i, line in enumerate(body_lines, start=body_start):
        if line.strip().lower().startswith("## frequently asked questions"):
            faq_start_ln = i
        elif faq_start_ln is not None and faq_end_ln is None and line.strip().startswith("## "):
            faq_end_ln = i
    if faq_start_ln is not None and faq_end_ln is None:
        faq_end_ln = body_start + len(body_lines)
    for para, start in iter_paragraphs(body, body_start):
        if faq_start_ln is not None and faq_start_ln < start < faq_end_ln:
            continue  # FAQ answers may run longer than 50 words
        n = len(para.split())
        if n > 50:
            r.fail(f"Line {start}: paragraph is {n} words (max 50)")

    # --- Headings analysis ---
    h2s = [(i, l.strip()[3:].strip())
           for i, l in enumerate(body_lines, start=body_start)
           if l.strip().startswith("## ")]
    h3s = [(i, l.strip()[4:].strip())
           for i, l in enumerate(body_lines, start=body_start)
           if l.strip().startswith("### ")]

    # All H2 are questions except whitelist
    for ln, title in h2s:
        t = title.lower().strip()
        if any(t.startswith(a) for a in H2_NON_QUESTION_ALLOWED):
            continue
        if not title.rstrip().endswith("?"):
            r.warn(f"Line {ln}: H2 '{title}' is not a question")

    # FAQ count = 3 (### N. under Frequently Asked Questions)
    faq_h3 = [t for _, t in h3s if re.match(r"^\d+\.", t)]
    if len(faq_h3) != 3:
        r.fail(f"FAQ should have exactly 3 numbered ### items, found {len(faq_h3)}")
    else:
        r.ok("FAQ has exactly 3 numbered questions")

    # Non-FAQ H3 should be noun phrases (not questions)
    for ln, title in h3s:
        if re.match(r"^\d+\.", title):
            continue
        if title.rstrip().endswith("?"):
            r.warn(f"Line {ln}: H3 '{title}' is a question (should be noun phrase)")

    # --- Required sections present ---
    h2_titles_low = [t.lower() for _, t in h2s]
    if not any(t.startswith("tl;dr") for t in h2_titles_low):
        r.fail("Missing `## TL;DR` section")
    if not any("frequently asked questions" in t for t in h2_titles_low):
        r.fail("Missing `## Frequently Asked Questions` section")
    if not any("the bottom line" in t for t in h2_titles_low):
        r.fail("Missing `## The Bottom Line` section")
    if not any(t.startswith("what is") or t.startswith("what are") for t in h2_titles_low):
        r.warn("No `## What Is/Are ...?` definition H2 found")

    # --- Fast Facts: exactly 2, not in TL;DR ---
    ff_lines = [i for i, l in enumerate(body_lines, start=body_start)
                if l.strip().startswith("> **Fast Fact:**")]
    if len(ff_lines) != 2:
        r.fail(f"Should have exactly 2 Fast Facts, found {len(ff_lines)}")
    else:
        r.ok("Exactly 2 Fast Facts present")
    # TL;DR boundaries
    tldr_ln = next((ln for ln, t in h2s if t.lower().startswith("tl;dr")), None)
    next_h2_after_tldr = None
    if tldr_ln is not None:
        later = [ln for ln, _ in h2s if ln > tldr_ln]
        next_h2_after_tldr = min(later) if later else None
        for ff in ff_lines:
            if tldr_ln < ff < (next_h2_after_tldr or 10**9):
                r.fail(f"Line {ff}: Fast Fact inside TL;DR section (not allowed)")

    # --- TL;DR bullet count 4-5 ---
    if tldr_ln is not None and next_h2_after_tldr is not None:
        bullets = 0
        for i in range(tldr_ln, next_h2_after_tldr):
            idx = i - body_start
            if 0 <= idx < len(body_lines) and body_lines[idx].strip().startswith("- "):
                bullets += 1
        if bullets < 4 or bullets > 5:
            r.warn(f"TL;DR has {bullets} bullets (target 4-5)")
        else:
            r.ok(f"TL;DR has {bullets} bullets")

    # --- Numbered lists in body (excluding FAQ headings) ---
    for i, line in enumerate(body_lines, start=body_start):
        if re.match(r"^\d+\.\s", line.strip()) and not line.strip().startswith("#"):
            r.warn(f"Line {i}: numbered list item in body (use bullets/prose)")

    # --- Infographic embed present ---
    if "/images/glossary-infographics/" not in body:
        r.fail("No infographic embedded (expected /images/glossary-infographics/...)")
    else:
        n_imgs = body.count("/images/glossary-infographics/")
        r.ok(f"{n_imgs} infographic embed(s) present")

    # --- Word count 1500-2500 ---
    wc = word_count_body(body)
    if wc < 1500:
        r.fail(f"Word count {wc} is below 1500")
    elif wc > 2500:
        r.warn(f"Word count {wc} is above 2500")
    else:
        r.ok(f"Word count {wc} (1500-2500)")

    return r


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 check_glossary.py <path-to-glossary.md>")
        sys.exit(2)
    path = sys.argv[1]
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        sys.exit(2)

    r = check(path)
    name = os.path.basename(path)
    print(f"\n=== Glossary rule check: {name} ===\n")

    if r.passes:
        print("PASSED:")
        for p in r.passes:
            print(f"  ✓ {p}")
        print()
    if r.warns:
        print("WARNINGS (review, not auto-fail):")
        for w in r.warns:
            print(f"  ⚠ {w}")
        print()
    if r.fails:
        print("FAILURES (must fix before saving):")
        for f in r.fails:
            print(f"  ✗ {f}")
        print()

    # Manual-review reminder for non-mechanical rules
    print("MANUAL REVIEW (not mechanically checkable — confirm by reading):")
    print("  • No setup-reframe ('X isn't A, it's B') as section opener/punchline")
    print("  • No crafted aphoristic closers ('The skill is in what you cut')")
    print("  • No parallel-clause triads (three parallel verb/clause beats)")
    print("  • No invented stats/names/timeframes for 'texture'")
    print("  • Voice matches reference/style-anchor.md (not generic-blog cadence)")
    print("  • Contrarian angle in first main H2; 2+ committed opinion sentences")
    print("  • All 3 E-E-A-T signals present (trade-off, contrarian, warning)")
    print()

    if r.fails:
        print(f"RESULT: FAIL — {len(r.fails)} issue(s) to fix.\n")
        sys.exit(1)
    else:
        print("RESULT: PASS (hard checks) — complete the manual review above.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
