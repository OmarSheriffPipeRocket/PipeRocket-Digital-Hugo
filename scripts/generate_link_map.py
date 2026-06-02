#!/usr/bin/env python3
"""
Generate starter LINK_MAP entries from existing Hugo content.

Walks content/blogs/, content/list/, content/compare/, content/alternative/,
and root-level service pages. For each file, extracts slug + title from the
frontmatter and emits one or more anchor-phrase candidates.

Output: a Python module at scripts/link_map_generated.py with a list named
GENERATED_LINK_MAP that can be merged into add_interlinks.LINK_MAP.

Anchor generation per type:
  Blog:      title cleaned of "the", "complete guide", year, ":", "?"
             e.g. "SaaS PPC: A Complete Guide for 2025" → "SaaS PPC"
  Listicle:  title cleaned + "best <topic> agencies" / "top <topic> agencies"
             e.g. "We Ranked The 10 Best SaaS PPC Agencies for 2026"
                  → "best SaaS PPC agencies", "top SaaS PPC agencies"
  Compare:   competitor name after "vs"
             e.g. "PipeRocket Digital vs KlientBoost" → "KlientBoost"
  Alternative: "<agency> alternatives"
             e.g. "KlientBoost Alternatives" → "KlientBoost alternatives"
  Service:   title verbatim
             e.g. "SaaS SEO Agency" → "SaaS SEO Agency"

Priority assigned: P1 (cross-type strong-fit). Reviewer can promote to P0
for cluster matches or demote individual rows. Glossary entries are NOT
generated — those live in the curated LINK_MAP in add_interlinks.py.

Usage:
    python3 scripts/generate_link_map.py
    # then review/edit scripts/link_map_generated.py
"""
import re
import sys
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
OUT_FILE = Path(__file__).resolve().parent / "link_map_generated.py"

# Service pages live at content root (Hugo single-page templates).
SERVICE_FILES = ["saas-seo-agency.md", "saas-ppc.md", "marketing-ops.md"]


def read_frontmatter(filepath: Path):
    """Return (slug, title, url) — best-effort extraction from YAML frontmatter."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return None, None, None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, None, None
    fm = parts[1]
    title = slug = url = None
    for line in fm.splitlines():
        m = re.match(r'\s*(title|slug|url):\s*"?([^"]+?)"?\s*$', line)
        if not m: continue
        key, val = m.group(1), m.group(2)
        if key == "title": title = val
        elif key == "slug": slug = val
        elif key == "url": url = val
    # fall back to filename stem if no slug
    if not slug:
        slug = filepath.stem
    return slug, title, url


# ----- Anchor-phrase generators -----

def clean_blog_anchor(title: str):
    if not title: return []
    t = title
    # strip year and trailing year-suffix
    t = re.sub(r"\b(20\d{2})\b", "", t)
    # strip "complete guide", "the ultimate guide", etc.
    t = re.sub(r":\s*(a\s+)?(complete|ultimate|no[-\s]?nonsense|definitive)\s+guide.*$", "", t, flags=re.I)
    t = re.sub(r":\s*how to.*$", "", t, flags=re.I)
    t = re.sub(r":\s*the .*$", "", t, flags=re.I)
    t = re.sub(r"\?$", "", t)
    t = re.sub(r"\s+", " ", t).strip(" :,-")
    # strip leading "the "
    t = re.sub(r"^the\s+", "", t, flags=re.I)
    return [t] if t else []


def clean_listicle_anchors(title: str, slug: str):
    """Listicles get 2 candidates: 'best X agencies' and 'top X agencies'."""
    out = []
    if not title and not slug: return out
    # Try to extract "<topic> agencies" or "<topic> companies" from title
    if title:
        m = re.search(r"(?:best|top|ranked).*?(\d+\s+)?([A-Z][\w\s\-]+?(?:agencies|companies))",
                       title, flags=re.I)
        topic = None
        if m:
            topic = re.sub(r"\s+(in|for)\s+20\d{2}.*$", "", m.group(2), flags=re.I)
            topic = re.sub(r"^\d+\s+", "", topic).strip()
    else:
        topic = None
    # Fallback: derive from slug like "best-saas-ppc-agencies"
    if not topic and slug:
        s = slug.lower()
        s = re.sub(r"^(best|top|\d+[\-_])+", "", s)
        s = re.sub(r"-(in|for)-20\d{2}$", "", s)
        s = re.sub(r"-\d{4}$", "", s)
        # leave the rest, replace dashes with spaces
        topic = s.replace("-", " ").strip()
        # Title-case keeping acronyms uppercase
        words = []
        ACRONYMS = {"saas","ppc","seo","b2b","crm","ctr","cpa","abm","aeo","geo","llm","ai"}
        for w in topic.split():
            words.append(w.upper() if w in ACRONYMS else w.title())
        topic = " ".join(words)
    if not topic: return out
    out.append(f"best {topic.lower()}")
    out.append(f"top {topic.lower()}")
    # Also a "<topic>" bare anchor (e.g. "SaaS PPC agencies")
    out.append(topic)
    return out


def clean_compare_anchors(slug: str):
    """Compare slugs look like 'piperocket-digital-vs-klientboost'. Extract competitor."""
    if not slug or "vs-" not in slug: return []
    competitor_slug = slug.split("vs-", 1)[1]
    # convert dashes to spaces, capitalize words
    parts = competitor_slug.split("-")
    competitor = " ".join(p.capitalize() for p in parts)
    return [competitor]


def clean_alternative_anchors(slug: str):
    """Alternative slugs like 'klientboost-alternatives' → 'KlientBoost alternatives'."""
    if not slug: return []
    base = slug.replace("-alternatives", "")
    agency = " ".join(p.capitalize() for p in base.split("-"))
    return [f"{agency} alternatives", agency]


def clean_service_anchors(title: str, slug: str):
    if title: return [title]
    return [slug.replace("-", " ").title()] if slug else []


# ----- Walk content & emit -----

def collect_targets():
    targets = []  # list of dicts {anchor, target, case_sensitive, priority, source_type, source_slug, source_title}

    # Blogs
    for f in sorted((CONTENT_DIR / "blogs").glob("*.md")):
        if f.name == "_index.md": continue
        slug, title, _ = read_frontmatter(f)
        if not slug: continue
        target = f"/blogs/{slug}/"
        for anchor in clean_blog_anchor(title):
            targets.append({"anchor": anchor, "target": target, "case_sensitive": False,
                            "priority": "P1", "type": "blog", "src_title": title})

    # Listicles
    for f in sorted((CONTENT_DIR / "list").glob("*.md")):
        if f.name == "_index.md": continue
        slug, title, url = read_frontmatter(f)
        if not slug: continue
        # Listicles often have `url:` overrides — prefer that
        target = url if (url and url.startswith("/list/")) else f"/list/{slug}/"
        if not target.startswith("/list/"):
            target = f"/list/{slug}/"
        for anchor in clean_listicle_anchors(title, slug):
            if not anchor: continue
            targets.append({"anchor": anchor, "target": target, "case_sensitive": False,
                            "priority": "P1", "type": "listicle", "src_title": title})

    # Compare
    for f in sorted((CONTENT_DIR / "compare").glob("*.md")):
        if f.name == "_index.md": continue
        slug, title, _ = read_frontmatter(f)
        if not slug: continue
        target = f"/compare/{slug}/"
        for anchor in clean_compare_anchors(slug):
            targets.append({"anchor": anchor, "target": target, "case_sensitive": False,
                            "priority": "P0", "type": "compare", "src_title": title})

    # Alternative
    for f in sorted((CONTENT_DIR / "alternative").glob("*.md")):
        if f.name == "_index.md": continue
        slug, title, _ = read_frontmatter(f)
        if not slug: continue
        target = f"/alternative/{slug}/"
        for anchor in clean_alternative_anchors(slug):
            targets.append({"anchor": anchor, "target": target, "case_sensitive": False,
                            "priority": "P1", "type": "alternative", "src_title": title})

    # Service pages (root .md files)
    for name in SERVICE_FILES:
        f = CONTENT_DIR / name
        if not f.exists(): continue
        slug, title, url = read_frontmatter(f)
        target = url if url else f"/{f.stem}/"
        for anchor in clean_service_anchors(title, slug):
            targets.append({"anchor": anchor, "target": target, "case_sensitive": False,
                            "priority": "P1", "type": "service", "src_title": title})

    return targets


def dedupe(targets):
    """Drop duplicate (anchor, target) pairs and obviously bad anchors (<3 chars)."""
    seen = set()
    out = []
    for t in targets:
        a = t["anchor"].strip()
        if len(a) < 3: continue
        key = (a.lower(), t["target"])
        if key in seen: continue
        seen.add(key)
        t["anchor"] = a
        out.append(t)
    return out


def emit_python(targets, out_path: Path):
    lines = [
        "#!/usr/bin/env python3",
        '"""Auto-generated LINK_MAP entries (see scripts/generate_link_map.py).',
        "",
        "Merge with hand-curated entries in add_interlinks.py:",
        "    from link_map_generated import GENERATED_LINK_MAP",
        "    LINK_MAP = LINK_MAP + GENERATED_LINK_MAP",
        "",
        'Review/edit before applying — anchor phrases are heuristic.',
        '"""',
        "",
        "# (anchor_phrase, target_url, case_sensitive, priority)",
        "GENERATED_LINK_MAP = [",
    ]
    # Group by type for readability
    by_type = {}
    for t in targets:
        by_type.setdefault(t["type"], []).append(t)
    for tname in ("compare", "alternative", "listicle", "blog", "service"):
        bucket = by_type.get(tname, [])
        if not bucket: continue
        lines.append(f"    # ---- {tname} targets ({len(bucket)} entries) ----")
        for t in bucket:
            anchor = t["anchor"].replace('"', '\\"')
            target = t["target"]
            lines.append(f'    ("{anchor}", "{target}", {t["case_sensitive"]}, "{t["priority"]}"),'
                         f'  # {t["src_title"] or t["target"]}')
        lines.append("")
    lines.append("]")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    targets = collect_targets()
    print(f"Collected {len(targets)} raw target/anchor pairs", file=sys.stderr)
    targets = dedupe(targets)
    print(f"After dedupe: {len(targets)}", file=sys.stderr)

    # summary by type
    counts = {}
    for t in targets:
        counts[t["type"]] = counts.get(t["type"], 0) + 1
    for k, v in counts.items():
        print(f"  {k:12s}: {v}", file=sys.stderr)

    emit_python(targets, OUT_FILE)
    print(f"\nWrote {OUT_FILE}")
    print(f"\nReview, then in add_interlinks.py:")
    print(f"    from link_map_generated import GENERATED_LINK_MAP")
    print(f"    LINK_MAP = LINK_MAP + GENERATED_LINK_MAP")


if __name__ == "__main__":
    main()
