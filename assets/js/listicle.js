/* Listicle v2 — minimal enhancement layer.
 *
 * Why this script exists at all:
 *   - The v2 template has a sticky sidebar "Jump to Agency" TOC that needs
 *     to be built from the agency H3s in the rendered article. Hugo's
 *     built-in .TableOfContents would include every heading (TL;DR,
 *     methodology, etc.), which isn't what we want.
 *   - The Side-by-Side Comparison table needs a couple of tweaks
 *     (highlight the PipeRocket row, etc.) that aren't expressible in pure
 *     Markdown.
 *   - Mobile needs a dropdown variant of the same TOC.
 *
 * What this script does NOT do anymore:
 *   - It used to rewrite each agency H3 + paragraphs into a structured
 *     "card" component because the legacy listicle format encoded data
 *     with loose keyword cues (score numbers on their own line, "Best for:"
 *     paragraphs, etc.). The v3 content format writes proper Markdown
 *     (tables, links, bold labels) that Goldmark renders into the right
 *     HTML directly — no rewriting needed. We rely on CSS alone to style
 *     headings, paragraphs, tables, lists. */
(function () {
  'use strict';

  var main = document.querySelector('[data-pr-listicle-main]');
  if (!main) return;

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  /* ─── Empty <thead> cleanup ────────────────────────────────────────────
     Goldmark renders 2-column key/value markdown tables with `| | |` as
     headers — an empty thead row that browsers still allocate column
     widths for, even with display:none. Strip those rows entirely so
     auto-layout can size columns based on real content. */
  function stripEmptyTableHeaders() {
    main.querySelectorAll('table thead').forEach(function (thead) {
      var rows = thead.querySelectorAll('tr');
      if (!rows.length) return;
      /* Consider the thead "empty" if every <th> has no text content */
      var allEmpty = Array.from(rows).every(function (tr) {
        return Array.from(tr.children).every(function (th) {
          return (th.textContent || '').trim() === '';
        });
      });
      if (allEmpty) thead.remove();
    });
  }

  /* ─── Comparison table — PipeRocket row highlight ──────────────────────
     The Side-by-Side Comparison table at the top is styled by the unified
     `.pr-blog__body table, .pr-listicle__body table, ...` rules in
     main.css (same look as Omar's v2 design). The only thing left to do
     here is to flag our own row so it's visually distinct. */
  function highlightPipeRocketRow() {
    var compareH2 = Array.from(main.querySelectorAll('h2')).find(function (h) {
      return /\b(compare|comparison|side[-\s]?by[-\s]?side)\b/i.test(h.textContent);
    });
    if (!compareH2) return;

    var tbl = null;
    var node = compareH2.nextElementSibling;
    while (node && !tbl) {
      if (node.tagName === 'TABLE') { tbl = node; break; }
      tbl = node.querySelector ? node.querySelector('table') : null;
      if (tbl) break;
      node = node.nextElementSibling;
    }
    if (!tbl) return;

    tbl.querySelectorAll('tbody tr').forEach(function (row) {
      /* Check first or second cell for the agency name (depending on
         whether the table has a leading rank-number column). */
      var cells = row.querySelectorAll('td');
      for (var i = 0; i < Math.min(2, cells.length); i++) {
        if (/piperocket/i.test(cells[i].textContent)) {
          row.classList.add('pr-listicle-v2__tbl-ours');
          break;
        }
      }
    });
  }

  /* ─── Sidebar TOC — section navigation (H2s only) ──────────────────────
     Lists every H2 in the article so the reader can jump between major
     sections (TL;DR, Side-by-Side Comparison, How We Chose, Detailed
     Comparison, FAQs). Agency h3s under "Detailed Comparison" are NOT
     in the TOC anymore — the section-level overview is easier to scan
     and matches how the rest of the site treats TOCs. */
  function buildSidebarTOC() {
    var tocNav = document.querySelector('[data-pr-agency-toc]');
    if (!tocNav) return;

    var headings = Array.from(main.querySelectorAll('h2'));
    /* Drop trailing empty / "Related Articles" h2 outside main */
    headings = headings.filter(function (h) { return (h.textContent || '').trim().length > 0; });
    if (!headings.length) return;

    var ol = document.createElement('ol');
    headings.forEach(function (h, i) {
      if (!h.id) {
        h.id = 'toc-' + (i + 1) + '-' + (h.textContent || '').toLowerCase()
          .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40);
      }
      var clean = (h.textContent || '').trim();
      var li = document.createElement('li');
      li.innerHTML = '<a href="#' + h.id + '">' +
        '<span class="toc-num">' + (i + 1) + '.</span> ' + clean + '</a>';
      ol.appendChild(li);
    });
    tocNav.appendChild(ol);

    /* Highlight the entry whose section is currently in view. */
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var id = entry.target.id;
        tocNav.querySelectorAll('li').forEach(function (li) {
          li.classList.toggle('is-active',
            li.querySelector('a').getAttribute('href') === '#' + id);
        });
      });
    }, { rootMargin: '0px 0px -60% 0px', threshold: 0 });
    headings.forEach(function (h) { observer.observe(h); });

    /* Update the "Jump to Agency" label → "In this article" so the
       sidebar reads correctly for section-level navigation. */
    var label = document.querySelector('.pr-listicle-v2__rail-label');
    if (label) label.textContent = 'In this article';
  }

  /* ─── Mobile TOC toggle ────────────────────────────────────────────────
     On narrow viewports the TOC is collapsed by default behind a button.
     Tapping the button expands the list; tapping a link or the button
     again collapses it. */
  function setupMobileTOCToggle() {
    var tocBlock = document.querySelector('.pr-listicle-v2__toc-block');
    if (!tocBlock) return;

    var label = tocBlock.querySelector('.pr-listicle-v2__rail-label');
    var body = tocBlock.querySelector('[data-pr-agency-toc]');
    if (!label || !body) return;

    /* Mark the label as a toggle button — only visually active < 1024px
       (CSS handles the show/hide of the body). */
    tocBlock.classList.add('pr-listicle-v2__toc-block--collapsible');
    label.setAttribute('role', 'button');
    label.setAttribute('tabindex', '0');
    label.setAttribute('aria-expanded', 'false');

    var caret = document.createElement('span');
    caret.className = 'pr-listicle-v2__toc-caret';
    caret.setAttribute('aria-hidden', 'true');
    caret.textContent = '▾';
    label.appendChild(caret);

    function toggle() {
      var isOpen = tocBlock.classList.toggle('is-open');
      label.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    }

    label.addEventListener('click', toggle);
    label.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    });

    /* Collapse after a TOC link is clicked (mobile only). */
    body.addEventListener('click', function (e) {
      var a = e.target.closest('a');
      if (a && window.matchMedia('(max-width: 1024px)').matches) {
        tocBlock.classList.remove('is-open');
        label.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ─── Update History — card wrap ───────────────────────────────────────
     Authors write a plain `## Update History` section (a bulleted list of
     dated, material changes) as the LAST section of the article, after the
     FAQs. Wrap that H2 + its list into a styled card that matches the author
     card's background, so it reads as a companion block beneath the FAQs. */
  function wrapUpdateHistory() {
    var h2 = Array.from(main.querySelectorAll('h2')).find(function (h) {
      return /^\s*update history\s*$/i.test(h.textContent || '');
    });
    if (!h2 || h2.closest('.pr-update-history')) return;
    var section = el('section', 'pr-update-history');
    h2.parentNode.insertBefore(section, h2);
    /* Absorb the H2 and the entries that follow it, but STOP at the author
       card (a sibling rendered after .Content) so it stays a separate box. */
    var node = section.nextSibling;
    while (node) {
      if (node.nodeType === 1 && node.classList &&
          node.classList.contains('pr-author-card')) break;
      var next = node.nextSibling;
      section.appendChild(node);
      node = next;
    }
  }

  function init() {
    stripEmptyTableHeaders();
    highlightPipeRocketRow();
    wrapUpdateHistory();
    buildSidebarTOC();
    setupMobileTOCToggle();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}());
