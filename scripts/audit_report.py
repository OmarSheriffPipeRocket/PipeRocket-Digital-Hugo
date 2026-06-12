"""
Synthesize the final per-page SEO report from:
  - audit/content_map_audit.json   (deterministic extractor output)
  - audit/_judgment.json           (workflow's verified judgments; optional)

Writes:
  - audit/content_map_seo_report.md   — executive summary + actionable issue
                                         sections (verified findings)
  - audit/content_map_per_page.md     — full per-page detail for ALL pages
                                         (links + anchors, meta, schema, kw freq,
                                          cannibalization, judgment findings)

Usage:
  python3 scripts/audit_report.py
"""

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "audit"
ARTICLE = {"blog", "glossary", "list", "compare", "alternative", "case-study"}


def load():
    audit = json.loads((AUDIT / "content_map_audit.json").read_text())["pages"]
    jpath = AUDIT / "_judgment.json"
    judg = json.loads(jpath.read_text()) if jpath.exists() else []
    return audit, judg


def index_judgment(judg):
    """Build per-page indexes of verified findings."""
    anchors = defaultdict(list)
    keywords = defaultdict(list)
    cannib = defaultdict(list)
    for c in judg:
        if not c or not c.get("judgment"):
            continue
        j = c["judgment"]
        ver = c.get("verified", {}) or {}
        # verified lookups (confirmed flag)
        van = {(x["page"], x["anchor"], x["href"]): x for x in ver.get("anchor_issues", [])}
        vcan = {(x["page"], x["competitor"]): x for x in ver.get("cannibalization", [])}
        for a in j.get("anchor_issues", []):
            v = van.get((a["page"], a["anchor"], a["href"]))
            a = dict(a)
            a["confirmed"] = v["confirmed"] if v else None
            a["verify_reason"] = v.get("verify_reason", "") if v else ""
            anchors[a["page"]].append(a)
        for k in j.get("keyword_issues", []):
            keywords[k["page"]].append(k)
        for x in j.get("cannibalization", []):
            v = vcan.get((x["page"], x["competitor"]))
            x = dict(x)
            x["confirmed"] = v["confirmed"] if v else None
            x["verify_reason"] = v.get("verify_reason", "") if v else ""
            cannib[x["page"]].append(x)
    return anchors, keywords, cannib


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


def write_summary(audit, anchors, keywords, cannib, have_judg):
    kw = [p for p in audit if p["keyword_target"]]
    L = ["# PipeRocket — Content-Map SEO Audit",
         "",
         f"_All {len(audit)} pages in `data/content_map.yml` ({len(kw)} keyword-target). "
         "Deterministic extraction (links, meta, schema, keyword frequency, GSC "
         "cannibalization, crawlability) + " +
         ("LLM judgment, adversarially verified" if have_judg else "judgment layer PENDING") +
         " for anchor mismatches, keyword targeting, and cannibalization severity._",
         ""]

    # ---- executive summary ----
    conf_anch = sum(1 for p in anchors.values() for a in p if a.get("confirmed"))
    conf_can = sum(1 for p in cannib.values() for x in p if x.get("confirmed"))
    kw_iss = sum(len(v) for v in keywords.values())
    L += ["## Executive summary", "",
          md_table(["Dimension", "Signal"], [
              ["Pages audited", f"{len(audit)} ({len(kw)} keyword-target)"],
              ["Title > 60 chars", sum(1 for p in audit if p["title_len"] > 60)],
              ["Meta desc > 160 / < 70", sum(1 for p in audit if p["desc_len"] > 160 or (p['rendered'] and 0 < p["desc_len"] < 70))],
              ["H1 ≠ 1", sum(1 for p in audit if p["rendered"] and not p["is_alias"] and p["h1_count"] != 1)],
              ["Article pages missing schema", sum(1 for p in audit if p["type"] in ARTICLE and "Article" not in p["schema_types"] and "DefinedTerm" not in p["schema_types"])],
              ["Keyword pages not indexable", sum(1 for p in kw if not p["indexable"])],
              ["Thin internal linking (long body, <2 links)", sum(1 for p in kw if p["body_word_count"] > 600 and p["internal_link_count"] < 2)],
              ["Confirmed anchor mismatches", conf_anch],
              ["Keyword-targeting issues", kw_iss],
              ["Confirmed cannibalization pairs", conf_can],
          ]), ""]

    # ---- crawlability ----
    L += ["## 1. Crawlability", ""]
    bad = [p for p in kw if not p["indexable"]]
    if bad:
        L.append(md_table(["Page", "noindex", "in_sitemap", "canonical_self", "alias"],
                          [[p["url"], p["noindex"], p["in_sitemap"], p["canonical_self"], p["is_alias"]] for p in bad]))
    else:
        L.append("All keyword-target pages are indexable (no noindex, self-canonical, in sitemap). ✅")
    L.append("")

    # ---- title ----
    L += ["## 2. Title tags", ""]
    rows = [[p["url"], p["title_len"], p["title"][:70]] for p in audit if p["title_len"] > 60 or (p["rendered"] and p["title_len"] < 15)]
    L.append(md_table(["Page", "Len", "Title"], rows) if rows else "No title-length problems. ✅")
    L.append("")

    # ---- description ----
    L += ["## 3. Meta descriptions", ""]
    rows = [[p["url"], p["desc_len"]] for p in audit
            if p["desc_len"] > 160 or (p["rendered"] and 0 < p["desc_len"] < 70)
            or (p["rendered"] and p["desc_len"] == 0 and not p["is_alias"])]
    L.append(md_table(["Page", "Desc len"], rows) if rows else "No meta-description problems. ✅")
    L.append("")

    # ---- headings ----
    L += ["## 4. Heading tags", ""]
    rows = [[p["url"], p["h1_count"], p["h2_count"]] for p in audit
            if p["rendered"] and not p["is_alias"] and p["h1_count"] != 1]
    L.append("H1 ≠ 1 (should be exactly one):\n\n" + md_table(["Page", "H1", "H2"], rows) if rows else "Every rendered page has exactly one H1. ✅")
    L.append("")

    # ---- schema ----
    L += ["## 5. Schema (JSON-LD)", ""]
    rows = [[p["url"], p["type"], ", ".join(p["schema_types"]) or "NONE"] for p in audit
            if p["type"] in ARTICLE and "Article" not in p["schema_types"] and "DefinedTerm" not in p["schema_types"]]
    L.append("Article-type pages missing Article/DefinedTerm schema:\n\n" + md_table(["Page", "Type", "Schema present"], rows) if rows else "All article-type pages emit Article/DefinedTerm schema. ✅")
    L.append("")

    # ---- internal linking ----
    L += ["## 6. Internal linking", ""]
    thin = [[p["url"], p["body_word_count"], p["internal_link_count"]] for p in kw
            if p["body_word_count"] > 600 and p["internal_link_count"] < 2]
    L.append("Thin internal linking (≥600-word body, <2 in-content internal links):\n\n" + md_table(["Page", "Words", "Internal links"], thin) if thin else "No thin-linking pages. ✅")
    L.append("\n_Per-page link counts + full anchor lists are in `content_map_per_page.md`._\n")

    # ---- anchor mismatches ----
    L += ["## 7. Anchor-text mismatches (verified)", "",
          "_Internal links whose anchor text points to a less-specific or wrong destination when a better page exists. Adversarially verified._", ""]
    rows = []
    for page, items in anchors.items():
        for a in items:
            if a.get("confirmed"):
                rows.append([page, f'"{a["anchor"]}"', a["href"], a["better_target"] or "—", a["why"][:80]])
    L.append(md_table(["Page", "Anchor", "Currently →", "Should →", "Why"], rows) if rows else "No confirmed anchor mismatches." )
    L.append("")

    # ---- keyword targeting ----
    L += ["## 8. Keyword targeting (multiple primary / doubtful secondary)", ""]
    rows = []
    for page, items in keywords.items():
        for k in items:
            rows.append([page, k["problem"], k["detail"][:90], k["suggestion"][:80]])
    L.append(md_table(["Page", "Problem", "Detail", "Suggestion"], rows) if rows else "No keyword-targeting issues flagged.")
    L.append("")

    # ---- cannibalization ----
    L += ["## 9. Cannibalization (verified real)", "",
          "_Pages competing for the same primary keyword in GSC. Confirmed by an adversarial verifier (manual audit + GSC query overlap)._", ""]
    rows = []
    for page, items in cannib.items():
        for x in items:
            if x.get("confirmed"):
                rows.append([page, x["competitor"], x["severity"], x["recommended_action"], x["why"][:80]])
    L.append(md_table(["Page", "Competing page", "Severity", "Action", "Why"], rows) if rows else "No confirmed cannibalization.")
    L.append("\n_All raw GSC cannibalization candidates (incl. unverified) are per-page in `content_map_per_page.md`._\n")

    (AUDIT / "content_map_seo_report.md").write_text("\n".join(L), encoding="utf-8")


def write_per_page(audit, anchors, keywords, cannib):
    L = ["# Per-page SEO detail — all pages", ""]
    for p in audit:
        L.append(f"\n## `{p['url']}`")
        L.append(f"- **type** {p['type']} · **funnel** {p['funnel']} · **intent** {p['intent']} · **cluster** {p['cluster'] or '—'} · **indexable** {p['indexable']}")
        if p["keyword_target"]:
            L.append(f"- **primary** \"{p['primary']}\"  ·  appears {p['primary_freq_exact']}× exact / {p['primary_freq_family']}× family in {p['body_word_count']}w body")
            if p["secondary"]:
                L.append(f"- **secondary** {', '.join(p['secondary'])}")
        L.append(f"- **title** ({p['title_len']}) {p['title']}")
        L.append(f"- **description** ({p['desc_len']}) {p['description']}")
        L.append(f"- **H1** {p['h1_count']} · **H2** {p['h2_count']} · **schema** {', '.join(p['schema_types']) or 'none'}")
        L.append(f"- **canonical** {p['canonical']} (self={p['canonical_self']}) · **robots** {p['robots'] or '—'} · **in_sitemap** {p['in_sitemap']}")
        # internal links
        L.append(f"- **internal links** ({p['internal_link_count']}):")
        for lk in p["internal_links"]:
            L.append(f"    - \"{lk['anchor']}\" → {lk['href']}")
        # external links
        L.append(f"- **external links** ({p['external_link_count']}):")
        for lk in p["external_links"]:
            L.append(f"    - \"{lk['anchor']}\" → {lk['href']}")
        # GSC top queries
        if p["gsc_top_queries"]:
            qs = "; ".join(f"{q['query']} (p{q['position']}, {q['impressions']}i)" for q in p["gsc_top_queries"][:6])
            L.append(f"- **GSC top queries** {qs}")
        # cannibalization candidates (raw)
        if p["cannibalization"]:
            cs = "; ".join(f"{o['page']} ({o['impressions']}i, p{o['position']})" for o in p["cannibalization"][:6])
            L.append(f"- **GSC cannibalization candidates** (same primary query) {cs}")
        # judgment findings
        for a in anchors.get(p["url"], []):
            mark = "✅" if a.get("confirmed") else ("❌unconf" if a.get("confirmed") is False else "·")
            L.append(f"- ⚠️ anchor {mark}: \"{a['anchor']}\" → {a['href']} (better: {a['better_target'] or '—'}; {a['severity']}) — {a['why']}")
        for k in keywords.get(p["url"], []):
            L.append(f"- ⚠️ keyword [{k['problem']}]: {k['detail']} → {k['suggestion']}")
        for x in cannib.get(p["url"], []):
            mark = "✅real" if x.get("confirmed") else ("❌" if x.get("confirmed") is False else x["verdict"])
            L.append(f"- ⚠️ cannibalization {mark} vs {x['competitor']} ({x['severity']}, {x['recommended_action']}) — {x['why']}")
    (AUDIT / "content_map_per_page.md").write_text("\n".join(L), encoding="utf-8")


def main():
    audit, judg = load()
    anchors, keywords, cannib = index_judgment(judg)
    write_summary(audit, anchors, keywords, cannib, bool(judg))
    write_per_page(audit, anchors, keywords, cannib)
    print("Wrote audit/content_map_seo_report.md + audit/content_map_per_page.md"
          + ("" if judg else "  (judgment layer PENDING — re-run after workflow)"))


if __name__ == "__main__":
    main()
