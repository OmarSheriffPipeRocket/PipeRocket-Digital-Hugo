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

  /* ── Collect headings ─────────────────────────────────────── */
  var headings = Array.from(main.querySelectorAll('h2, h3'));
  if (!headings.length) return;

  /* Assign stable IDs */
  headings.forEach(function (h, i) {
    if (!h.id) h.id = 'section-' + (i + 1);
  });

  /* ── Build TOC ────────────────────────────────────────────── */
  var ol = document.createElement('ol');
  var currentH2Li  = null;
  var currentSubUl = null;
  var h2Items      = []; /* [{li, h2el}] — for observer callbacks */

  headings.forEach(function (h) {
    if (h.tagName === 'H2') {
      var li = document.createElement('li');
      li.className = 'pr-blog-toc__item pr-blog-toc__item--h2';
      var a = document.createElement('a');
      a.href        = '#' + h.id;
      a.textContent = h.textContent;
      li.appendChild(a);

      currentSubUl = document.createElement('ul');
      currentSubUl.className = 'pr-blog-toc__sub';
      currentSubUl.hidden    = true;
      li.appendChild(currentSubUl);

      ol.appendChild(li);
      currentH2Li = li;
      h2Items.push({ li: li, h2el: h, subUl: currentSubUl });
    } else if (h.tagName === 'H3') {
      if (!currentSubUl) {
        /* H3 with no preceding H2 — attach to a synthetic group */
        currentSubUl = document.createElement('ul');
        currentSubUl.className = 'pr-blog-toc__sub';
        currentSubUl.hidden    = true;
        ol.appendChild(currentSubUl);
      }
      var subLi = document.createElement('li');
      subLi.className = 'pr-blog-toc__item pr-blog-toc__item--h3';
      var subA = document.createElement('a');
      subA.href        = '#' + h.id;
      subA.textContent = h.textContent;
      subLi.appendChild(subA);
      currentSubUl.appendChild(subLi);
    }
  });

  tocNav.appendChild(ol);

  /* If any h2 has no h3 children, remove the empty sub-list */
  h2Items.forEach(function (item) {
    if (!item.subUl.children.length) {
      item.subUl.parentNode.removeChild(item.subUl);
      item.subUl = null;
    }
  });

  /* ── Helpers ──────────────────────────────────────────────── */
  function expandH2(idx) {
    h2Items.forEach(function (item, i) {
      var isActive = (i === idx);
      item.li.classList.toggle('is-active-h2', isActive);
      if (item.subUl) item.subUl.hidden = !isActive;
    });
  }

  function findParentH2Idx(h3el) {
    /* Walk backwards through h2Items to find the closest preceding h2 */
    for (var i = h2Items.length - 1; i >= 0; i--) {
      var pos = h2Items[i].h2el.compareDocumentPosition(h3el);
      if (pos & Node.DOCUMENT_POSITION_FOLLOWING) return i;
    }
    return 0;
  }

  /* ── Active highlight ─────────────────────────────────────── */
  function setActive(id) {
    tocNav.querySelectorAll('.pr-blog-toc__item').forEach(function (item) {
      var a = item.querySelector(':scope > a');
      item.classList.toggle('is-active', a && a.getAttribute('href') === '#' + id);
    });
  }

  /* ── IntersectionObserver ─────────────────────────────────── */
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var h   = entry.target;
      var idx = h.tagName === 'H2'
        ? h2Items.findIndex(function (item) { return item.h2el === h; })
        : findParentH2Idx(h);

      expandH2(idx);
      setActive(h.id);
    });
  }, { rootMargin: '0px 0px -55% 0px', threshold: 0 });

  headings.forEach(function (h) { observer.observe(h); });

  /* Expand first h2 on load so TOC isn't empty */
  if (h2Items.length) expandH2(0);
}());
