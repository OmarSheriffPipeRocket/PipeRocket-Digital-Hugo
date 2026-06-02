#!/usr/bin/env python3
"""
Build content clusters from the canonical CSV source.

Source of truth: clusters_source.csv at repo root. Columns:
    clusters,title,content_type,slug,url

A single value per row in the `clusters` column (strict 1:1 file→cluster).

Output: scripts/clusters_generated.py with:
    CONTENT_CLUSTERS   — {url: (cluster,)}
    CLUSTER_INDEX      — {cluster: {content_type: [urls]}}
    CLUSTER_AFFINITY   — {cluster: {cluster}} (self-only by default)

Run after editing clusters_source.csv:
    python3 scripts/build_clusters.py
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_CSV = ROOT / "clusters_source.csv"
OUT_FILE = Path(__file__).resolve().parent / "clusters_generated.py"


def load():
    content_clusters = {}
    cluster_index = defaultdict(lambda: defaultdict(list))
    type_dir = {
        "Blog": "blogs", "Listicle": "list", "Glossary": "glossary",
        "Comparison": "compare", "Alternative": "alternative",
    }
    with SOURCE_CSV.open(encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            cluster = row["clusters"].strip()
            url = row["url"].strip()
            ctype = row["content_type"].strip()
            if not cluster or not url:
                continue
            content_clusters[url] = (cluster,)
            d = type_dir.get(ctype, ctype.lower())
            cluster_index[cluster][d].append(url)
    return content_clusters, cluster_index


def emit(content_clusters, cluster_index):
    clusters_present = sorted(cluster_index.keys())
    # Default affinity: every cluster matches itself only (no cross-cluster
    # promotion). Edit this block by hand if you want generic glossary
    # clusters to bump to P0 from specific source clusters.
    affinity = {c: {c} for c in clusters_present}

    lines = [
        "#!/usr/bin/env python3",
        '"""Auto-generated from clusters_source.csv. Do not hand-edit — re-run',
        "scripts/build_clusters.py after changing the CSV.",
        '"""',
        "",
        f"# {len(content_clusters)} files across {len(clusters_present)} clusters",
        "",
        "CONTENT_CLUSTERS = {",
    ]
    for url in sorted(content_clusters.keys()):
        cluster = content_clusters[url][0]
        lines.append(f'    "{url}": ("{cluster}",),')
    lines.append("}")
    lines.append("")
    lines.append("CLUSTER_INDEX = {")
    for c in clusters_present:
        lines.append(f'    "{c}": {{')
        for ctype in sorted(cluster_index[c].keys()):
            urls = sorted(cluster_index[c][ctype])
            lines.append(f'        "{ctype}": [')
            for u in urls:
                lines.append(f'            "{u}",')
            lines.append("        ],")
        lines.append("    },")
    lines.append("}")
    lines.append("")
    lines.append("# CLUSTER_AFFINITY: cluster → set of clusters considered same-topic")
    lines.append("# for P0 promotion. Self-only by default (no cross-cluster matching).")
    lines.append("CLUSTER_AFFINITY = {")
    for c in clusters_present:
        members = sorted(affinity[c])
        formatted = "{" + ", ".join(f'"{m}"' for m in members) + "}"
        lines.append(f'    "{c}": {formatted},')
    lines.append("}")
    OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if not SOURCE_CSV.exists():
        raise SystemExit(f"missing {SOURCE_CSV} — provide the canonical CSV first")
    cc, ci = load()
    emit(cc, ci)
    print(f"Read {SOURCE_CSV}")
    print(f"Wrote {OUT_FILE}")
    print(f"\n{len(cc)} files into {len(ci)} clusters:")
    for c in sorted(ci.keys(), key=lambda k: -sum(len(v) for v in ci[k].values())):
        total = sum(len(v) for v in ci[c].values())
        by_type = ", ".join(f"{t}={len(v)}" for t, v in sorted(ci[c].items()))
        print(f"  {c:28s} {total:>3} files  ({by_type})")


if __name__ == "__main__":
    main()
