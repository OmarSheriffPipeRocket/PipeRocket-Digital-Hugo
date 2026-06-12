"""
Build ONE master per-page CSV for the content-map SEO audit (handoff to Kim).

277 rows (one per page). All per-page dimensions plus the verified findings,
link inventory, and GSC detail flattened into delimited cells. Reads:
  audit/content_map_audit.json   (deterministic extractor output)
  audit/_judgment.json           (verified LLM findings — redirect-filtered)
  data/content_map.yml           (GSC alignment block per page)

Writes: audit/content_map_master.csv

Usage: python3 scripts/audit_master_csv.py
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

from audit_content_map import load_redirects, resolve, norm_path, parse_content_map

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "audit"
RMAP, _stray, _broken = load_redirects()


def redirect_pair(page, competitor):
    return (competitor in RMAP
            or resolve(norm_path(competitor), RMAP) == resolve(norm_path(page), RMAP))


def load_judgment():
    """Per-page verified findings (anchor / keyword / cannibalization), redirect-filtered."""
    anchors, keywords, cannib = defaultdict(list), defaultdict(list), defaultdict(list)
    jpath = AUDIT / "_judgment.json"
    if not jpath.exists():
        return anchors, keywords, cannib
    for c in json.loads(jpath.read_text()):
        if not c or not c.get("judgment"):
            continue
        j = c["judgment"]
        ver = c.get("verified", {}) or {}
        van = {(x["page"], x["anchor"], x["href"]): x for x in ver.get("anchor_issues", [])}
        vcan = {(x["page"], x["competitor"]): x for x in ver.get("cannibalization", [])}
        for a in j.get("anchor_issues", []):
            if a.get("better_target") and a["better_target"] in RMAP:
                continue
            v = van.get((a["page"], a["anchor"], a["href"]))
            if v and v.get("confirmed"):
                anchors[a["page"]].append(a)
        for k in j.get("keyword_issues", []):
            keywords[k["page"]].append(k)
        for x in j.get("cannibalization", []):
            if redirect_pair(x["page"], x["competitor"]):
                continue
            v = vcan.get((x["page"], x["competitor"]))
            if v and v.get("confirmed"):
                cannib[x["page"]].append(x)
    return anchors, keywords, cannib


def main():
    pages = json.loads((AUDIT / "content_map_audit.json").read_text())["pages"]
    cmeta = parse_content_map()
    anchors, keywords, cannib = load_judgment()

    cols = [
        # A — identity & taxonomy
        "url", "type", "keyword_target", "primary", "secondary", "intent", "funnel",
        "cluster", "redirected", "redirect_target",
        # B — on-page metadata
        "title", "title_len", "description", "desc_len", "h1_count", "h2_count",
        # C — schema
        "schema_types", "schema_issue_count", "schema_issues",
        # D — content & keyword
        "body_word_count", "rendered_word_count", "primary_freq_exact", "primary_freq_family",
        # E — linking
        "internal_link_count", "external_link_count", "inbound_count", "outbound_count",
        "anchor_flag_count", "internal_links", "external_links", "inbound_pages", "outbound_pages",
        # F — crawlability
        "indexable", "canonical", "canonical_self", "robots", "noindex", "in_sitemap", "is_alias",
        # G — GSC performance
        "gsc_total_impressions", "gsc_top_query", "gsc_top_query_position",
        "gsc_primary_position", "gsc_aligned", "cannibalization_count",
        "gsc_top_queries", "gsc_cannibalization_candidates",
        # H/I — verified findings (flattened)
        "finding_anchor_mismatches", "finding_keyword_targeting", "finding_cannibalization",
    ]

    def links_str(lst):
        return " | ".join(f'"{l["anchor"]}" -> {l["href"]}' for l in lst)

    with (AUDIT / "content_map_master.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for p in pages:
            g = cmeta.get(p["url"], {}).get("gsc", {})
            anch = anchors.get(p["url"], [])
            kw = keywords.get(p["url"], [])
            can = cannib.get(p["url"], [])
            w.writerow([
                p["url"], p["type"], p["keyword_target"], p["primary"],
                "; ".join(p["secondary"]), p["intent"], p["funnel"], p["cluster"] or "",
                p["redirected"], p["redirect_target"],
                p["title"], p["title_len"], p["description"], p["desc_len"],
                p["h1_count"], p["h2_count"],
                "|".join(p["schema_types"]), len(p["schema_issues"]), "; ".join(p["schema_issues"]),
                p["body_word_count"], p["rendered_word_count"], p["primary_freq_exact"],
                p["primary_freq_family"],
                p["internal_link_count"], p["external_link_count"], p["inbound_count"],
                p["outbound_count"], len(p["anchor_flags"]),
                links_str(p["internal_links"]), links_str(p["external_links"]),
                "; ".join(p["inbound_pages"]), "; ".join(p["outbound_pages"]),
                p["indexable"], p["canonical"], p["canonical_self"], p["robots"],
                p["noindex"], p["in_sitemap"], p["is_alias"],
                g.get("total_impressions", ""), g.get("top_query", ""),
                g.get("top_query_position", ""), g.get("primary_position", ""),
                g.get("aligned", ""), len(p["cannibalization"]),
                "; ".join(f"{x['query']} (p{x['position']}, {x['impressions']}i)" for x in p["gsc_top_queries"]),
                "; ".join(f"{o['page']} ({o['impressions']}i, p{o['position']})" for o in p["cannibalization"]),
                " | ".join(f'"{a["anchor"]}" {a["href"]} -> {a["better_target"] or "—"} [{a["why"]}]' for a in anch),
                " | ".join(f'[{k["problem"]}] {k["detail"]} -> {k["suggestion"]}' for k in kw),
                " | ".join(f'{x["competitor"]} ({x["severity"]}/{x["recommended_action"]}) {x["why"]}' for x in can),
            ])
    print(f"Wrote audit/content_map_master.csv  ({len(pages)} rows, {len(cols)} columns)")


if __name__ == "__main__":
    main()
