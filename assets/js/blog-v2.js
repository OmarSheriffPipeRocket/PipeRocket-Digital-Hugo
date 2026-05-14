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

  /* ── Collect h2s only ────────────────────────────────────── */
  var headings = Array.from(main.querySelectorAll('h2'));
  if (!headings.length) return;

  /* Assign stable IDs */
  headings.forEach(function (h, i) {
    if (!h.id) h.id = 'section-' + (i + 1);
  });

  /* ── Build TOC ────────────────────────────────────────────── */
  var ol = document.createElement('ol');

  headings.forEach(function (h) {
    var li = document.createElement('li');
    li.className = 'pr-blog-toc__item pr-blog-toc__item--h2';
    var a = document.createElement('a');
    a.href        = '#' + h.id;
    a.textContent = h.textContent;
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
}());
