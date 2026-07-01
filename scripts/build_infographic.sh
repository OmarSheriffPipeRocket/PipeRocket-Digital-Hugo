#!/usr/bin/env bash
#
# The ONLY sanctioned way to rasterize a PipeRocket infographic SVG to WebP.
# Refuses to emit a .webp unless the source SVG contains the verbatim
# PipeRocket logo signature, so the wrong/hand-drawn logo can never ship.
#
# Usage:
#   scripts/build_infographic.sh /tmp/<slug>-infographic-<n>.svg \
#       static/images/blog-infographics/<slug>-infographic-<n>.webp
#
# The canonical logo block to paste into every SVG lives at:
#   reference/infographic-logo-block.svg
#
set -euo pipefail

SVG="${1:-}"
OUT="${2:-}"

if [[ -z "$SVG" || -z "$OUT" ]]; then
  echo "usage: build_infographic.sh <source.svg> <out.webp>" >&2
  exit 2
fi
if [[ ! -f "$SVG" ]]; then
  echo "FAIL: source SVG not found: $SVG" >&2
  exit 1
fi

# --- Logo signature gate (the whole point of this script) ---
missing=()
grep -q 'fill="#0ba6e2"'            "$SVG" || missing+=("blue pennant fill #0ba6e2")
grep -q '#ff0025'                   "$SVG" || missing+=("red pennant gradient #ff0025")
grep -q 'translate(50, 26) scale(0.65)' "$SVG" || missing+=("logo transform translate(50, 26) scale(0.65)")
grep -q 'width="1200"'              "$SVG" || missing+=("root width=1200 (won't render without it)")

if (( ${#missing[@]} )); then
  echo "FAIL: $SVG is missing the required PipeRocket logo/chrome signature:" >&2
  for m in "${missing[@]}"; do echo "   - $m" >&2; done
  echo "Paste the verbatim block from reference/infographic-logo-block.svg. NOT built." >&2
  exit 1
fi

# --- Reject hand-drawn approximations of the logo ---
if grep -qiE '<text[^>]*>PipeRocket</text>|>PipeRocket<' "$SVG"; then
  echo "FAIL: $SVG draws 'PipeRocket' as a <text> wordmark — that is the hand-drawn logo." >&2
  echo "The wordmark must be the vector <path> from reference/infographic-logo-block.svg. NOT built." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
rsvg-convert -w 2400 -h 1260 "$SVG" | magick - -quality 92 "$OUT"
echo "OK: built $OUT (logo signature verified)"
