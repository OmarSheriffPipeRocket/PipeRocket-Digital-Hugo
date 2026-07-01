#!/usr/bin/env python3
"""
Full-site interlink report — every internal markdown link across content/,
with anchor text, resolved both as an edge list and as per-page inbound +
outbound rollups.

Unlike scripts/interlinking_audit.py (rendered HTML, chrome-stripped,
orphan-focused) this reads content/*.md directly so it captures every
editorial `[anchor](target)` link exactly as authored, including on
data-driven pages (compare/) where the link lives inside a YAML string field.

Writes:
  audit/interlink_full_report_edges.csv     — one row per link
  audit/interlink_full_report_by_page.csv   — one row per page (in+out rollup)
  audit/interlink_full_report_summary.csv   — rollup by page type

Usage: python3 scripts/interlink_full_report.py
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
AUDIT_DIR = ROOT / "audit"
AUDIT_DIR.mkdir(exist_ok=True)

# directory name -> page type label
DIR_TYPE = {
    "blogs": "blog",
    "list": "listicle",
    "glossary": "glossary",
    "compare": "compare",
    "alternative": "alternative",
    "case-study": "case-study",
    "author": "author",
    "tools": "tool",
    "vs": "vs",
}

LINK_RE = re.compile(r'(!?)\[([^\]]+)\]\((/[^\s)]+)(?:\s+"[^"]*")?\)')
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
TITLE_RE = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.M)
URL_FM_RE = re.compile(r'^url:\s*"?([^"\n]+?)"?\s*$', re.M)


def norm(url: str) -> str:
    url = url.split("#")[0].split("?")[0].strip()
    if not url:
        return "/"
    if not url.startswith("/"):
        url = "/" + url
    return url.rstrip("/") + "/" if url != "/" else "/"


def collect_pages():
    """Return {url: {"type":..., "title":..., "path": Path, "is_index": bool}}"""
    pages = {}
    files = sorted(CONTENT_DIR.rglob("*.md"))
    for f in files:
        rel = f.relative_to(CONTENT_DIR)
        raw = f.read_text(encoding="utf-8", errors="ignore")
        fm_m = FRONTMATTER_RE.match(raw)
        fm = fm_m.group(1) if fm_m else ""
        title_m = TITLE_RE.search(fm)
        title = title_m.group(1) if title_m else f.stem

        url_m = URL_FM_RE.search(fm)
        is_index = f.name == "_index.md"
        top_dir = rel.parts[0] if len(rel.parts) > 1 else None

        if url_m:
            url = norm(url_m.group(1))
        elif is_index:
            if len(rel.parts) == 1:  # content/_index.md
                url = "/"
            else:
                url = norm("/" + top_dir + "/")
        elif top_dir in DIR_TYPE:
            url = norm(f"/{top_dir}/{f.stem}/")
        else:
            # root-level service/landing page: content/foo.md -> /foo/
            url = norm(f"/{f.stem}/")

        if is_index:
            ptype = "home" if url == "/" else "section"
        elif top_dir in DIR_TYPE:
            ptype = DIR_TYPE[top_dir]
        else:
            ptype = "service"

        pages[url] = {"type": ptype, "title": title, "path": f, "raw": raw}
    return pages


def line_context(raw: str, start: int, end: int) -> str:
    """Return the full source line containing raw[start:end], with every
    non-image markdown link on that line unwrapped to plain anchor text so
    it reads as normal prose instead of raw markdown."""
    line_start = raw.rfind("\n", 0, start) + 1
    line_end = raw.find("\n", end)
    if line_end == -1:
        line_end = len(raw)
    line = raw[line_start:line_end].strip()
    line = LINK_RE.sub(lambda m: m.group(2) if m.group(1) != "!" else "", line)
    return line


def extract_links(raw: str):
    """Yield (anchor_text, target_url, context_line) for every non-image
    internal link."""
    for m in LINK_RE.finditer(raw):
        bang, anchor, target = m.group(1), m.group(2), m.group(3)
        if bang == "!":
            continue
        if target.startswith("//"):
            continue  # protocol-relative external
        yield anchor.strip(), norm(target), line_context(raw, m.start(), m.end())


def main():
    pages = collect_pages()
    url_set = set(pages.keys())

    edges = []  # (src_url, src_type, src_title, anchor, context, tgt_url, tgt_type, tgt_title, resolved)
    for url, meta in pages.items():
        for anchor, target, context in extract_links(meta["raw"]):
            if target == url:
                continue  # self-link
            tgt_meta = pages.get(target)
            resolved = tgt_meta is not None
            edges.append((
                url, meta["type"], meta["title"],
                anchor, context, target,
                tgt_meta["type"] if resolved else "UNRESOLVED",
                tgt_meta["title"] if resolved else "",
                resolved,
            ))

    # de-dupe exact duplicate edges (same source/anchor/target appearing twice)
    seen = set()
    dedup_edges = []
    for e in edges:
        key = (e[0], e[3], e[5])
        if key in seen:
            continue
        seen.add(key)
        dedup_edges.append(e)
    edges = dedup_edges

    # ---- edges CSV ----
    with open(AUDIT_DIR / "interlink_full_report_edges.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Source URL", "Source Type", "Source Title", "Anchor Text", "Anchor Text Context",
                    "Target URL", "Target Type", "Target Title", "Resolved"])
        for e in sorted(edges, key=lambda x: (x[0], x[5])):
            w.writerow([e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], "Yes" if e[8] else "No (broken/external path)"])

    # ---- per-page rollup ----
    outbound = defaultdict(list)  # url -> [(anchor, target, tgt_type, resolved)]
    inbound = defaultdict(list)   # url -> [(anchor, source, src_type)]
    for src, styp, stitle, anchor, context, tgt, ttyp, ttitle, resolved in edges:
        outbound[src].append((anchor, tgt, ttyp, resolved))
        if resolved:
            inbound[tgt].append((anchor, src, styp))

    with open(AUDIT_DIR / "interlink_full_report_by_page.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Page URL", "Type", "Title", "Inbound Count", "Outbound Count",
                    "Orphan (0 inbound)", "Inbound Links (anchor <- source)",
                    "Outbound Links (anchor -> target)"])
        for url in sorted(pages.keys()):
            meta = pages[url]
            ins = inbound.get(url, [])
            outs = outbound.get(url, [])
            in_str = "\n".join(f'"{a}" <- {s}' for a, s, _t in sorted(ins, key=lambda x: x[1]))
            out_str = "\n".join(
                f'"{a}" -> {t}' + ("" if r else "  [UNRESOLVED]")
                for a, t, _tt, r in sorted(outs, key=lambda x: x[1])
            )
            w.writerow([url, meta["type"], meta["title"], len(ins), len(outs),
                        "YES" if len(ins) == 0 and meta["type"] not in ("home", "section") else "",
                        in_str, out_str])

    # ---- summary by type ----
    bytype = defaultdict(lambda: {"pages": 0, "orphans": 0, "in_total": 0, "out_total": 0})
    for url, meta in pages.items():
        t = meta["type"]
        bytype[t]["pages"] += 1
        bytype[t]["in_total"] += len(inbound.get(url, []))
        bytype[t]["out_total"] += len(outbound.get(url, []))
        if len(inbound.get(url, [])) == 0 and t not in ("home", "section"):
            bytype[t]["orphans"] += 1

    with open(AUDIT_DIR / "interlink_full_report_summary.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Type", "Pages", "Total Inbound Links", "Avg Inbound", "Total Outbound Links", "Avg Outbound", "Orphans (0 inbound)"])
        for t, d in sorted(bytype.items(), key=lambda x: -x[1]["pages"]):
            avg_in = d["in_total"] / d["pages"] if d["pages"] else 0
            avg_out = d["out_total"] / d["pages"] if d["pages"] else 0
            w.writerow([t, d["pages"], d["in_total"], f"{avg_in:.1f}", d["out_total"], f"{avg_out:.1f}", d["orphans"]])

    unresolved = [e for e in edges if not e[8]]
    print(f"Pages scanned      : {len(pages)}")
    print(f"Edges (unique)     : {len(edges)}")
    print(f"  resolved         : {len(edges) - len(unresolved)}")
    print(f"  unresolved       : {len(unresolved)}")
    print(f"Wrote audit/interlink_full_report_edges.csv, _by_page.csv, _summary.csv")


if __name__ == "__main__":
    main()
