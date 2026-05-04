"""
PDF image extraction splits images-with-transparency into JPG (color) + PNG (alpha mask).
This script walks each pair (raw-NNN.jpg + raw-NNN+1.png with matching dimensions)
and combines them into a proper RGBA PNG named raw-NNN_alpha.png.
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).parent
pairs_made = 0
skipped = 0

for jpg in sorted(HERE.glob("raw-*.jpg")):
    n = int(jpg.stem.split("-")[1])
    png = HERE / f"raw-{n+1:03d}.png"
    if not png.exists():
        skipped += 1
        continue
    try:
        color = Image.open(jpg).convert("RGB")
        mask = Image.open(png).convert("L")
        if color.size != mask.size:
            skipped += 1
            continue
        out = color.convert("RGBA")
        out.putalpha(mask)
        out.save(HERE / f"raw-{n:03d}_alpha.png", "PNG", optimize=True)
        pairs_made += 1
    except Exception as e:
        print(f"skip {jpg.name}: {e}")
        skipped += 1

print(f"created {pairs_made} alpha PNGs; skipped {skipped}")
