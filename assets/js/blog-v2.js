/* Blog v2 — sidebar TOC with h2/h3 expand-on-scroll behaviour.
 *
 * Builds the TOC from all h2/h3 elements in [data-pr-blog-main].
 * H3s are nested under their parent h2 in a hidden <ul>.
 * An IntersectionObserver reveals a h2's h3 sub-list when that
 * section scrolls into view, and collapses all others. */
(function () {
  'use strict';

  var main   = document.querySelector('[data-pr-blog-main]');
  var tocNav = document.querySelector('[data-pr-blog-toc]');
  if (!main || !tocNav) return;

  /* If the template has pre-populated the TOC (e.g. compare / alternative
     templates that derive items from frontmatter), skip the H2 scanner —
     we don't want to append a duplicate <ol>. The mobile-toggle wiring
     at the bottom of this file still runs either way. */
  var preBuilt = tocNav.children.length > 0;

  /* ── Collect h2s only ────────────────────────────────────── */
  var headings = preBuilt ? [] : Array.from(main.querySelectorAll('h2'));
  if (!preBuilt && !headings.length) return;

  /* Assign stable IDs */
  headings.forEach(function (h, i) {
    if (!h.id) h.id = 'section-' + (i + 1);
  });

  /* ── Build TOC ────────────────────────────────────────────── */
  var ol = document.createElement('ol');

  headings.forEach(function (h, i) {
    var li = document.createElement('li');
    li.className = 'pr-blog-toc__item pr-blog-toc__item--h2';
    var a = document.createElement('a');
    a.href = '#' + h.id;

    /* "1." "2." "3." prefix using the same .toc-num pattern as the
       listicle TOC, so blogs + listicles share one numbered TOC visual. */
    var num = document.createElement('span');
    num.className = 'toc-num';
    num.textContent = (i + 1) + '.';
    a.appendChild(num);
    a.appendChild(document.createTextNode(' ' + h.textContent));

    li.appendChild(a);
    ol.appendChild(li);
  });

  tocNav.appendChild(ol);

  /* ── Active highlight ─────────────────────────────────────── */
  function setActive(id) {
    tocNav.querySelectorAll('.pr-blog-toc__item').forEach(function (item) {
      var a = item.querySelector('a');
      item.classList.toggle('is-active', a && a.getAttribute('href') === '#' + id);
    });
  }

  /* ── IntersectionObserver ─────────────────────────────────── */
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      setActive(entry.target.id);
    });
  }, { rootMargin: '0px 0px -55% 0px', threshold: 0 });

  headings.forEach(function (h) { observer.observe(h); });

  /* ── Mobile TOC toggle ─────────────────────────────────────
     Mirrors the listicle pattern: on narrow viewports the TOC body
     is collapsed; the heading acts as a toggle button with a caret
     indicator. Desktop CSS keeps the body visible regardless. */
  (function setupMobileTOCToggle() {
    var tocBlock = document.querySelector('.pr-blog-v2__toc-block');
    var label = tocBlock && tocBlock.querySelector('.pr-blog-v2__rail-label');
    if (!tocBlock || !label) return;

    tocBlock.classList.add('pr-blog-v2__toc-block--collapsible');
    label.setAttribute('role', 'button');
    label.setAttribute('tabindex', '0');
    label.setAttribute('aria-expanded', 'false');

    var caret = document.createElement('span');
    caret.className = 'pr-blog-v2__toc-caret';
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
    tocNav.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a');
      if (a && window.matchMedia('(max-width: 1024px)').matches) {
        tocBlock.classList.remove('is-open');
        label.setAttribute('aria-expanded', 'false');
      }
    });
  })();
}());
