"""
Render the complete Content-Map SEO Audit as a branded PDF.

Consumes:
  audit/content_map_audit.json   (deterministic extractor output)
  audit/_judgment.json           (verified LLM judgments)

Writes:
  audit/PipeRocket-Content-Map-SEO-Audit.pdf

Sections: cover, table of contents, methodology, executive summary,
10 dimension sections (crawlability, titles, descriptions, headings, schema,
internal linking, anchor mismatches, keyword targeting, cannibalization,
keyword frequency), prioritized recommendations, and a per-page appendix
covering ALL pages.
"""

import html
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (BaseDocTemplate, Frame, NextPageTemplate, PageBreak,
                                Paragraph, Spacer, Table, TableStyle, PageTemplate)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from audit_content_map import load_redirects, resolve, norm_path

RMAP, STRAY_REDIRECTS, BROKEN_REDIRECTS = load_redirects()


def redirect_pair(page, competitor):
    """True if competitor is a redirect source or resolves to the same final URL
    as page (legacy/duplicate URL → not real cannibalization)."""
    return (competitor in RMAP
            or resolve(norm_path(competitor), RMAP) == resolve(norm_path(page), RMAP))

# Embed real TrueType fonts so the PDF renders in every viewer (the base-14
# Helvetica/Courier are not embedded and fail in some rasterizers).
_F = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("Body", _F + "Arial.ttf"))
pdfmetrics.registerFont(TTFont("Body-Bold", _F + "Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body-Italic", _F + "Arial Italic.ttf"))
pdfmetrics.registerFont(TTFont("Body-BoldItalic", _F + "Arial Bold Italic.ttf"))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                              italic="Body-Italic", boldItalic="Body-BoldItalic")
pdfmetrics.registerFont(TTFont("Mono", _F + "Courier New.ttf"))
pdfmetrics.registerFont(TTFont("Mono-Bold", _F + "Courier New Bold.ttf"))
pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono-Bold")

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "audit"
OUT = AUDIT / "PipeRocket-Content-Map-SEO-Audit.pdf"
SNAPSHOT = "qp_rollup_2026-06-08.json"
GSC_ROWS = ROOT / "credentials" / "gsc_output" / "qp_2026-06-08.json"
# Off-page profile (Semrush, owner-supplied 2026-06-12) — not computable from the repo.
SEMRUSH_AS = 20
SEMRUSH_RD = 133
SEMRUSH_RD_QUALITY = "~30–70"


def gsc_aggregate():
    """Brand vs non-brand performance + position distribution from the raw
    query-page rows — the evidence behind the ranking diagnosis."""
    rows = json.loads(GSC_ROWS.read_text())["rows"]

    def is_brand(q):
        q = q.lower()
        return "piperocket" in q or "pipe rocket" in q

    def wpos(rs):
        ti = sum(r["impressions"] for r in rs)
        return (sum(r["position"] * r["impressions"] for r in rs) / ti) if ti else 0
    brand = [r for r in rows if is_brand(r["query"])]
    non = [r for r in rows if not is_brand(r["query"])]
    buckets = {"1–3": 0, "4–10": 0, "11–20": 0, "21–50": 0, "51–100": 0}
    for r in rows:
        p = r["position"]
        b = ("1–3" if p <= 3 else "4–10" if p <= 10 else "11–20" if p <= 20
             else "21–50" if p <= 50 else "51–100")
        buckets[b] += r["impressions"]
    tot_i = sum(r["impressions"] for r in rows)
    return {
        "brand": {"rows": len(brand), "clicks": sum(r["clicks"] for r in brand), "pos": wpos(brand)},
        "non": {"rows": len(non), "clicks": sum(r["clicks"] for r in non), "pos": wpos(non)},
        "buckets": buckets, "tot_impr": tot_i,
        "tot_clicks": sum(r["clicks"] for r in rows),
    }
ARTICLE = {"blog", "glossary", "list", "compare", "alternative", "case-study"}

# ---- brand palette ----
ACCENT = colors.HexColor("#0BA6E2")
NAVY = colors.HexColor("#0B2440")
INK = colors.HexColor("#1A2430")
MUTE = colors.HexColor("#5B6B7A")
LIGHT = colors.HexColor("#F1F8FC")
BORDER = colors.HexColor("#CFE0EC")
RED = colors.HexColor("#C0392B")
AMBER = colors.HexColor("#D9870B")
GREEN = colors.HexColor("#2E9E5B")
GREY = colors.HexColor("#8595A3")

PAGE_W, PAGE_H = letter
LM = RM = 54
TM = 64
BM = 54
FRAME_W = PAGE_W - LM - RM

# ---- styles ----
ss = getSampleStyleSheet()
S = {}
S["h1"] = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Body-Bold",
                         fontSize=17, textColor=NAVY, spaceBefore=10, spaceAfter=8, leading=21)
S["h2"] = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Body-Bold",
                         fontSize=12.5, textColor=ACCENT, spaceBefore=12, spaceAfter=5, leading=16)
S["body"] = ParagraphStyle("body", parent=ss["Normal"], fontName="Body",
                           fontSize=9.5, textColor=INK, leading=13.5, spaceAfter=6)
S["small"] = ParagraphStyle("small", parent=S["body"], fontSize=8, leading=11, textColor=MUTE)
S["cell"] = ParagraphStyle("cell", fontName="Body", fontSize=7.2, textColor=INK, leading=9)
S["cellb"] = ParagraphStyle("cellb", parent=S["cell"], fontName="Body-Bold")
S["cellh"] = ParagraphStyle("cellh", parent=S["cell"], fontName="Body-Bold",
                            textColor=colors.white, fontSize=7.4)
S["code"] = ParagraphStyle("code", parent=S["cell"], fontName="Mono", fontSize=7)
S["appurl"] = ParagraphStyle("appurl", fontName="Body-Bold", fontSize=9.5,
                             textColor=colors.white, leading=12)
S["appkv"] = ParagraphStyle("appkv", fontName="Body", fontSize=7.6, textColor=INK, leading=10.5)
S["appfind"] = ParagraphStyle("appfind", fontName="Body", fontSize=7.6, textColor=RED, leading=10.5)
S["cover_t"] = ParagraphStyle("cover_t", fontName="Body-Bold", fontSize=30,
                              textColor=NAVY, leading=34, alignment=TA_LEFT)
S["cover_s"] = ParagraphStyle("cover_s", fontName="Body", fontSize=13,
                              textColor=ACCENT, leading=18)
S["cover_m"] = ParagraphStyle("cover_m", fontName="Body", fontSize=10, textColor=MUTE, leading=15)
S["toc1"] = ParagraphStyle("toc1", fontName="Body-Bold", fontSize=10.5, textColor=NAVY,
                           leftIndent=0, spaceBefore=6, leading=15)
S["toc2"] = ParagraphStyle("toc2", fontName="Body", fontSize=9.5, textColor=INK,
                           leftIndent=16, spaceBefore=2, leading=13)


def esc(s):
    return html.escape(str(s if s is not None else ""))


def P(text, style="cell"):
    return Paragraph(esc(text), S[style])


def sev_color(s):
    return {"high": RED, "medium": AMBER, "low": GREY}.get(str(s).lower(), INK)


# ---- TOC-aware doc ----
class AuditDoc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if not hasattr(flowable, "style"):
            return
        name = flowable.style.name
        txt = flowable.getPlainText()
        if name == "h1":
            self.notify("TOCEntry", (0, txt, self.page))
        elif name == "h2":
            self.notify("TOCEntry", (1, txt, self.page))


def header_footer(canvas, doc):
    canvas.saveState()
    # top accent rule
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(LM, PAGE_H - 44, PAGE_W - RM, PAGE_H - 44)
    canvas.setFont("Body", 7.5)
    canvas.setFillColor(MUTE)
    canvas.drawString(LM, PAGE_H - 40, "PipeRocket Digital — Content-Map SEO Audit")
    canvas.drawRightString(PAGE_W - RM, PAGE_H - 40, SNAPSHOT)
    # footer
    canvas.line(LM, 40, PAGE_W - RM, 40)
    canvas.drawString(LM, 30, "Confidential — internal SEO audit")
    canvas.drawRightString(PAGE_W - RM, 30, f"Page {doc.page}")
    canvas.restoreState()


def cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 200, PAGE_W, 200, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 206, PAGE_W, 6, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Body-Bold", 13)
    canvas.drawString(LM, PAGE_H - 70, "PipeRocket Digital")
    canvas.setFont("Body", 10)
    canvas.setFillColor(colors.HexColor("#9FD8F2"))
    canvas.drawString(LM, PAGE_H - 88, "Technical SEO · Content Map")
    canvas.restoreState()


# ---------------- table builder ----------------

def styled_table(header, rows, col_widths, body_styles=None, zebra=True):
    body_styles = body_styles or ["cell"] * len(header)
    data = [[Paragraph(esc(h), S["cellh"]) for h in header]]
    for r in rows:
        data.append([c if isinstance(c, Paragraph) else Paragraph(esc(c), S[body_styles[i]])
                     for i, c in enumerate(r)])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER),
        ("LINEAFTER", (0, 0), (-2, -1), 0.4, BORDER),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
    ]
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(cmds))
    return t


def callout(text, color=ACCENT):
    t = Table([[Paragraph(text, S["body"])]], colWidths=[FRAME_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LINEBEFORE", (0, 0), (0, -1), 3, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


# ---------------- data ----------------

def load():
    audit = json.loads((AUDIT / "content_map_audit.json").read_text())["pages"]
    judg = json.loads((AUDIT / "_judgment.json").read_text()) if (AUDIT / "_judgment.json").exists() else []
    anchors, keywords, cannib = defaultdict(list), defaultdict(list), defaultdict(list)
    for c in judg:
        if not c or not c.get("judgment"):
            continue
        j = c["judgment"]
        ver = c.get("verified", {}) or {}
        van = {(x["page"], x["anchor"], x["href"]): x for x in ver.get("anchor_issues", [])}
        vcan = {(x["page"], x["competitor"]): x for x in ver.get("cannibalization", [])}
        for a in j.get("anchor_issues", []):
            v = van.get((a["page"], a["anchor"], a["href"]))
            a = dict(a); a["confirmed"] = v["confirmed"] if v else None
            # drop suggestions to link to a redirected URL (stale better_target)
            if a.get("better_target") and a["better_target"] in RMAP:
                continue
            anchors[a["page"]].append(a)
        for k in j.get("keyword_issues", []):
            keywords[k["page"]].append(k)
        for x in j.get("cannibalization", []):
            # redirect-aware: skip legacy/duplicate competitors that 301 away
            if redirect_pair(x["page"], x["competitor"]):
                continue
            v = vcan.get((x["page"], x["competitor"]))
            x = dict(x); x["confirmed"] = v["confirmed"] if v else None
            cannib[x["page"]].append(x)
    return audit, anchors, keywords, cannib


# ---------------- build ----------------

def build():
    audit, anchors, keywords, cannib = load()
    kw = [p for p in audit if p["keyword_target"]]
    story = []

    # cover page content (drawn area handled by onPage=cover)
    story.append(Spacer(1, 150))
    story.append(Paragraph("Content-Map<br/>SEO Audit", S["cover_t"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Full-site technical &amp; on-page audit driven by the content map", S["cover_s"]))
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"Scope: all {len(audit)} pages in <b>data/content_map.yml</b> "
        f"({len(kw)} keyword-target).<br/>"
        f"GSC snapshot: {SNAPSHOT}.<br/>"
        f"Generated: {date.today().isoformat()}.", S["cover_m"]))
    story.append(Spacer(1, 30))
    story.append(callout(
        "<b>Method.</b> Ten dimensions extracted deterministically from the rendered "
        "site, markdown source, and Google Search Console; three subjective dimensions "
        "(anchor mismatches, keyword targeting, cannibalization) judged by an "
        "AI agent panel and adversarially verified before inclusion."))
    story.append(NextPageTemplate("main"))
    story.append(PageBreak())

    # TOC
    story.append(Paragraph("Contents", S["h1"]))
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"], S["toc2"]]
    story.append(toc)
    story.append(PageBreak())

    # ---- Methodology ----
    story.append(Paragraph("Methodology", S["h1"]))
    story.append(Paragraph(
        "This audit treats <b>data/content_map.yml</b> as the source of truth for what each "
        "page is supposed to target. Every page is then measured on ten dimensions:", S["body"]))
    method_rows = [
        ["1. Internal links", "Count + full anchor list of in-content editorial links (markdown body)."],
        ["2. External links", "Count + list of outbound links."],
        ["3. Anchor check", "Internal anchors whose text is more/less specific than the destination page's target keyword (e.g. an “early-stage startups” anchor pointing at the generic hub)."],
        ["4. Title", "Title tag text + length."],
        ["5. Description", "Meta description text + length."],
        ["6. Headings", "H1 count (rendered) + H2 outline (markdown)."],
        ["7. Schema", "JSON-LD @types emitted by the page."],
        ["8. Keyword frequency", "Exact + stemmed-family occurrences of the primary keyword in the body."],
        ["9. Cannibalization", "Other pages drawing GSC impressions for this page's primary query."],
        ["10. Crawlability", "Indexability: noindex, canonical (self/cross), sitemap inclusion, redirect aliases."],
    ]
    story.append(styled_table(["Dimension", "What it measures"], method_rows, [120, FRAME_W - 120]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Dimensions 1–2 and 4–10 are computed deterministically. Dimensions 3, 8-targeting and "
        "9-severity require judgment: a per-cluster AI agent assessed them, then a second "
        "adversarial agent attempted to refute each finding. Only findings that survived "
        "verification are reported as confirmed.", S["small"]))
    story.append(PageBreak())

    # ---- Executive summary ----
    story.append(Paragraph("Executive summary", S["h1"]))
    n_title = sum(1 for p in audit if p["title_len"] > 60)
    n_desc = sum(1 for p in audit if p["desc_len"] > 160 or (p["rendered"] and 0 < p["desc_len"] < 70))
    n_h1 = sum(1 for p in audit if p["rendered"] and not p["is_alias"] and p["h1_count"] != 1)
    n_schema = sum(1 for p in audit if p["schema_issues"])
    n_idx = sum(1 for p in kw if not p["indexable"])
    n_orphan = sum(1 for p in kw if p["inbound_count"] == 0)
    n_almost = sum(1 for p in kw if p["inbound_count"] == 1)
    n_poor_in = sum(1 for p in kw if p["inbound_count"] <= 2)
    conf_anch = sum(1 for v in anchors.values() for a in v if a.get("confirmed"))
    conf_can = sum(1 for v in cannib.values() for x in v if x.get("confirmed"))
    kw_iss = sum(len(v) for v in keywords.values())

    def status(n, good=0):
        return "OK" if n <= good else "REVIEW"

    rows = [
        ["Pages audited", f"{len(audit)} ({len(kw)} keyword-target)", ""],
        ["Crawlability (not indexable)", str(n_idx), status(n_idx)],
        ["Title tags > 60 chars", str(n_title), status(n_title)],
        ["Meta description > 160 / < 70", str(n_desc), status(n_desc)],
        ["H1 ≠ 1", str(n_h1), status(n_h1)],
        ["Pages with schema issues", str(n_schema), status(n_schema)],
        ["Orphan pages (0 inbound)", str(n_orphan), status(n_orphan)],
        ["Almost-orphan (1 inbound)", str(n_almost), status(n_almost)],
        ["Poor inbound (≤2)", str(n_poor_in), status(n_poor_in)],
        ["Confirmed anchor mismatches", str(conf_anch), status(conf_anch)],
        ["Keyword-targeting issues", str(kw_iss), status(kw_iss)],
        ["Confirmed cannibalization pairs", str(conf_can), status(conf_can)],
    ]
    trows = []
    for label, val, st in rows:
        stp = Paragraph(f'<font color="{"#2E9E5B" if st=="OK" else ("#C0392B" if st=="REVIEW" else "#5B6B7A")}"><b>{st}</b></font>', S["cell"])
        trows.append([Paragraph(esc(label), S["cellb"]), P(val), stp])
    story.append(styled_table(["Dimension", "Count", "Status"], trows, [300, 120, FRAME_W - 420]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Headline findings", S["h2"]))
    story.append(callout(
        "<b>1. Systemic anchor mismatch (27 pages).</b> Every glossary “Also read” link uses the "
        "anchor <i>“best SaaS SEO agencies for early-stage startups”</i> but points to the generic "
        "<b>/list/best-saas-seo-agencies/</b> hub — while the dedicated "
        "<b>/list/best-saas-seo-agencies-for-startups/</b> exists. One repoint fixes all 27.", RED))
    story.append(Spacer(1, 6))
    story.append(callout(
        "<b>2. Compare pages target zero-demand strings.</b> Pages like "
        "<b>/compare/piperocket-digital-vs-klientboost/</b> target branded “X vs Y” terms that "
        "capture no impressions; the real GSC demand is competitor-review queries "
        "(“klientboost reviews / pricing”). Retarget to proven demand.", AMBER))
    story.append(Spacer(1, 6))
    story.append(callout(
        "<b>3. Fifteen confirmed cannibalization pairs.</b> Including near-duplicate listicles "
        "(best-saas-marketing-agencies-2026 ↔ best-saas-growth-marketing-agencies) and "
        "split SaaS-SEO blogs. Merge / canonical / differentiate as noted in §9.", AMBER))
    story.append(PageBreak())

    # ---- Conclusion / goal validation (separate section; per-page detail untouched) ----
    add_conclusion(story, audit, kw)

    # ---- Dimension sections ----
    add_crawl(story, kw)
    add_titles(story, audit)
    add_desc(story, audit)
    add_headings(story, audit)
    add_schema(story, audit)
    add_linking(story, audit, kw)
    add_anchor(story, anchors)
    add_keyword(story, keywords)
    add_cannib(story, cannib)
    add_freq(story, kw)
    add_recommendations(story, conf_anch, kw_iss, conf_can, n_title, n_desc, n_schema, n_orphan)

    # ---- Appendix ----
    story.append(PageBreak())
    story.append(Paragraph("Appendix — per-page detail (all pages)", S["h1"]))
    story.append(Paragraph(
        "Every page in the content map, with its target, metadata, link inventory, "
        "GSC performance, and any confirmed findings.", S["small"]))
    for p in audit:
        add_page_block(story, p, anchors, keywords, cannib)

    # ---- doc templates ----
    cover_tpl = PageTemplate(id="cover", frames=[Frame(LM, BM, FRAME_W, PAGE_H - TM - BM, id="cf")], onPage=cover)
    main_tpl = PageTemplate(id="main", frames=[Frame(LM, BM, FRAME_W, PAGE_H - TM - BM, id="mf")], onPage=header_footer)
    doc = AuditDoc(str(OUT), pagesize=letter, leftMargin=LM, rightMargin=RM,
                   topMargin=TM, bottomMargin=BM, title="PipeRocket Content-Map SEO Audit",
                   author="PipeRocket Digital")
    doc.addPageTemplates([cover_tpl, main_tpl])
    doc.multiBuild(story)
    print(f"Wrote {OUT}")


# ---------------- sections ----------------

def add_conclusion(story, audit, kw):
    g = gsc_aggregate()
    story.append(Paragraph("Conclusion — why the site isn't ranking (goal validation)", S["h1"]))
    story.append(Paragraph(
        "This audit was commissioned because the site has published consistently since ~November yet "
        "non-brand content does not rank. The per-page sections that follow are <b>hygiene</b> — real, "
        "worth fixing, but <b>not</b> the reason nothing ranks. The actual bottleneck is below.", S["body"]))

    story.append(Paragraph("The decisive split: brand vs non-brand", S["h2"]))
    b, n = g["brand"], g["non"]
    story.append(styled_table(
        ["Query type", "Query-rows", "Clicks", "Impr-weighted avg position"],
        [["Branded (“piperocket…”)", str(b["rows"]), str(b["clicks"]), f"{b['pos']:.1f}  (page 1)"],
         ["Non-brand (the whole content program)", str(n["rows"]), str(n["clicks"]), f"{n['pos']:.1f}  (page 5)"]],
        [220, 70, 60, FRAME_W - 350], body_styles=["cell", "cell", "cellb", "cellb"]))
    pct = round(b["clicks"] / max(1, g["tot_clicks"]) * 100)
    story.append(Paragraph(
        f"<b>{pct}% of all clicks come from people already searching the brand name.</b> Every non-brand "
        f"commercial/informational term — the entire purpose of the content — averages position "
        f"{n['pos']:.0f} and produced {n['clicks']} clicks in 6 weeks despite {g['tot_impr']:,} impressions. "
        "Google indexes the content and shows it for the right queries, then ranks it on page 5.", S["body"]))

    story.append(Paragraph("Where impressions actually sit", S["h2"]))
    bk = g["buckets"]; ti = g["tot_impr"]
    story.append(styled_table(["Position bucket", "Impressions", "Share"],
                              [[k, f"{v:,}", f"{v/ti*100:.0f}%"] for k, v in bk.items()],
                              [FRAME_W - 200, 120, 80]))

    story.append(Paragraph("The cause: authority deficit + targeting above weight class", S["h2"]))
    story.append(callout(
        f"<b>Authority, not on-page.</b> Semrush Authority Score <b>{SEMRUSH_AS}</b>, ~{SEMRUSH_RD} referring "
        f"domains ({SEMRUSH_RD_QUALITY} genuinely good). The SERPs the program targets — “best b2b seo "
        "agency”, “enter­prise seo agency”, “saas marketing agency” — are owned by AS 50–80 sites with "
        "hundreds-to-thousands of referring domains. An AS-20 site cannot rank there regardless of page "
        "quality. The branded rankings (pos "
        f"{b['pos']:.1f}) prove Google knows the brand — it just doesn't trust the domain for non-brand terms yet.", RED))
    story.append(Spacer(1, 4))
    story.append(callout(
        "<b>Not the migration.</b> The site never ranked well for non-brand terms — pre- or post-migration. "
        "The WP→Hugo move (~Apr 2026) only adds minor friction (5 broken redirects → 404, see §6). "
        "<b>Not indexing</b> either — 283 pages indexed, shown for the right queries.", AMBER))
    story.append(Spacer(1, 4))
    story.append(callout(
        "<b>Trend confirms it.</b> Avg position crept 33→29 over the window but impressions fell ~21% and "
        "CTR is stuck at 0.3% — not a healthy authority-building ramp. Publishing more content will not move this.", AMBER))

    story.append(Paragraph("What actually moves rankings (in priority order)", S["h2"]))
    story.append(styled_table(["#", "Lever", "Why"], [
        ["1", "Backlinks / digital PR — referring domains ~50 → 150+", "The bottleneck. Original data studies (you have a stats page), founder-led/HARO, write-for-us, partnerships."],
        ["2", "Target within weight class", "Pursue keywords whose page-1 competitors are AS ≤25–30 (long-tail, segment-specific, BOFU niche) using the content-map intent/funnel/cluster lens. Win those first, then climb."],
        ["3", "Consolidate topical authority", "A weak domain spread across 240 pages (saas-seo + saas-ppc + 15 verticals + tools + glossary) signals shallow everywhere. Dominate ONE cluster first."],
        ["4", "Stop equity leaks", "Fix the 5 broken redirects → real targets; fix orphaned money pages. Free, but won't move rankings alone."],
    ], [22, 200, FRAME_W - 222], body_styles=["cellb", "cellb", "cell"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Bottom line:</b> the content and the pages are not the problem. The bottleneck is off-page "
        "authority and over-ambitious keyword targeting. Fix authority + targeting; treat the per-page "
        "findings below as hygiene.", S["body"]))
    story.append(PageBreak())


def add_crawl(story, kw):
    story.append(Paragraph("1. Crawlability", S["h1"]))
    bad = [p for p in kw if not p["indexable"]]
    if not bad:
        story.append(callout("All keyword-target pages are indexable: no <b>noindex</b>, "
                             "self-referencing canonical, present in the sitemap, no redirect alias. "
                             "✅ No action.", GREEN))
    else:
        rows = [[p["url"], str(p["noindex"]), str(p["in_sitemap"]), str(p["canonical_self"]), str(p["is_alias"])] for p in bad]
        story.append(styled_table(["Page", "noindex", "in sitemap", "self-canonical", "alias"],
                                  rows, [220, 60, 70, 80, FRAME_W - 430]))
    story.append(PageBreak())


def add_titles(story, audit):
    story.append(Paragraph("2. Title tags", S["h1"]))
    rows = [[p["url"], str(p["title_len"]), p["title"]] for p in audit
            if p["title_len"] > 60 or (p["rendered"] and p["title_len"] < 15)]
    story.append(Paragraph(f"{len(rows)} titles outside the 15–60 character window "
                          "(SERP truncation risk).", S["body"]))
    if rows:
        story.append(styled_table(["Page", "Len", "Title"], rows, [170, 30, FRAME_W - 200]))
    story.append(PageBreak())


def add_desc(story, audit):
    story.append(Paragraph("3. Meta descriptions", S["h1"]))
    rows = [[p["url"], str(p["desc_len"]),
             ("too long" if p["desc_len"] > 160 else ("too short" if p["desc_len"] < 70 else "missing"))]
            for p in audit if p["desc_len"] > 160 or (p["rendered"] and 0 < p["desc_len"] < 70)
            or (p["rendered"] and p["desc_len"] == 0 and not p["is_alias"])]
    story.append(Paragraph(f"{len(rows)} meta descriptions outside the 70–160 character window.", S["body"]))
    if rows:
        story.append(styled_table(["Page", "Len", "Issue"], rows, [330, 50, FRAME_W - 380]))
    story.append(PageBreak())


def add_headings(story, audit):
    story.append(Paragraph("4. Heading tags", S["h1"]))
    rows = [[p["url"], str(p["h1_count"]), str(p["h2_count"])] for p in audit
            if p["rendered"] and not p["is_alias"] and p["h1_count"] != 1]
    story.append(Paragraph("Every page should have exactly one H1. Pages failing that:", S["body"]))
    if rows:
        story.append(styled_table(["Page", "H1", "H2"], rows, [330, 60, FRAME_W - 390]))
    else:
        story.append(callout("Every rendered page has exactly one H1. ✅", GREEN))
    story.append(PageBreak())


def add_schema(story, audit):
    story.append(Paragraph("5. Schema (correctness &amp; usability)", S["h1"]))
    flagged = [p for p in audit if p["schema_issues"]]
    story.append(Paragraph(
        f"Every page's JSON-LD was parsed and validated against schema.org + Google rich-result "
        f"requirements (required fields, ISO dates, usable image, author E-E-A-T link, expected "
        f"types per page type). <b>{len(flagged)}</b> pages have at least one schema issue.", S["body"]))
    # issue-type frequency
    freq = defaultdict(int)
    for p in audit:
        for s in p["schema_issues"]:
            freq[s.split("(")[0].strip().rstrip(":").strip()] += 1
    story.append(Paragraph("Issue frequency (pages affected):", S["h2"]))
    story.append(styled_table(["Schema issue", "Pages"],
                              [[k, str(v)] for k, v in sorted(freq.items(), key=lambda x: -x[1])],
                              [FRAME_W - 70, 70]))
    story.append(Paragraph("Most impactful:", S["h2"]))
    story.append(callout(
        "<b>106 Article pages use the fallback logo SVG as their schema image.</b> Google won't use "
        "a logo SVG for article rich results — set <b>featuredImage</b> in frontmatter to the page's "
        "cover so the Article/OG image is unique and usable.", AMBER))
    story.append(Spacer(1, 4))
    story.append(callout(
        "<b>11 /compare/ pages emit no Article and no BreadcrumbList</b> (the “compare” section is "
        "missing from the template's article-schema list). They also miss the breadcrumb rich result. "
        "Add “compare” to the $isArticle set in <b>partials/head-meta.html</b>.", RED))
    story.append(Spacer(1, 4))
    story.append(callout(
        "<b>11 /alternative/ pages emit no ItemList</b> — the ItemList extractor only fires for the "
        "/list/ section, so ranked “alternatives” pages lose “best X” / carousel eligibility.", AMBER))
    # per-page issue table (article-type + any with issues)
    story.append(Paragraph("Pages with schema issues:", S["h2"]))
    rows = [[p["url"], p["type"], "; ".join(p["schema_issues"])] for p in flagged]
    story.append(styled_table(["Page", "Type", "Issues"], rows, [150, 55, FRAME_W - 205],
                              body_styles=["code", "cell", "cell"]))
    story.append(PageBreak())


def add_linking(story, audit, kw):
    story.append(Paragraph("6. Internal linking (link graph)", S["h1"]))
    tot_int = sum(p["internal_link_count"] for p in audit)
    tot_ext = sum(p["external_link_count"] for p in audit)
    story.append(Paragraph(
        f"In-content editorial links only (markdown body; navigation, directory grids and CTAs are "
        f"excluded — they don't pass topical equity). Across all pages: <b>{tot_int}</b> internal and "
        f"<b>{tot_ext}</b> external links. Inbound/outbound are redirect-resolved. "
        "“Orphan” = no in-content link from any other page points to it.", S["body"]))

    orphans = [p for p in kw if p["inbound_count"] == 0]
    almost = [p for p in kw if p["inbound_count"] == 1]
    poor_in = [p for p in kw if 2 <= p["inbound_count"] <= 2]
    poor_out = [p for p in kw if p["body_word_count"] > 600 and p["outbound_count"] < 2]
    both = [p for p in kw if p["inbound_count"] <= 2 and p["body_word_count"] > 600 and p["outbound_count"] < 2]

    story.append(styled_table(["Link-equity bucket", "Pages"], [
        ["Orphans (0 inbound)", str(len(orphans))],
        ["Almost-orphans (1 inbound)", str(len(almost))],
        ["Poor inbound (exactly 2)", str(len(poor_in))],
        ["Poor outbound (≥600w body, <2 outbound)", str(len(poor_out))],
        ["Both poor (≤2 in & <2 out)", str(len(both))],
    ], [FRAME_W - 70, 70]))

    def grp(title, items, color=AMBER):
        story.append(Paragraph(title, S["h2"]))
        if not items:
            story.append(callout("None. ✅", GREEN)); return
        rows = [[p["url"], p["type"], str(p["inbound_count"]), str(p["outbound_count"]), str(p["body_word_count"])]
                for p in sorted(items, key=lambda x: (x["type"], -x["body_word_count"]))]
        story.append(styled_table(["Page", "Type", "In", "Out", "Words"], rows,
                                  [250, 70, 35, 35, FRAME_W - 390], body_styles=["code", "cell", "cell", "cell", "cell"]))

    grp(f"Orphans — 0 in-content inbound links ({len(orphans)})", orphans, RED)
    grp(f"Almost-orphans — 1 inbound link ({len(almost)})", almost)
    grp(f"Poor outbound — long body, &lt;2 internal targets ({len(poor_out)})", poor_out)

    # redirect hygiene (real bugs surfaced by redirect-awareness)
    story.append(Paragraph(f"Broken redirects — active 301 → a 404 target ({len(BROKEN_REDIRECTS)})", S["h2"]))
    story.append(Paragraph(
        "Legacy URLs (several have live GSC impressions / inbound equity) that 301 to a slug that "
        "doesn't exist — so the equity lands on a <b>404</b>. Repoint each to the correct live page.", S["small"]))
    if BROKEN_REDIRECTS:
        story.append(styled_table(["Redirect source", "→ 404 target"],
                                  [[s, t] for s, t in BROKEN_REDIRECTS],
                                  [FRAME_W / 2, FRAME_W / 2], body_styles=["code", "code"]))
    else:
        story.append(callout("No broken redirects. ✅", GREEN))
    story.append(Paragraph(f"Stray redirect rules — non-firing 301 on a live page ({len(STRAY_REDIRECTS)})", S["h2"]))
    story.append(Paragraph(
        "A live page has a non-forced 301 in _redirects. Netlify serves the file and skips the rule, "
        "so it's dead config — but it's a latent trap (e.g. /blogs/optimize-saas-landing-pages-for-seo/ "
        "points at a doubled-slug 404). Remove these rules.", S["small"]))
    if STRAY_REDIRECTS:
        story.append(styled_table(["Live page", "Dead rule → target"],
                                  [[s, t] for s, t in STRAY_REDIRECTS],
                                  [FRAME_W / 2, FRAME_W / 2], body_styles=["code", "code"]))
    story.append(PageBreak())


def add_anchor(story, anchors):
    story.append(Paragraph("7. Anchor-text mismatches (verified)", S["h1"]))
    rows = []
    for page, items in anchors.items():
        for a in items:
            if a.get("confirmed"):
                rows.append([page, a["anchor"], a["href"], a["better_target"] or "—", a["why"]])
    story.append(Paragraph(
        f"{len(rows)} internal links where the anchor points to a less-specific or wrong destination "
        "when a better page exists. Adversarially verified. The dominant pattern is the "
        "“early-stage startups” glossary anchor (see headline finding #1).", S["body"]))
    if rows:
        story.append(styled_table(["Page", "Anchor", "Currently →", "Should →", "Why"],
                                  rows, [95, 90, 95, 95, FRAME_W - 375],
                                  body_styles=["code", "cell", "code", "code", "cell"]))
    story.append(PageBreak())


def add_keyword(story, keywords):
    story.append(Paragraph("8. Keyword targeting", S["h1"]))
    rows = []
    for page, items in keywords.items():
        for k in items:
            rows.append([page, k["problem"].replace("_", " "), k["detail"], k["suggestion"]])
    story.append(Paragraph(
        f"{len(rows)} pages where the editorial primary doesn't match the page's content or its "
        "actual GSC demand (multiple primaries, doubtful secondaries, or primary mismatch).", S["body"]))
    if rows:
        story.append(styled_table(["Page", "Problem", "Detail", "Suggestion"],
                                  rows, [95, 70, FRAME_W - 405, 240],
                                  body_styles=["code", "cellb", "cell", "cell"]))
    story.append(PageBreak())


def add_cannib(story, cannib):
    story.append(Paragraph("9. Cannibalization (verified real)", S["h1"]))
    rows = []
    for page, items in cannib.items():
        for x in items:
            if x.get("confirmed"):
                rows.append([page, x["competitor"], x["severity"].upper(), x["recommended_action"], x["why"]])
    story.append(Paragraph(
        f"{len(rows)} confirmed page pairs competing for the same primary keyword in GSC. "
        "Verified by an adversarial pass, then <b>redirect-filtered</b>: competitors that 301 to the "
        "page (legacy WordPress URLs, the best-geo-agency→best-geo-agencies and "
        "top-b2b-ppc→best-affordable-b2b-ppc consolidations) are excluded as already-resolved.", S["body"]))
    if rows:
        story.append(styled_table(["Page", "Competing page", "Sev.", "Action", "Why"],
                                  rows, [95, 95, 38, 62, FRAME_W - 290],
                                  body_styles=["code", "code", "cellb", "cellb", "cell"]))
    else:
        story.append(callout("No confirmed live cannibalization after redirect-filtering. ✅", GREEN))
    story.append(PageBreak())


def add_freq(story, kw):
    story.append(Paragraph("10. Primary-keyword frequency", S["h1"]))
    story.append(Paragraph(
        "How often the primary keyword (and its morphological family — e.g. agency/agencies) appears "
        "in the body. Priority order: <b>landing pages first</b> (the money pages must own their term), "
        "<b>then listicles</b>, then everything else. A long page where the primary barely appears is "
        "under-optimised.", S["body"]))

    def freq_table(title, pages, note=""):
        story.append(Paragraph(title, S["h2"]))
        if note:
            story.append(Paragraph(note, S["small"]))
        if not pages:
            story.append(callout("None in this group. ✅", GREEN)); return
        rows = [[p["url"], str(p.get("rendered_word_count", p["body_word_count"])),
                 str(p["primary_freq_exact"]), str(p["primary_freq_family"]), p["primary"]]
                for p in sorted(pages, key=lambda x: x["primary_freq_family"])]
        story.append(styled_table(["Page", "Words", "Exact", "Family", "Primary"], rows,
                                  [165, 45, 40, 45, FRAME_W - 295],
                                  body_styles=["code", "cell", "cell", "cell", "cell"]))

    # 1) LANDING — highest priority. Flag any with weak primary density.
    landing = [p for p in kw if p["type"] == "landing" and p["primary"]]
    land_weak = [p for p in landing if p["primary_freq_family"] < 3]
    freq_table(f"Landing pages — primary density below 3 ({len(land_weak)} of {len(landing)})",
               land_weak, "Money pages should mention their exact target keyword several times. Sorted by frequency (lowest first).")

    # 2) LISTICLES
    lists = [p for p in kw if p["type"] == "list"]
    list_weak = [p for p in lists if p["primary_freq_family"] < 3]
    freq_table(f"Listicles — primary density below 3 ({len(list_weak)} of {len(lists)})", list_weak)

    # 3) OTHERS — only flag clearly under-optimised long pages
    others = [p for p in kw if p["type"] not in ("landing", "list")]
    other_weak = [p for p in others if p["body_word_count"] > 800 and p["primary_freq_family"] < 2]
    freq_table(f"Other pages — long body but &lt;2 primary mentions ({len(other_weak)})", other_weak)
    story.append(PageBreak())


def add_recommendations(story, conf_anch, kw_iss, conf_can, n_title, n_desc, n_schema, n_orphan):
    story.append(Paragraph("Prioritized recommendations", S["h1"]))
    recs = [
        ["P0", "Add “compare” to the $isArticle set in partials/head-meta.html — 11 /compare/ pages emit no Article or BreadcrumbList schema (§5).", "1 template"],
        ["P0", "Set featuredImage on the ~106 Article pages using the fallback logo SVG, so the schema/OG image is a usable cover (§5).", "Batch / template"],
        ["P0", "Repoint the 27 “early-stage startups” glossary anchors to /list/best-saas-seo-agencies-for-startups/ (§7).", "1 batch edit"],
        ["P1", f"Resolve the {conf_can} confirmed (live, redirect-filtered) cannibalization pairs — merge near-duplicate listicles, differentiate split blogs (§9).", "Per §9"],
        ["P1", f"Add in-content inbound links to the {n_orphan} orphan pages (esp. listicles & landing pages) from topically-related blogs/glossary (§6).", "Per §6"],
        ["P1", "Retarget /compare/ pages from zero-demand “X vs Y” strings to proven competitor-review demand (§8).", "Per §8"],
        ["P1", f"Fix the {kw_iss} keyword-targeting mismatches — one canonical owner per head term (§8).", "Per §8"],
        ["P2", "Lift primary-keyword density on landing pages first, then listicles, that fall below 3 mentions (§10).", "Per §10"],
        ["P2", f"Trim {n_desc} over/under-length meta descriptions and {n_title} long titles into the SERP window (§2–3).", "Cosmetic"],
        ["P2", "Update the 7 in-content links that point to redirected URLs to their final targets (§6); fix the H1 on /glossary/what-is-crawling/ (§4).", "Few files"],
    ]
    trows = []
    for pri, txt, eff in recs:
        col = RED if pri == "P0" else (AMBER if pri == "P1" else GREY)
        trows.append([Paragraph(f'<font color="{col.hexval().replace("0x","#")}"><b>{pri}</b></font>', S["cell"]),
                      Paragraph(esc(txt), S["cell"]), P(eff)])
    story.append(styled_table(["Pri", "Recommendation", "Effort"], trows, [36, FRAME_W - 116, 80]))
    story.append(PageBreak())


def add_page_block(story, p, anchors, keywords, cannib):
    # url bar
    bar = Table([[Paragraph(esc(p["url"]), S["appurl"])]], colWidths=[FRAME_W])
    bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT),
                             ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 3),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    bar.keepWithNext = True
    story.append(Spacer(1, 6))
    story.append(bar)
    meta = (f"<b>type</b> {esc(p['type'])} &nbsp; <b>funnel</b> {esc(p['funnel'])} &nbsp; "
            f"<b>intent</b> {esc(p['intent'])} &nbsp; <b>cluster</b> {esc(p['cluster'] or '—')} &nbsp; "
            f"<b>indexable</b> {esc(p['indexable'])}")
    if p["keyword_target"]:
        meta += (f"<br/><b>primary</b> “{esc(p['primary'])}” &nbsp; freq {p['primary_freq_exact']} exact / "
                 f"{p['primary_freq_family']} family &nbsp; <b>body</b> {p['body_word_count']}w")
        if p["secondary"]:
            meta += f"<br/><b>secondary</b> {esc(', '.join(p['secondary']))}"
    meta += (f"<br/><b>title</b> ({p['title_len']}) {esc(p['title'])}"
             f"<br/><b>desc</b> ({p['desc_len']}) {esc(p['description'])}"
             f"<br/><b>H1</b> {p['h1_count']} &nbsp; <b>H2</b> {p['h2_count']} &nbsp; "
             f"<b>inbound</b> {p['inbound_count']} &nbsp; <b>outbound</b> {p['outbound_count']}"
             f"<br/><b>schema</b> {esc(', '.join(p['schema_types']) or 'none')}"
             f"<br/><b>canonical</b> {esc(p['canonical'])} (self={p['canonical_self']}) &nbsp; "
             f"<b>in sitemap</b> {p['in_sitemap']}"
             + (f" &nbsp; <b>redirected→</b> {esc(p['redirect_target'])}" if p['redirected'] else ""))
    story.append(Paragraph(meta, S["appkv"]))
    if p["schema_issues"]:
        story.append(Paragraph(f"<b>schema issues:</b> {esc('; '.join(p['schema_issues']))}", S["appfind"]))
    # links
    if p["internal_links"]:
        il = "; ".join(f"“{esc(l['anchor'])}” → {esc(l['href'])}" for l in p["internal_links"])
        story.append(Paragraph(f"<b>internal links ({p['internal_link_count']}):</b> {il}", S["appkv"]))
    else:
        story.append(Paragraph(f"<b>internal links (0)</b>", S["appkv"]))
    if p["external_links"]:
        el = "; ".join(f"“{esc(l['anchor'])}” → {esc(l['href'])}" for l in p["external_links"])
        story.append(Paragraph(f"<b>external links ({p['external_link_count']}):</b> {el}", S["appkv"]))
    if p["gsc_top_queries"]:
        q = "; ".join(f"{esc(x['query'])} (p{x['position']}, {x['impressions']}i)" for x in p["gsc_top_queries"][:6])
        story.append(Paragraph(f"<b>GSC top queries:</b> {q}", S["appkv"]))
    if p["cannibalization"]:
        c = "; ".join(f"{esc(o['page'])} ({o['impressions']}i, p{o['position']})" for o in p["cannibalization"][:6])
        story.append(Paragraph(f"<b>GSC cannibalization candidates:</b> {c}", S["appkv"]))
    # findings
    for a in anchors.get(p["url"], []):
        if a.get("confirmed"):
            story.append(Paragraph(f"⚠ anchor: “{esc(a['anchor'])}” → {esc(a['href'])} should be "
                                   f"{esc(a['better_target'] or '—')} — {esc(a['why'])}", S["appfind"]))
    for k in keywords.get(p["url"], []):
        story.append(Paragraph(f"⚠ keyword [{esc(k['problem'])}]: {esc(k['suggestion'])}", S["appfind"]))
    for x in cannib.get(p["url"], []):
        if x.get("confirmed"):
            story.append(Paragraph(f"⚠ cannibalization vs {esc(x['competitor'])} "
                                   f"({esc(x['severity'])}, {esc(x['recommended_action'])})", S["appfind"]))


if __name__ == "__main__":
    build()
