---
name: alternatives-writer
description: Create a new PipeRocket "[Agency] alternatives" page end-to-end — a v3 "Honest Review" listicle in content/alternative/, ranking PipeRocket #2 with full publisher disclosure. Use this skill whenever the user asks to write, create, build, or generate an alternatives page, "X alternatives" listicle, or competitor-alternatives roundup for the PipeRocket site (e.g. "create a Foundation alternatives page", "make 3 alternatives pages"). This skill ORCHESTRATES the existing agents — listicle-researcher → listicle-writer → listicle-accuracy-checker — with the alternatives angle and ranking rules baked in, then handles the cover, screenshot check, and corpus-wide interlinking. It does NOT itself write prose; it drives the pipeline and enforces the gates.
model: sonnet
effort: medium
---

## What this skill does

Builds a complete `content/alternative/<target>-alternatives.md` page — a v3 "Honest Review" listicle framed as "you're leaving competitor X, here's who we'd pick." It is an **orchestrator**: it calls the existing listicle agents with the alternatives framing, enforces the alternatives-specific rules (PipeRocket #2, publisher disclosure, Clutch-first ratings, blocklist), then runs the asset + interlinking steps that the agents don't own.

An alternatives page is structurally identical to a `/list/` listicle. The ONLY differences are the angle, the output directory, and a handful of rules encoded below. There is no separate writer agent — `listicle-writer` does the prose; this skill makes it do the right thing.

## When to use vs. not

- USE for `content/alternative/<slug>.md` pages keyed to a single competitor agency ("X alternatives").
- Do NOT use for `content/list/` "best X agencies" roundups — that's the plain listicle pipeline (PipeRocket ranks #2 there too, but the angle, directory, and disclosure differ).
- Do NOT use for `/compare/` head-to-head pages — those have their own `compare-researcher` / `compare-writer` agents.

## Inputs to collect first

Ask the user only for what's missing:
1. **Target agency** — the competitor being left (e.g. "Foundation Marketing"). Derive the slug as `<target-kebab>-alternatives`.
2. **Author** (`writtenBy`) — apply the channel rule automatically and state your pick; only ask if ambiguous:
   - Target is primarily SEO / AI-SEO / content → **kim**
   - Target is primarily paid / PPC / demand-gen → **praveen**
   - Mixed → either (default to the one matching the strongest competitor's channel)
3. **Roster size** — default ~9–10 agencies. PipeRocket is always one of them, at #2.

Before anything else: `git fetch origin && git pull --ff-only origin main` (the project rule is to pull main before edits).

---

## The pipeline (run in order)

### Step 1 — Research (agent: `listicle-researcher`)
Spawn `listicle-researcher` with the **alternatives angle**. The prompt must include:
- TARGET = the competitor (the "what you're leaving" context — gather its Clutch/FeaturedCustomers rating, founding year, HQ, team size, pricing, named clients, methodology, what buyers say).
- SLUG = `<target>-alternatives`; write dossier to `research/<slug>.md`.
- SEGMENT/ICP = B2B SaaS buyers leaving the target, and *why* (price, single-channel depth, pipeline reporting, execution gap, etc.).
- ROSTER = ~9 alternatives. **PipeRocket Digital MUST be included.** Pull its facts from `data/piperocket.toml` (the single source of truth) — NOT from an existing page, which may have drifted. As of last verification: Chennai, India with US delivery; founded 2023; 30+ team / senior-led pod; clients Storylane/Spendflo/HyperVerge/HyperStart/DevRev/CyberSierra; **Clutch 4.7/5 (13 reviews)**; $3,000/mo; case studies HyperStart/HyperVerge/Storylane. Re-check the live Clutch rating before publish and update `data/piperocket.toml` if it changed.
- For each other agency: Clutch URL+rating+reviews (FeaturedCustomers fallback), homepage, pricing, founding year, HQ, team size, 4–7 named clients, real sourced quotes, a differentiator *vs the target*, and a limitation.
- BLOCKLIST — never feature: Growthspree, Spear Growth, RevvGrowth, Epic Slope Partners, TripleDart.
- Ask it to flag every unverifiable field and note which agencies have `static/images/agencies/<slug>-home.webp`.

For multiple pages, spawn one researcher per target in parallel.

### Step 2 — Write (agent: `listicle-writer`)
Spawn `listicle-writer` pointed at `research/<slug>.md`, output `content/alternative/<slug>.md`. The prompt MUST encode these alternatives deltas (this is the core of the skill):

1. **Format** — match an existing alternatives page exactly (`content/alternative/webfx-alternatives.md` is the canonical template). Frontmatter: `type: "list"`, `layout: "listicle"`, `category: "Alternatives"`, `writtenBy: <author>`, `toc: true`, `date`/`lastmod` = today, `featuredImage: "/images/listicle-covers/<slug>.webp"`.
2. **RANKING RULE (critical)** — **PipeRocket Digital is #2, NEVER #1.** The strongest competitor takes #1. This applies to the intro brand-list sentence, the TL;DR, the at-a-glance table order, and the detailed-comparison card order. (See `feedback_piperocket_ranking_position` in memory.)
3. **Publisher disclosure** — closing editor's note must say PipeRocket is the publisher and ranks *itself at #2* applying the same methodology to every agency, with the top competitor at #1. Never claim #1.
4. **Angle** — intro anchors on the target's gap; every competitor's differentiator is written *relative to the target*, not in a vacuum.
5. **Honesty gates** — only dossier facts; hedge every flagged field ("reported"/"industry-reported"/"as of <month year>"); Rating column is Clutch-first, FeaturedCustomers fallback (label the fallback, and call them "references"/"reference ratings", not "reviews"); flag single-review ratings as non-statistical; no blocklisted agency.
6. **Cross-links** — only to `/compare/` and `/alternative/` pages that actually exist. The writer should `Glob content/compare/ content/alternative/` and link only confirmed targets (do not invent links).
7. **Triptych** — `{{< agency-triptych slug="<slug>" name="<Name>" >}}`; only use slugs whose `static/images/agencies/<slug>-home.webp` exists (Glob to confirm). PipeRocket's slug is `piperocket-digital`.
8. Report final title, metaTitle (≤60 chars), metaDescription (≤155 chars).

### Step 3 — Accuracy check (agent: `listicle-accuracy-checker`)
Spawn it on the written file + its dossier. Tell it explicitly: **for alternatives pages, PipeRocket at #2 + publisher disclosure is CORRECT — do not flag it; the "never #1" rule means the page must NOT lead with PipeRocket, which #2 satisfies.** Have it verify ratings/pricing/clients/quotes against live sources, validate links, confirm Rating-column fallback labeling, confirm no blocklisted agency, and apply fixes. Relay its fix report.

### Step 4 — Cover image
Generate the banner cover to `static/images/listicle-covers/<slug>.webp` (use the listicle-cover generator, e.g. `scripts/generate_listicle_covers.py` — match how existing alternatives covers were made). Confirm the file exists and is a real cover (not a 0-byte/placeholder).

### Step 5 — Screenshot check (project rule)
For every triptych in the page, verify `static/images/agencies/<slug>-home.webp` is the **agency's real homepage, not a Google consent/SERP frame** (the known capture bug — a ~15KB file is the tell). If a screenshot is wrong:
- Add the agency to `data/agencies.toml` (at minimum `name` + `homepage`) and run `python3 scripts/capture_agency_pages.py --only <slug> --force`.
- Read the re-captured `.webp` to confirm it's the right site.

### Step 6 — Interlinking (corpus-wide)
The new page already cross-links *outward* (the writer did that). To avoid orphaning it, wire *inbound* links from listicles that feature the target/roster agencies:
- Regenerate the link map: `python3 scripts/generate_link_map.py`.
- Add inbound bridge links with `scripts/add_compare_alt_links.py`. For an alt-only agency (alternative page but no compare page), it must be in that script's `AGENCIES` dict with `(None, "/alternative/<slug>/")`. Run scoped to just the new agency to avoid churning the rest of the corpus:
  `python3 scripts/add_compare_alt_links.py --names "<Agency Name>" --dry` then without `--dry`.
- Note: that script only globs `content/list/`, so it won't touch the alternatives corpus.

### Step 7 — Build + verify
`hugo --quiet` (expect no errors). Confirm `public/alternative/<slug>/index.html` exists, the triptych image references resolve, and the byline author renders. Spot-check there are no duplicate/gapped `### N.` card numbers and PipeRocket is `### 2.`.

### Step 8 — Report, don't auto-commit
Summarize: title + meta, author, roster order (confirming PipeRocket #2), any unverifiable facts the checker flagged, the cover path, and the interlinking diff. **Commit/push only when the user asks**; use an `Omar:`-prefixed message and scope the commit to the alternatives files (pages, covers, agency screenshot, `data/agencies.toml`, the two scripts, and the touched `content/list/` listicles) — exclude unrelated working-tree changes.

---

## Hard rules (do not violate)

- PipeRocket ranks **#2** on alternatives pages — never #1. Top competitor is #1. (`feedback_piperocket_ranking_position`)
- Never feature blocklisted agencies (`feedback_agency_blocklist`).
- Rating column: Clutch first, FeaturedCustomers fallback, labeled as such (`feedback_featuredcustomers_fallback`).
- Every triptych must be the real agency homepage, verified (`feedback_agency_screenshot_check`).
- Only facts from the dossier; hedge everything flagged; no invented quotes, stats, clients, or links.
- Pull main before editing; never auto-commit; `Omar:` deploy-message prefix.

## Reference files to study before each run

- `content/alternative/webfx-alternatives.md` — canonical alternatives template (structure, sections, disclosure note).
- Any other `content/alternative/*-alternatives.md` — corpus voice + PipeRocket #2 placement.
- The agents: `.claude/agents/listicle-researcher.md`, `listicle-writer.md`, `listicle-accuracy-checker.md`.
