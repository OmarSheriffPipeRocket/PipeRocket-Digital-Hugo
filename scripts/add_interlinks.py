#!/usr/bin/env python3
"""
Hugo-native interlink applier (P0/P1/P2 contextual links).

Implements the rules from piperocket_interlinking_rules.md with the fixes
identified in the 2026-06-02 audit:

  R5a (FIXED): anchors must land past word 450 of the body. Word counting
               uses \b\w+\b (matches human reading; differs from \S+ token
               counting by ~5-15 words near the threshold).
  R5d (FIXED): no two anchors added to the same paragraph in a single run.
               Each newly-wrapped phrase claims its enclosing paragraph;
               subsequent suggestions targeting the same paragraph are
               deferred to the next paragraph that contains a valid match,
               or skipped.
  R5b/R6a (OPTIONAL): FAQ / Conclusion / Author section skip. Off by
               default per the 2026-06-02 user override ("Interlinks on
               FAQs are fine"). Enable with `--skip-faq`.

What this script does NOT do:
  - Score paragraph-context fit (R5 LLM check) — that's a suggestion-time
    concern, not an apply-time one
  - Insert NEW bridging sentences — this iteration only wraps existing
    phrases (the simpler half of the spec). New-sentence insertion would
    layer on top of this same word-position / per-paragraph engine
  - Cross-file linkability (P0/P1 require external suggestion data)

Usage:
  python scripts/add_interlinks.py                # dry-run on all blogs
  python scripts/add_interlinks.py --apply        # write changes
  python scripts/add_interlinks.py --slug saas-ppc --apply
  python scripts/add_interlinks.py --skip-faq --apply

The link map at the top can be extended with blog→blog and blog→listicle
entries (just change `target_prefix`).
"""
import argparse
import os
import re
import sys
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

# Per-type configuration. WORD_GATE is the minimum word position past which
# a new anchor may be inserted (R5a). Blogs are long-form so we enforce w450;
# shorter content types use lower floors. Compare pages have their body in
# YAML frontmatter (data-driven template) so the script will naturally find
# few/no candidates there — included for completeness.
CONTENT_TYPES = {
    "blogs":       {"dir": "blogs",       "word_gate": 450},
    "list":        {"dir": "list",        "word_gate": 200},
    "alternative": {"dir": "alternative", "word_gate": 200},
    "glossary":    {"dir": "glossary",    "word_gate": 0},
    "compare":     {"dir": "compare",     "word_gate": 0},
}

# Backwards compatibility — older callers referenced WORD_GATE as a constant.
WORD_GATE = CONTENT_TYPES["blogs"]["word_gate"]

# ---------------------------------------------------------------------------
# Interlinking flow routing (2026-06-02 rules)
# ---------------------------------------------------------------------------
# Allowed (source content type) → (destination content type) edges. Values:
#   True              — allowed unconditionally
#   "after_5th"       — only after the 5th agency-card heading in the source
#                        (listicle-internal pacing rule)
#   False / missing   — disallowed; the link will be skipped
#
# Destinations are inferred from URL path:
#   /blogs/…       → blog
#   /list/…        → listicle
#   /glossary/…    → glossary
#   /compare/…     → compare
#   /alternative/… → alternative
#   anything else  → service  (industry / landing / home / contact / author)
ALLOWED_FLOWS = {
    # Blogs as source
    ("blogs", "blog"):        True,         # rule 1 (same type)
    ("blogs", "listicle"):    True,         # rule 4
    ("blogs", "glossary"):    True,         # rule 11 (user override 2026-06-02)
    ("blogs", "service"):     True,         # rule 5

    # Listicles as source
    ("list",  "blog"):        "after_5th",  # rule 6
    ("list",  "listicle"):    "after_5th",  # rule 7
    ("list",  "service"):     True,         # rule 8
    ("list",  "compare"):     True,         # rule 9

    # Glossary as source
    ("glossary", "blog"):     True,         # rule 2
    ("glossary", "listicle"): True,         # rule 3
    ("glossary", "glossary"): True,         # rule 1 (same type)

    # Compare as source — only same-type (rule 1)
    ("compare", "compare"):   True,

    # Alternative as source
    ("alternative", "compare"):     True,   # rule 10
    ("alternative", "alternative"): True,   # rule 1 (same type)
}


def classify_target(target_path: str) -> str:
    """Return destination type string for a target URL path."""
    p = (target_path or "/").rstrip("/") or "/"
    if p.startswith("/blogs/"):       return "blog"
    if p.startswith("/list/"):        return "listicle"
    if p.startswith("/glossary"):     return "glossary"
    if p.startswith("/compare"):      return "compare"
    if p.startswith("/alternative"):  return "alternative"
    return "service"


# Listicle agency-entry heading detector. Matches `### 1. Agency Name`,
# `## 1. Agency`, `### 1) Agency`, etc. — a numbered heading at h2 or h3.
AGENCY_HEADING_RE = re.compile(r"^#{2,3}\s+\d+[\.\)]\s+\S", re.MULTILINE)

# ---------------------------------------------------------------------------
# Compare-page bridging sentence inserts (new-sentence mode)
# ---------------------------------------------------------------------------
# For listicle→compare and alternative→compare flows (rules 9 + 10), the
# applier inserts a templated nudge sentence inside or right after the
# agency's section in the source body. Each compare URL has a competitor
# name parsed from the slug (`piperocket-digital-vs-klientboost` → "KlientBoost").
#
# Templates rotate to avoid the same phrasing appearing on every page.
COMPARE_BRIDGE_TEMPLATES = [
    "Want a side-by-side? See our [PipeRocket vs {competitor}](/compare/{slug}/) breakdown.",
    "For a head-to-head on paid, organic, and pricing, see [PipeRocket vs {competitor}](/compare/{slug}/).",
    "Weighing PipeRocket against {competitor}? Our [{competitor} comparison](/compare/{slug}/) covers the four things founders ask about most.",
]

ALTERNATIVE_BRIDGE_TEMPLATES = [
    "Also evaluating {competitor}? See our [{competitor} alternatives](/alternative/{slug}/) breakdown.",
    "Looking at {competitor} too? Our [{competitor} alternatives](/alternative/{slug}/) review covers who beats them on what.",
    "If {competitor} isn't quite the fit, check our [{competitor} alternatives](/alternative/{slug}/) shortlist.",
]

# Known brand casings — applied when converting URL slugs back to display names.
_BRAND_CASING = {
    "klientboost": "KlientBoost", "nogood": "NoGood", "webfx": "WebFX",
    "directive": "Directive", "consulting": "Consulting",
    "omniscient": "Omniscient", "digital": "Digital",
    "siege": "Siege", "media": "Media",
}


def _slug_to_brand(slug_fragment: str) -> str:
    words = []
    for w in slug_fragment.split("-"):
        words.append(_BRAND_CASING.get(w.lower(), w.capitalize()))
    return " ".join(words)


def parse_competitor_from_compare_url(target_url: str):
    """Extract (slug, competitor_name) from a /compare/<slug>/ URL."""
    m = re.match(r"/compare/([^/]+)/?$", target_url.rstrip("/") + "/")
    if not m:
        return None, None
    slug = m.group(1)
    rest = re.sub(r"^piperocket(?:-digital)?-vs-", "", slug)
    if rest == slug:
        rest = re.sub(r"^piperocket-vs-", "", slug)
    return slug, _slug_to_brand(rest)


def parse_competitor_from_alternative_url(target_url: str):
    """Extract (slug, competitor_name) from an /alternative/<slug>-alternatives/ URL."""
    m = re.match(r"/alternative/([^/]+)/?$", target_url.rstrip("/") + "/")
    if not m:
        return None, None
    slug = m.group(1)
    rest = re.sub(r"-alternatives$", "", slug)
    return slug, _slug_to_brand(rest)


def find_listicle_agency_section(body: str, competitor_name: str):
    """Return (start_offset, end_offset) of the agency section in a listicle
    whose heading mentions `competitor_name`. Returns None if not found.

    Sections start at `### N. AgencyName...` and end before the next `### `.
    """
    headings = list(re.finditer(r"^(#{2,3})\s+(.+)$", body, re.MULTILINE))
    target_norm = competitor_name.lower().replace(" ", "")
    for i, h in enumerate(headings):
        heading_text = h.group(2)
        # Heading must be a numbered agency entry (rule 6/7 — after-5th gate)
        if not re.match(r"^\d+[\.\)]\s+", heading_text):
            continue
        # Normalize: strip number prefix, lower, remove spaces
        rest = re.sub(r"^\d+[\.\)]\s+", "", heading_text).lower().replace(" ", "")
        # Match if competitor name appears in the heading
        if target_norm in rest or rest.startswith(target_norm):
            start = h.start()
            # End = start of next heading (any level) or end of body
            end = len(body)
            for h2 in headings[i + 1:]:
                end = h2.start()
                break
            return (start, end)
    return None


def find_alternative_agency_block(body: str, competitor_name: str):
    """For an alternative page, find a section/paragraph mentioning the
    competitor (e.g. 'KlientBoost' on klientboost-alternatives.md). Returns
    (start, end) of the enclosing block, or None.
    """
    pat = re.compile(r"\b" + re.escape(competitor_name) + r"\b", re.IGNORECASE)
    m = pat.search(body)
    if not m:
        return None
    # Find paragraph end (next blank line) so we can insert just after
    next_blank = body.find("\n\n", m.end())
    if next_blank == -1:
        next_blank = len(body)
    # Use paragraph containing the match
    para_start = body.rfind("\n\n", 0, m.start())
    para_start = 0 if para_start == -1 else para_start + 2
    return (para_start, next_blank)


def render_bridge_sentence(template_index: int, competitor: str, slug: str,
                            dest_type: str = "compare") -> str:
    templates = COMPARE_BRIDGE_TEMPLATES if dest_type == "compare" else ALTERNATIVE_BRIDGE_TEMPLATES
    return templates[template_index % len(templates)].format(competitor=competitor, slug=slug)


def fifth_entry_offset(body: str):
    """Return char offset of the 5th numbered agency heading in a listicle
    body, or None if fewer than 5 exist."""
    matches = list(AGENCY_HEADING_RE.finditer(body))
    if len(matches) < 5:
        return None
    return matches[4].start()

# ---------------------------------------------------------------------------
# Link map. Each entry is (anchor_phrase, target_path, case_sensitive, priority).
# Priority controls iteration order: P0 candidates are placed before P1, P1
# before P2. Within a priority, longest phrase wins (so "technical SEO" claims
# its slot before "SEO").
# ---------------------------------------------------------------------------
LINK_MAP = [
    # ---- P2 glossary anchors (extend as needed) ----
    ("retrieval-augmented generation", "/glossary/what-is-rag/", False, "P2"),
    ("retrieval augmented generation", "/glossary/what-is-rag/", False, "P2"),
    ("account-based marketing", "/glossary/what-is-abm/", False, "P2"),
    ("account based marketing", "/glossary/what-is-abm/", False, "P2"),
    ("technical SEO", "/glossary/what-is-technical-seo/", False, "P2"),
    ("on-page SEO", "/glossary/what-is-on-page-seo/", False, "P2"),
    ("on page SEO", "/glossary/what-is-on-page-seo/", False, "P2"),
    ("keyword research", "/glossary/what-is-keyword-research/", False, "P2"),
    ("content marketing", "/glossary/what-is-content-marketing/", False, "P2"),
    ("performance marketing", "/glossary/what-is-performance-marketing/", False, "P2"),
    ("lead generation", "/glossary/what-is-lead-generation/", False, "P2"),
    ("google ads", "/glossary/what-is-google-ads/", False, "P2"),
    ("domain authority", "/glossary/what-is-domain-authority/", False, "P2"),
    ("backlinks", "/glossary/what-is-a-backlink/", False, "P2"),
    ("backlink", "/glossary/what-is-a-backlink/", False, "P2"),
    ("anchor text", "/glossary/what-is-anchor-text/", False, "P2"),
    ("canonical tag", "/glossary/what-is-a-canonical-tag/", False, "P2"),
    ("meta description", "/glossary/what-is-a-meta-description/", False, "P2"),
    ("evergreen content", "/glossary/what-is-evergreen-content/", False, "P2"),
    ("SEO audit", "/glossary/what-is-an-seo-audit/", False, "P2"),
    ("prompt engineering", "/glossary/what-is-prompt-engineering/", False, "P2"),
    ("LLM", "/glossary/what-is-an-llm/", True, "P2"),
    ("SEO", "/glossary/what-is-seo/", True, "P2"),
    ("PPC", "/glossary/what-is-ppc/", True, "P2"),
    ("CPC", "/glossary/what-is-cost-per-click/", True, "P2"),
    ("CPA", "/glossary/what-is-cpa/", True, "P2"),
    ("CTR", "/glossary/what-is-ctr/", True, "P2"),
    ("ICP", "/glossary/what-is-icp/", True, "P2"),
    ("ABM", "/glossary/what-is-abm/", True, "P2"),
    ("ROAS", "/glossary/what-is-roas/", True, "P2"),
    ("SERP", "/glossary/what-is-serp/", True, "P2"),
    ("ARR", "/glossary/what-is-arr/", True, "P2"),
    # ---- P1 tool-listicle targets (added 2026-06-09) ----
    ("rank tracking tools", "/list/best-rank-tracking-tools-for-saas/", False, "P1"),
    ("rank trackers", "/list/best-rank-tracking-tools-for-saas/", False, "P1"),
    ("rank tracker", "/list/best-rank-tracking-tools-for-saas/", False, "P1"),
    ("session recording tools", "/list/best-heatmap-session-recording-tools-for-saas/", False, "P1"),
    ("heatmap tools", "/list/best-heatmap-session-recording-tools-for-saas/", False, "P1"),
    ("landing page builders", "/list/best-landing-page-builders-for-saas/", False, "P1"),
    ("schema markup tools", "/list/best-schema-markup-tools-for-saas/", False, "P1"),
    ("schema markup generators", "/list/best-schema-markup-tools-for-saas/", False, "P1"),
    ("SERP testing tools", "/list/best-serp-testing-tools-for-saas/", False, "P1"),
    ("rich results testing", "/list/best-serp-testing-tools-for-saas/", False, "P1"),

    # ---- example P0/P1 entries (extend as needed) ----
    # ("SaaS PPC checklist", "/blogs/saas-ppc-checklist/", False, "P0"),
    # ("best SaaS SEO agencies", "/list/best-saas-seo-agencies/", False, "P1"),
]

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}

# Optional content cluster map. If clusters_generated.py is present, the
# applier will promote same-cluster (source→target) candidates to P0
# priority. Generated by scripts/build_clusters.py.
try:
    from clusters_generated import CONTENT_CLUSTERS  # type: ignore
except Exception:
    CONTENT_CLUSTERS = {}

try:
    from clusters_generated import CLUSTER_AFFINITY  # type: ignore
except Exception:
    CLUSTER_AFFINITY = {}

# Section-skip regexes (only used when --skip-faq is passed)
FAQ_RE = re.compile(r"\b(faqs?|frequently\s+asked|q\s*&\s*a|q\s*and\s*a|common\s+questions)\b", re.I)
SKIP_HEADING_RE = re.compile(r"\b(author|share\s+this|related\s+(posts|reading|articles)|table\s+of\s+contents|about\s+the\s+author)\b", re.I)
CONCLUSION_RE = re.compile(r"\b(conclusion|wrap[\s-]?up|final\s+thoughts|key\s+takeaways|summary|bottom\s+line|in\s+closing)\b", re.I)


# ---------------------------------------------------------------------------
# Body parsing helpers
# ---------------------------------------------------------------------------

def split_frontmatter(content: str):
    """Return (frontmatter_block, body). frontmatter_block keeps its --- fences."""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return "", content
    fm = parts[0] + "---" + parts[1] + "---"
    return fm, parts[2]


def get_protected_spans(body: str):
    """Char ranges where we must NOT add a new link (mirrors add_glossary_links.py)."""
    spans = []
    for m in re.finditer(r"^#{1,6}\s.*$", body, re.MULTILINE):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"!?\[([^\]]*)\]\([^\)]*\)", body):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"\[[^\]]*\]\[[^\]]*\]", body):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"`[^`\n]+`", body):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"```[\s\S]*?```", body):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"https?://[^\s\)\]>]+", body):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"<[^>]+>", body):
        spans.append((m.start(), m.end()))
    return spans


def overlaps(s, e, spans):
    return any(s < pe and e > ps for ps, pe in spans)


# ---------------------------------------------------------------------------
# Word-position index (R5a fix — use \b\w+\b counting)
# ---------------------------------------------------------------------------

def build_word_index(body: str, protected_spans):
    """Return a list of (word_start_char, word_end_char, word_index) for every
    \\b\\w+\\b token in body that's NOT inside a protected span.

    Markdown link text counts toward word position (a reader sees those words),
    but the link wrapper itself is protected. Code blocks / bare URLs do not
    count — they're hidden from prose flow.

    We exclude tokens inside code blocks / bare URLs by checking protected
    spans, but allow tokens inside markdown link text by splitting protected
    spans into "counts" vs "doesn't-count" categories.
    """
    # Spans that should NOT count as readable prose words:
    nocount_spans = []
    for m in re.finditer(r"```[\s\S]*?```", body):
        nocount_spans.append((m.start(), m.end()))
    for m in re.finditer(r"`[^`\n]+`", body):
        nocount_spans.append((m.start(), m.end()))
    for m in re.finditer(r"https?://[^\s\)\]>]+", body):
        nocount_spans.append((m.start(), m.end()))
    for m in re.finditer(r"<[^>]+>", body):
        nocount_spans.append((m.start(), m.end()))
    # The URL part of [text](url) doesn't count; the [text] part does.
    for m in re.finditer(r"!?\[([^\]]*)\]\(([^\)]*)\)", body):
        # url range
        text_end = m.start() + len(m.group(1)) + 3  # `[text](` ends here-ish
        # easier: just mark from `(` to `)`
        paren_open = body.find("(", m.start(), m.end())
        if paren_open != -1:
            nocount_spans.append((paren_open, m.end()))
        # if it's an image (`!`), exclude the alt text too
        if body[m.start():m.start()+1] == "!":
            nocount_spans.append((m.start(), m.end()))

    out = []
    wi = 0
    for m in re.finditer(r"\b\w+\b", body):
        s, e = m.start(), m.end()
        if overlaps(s, e, nocount_spans):
            continue
        out.append((s, e, wi))
        wi += 1
    return out


def word_at(word_index, char_offset):
    """Return the word-position (count of \\b\\w+\\b tokens before char_offset)."""
    lo, hi = 0, len(word_index)
    while lo < hi:
        mid = (lo + hi) // 2
        if word_index[mid][0] < char_offset:
            lo = mid + 1
        else:
            hi = mid
    return lo  # number of words strictly before this char offset


# ---------------------------------------------------------------------------
# Paragraph-range index (R5d fix — no two anchors in same paragraph per run)
# ---------------------------------------------------------------------------

def paragraph_ranges(body: str):
    """Return list of (start, end) char ranges for each prose paragraph.
    A paragraph is text between blank lines (Markdown convention).
    Heading lines and fenced-code blocks are their own ranges.
    """
    ranges = []
    cursor = 0
    for m in re.finditer(r"\n\s*\n", body):
        ranges.append((cursor, m.start()))
        cursor = m.end()
    if cursor < len(body):
        ranges.append((cursor, len(body)))
    return ranges


def find_paragraph(par_ranges, offset):
    """Return (start, end) of the paragraph containing offset, or None."""
    for s, e in par_ranges:
        if s <= offset < e:
            return (s, e)
    return None


# ---------------------------------------------------------------------------
# Optional R5b/R6a — FAQ/Conclusion section skip
# ---------------------------------------------------------------------------

def build_excluded_section_spans(body: str):
    """Return char ranges covered by FAQ / Conclusion / Author sections.
    A section runs from one ## heading to the next ##-or-higher heading.
    """
    spans = []
    headings = list(re.finditer(r"^(#{2,3})\s+(.+)$", body, re.MULTILINE))
    for i, h in enumerate(headings):
        title = h.group(2).strip()
        if not (FAQ_RE.search(title) or SKIP_HEADING_RE.search(title) or CONCLUSION_RE.search(title)):
            continue
        section_start = h.start()
        # find next heading of same-or-higher level
        my_level = len(h.group(1))
        section_end = len(body)
        for h2 in headings[i + 1:]:
            if len(h2.group(1)) <= my_level:
                section_end = h2.start()
                break
        spans.append((section_start, section_end))
    return spans


# ---------------------------------------------------------------------------
# Main per-file pass
# ---------------------------------------------------------------------------

def own_url_paths(filepath: Path, fm_block: str):
    """Return set of URL paths that point to this page (for self-link suppression).
    Includes the conventional path derived from the file's parent dir + stem,
    plus any explicit `url:` override in frontmatter.
    """
    paths = set()
    parent = filepath.parent.name  # "blogs", "list", "compare", etc.
    if parent in CONTENT_TYPES:
        paths.add(f"/{CONTENT_TYPES[parent]['dir']}/{filepath.stem}/")
    # Service pages live at content root — URL is /<stem>/
    elif filepath.parent.name == "content":
        paths.add(f"/{filepath.stem}/")
    m = re.search(r'^url:\s*"?([^"]+?)"?\s*$', fm_block, re.MULTILINE)
    if m:
        u = m.group(1).strip()
        if not u.endswith("/"): u = u + "/"
        paths.add(u)
    return {p.rstrip("/") + "/" for p in paths}


def process_file(filepath: Path, skip_faq: bool = False, word_gate: int = WORD_GATE,
                 source_type: str = "blogs"):
    content = filepath.read_text(encoding="utf-8")
    fm, body = split_frontmatter(content)
    if not fm:
        return content, [], "no frontmatter"
    self_paths = own_url_paths(filepath, fm)
    # Resolve source clusters (tuple; promote same-cluster targets to P0).
    src_clusters = set()
    for sp in self_paths:
        entry = CONTENT_CLUSTERS.get(sp)
        if entry:
            # Tolerate both legacy string form and new tuple form
            if isinstance(entry, str):
                src_clusters.add(entry)
            else:
                src_clusters.update(entry)

    protected = get_protected_spans(body)
    excluded_sections = build_excluded_section_spans(body) if skip_faq else []
    word_index = build_word_index(body, protected)
    par_ranges = paragraph_ranges(body)

    # Listicle "after the 5th entry" gate (rules 6 + 7). For non-list sources,
    # this is None and the check is a no-op.
    fifth_offset = fifth_entry_offset(body) if source_type == "list" else None

    # Source affinity set: union of CLUSTER_AFFINITY for every cluster the
    # source belongs to. A generic glossary target (cluster "seo") is now
    # considered same-topic by any saas-seo/b2b-seo/ai-seo/etc. source.
    src_affinity = set(src_clusters)
    for c in src_clusters:
        src_affinity.update(CLUSTER_AFFINITY.get(c, ()))

    # Apply cluster-aware priority promotion: if the target's cluster is in
    # the source's affinity set, bump to P0 regardless of map priority.
    def effective_priority(anchor, target, prio):
        if not src_affinity:
            return prio
        norm = target.rstrip("/") + "/"
        entry = CONTENT_CLUSTERS.get(norm)
        if not entry:
            return prio
        tgt_clusters = {entry} if isinstance(entry, str) else set(entry)
        if src_affinity & tgt_clusters:
            return "P0"
        return prio

    # Sort link map by (effective priority, longest-first) so P0 > P1 > P2
    # and longer phrases claim their slot before substrings.
    sorted_map = sorted(
        LINK_MAP,
        key=lambda x: (PRIORITY_ORDER.get(effective_priority(x[0], x[1], x[3]), 9), -len(x[0])),
    )

    claimed_char_spans = []      # spans of newly-wrapped phrases
    claimed_para_ranges = []     # paragraphs already used by this run
    already_linked_targets = set()
    replacements = []            # (start, end, repl, anchor, target, priority, word_pos)

    # Don't re-link a target that already has a link anywhere in the body
    for m in re.finditer(r"\[[^\]]+\]\((/[^\)]+)\)", body):
        already_linked_targets.add(m.group(1).rstrip("/") + "/")

    for anchor, target, case_sensitive, priority in sorted_map:
        norm_target = target.rstrip("/") + "/"
        if norm_target in already_linked_targets:
            continue
        # Self-link suppression — never link a page to itself
        if norm_target in self_paths:
            continue
        # Routing gate — is this src→dst flow allowed at all?
        dst = classify_target(target)
        flow = ALLOWED_FLOWS.get((source_type, dst))
        if not flow:
            continue
        # Compare and alternative links are handled by the new-sentence bridge
        # pass below — they get CTA-style inserts rather than inline wraps.
        if dst in ("compare", "alternative"):
            continue
        flags = 0 if case_sensitive else re.IGNORECASE
        pat = re.compile(r"\b" + re.escape(anchor) + r"\b", flags)
        for m in pat.finditer(body):
            s, e = m.start(), m.end()
            if overlaps(s, e, protected):     continue
            if overlaps(s, e, claimed_char_spans): continue
            if skip_faq and overlaps(s, e, excluded_sections): continue
            # Listicle "after the 5th entry" check (rules 6/7)
            if flow == "after_5th":
                if fifth_offset is None or s < fifth_offset:
                    continue
            # R5a — past the configured word floor
            wpos = word_at(word_index, s)
            if wpos < word_gate:
                continue
            # R5d — paragraph not already used this run
            pr = find_paragraph(par_ranges, s)
            if pr and any(pr == cpr for cpr in claimed_para_ranges):
                continue
            # Wrap it. Log the effective priority (P0 if same-cluster bumped).
            phrase = m.group(0)
            eff_prio = effective_priority(anchor, target, priority)
            replacements.append((s, e, f"[{phrase}]({target})", phrase, target, eff_prio, wpos))
            claimed_char_spans.append((s, e))
            if pr: claimed_para_ranges.append(pr)
            already_linked_targets.add(norm_target)
            break

    # ---- Bridge inserts (new-sentence mode) for compare + alternative targets ----
    # Each adds a brand-new CTA paragraph nudging readers to the destination.
    bridge_inserts = []  # (insert_offset, sentence_text, target, anchor_display, priority, dest_type)
    bridge_idx = 0
    for anchor, target, _cs, priority in LINK_MAP:
        dst = classify_target(target)
        if dst not in ("compare", "alternative"):
            continue
        norm = target.rstrip("/") + "/"
        if norm in already_linked_targets:
            continue
        if norm in self_paths:  # self-link suppression
            continue
        flow = ALLOWED_FLOWS.get((source_type, dst))
        if not flow:
            continue

        # Resolve competitor name from URL
        if dst == "compare":
            slug, competitor = parse_competitor_from_compare_url(target)
            anchor_display = f"PipeRocket vs {competitor}" if competitor else None
        else:  # alternative
            slug, competitor = parse_competitor_from_alternative_url(target)
            anchor_display = f"{competitor} alternatives" if competitor else None
        if not competitor:
            continue

        # Find an anchor location in the source body.
        # Both listicles AND alternative pages use the same `### N. AgencyName`
        # card structure, so the same section-locator works for both. Insertion
        # goes at the END of the matching agency section (just before the next
        # numbered card or following heading), matching the listicle behavior.
        loc = find_listicle_agency_section(body, competitor)
        if not loc:
            # Fall back to first-mention paragraph if the page doesn't use the
            # numbered card pattern (rare on alt pages, common on free-form prose)
            loc = find_alternative_agency_block(body, competitor)
            if not loc:
                continue
            _, insert_at = loc
        else:
            section_start, section_end = loc
            # Rules 6/7 — after-5th gate (only applies to flows tagged "after_5th")
            if flow == "after_5th":
                if fifth_offset is None or section_start < fifth_offset:
                    continue
            insert_at = section_end
            while insert_at > section_start and body[insert_at - 1] in " \t\r\n":
                insert_at -= 1

        sentence = render_bridge_sentence(bridge_idx, competitor, slug, dest_type=dst)
        bridge_inserts.append((insert_at, sentence, target, anchor_display, priority, dst))
        already_linked_targets.add(norm)
        bridge_idx += 1

    if not replacements and not bridge_inserts:
        return content, [], None

    # Apply existing-phrase wraps right-to-left so earlier offsets stay valid.
    replacements.sort(key=lambda x: x[0], reverse=True)
    chars = list(body)
    log = []
    for s, e, repl, anchor, target, prio, wpos in replacements:
        chars[s:e] = list(repl)
        log.append({
            "anchor": anchor, "target": target, "priority": prio,
            "word_pos": wpos, "method": "existing_phrase",
        })
    new_body = "".join(chars)

    # Apply bridge inserts. Each is a brand-new paragraph between blank lines.
    # Apply right-to-left (descending offsets) so earlier offsets stay valid.
    for insert_at, sentence, target, anchor_display, prio, _dst in sorted(
        bridge_inserts, key=lambda x: -x[0]
    ):
        eff = effective_priority(anchor_display, target, prio)
        wpos_index = build_word_index(new_body, get_protected_spans(new_body))
        wpos = word_at(wpos_index, insert_at)
        insertion = f"\n\n{sentence}\n\n"
        new_body = new_body[:insert_at] + insertion + new_body[insert_at:]
        log.append({
            "anchor": anchor_display, "target": target, "priority": eff,
            "word_pos": wpos, "method": "new_sentence",
        })

    return fm + new_body, log, None


def collect_files(types):
    """Return list of (filepath, type_name, word_gate) for every content file
    in the requested types."""
    out = []
    for tname in types:
        cfg = CONTENT_TYPES[tname]
        d = CONTENT_DIR / cfg["dir"]
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name == "_index.md":
                continue
            out.append((f, tname, cfg["word_gate"]))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    p.add_argument("--slug", help="process only this slug (omit .md), across all types")
    p.add_argument("--type", choices=list(CONTENT_TYPES.keys()) + ["all"], default="all",
                   help="content type to process (default: all)")
    p.add_argument("--skip-faq", action="store_true",
                   help="enable R5b/R6a section skip (off by default per 2026-06-02 user override)")
    args = p.parse_args()

    types = list(CONTENT_TYPES.keys()) if args.type == "all" else [args.type]
    entries = collect_files(types)
    if args.slug:
        entries = [e for e in entries if e[0].stem == args.slug]
        if not entries:
            print(f"no file matches --slug {args.slug} in types {types}", file=sys.stderr)
            sys.exit(1)

    type_word_gates = ", ".join(f"{t}=w{CONTENT_TYPES[t]['word_gate']}" for t in types)
    print(f"{'APPLYING' if args.apply else 'DRY RUN'} — {len(entries)} files"
          f" ({type_word_gates})"
          f"{' [skip-faq ON]' if args.skip_faq else ''}")
    print("=" * 70)

    totals_by_type = {t: {"files": 0, "links": 0} for t in types}
    grand_files = 0
    grand_links = 0
    for f, tname, wgate in entries:
        new_content, log, err = process_file(f, skip_faq=args.skip_faq, word_gate=wgate,
                                             source_type=tname)
        if err:
            print(f"  SKIP [{tname}] {f.name}: {err}")
            continue
        if not log:
            continue
        totals_by_type[tname]["files"] += 1
        totals_by_type[tname]["links"] += len(log)
        grand_files += 1
        grand_links += len(log)
        print(f"\n[{tname}] {f.name} ({len(log)} link{'s' if len(log)!=1 else ''}):")
        for entry in log:
            print(f"  [{entry['priority']}] {entry['anchor']!r:35s} → {entry['target']} (w{entry['word_pos']})")
        if args.apply:
            f.write_text(new_content, encoding="utf-8")

    print("\n" + "=" * 70)
    for t in types:
        s = totals_by_type[t]
        print(f"  {t:12s}: {s['links']:>4} links across {s['files']:>3} files")
    print("-" * 70)
    print(f"  {'TOTAL':12s}: {grand_links:>4} links across {grand_files:>3} files"
          f"{'  (written)' if args.apply else '  (DRY RUN)'}")


if __name__ == "__main__":
    main()
