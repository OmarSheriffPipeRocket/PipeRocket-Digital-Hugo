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

  /* ─── Sidebar TOC — "Jump to Agency" ────────────────────────────────── */
  function buildSidebarTOC() {
    var tocNav = document.querySelector('[data-pr-agency-toc]');
    if (!tocNav) return;

    /* The TOC should list only the ranked agency h3s (those starting with
       a digit), not every h3 on the page. */
    var firstRankedH3 = Array.from(main.querySelectorAll('h3')).find(function (h) {
      return /^\s*1[\.\)]/.test(h.textContent);
    });
    if (!firstRankedH3) return;

    /* Walk back from the first ranked h3 to find its containing H2 — every
       agency in this section is what we want in the TOC. */
    var rankH2 = null;
    var prev = firstRankedH3.previousElementSibling;
    while (prev) {
      if (prev.tagName === 'H2') { rankH2 = prev; break; }
      prev = prev.previousElementSibling;
    }
    if (!rankH2) rankH2 = main.querySelector('h2');
    if (!rankH2) return;

    var headings = [];
    var node = rankH2.nextElementSibling;
    while (node) {
      if (node.tagName === 'H2') break;
      if (node.tagName === 'H3' && /^\s*\d+[\.\)]/.test(node.textContent)) {
        headings.push(node);
      }
      node = node.nextElementSibling;
    }
    if (!headings.length) return;

    var ol = document.createElement('ol');
    headings.forEach(function (h, i) {
      if (!h.id) h.id = 'agency-' + (i + 1);
      /* Strip "N. " prefix + any " – Best for ..." suffix so the TOC link
         is just the agency name. */
      var clean = h.textContent
        .replace(/^\s*\d+[\.\)]\s*/, '')
        .split(/\s*[–—-]\s*Best\s+for/i)[0]
        .trim();
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

    /* Mobile dropdown copy */
    var sel = document.querySelector('[data-pr-mobile-select]');
    var go = document.querySelector('[data-pr-mobile-go]');
    var mob = document.querySelector('[data-pr-mobile-nav]');
    if (sel && headings.length) {
      headings.forEach(function (h) {
        var opt = document.createElement('option');
        opt.value = '#' + h.id;
        opt.textContent = h.textContent.replace(/^\s*\d+[\.\)]\s*/, '');
        sel.appendChild(opt);
      });
      if (mob) mob.hidden = false;
      if (go) {
        go.addEventListener('click', function () {
          var target = document.querySelector(sel.value);
          if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
      }
    }
  }

  function init() {
    stripEmptyTableHeaders();
    highlightPipeRocketRow();
    buildSidebarTOC();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}());
