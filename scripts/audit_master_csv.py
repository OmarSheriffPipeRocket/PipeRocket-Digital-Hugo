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
import re
from collections import defaultdict
from pathlib import Path

from audit_content_map import (load_redirects, resolve, norm_path, parse_content_map,
                               read_html, rendered_text, phrase_counts)


def editorial_secondaries(primary, ptype):
    """Generate editorial secondary keywords = intent-based variants of the
    primary (synonyms, plural/singular, qualifier forms, top↔best). Derived from
    the primary only — NOT from GSC. Returns up to 4, deduped, excluding primary."""
    p = (primary or "").strip().lower()
    if not p:
        return []
    out = []

    def add(s):
        s = re.sub(r"\s+", " ", s or "").strip()
        if s and s != p and s not in out:
            out.append(s)

    if ptype in ("landing", "home"):
        if p.endswith(" agency"):
            base = p[:-len(" agency")]
            add(base + " services"); add(base + " company")
            if not p.startswith("b2b"):
                add("b2b " + p)
            add(base + " firm")
        elif p.endswith(" services"):
            base = p[:-len(" services")]
            add(base + " agency"); add(base + " company"); add("best " + base + " agency")
        else:
            add("best " + p); add(p + " services"); add(p + " company")
    elif ptype == "list":
        if p.startswith("best "):
            rest = p[5:]
            add("top " + rest); add(rest)
            if rest.endswith("agencies"):
                add(rest[:-len("agencies")] + "companies")
            elif rest.endswith("tools"):
                add(rest[:-len("tools")] + "software"); add(rest[:-len("tools")] + "tool")
            elif rest.endswith("companies"):
                add(rest[:-len("companies")] + "agencies")
        else:
            add("best " + p); add("top " + p)
    elif ptype == "alternative":
        base = p[:-len(" alternatives")] if p.endswith(" alternatives") else p
        add(base + " competitors"); add("alternatives to " + base); add("best " + base + " alternatives")
    elif ptype == "compare":
        if " vs " in p:
            a, b = p.split(" vs ", 1)
            add(p + " comparison"); add(b + " vs " + a); add(a + " or " + b)
    elif ptype == "glossary":
        base = re.sub(r"^what is (a |an |the )?", "", p)
        add(base + " meaning"); add(base + " definition"); add("what is " + base); add(base + " explained")
    elif ptype == "tool":
        add("free " + p) if not p.startswith("free") else None
        add(p.replace("calculator", "").strip() + " calculator") if "calculator" in p else add(p + " tool")
        add(p + " online")
    elif ptype == "blog":
        if p.startswith("how to "):
            rest = p[7:]
            add(rest); add(rest + " guide"); add(rest + " best practices")
        else:
            add(p + " guide"); add(p + " strategy"); add(p + " best practices")
    return out[:4]

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "audit"
RMAP, _stray, _broken = load_redirects()


def redirect_pair(page, competitor):
    return (competitor in RMAP
            or resolve(norm_path(competitor), RMAP) == resolve(norm_path(page), RMAP))


def load_judgment():
    """Per-page findings (anchor / keyword / cannibalization), redirect-filtered.

    Prefers the DEEP pass (audit/_judgment_deep.json) — recall-oriented, every
    finding confidence-labeled, no verify filter. Falls back to the conservative
    verified pass (audit/_judgment.json, confirmed-only) when the deep file is
    absent."""
    anchors, keywords, cannib = defaultdict(list), defaultdict(list), defaultdict(list)
    deep = AUDIT / "_judgment_deep.json"
    if deep.exists():
        for c in json.loads(deep.read_text()):
            if not c or not c.get("judgment"):
                continue
            j = c["judgment"]
            for a in j.get("anchor_issues", []):
                if a.get("better_target") and a["better_target"] in RMAP:
                    continue
                anchors[a["page"]].append(a)
            for k in j.get("keyword_issues", []):
                keywords[k["page"]].append(k)
            for x in j.get("cannibalization", []):
                if x.get("verdict") == "benign" or redirect_pair(x["page"], x["competitor"]):
                    continue
                cannib[x["page"]].append(x)
        return anchors, keywords, cannib
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
        # A — identity & taxonomy  (secondary sits right after primary)
        "url", "type", "keyword_target", "primary", "secondary", "intent", "funnel",
        "cluster", "redirected", "redirect_target",
        # B — on-page metadata  (description next to title_len; H1s next to h1_count; H2s next to h2_count)
        "title", "title_len", "description", "desc_len",
        "h1_count", "h1s", "h2_count", "h2s",
        # C — schema
        "schema_types", "schema_issue_count", "schema_issues",
        # D — content & keyword  (secondary_freq replaces primary_freq_family)
        "body_word_count", "rendered_word_count", "primary_freq_exact", "secondary_freq",
        # E — linking  (link lists sit right after their counts)
        "internal_link_count", "internal_links", "external_link_count", "external_links",
        "inbound_count", "inbound_pages", "outbound_count", "outbound_pages", "anchor_flag_count",
        # F — crawlability
        "indexable", "canonical", "canonical_self", "robots", "noindex", "in_sitemap", "is_alias",
        # G — GSC performance  (cannibalization URLs sit right after the count)
        "gsc_total_impressions", "gsc_top_query", "gsc_top_query_position",
        "gsc_primary_position", "gsc_aligned",
        "cannibalization_count", "cannibalization_urls", "gsc_top_queries",
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
            # editorial secondary keywords (generated from the primary) + their
            # frequency on the rendered page — master CSV only, content map untouched.
            sec_kw = editorial_secondaries(p["primary"], p["type"]) if p["keyword_target"] else []
            if sec_kw:
                _, html_text = read_html(p["url"])
                rtext = rendered_text(html_text) if html_text else ""
                sec_freq = "; ".join(f"{s}: {phrase_counts(rtext, s)[0]}" for s in sec_kw)  # exact-phrase count
            else:
                sec_freq = ""
            w.writerow([
                p["url"], p["type"], p["keyword_target"], p["primary"],
                "; ".join(sec_kw), p["intent"], p["funnel"], p["cluster"] or "",
                p["redirected"], p["redirect_target"],
                p["title"], p["title_len"], p["description"], p["desc_len"],
                p["h1_count"], " | ".join(p.get("h1_texts", [])),
                p["h2_count"], " | ".join(p.get("h2_texts", [])),
                "|".join(p["schema_types"]), len(p["schema_issues"]), "; ".join(p["schema_issues"]),
                p["body_word_count"], p["rendered_word_count"], p["primary_freq_exact"], sec_freq,
                p["internal_link_count"], links_str(p["internal_links"]),
                p["external_link_count"], links_str(p["external_links"]),
                p["inbound_count"], "; ".join(p["inbound_pages"]),
                p["outbound_count"], "; ".join(p["outbound_pages"]), len(p["anchor_flags"]),
                p["indexable"], p["canonical"], p["canonical_self"], p["robots"],
                p["noindex"], p["in_sitemap"], p["is_alias"],
                g.get("total_impressions", ""), g.get("top_query", ""),
                g.get("top_query_position", ""), g.get("primary_position", ""), g.get("aligned", ""),
                len(p["cannibalization"]),
                "; ".join(f"{o['page']} ({o['impressions']}i, p{o['position']})" for o in p["cannibalization"]),
                "; ".join(f"{x['query']} (p{x['position']}, {x['impressions']}i)" for x in p["gsc_top_queries"]),
                " | ".join(f'[{a.get("confidence","?")}] "{a["anchor"]}" {a["href"]} -> {a["better_target"] or "—"} ({a["why"]})' for a in anch),
                " | ".join(f'[{k.get("confidence","?")}|{k["problem"]}] {k["detail"]} -> {k["suggestion"]}' for k in kw),
                " | ".join(f'[{x.get("confidence","?")}|{x.get("verdict","?")}/{x["severity"]}/{x["recommended_action"]}] {x["competitor"]} — {x["why"]}' for x in can),
            ])
    print(f"Wrote audit/content_map_master.csv  ({len(pages)} rows, {len(cols)} columns)")


if __name__ == "__main__":
    main()
