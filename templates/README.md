# Page Templates — How to use these

This folder holds **fill-in-the-blank templates** for the two comparison-style page
types on piperocket.digital. Copy a template, rename it, replace every `[PLACEHOLDER]`,
delete the `# comment` / `<!-- comment -->` lines, and you have a publishable page.

> These files live OUTSIDE `content/`, so Hugo never builds them. They're reference only.

---

## The two page types

| Type | What it is | Lives in | Rendered by | Example live page |
|------|------------|----------|-------------|-------------------|
| **Alternatives** | "10 Best [X] Alternatives" ranked list | `content/alternative/<slug>.md` | `layouts/list/listicle.html` | `/alternative/webfx-alternatives/` |
| **Comparison** | Head-to-head "PipeRocket vs [X]" | `content/compare/<slug>.md` | `layouts/compare/single.html` | `/compare/piperocket-digital-vs-webfx/` |

The key difference for a writer:

- **Alternatives = a listicle.** You write almost everything as normal markdown in the
  body (headings, tables, paragraphs). The frontmatter is short. It's the same format as
  every other listicle on the site.
- **Comparison = a structured data page.** You fill in *fields* (the two companies, the
  comparison tables, the FAQ, etc.) in the frontmatter at the top. The layout turns those
  fields into the cards, tables and columns on the page. The markdown body underneath is
  only three tables (decision matrix, strengths, social proof).

So: for an alternatives page you think in **prose**; for a comparison page you think in
**fields**.

---

## How to create a new page

1. **Pull latest first** (`git pull`), so you're not editing a stale copy.
2. Copy the matching template into the right folder and rename it:
   - Alternatives: `cp templates/alternatives-page-TEMPLATE.md content/alternative/<competitor>-alternatives.md`
   - Comparison: `cp templates/comparison-page-TEMPLATE.md content/compare/piperocket-digital-vs-<competitor>.md`
3. Replace every `[PLACEHOLDER]`. Delete the explanatory comment lines as you go.
4. Add the cover image:
   - Alternatives → `/static/images/listicle-covers/<slug>.webp`
   - Comparison → `/static/images/compare-covers/<slug>.webp`
5. Preview locally with `hugo server` and open the URL.

## A few rules that matter

- **PipeRocket is always ranked #2 or #3** on alternatives lists — never #1, never 4th or
  lower. Promote another credible agency to #1.
- **Never invent ratings, prices, or reviews.** If a number isn't public, write
  "Custom pricing" / "Not rated on Clutch". Every Clutch/pricing link should be real.
- `writtenBy:` / `reviewedBy:` values are author keys from `data/authors.toml` — use an
  existing key (e.g. `praveen`, `kim`, `kamaraj`), don't make one up.
- `slug:` becomes the URL. Keep it lowercase-with-hyphens and matching the filename.
