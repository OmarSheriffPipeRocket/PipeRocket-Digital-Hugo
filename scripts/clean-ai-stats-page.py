#!/usr/bin/env python3
"""
One-shot cleanup for content/blogs/research-ai-seo-statistics.md.

The WP import left several types of orphan content in the markdown:
  · 38 zombie ".Copy" suffixes from the old copy-to-clipboard buttons
  · Standalone number lines (e.g. "91.3%") followed by their label —
    they were a visual layout on WP that no longer makes sense once
    the same stat appears in the bullet list immediately below
  · Orphan "Image source: PipeRocket Digital — ..." caption lines for
    charts that no longer exist (replaced by SVG infographics)
  · Concatenated label fragments like "Avg. time on page4m 40s"
  · Standalone metric labels with no number ("ChatGPT" on its own line)

This script removes all of them with surgical regexes. The bullet
lists below each section header carry the same numbers in proper
sentence form, so nothing factual is lost.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "blogs" / "research-ai-seo-statistics.md"

text = SRC.read_text(encoding="utf-8")

# 1. Strip trailing ".Copy" from any line (zombie copy-button label).
text = re.sub(r"\.Copy(?=\s*$)", ".", text, flags=re.MULTILINE)

# 2. Remove orphan "Image source: PipeRocket Digital ..." lines.
text = re.sub(r"^Image source: PipeRocket Digital[^\n]*\n+", "", text, flags=re.MULTILINE)

# 3. Remove standalone number-only paragraphs (a number, optional
#    decimal, optional %) — these were the big visual numbers on the
#    old WP layout, now redundant with the bullet list.
text = re.sub(r"\n\s*\d+(\.\d+)?%\s*\n", "\n", text)

# 4. Remove orphan "Avg. time on pageXm Ys" and "Bounce rateXX.X%" lines —
#    these are concatenated number+label fragments from a stat-card
#    visual that no longer exists.
text = re.sub(r"^Avg\. time on page[^\n]*\n+", "", text, flags=re.MULTILINE)
text = re.sub(r"^Bounce rate[^\n]*\n+", "", text, flags=re.MULTILINE)

# 5. Remove orphan metric labels that were paired with the number lines
#    just removed. These are textual labels with no surrounding sentence.
ORPHAN_LABELS = [
    "of all analyzed traffic from organic search",
    "of all analyzed traffic from AI engines",
    "of all traffic analyzed",
    "Organic visitor-to-lead [conversion rate](/glossary/what-is-conversion-rate/)",
    "AI visitor-to-lead [conversion rate](/glossary/what-is-conversion-rate/)",
    "Organic search",
    "AI engines",
    "Organic traffic",
    "AI referral traffic",
    "Top-of-funnel (ToFu)",
    "Bottom-of-funnel (BoFu)",
    "Organic Lead-to-SQL rate",
    "AI Lead-to-SQL rate",
    "Share of all AI referral traffic",
    "ChatGPT",
    "Perplexity",
    "Gemini",
    "Copilot",
    "Claude",
]
for label in ORPHAN_LABELS:
    pat = r"^" + re.escape(label) + r"\s*\n+"
    text = re.sub(pat, "", text, flags=re.MULTILINE)

# 6. Collapse 3+ consecutive blank lines down to 2 (one blank between
#    paragraphs is fine, more is the residue of removed blocks).
text = re.sub(r"\n{3,}", "\n\n", text)

SRC.write_text(text, encoding="utf-8")
print(f"Cleaned {SRC.name}")
print(f"  new size: {len(text)} chars")
