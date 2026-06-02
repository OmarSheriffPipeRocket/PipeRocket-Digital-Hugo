#!/usr/bin/env python3
"""Export the full cluster/topic/type table as Markdown and CSV."""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from clusters_generated import CONTENT_CLUSTERS  # noqa: E402

CONTENT_DIR = ROOT / "content"
OUT_MD = ROOT / "clusters_table.md"
OUT_CSV = ROOT / "clusters_table.csv"

TYPE_LABEL = {
    "blogs": "Blog",
    "list": "Listicle",
    "glossary": "Glossary",
    "compare": "Comparison",
    "alternative": "Alternative",
}


def read_title(filepath: Path):
    text = filepath.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return filepath.stem, filepath.stem
    fm = parts[1]
    title = slug = None
    for line in fm.splitlines():
        m = re.match(r'\s*(title|slug):\s*"?([^"]+?)"?\s*$', line)
        if m:
            if m.group(1) == "title":
                title = m.group(2)
            elif m.group(1) == "slug":
                slug = m.group(2)
    return title or (slug or filepath.stem), slug or filepath.stem


# Map url → (title, type, slug)
url_meta = {}
for d in TYPE_LABEL:
    for f in sorted((CONTENT_DIR / d).glob("*.md")):
        if f.name == "_index.md":
            continue
        title, slug = read_title(f)
        url = f"/{d}/{slug}/"
        url_meta[url] = (title, TYPE_LABEL[d], slug)


# Build one row per file. `clusters` is a comma-separated list when a file
# belongs to multiple clusters (typical for generic glossary entries).
TYPE_RANK = {"Blog": 0, "Listicle": 1, "Glossary": 2, "Comparison": 3, "Alternative": 4}

rows = []  # (primary_cluster, clusters_str, title, content_type, slug, url)
for url, clusters in CONTENT_CLUSTERS.items():
    if isinstance(clusters, str):
        clusters = (clusters,)
    title, ctype, slug = url_meta.get(url, (url, "?", ""))
    clusters_str = ", ".join(sorted(clusters))
    primary = sorted(clusters)[0]  # for grouping/sorting
    rows.append((primary, clusters_str, title, ctype, slug, url))

# Sort by primary cluster, then type, then title
rows.sort(key=lambda r: (r[0], TYPE_RANK.get(r[3], 99), r[2].lower()))

# Markdown
md_lines = [
    "# Cluster / Topic / Content Type — table",
    "",
    f"_{len(rows)} rows (one per file). Files in multiple clusters list them in the Clusters column._",
    "",
    "| Clusters | Topic (Title) | Content Type | Slug |",
    "|---|---|---|---|",
]
for _, clusters_str, title, ctype, slug, _url in rows:
    safe_title = title.replace("|", "\\|")
    md_lines.append(f"| {clusters_str} | {safe_title} | {ctype} | `{slug}` |")

OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

# CSV
with OUT_CSV.open("w", newline="", encoding="utf-8") as fp:
    w = csv.writer(fp)
    w.writerow(["clusters", "title", "content_type", "slug", "url"])
    for _, clusters_str, title, ctype, slug, url in rows:
        w.writerow([clusters_str, title, ctype, slug, url])

print(f"Wrote {OUT_MD}  ({len(rows)} rows — one per file)")
print(f"Wrote {OUT_CSV}")
