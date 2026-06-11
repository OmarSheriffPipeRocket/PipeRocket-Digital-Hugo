#!/usr/bin/env python3
"""
Consolidate compare/alternative interlinks at the bottom of each target agency
card across all listicles.

For each of the 6 agencies that have a /compare/ and/or /alternative/ page, we:
  1. Find their card in each listicle (### N. <Name>).
  2. Remove any existing compare/alternative link lines inside that card.
  3. Repair the known broken Clutch-rating table cell (split across lines).
  4. Insert ONE consolidated interlink line at the very bottom of the card,
     just before the next ### / ## section.

Run from repo root:  python3 scripts/add_compare_alt_links.py [--dry]
"""
import re, sys, glob, os

DRY = "--dry" in sys.argv

# name -> (compare_url, alt_url)
AGENCIES = {
    "Directive Consulting": (
        "/compare/piperocket-vs-directive-consulting/",
        "/alternative/directive-consulting-alternatives/",
    ),
    "KlientBoost": (
        "/compare/piperocket-digital-vs-klientboost/",
        "/alternative/klientboost-alternatives/",
    ),
    "NoGood": (
        "/compare/piperocket-digital-vs-nogood/",
        "/alternative/nogood-alternatives/",
    ),
    "Omniscient Digital": (
        "/compare/piperocket-digital-vs-omniscient-digital/",
        "/alternative/omniscient-digital-alternatives/",
    ),
    "Siege Media": (
        "/compare/piperocket-digital-vs-siege-media/",
        "/alternative/siege-media-alternatives/",
    ),
    "WebFX": (
        "/compare/piperocket-digital-vs-webfx/",
        "/alternative/webfx-alternatives/",
    ),
    # Alt-only agencies (have an /alternative/ page but no /compare/ page yet).
    # cmp_url is None — these render via ALT_ONLY_TEMPLATES.
    "Kalungi": (None, "/alternative/kalungi-alternatives/"),
    "Animalz": (None, "/alternative/animalz-alternatives/"),
    "Powered by Search": (None, "/alternative/powered-by-search-alternatives/"),
    "Refine Labs": (None, "/alternative/refine-labs-alternatives/"),
    "Single Grain": (None, "/alternative/single-grain-alternatives/"),
}

# Lead-in variants, rotated per card occurrence so the corpus isn't
# robotically identical. Each includes BOTH the compare and alternative link.
TEMPLATES = [
    "Want a side-by-side? Read our [PipeRocket vs {name}]({cmp}) breakdown, or see the [best {name} alternatives]({alt}).",
    "Weighing your options? Compare [PipeRocket vs {name}]({cmp}), or browse the [top {name} alternatives]({alt}).",
    "For a closer look, see our [PipeRocket vs {name}]({cmp}) comparison and our roundup of [{name} alternatives]({alt}).",
]

# Used when an agency has an /alternative/ page but no /compare/ page.
ALT_ONLY_TEMPLATES = [
    "Also weighing {name}? See our roundup of the [best {name} alternatives]({alt}).",
    "Looking at {name} too? Browse the [top {name} alternatives]({alt}).",
    "If {name} isn't quite the fit, check our [{name} alternatives]({alt}) shortlist.",
]

HEAD_RE = re.compile(r"^### (\d+)\.\s+(.*?)\s*$")
SECTION_RE = re.compile(r"^## ")  # H2 section like ## FAQs


def card_name(heading_text):
    for name in AGENCIES:
        if heading_text.strip().lower() == name.lower():
            return name
    return None


def repair_split_clutch(lines):
    """Rejoin '| Clutch Rating | 4' + '.9/5 (402 reviews) |' style breaks."""
    out = []
    i = 0
    while i < len(lines):
        cur = lines[i]
        if re.search(r"\|\s*\d\s*$", cur):
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and re.match(r"^\.\d/5", lines[j].strip()):
                out.append(cur.rstrip() + lines[j].strip())
                i = j + 1
                continue
        out.append(cur)
        i += 1
    return out


def process(path, counter):
    with open(path) as f:
        text = f.read()
    lines = text.split("\n")

    head_idxs = [(i, HEAD_RE.match(l)) for i, l in enumerate(lines)]
    head_idxs = [(i, m) for i, m in head_idxs if m]

    cards = []
    for (idx, m) in head_idxs:
        name = card_name(m.group(2))
        if not name:
            continue
        end = len(lines)
        for j in range(idx + 1, len(lines)):
            if HEAD_RE.match(lines[j]) or SECTION_RE.match(lines[j]):
                end = j
                break
        cards.append((idx, end, name))

    if not cards:
        return False, counter

    changed = False
    for (start, end, name) in sorted(cards, reverse=True):
        cmp_url, alt_url = AGENCIES[name]
        block = lines[start:end]

        cleaned = [l for l in block if "/compare/" not in l and "/alternative/" not in l]
        cleaned = repair_split_clutch(cleaned)
        while len(cleaned) > 1 and cleaned[-1].strip() == "":
            cleaned.pop()

        if cmp_url:
            tmpl = TEMPLATES[counter % len(TEMPLATES)]
            link_line = tmpl.format(name=name, cmp=cmp_url, alt=alt_url)
        else:
            tmpl = ALT_ONLY_TEMPLATES[counter % len(ALT_ONLY_TEMPLATES)]
            link_line = tmpl.format(name=name, alt=alt_url)
        counter += 1

        cleaned.append("")
        cleaned.append(link_line)
        cleaned.append("")

        lines[start:end] = cleaned
        changed = True

    if changed and not DRY:
        with open(path, "w") as f:
            f.write("\n".join(lines))
    return changed, counter


def main():
    global AGENCIES
    # --names "Single Grain,Refine Labs" restricts the run to specific agency
    # cards, leaving every other card (and its existing links) untouched.
    if "--names" in sys.argv:
        wanted = sys.argv[sys.argv.index("--names") + 1]
        names = {n.strip().lower() for n in wanted.split(",") if n.strip()}
        AGENCIES = {k: v for k, v in AGENCIES.items() if k.lower() in names}
        print(f"Restricted to: {', '.join(AGENCIES) or '(none matched)'}")

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = sorted(glob.glob(os.path.join(root, "content/list/*.md")))
    counter = 0
    touched = []
    for path in files:
        changed, counter = process(path, counter)
        if changed:
            touched.append(os.path.basename(path))
    print(f"{'DRY-RUN: ' if DRY else ''}touched {len(touched)} files, {counter} cards:")
    for t in touched:
        print("  -", t)


if __name__ == "__main__":
    main()
