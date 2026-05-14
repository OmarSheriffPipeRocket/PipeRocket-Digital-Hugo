/* Listicle v2 — pattern-detection engine.
 *
 * Same idea as the WP `single-listicle.php` script: editors write loose
 * Markdown (headings + paragraphs with keyword prefixes), and this script
 * walks the rendered HTML in [data-pr-listicle-main] and reshapes it into
 * the structured listicle components (TL;DR box, methodology, agency cards,
 * comparison table, FAQ, sidebar TOC, mobile nav).
 *
 * Each transform is its own function so we can wire them in one by one as
 * we build out the new design. */
(function () {
  'use strict';

  var main = document.querySelector('[data-pr-listicle-main]');
  if (!main) return;

  /* ─── Utilities ──────────────────────────────────────────────── */
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  function childrenBetween(startAfter, stopAt) {
    var result = [];
    var node = startAfter ? startAfter.nextElementSibling : main.firstElementChild;
    while (node) {
      if (stopAt && node === stopAt) break;
      result.push(node);
      node = node.nextElementSibling;
    }
    return result;
  }

  /* ─── Transforms (stubs — fill in as the new design lands) ───── */
  function transformTLDR() { /* TODO */ }
  function transformMethodology() {
    var allH2 = Array.from(main.querySelectorAll('h2'));
    var mH2 = allH2.find(function (h) {
      var t = h.textContent.toLowerCase().replace(/ /g, ' ').trim();
      return t.includes('how we evaluated') || t.includes('how we scored') || t.includes('our methodology') || t.includes('how i evaluated');
    });
    if (!mH2) return;

    var nextH2 = mH2.nextElementSibling;
    while (nextH2 && nextH2.tagName !== 'H2') nextH2 = nextH2.nextElementSibling;

    var sectionEls = childrenBetween(mH2, nextH2);
    var box = el('div', 'pr-listicle-v2__method');
    box.appendChild(el('h2', 'pr-listicle-v2__method-title', mH2.innerHTML));

    sectionEls.forEach(function (e) {
      var text = e.textContent.trim();
      var m = text.match(/^(\d+)%\s*[—–\-]\s*([\s\S]+)$/);
      if (!m) {
        var pctM = text.match(/^(\d+)%/);
        if (pctM && e.querySelector('strong')) {
          var labelHTML = e.innerHTML.replace(/^\d+%/, '').trim();
          m = [null, pctM[1], labelHTML];
        }
      }
      if (m) {
        var body = m[2];
        /* Bold the criterion name — text before first " — ", "–", or ":" */
        body = body.replace(/^([^—–:]+)([—–:])\s*/, function (_, name, sep) {
          return '<strong>' + name.trim() + '</strong>' + sep + ' ';
        });
        var mi = el('div', 'pr-listicle-v2__mi');
        mi.innerHTML = '<span class="pr-listicle-v2__mi-pct">' + m[1] + '%</span><span>' + body + '</span>';
        box.appendChild(mi);
      }
    });

    mH2.parentNode.insertBefore(box, mH2);
    mH2.remove();
    sectionEls.forEach(function (e) { e.remove(); });
  }
  function transformQuickPicks() {
    var allH2 = Array.from(main.querySelectorAll('h2'));
    var qH2 = allH2.find(function (h) {
      var t = h.textContent.toLowerCase();
      return t.includes('compare') || t.includes('quick pick') || t.includes('at a glance');
    });
    if (!qH2) return;

    var listEl = qH2.nextElementSibling;
    if (!listEl || (listEl.tagName !== 'OL' && listEl.tagName !== 'UL')) return;

    var ol = document.createElement('ol');
    ol.className = 'pr-listicle-v2__picks';

    Array.from(listEl.querySelectorAll('li')).forEach(function (li) {
      var text   = li.textContent.trim();
      var sepIdx = text.search(/[·—–]/);
      var name   = sepIdx > -1 ? text.slice(0, sepIdx).trim() : text;
      var best   = sepIdx > -1 ? text.slice(sepIdx + 1).trim() : '';
      var item   = document.createElement('li');
      item.innerHTML = '<strong>' + name + '</strong>' +
        (best ? ' <span class="pr-listicle-v2__pick-sep">·</span> <span class="pr-listicle-v2__pick-best">' + best + '</span>' : '');
      ol.appendChild(item);
    });

    /* Insert heading + list before the methodology box if it exists, otherwise in place */
    var methodBox = main.querySelector('.pr-listicle-v2__method');
    if (methodBox) {
      methodBox.parentNode.insertBefore(ol, methodBox);
      methodBox.parentNode.insertBefore(qH2, ol);
    } else {
      listEl.parentNode.insertBefore(ol, listEl);
    }
    listEl.remove();
  }
  function transformAgencyCards() {
    var allH3 = Array.from(main.querySelectorAll('h3')).filter(function(h) {
      return /^\s*\d+[\.\)]/.test(h.textContent);
    });
    if (!allH3.length) return;

    allH3.forEach(function(h3) {
      var parent = h3.parentNode;
      var els = [];
      var node = h3.nextElementSibling;
      while (node && node.tagName !== 'H2' && node.tagName !== 'H3') {
        els.push(node);
        node = node.nextElementSibling;
      }

      var score = '', subscores = '', bestFor = '', bodyEls = [];
      var expertiseItems = [], bestSuited = '', notIdeal = '';
      var quoteEl = null, pricing = '', inExpertise = false, postQuoteEls = [];

      els.forEach(function(e) {
        var tag = e.tagName;
        var text = e.textContent.trim();
        if (tag === 'H4') { inExpertise = /expertise/i.test(text); return; }
        if (inExpertise && (tag === 'UL' || tag === 'OL')) {
          expertiseItems = Array.from(e.querySelectorAll('li')).map(function(li) { return li.innerHTML; });
          inExpertise = false; return;
        }
        if (tag === 'BLOCKQUOTE') { quoteEl = e; return; }
        if (!score && /^\d+$/.test(text)) { score = text; return; }
        if (!subscores && text.indexOf(' | ') > -1) {
          subscores = e.innerHTML
            .replace(/(\d+\/\d+)/g, '<strong>$1</strong>')
            .replace(/ \| /g, '<span class="pr-card__subscore-sep"> | </span>');
          return;
        }
        if (!bestFor && /^best for:/i.test(text)) { bestFor = e.innerHTML.replace(/^best for:\s*/i, ''); return; }
        if (/^best suited for:/i.test(text)) { bestSuited = e.innerHTML.replace(/^best suited for:\s*/i, ''); return; }
        if (/^not ideal for:/i.test(text)) { notIdeal = e.innerHTML.replace(/^not ideal for:\s*/i, ''); return; }
        if (/^pricing:/i.test(text)) { pricing = e.innerHTML; return; }
        if (quoteEl && tag === 'P') { postQuoteEls.push(e); return; }
        if (bestFor && !expertiseItems.length && !bestSuited && tag === 'P') bodyEls.push(e);
      });

      var card = el('div', 'pr-card');

      /* Head: move original h3 (keeps its id for TOC) + score */
      var head = el('div', 'pr-card__head');
      h3.className = 'pr-card__name';
      head.appendChild(h3);
      if (score) {
        var scoreWrap = el('div', 'pr-card__score');
        scoreWrap.innerHTML = '<span class="pr-card__score-num">' + score + '</span><span class="pr-card__score-denom"> / 100</span>';
        head.appendChild(scoreWrap);
      }
      card.appendChild(head);

      if (subscores) card.appendChild(el('p', 'pr-card__subscores', subscores));

      /* PipeRocket-specific: blue score + disclaimer */
      var isPR = /piperocket/i.test(h3.textContent);
      if (isPR) {
        var scoreNum = card.querySelector('.pr-card__score-num');
        if (scoreNum) scoreNum.style.color = '#0ba6e2';
        card.appendChild(el('div', 'pr-card__disclaimer',
          '<strong>Disclaimer:</strong> PipeRocket Digital is our agency. Evaluated on the same criteria as all others on this list. No score or placement adjustments were made.'));
      }

      if (bestFor) card.appendChild(el('p', 'pr-card__bestfor', '<strong>Best for:</strong> ' + bestFor));

      if (bodyEls.length) {
        var bodyWrap = el('div', 'pr-card__body');
        bodyEls.forEach(function(p) { bodyWrap.appendChild(p.cloneNode(true)); });
        card.appendChild(bodyWrap);
      }

      if (expertiseItems.length) {
        var tags = el('div', 'pr-card__tags');
        expertiseItems.forEach(function(html) { tags.appendChild(el('span', 'pr-card__tag', html)); });
        card.appendChild(tags);
      }

      if (bestSuited || notIdeal) {
        var fitGrid = el('div', 'pr-card__fit-grid');
        if (bestSuited) {
          var f1 = el('div', 'pr-card__fit');
          f1.appendChild(el('div', 'pr-card__fit-label', 'Best Suited For'));
          f1.appendChild(el('p', null, bestSuited));
          fitGrid.appendChild(f1);
        }
        if (notIdeal) {
          var f2 = el('div', 'pr-card__fit');
          f2.appendChild(el('div', 'pr-card__fit-label', 'Not Ideal For'));
          f2.appendChild(el('p', null, notIdeal));
          fitGrid.appendChild(f2);
        }
        card.appendChild(fitGrid);
      }

      if (quoteEl) {
        var qHTML = quoteEl.innerHTML.replace(/\s*[—–]\s*(.*?)(<\/p>|$)/g, '<br><strong>— $1</strong>$2');
        card.appendChild(el('blockquote', 'pr-card__quote', qHTML));
      }
      postQuoteEls.forEach(function(p) { card.appendChild(el('p', 'pr-card__compare', p.innerHTML)); });
      if (pricing) card.appendChild(el('p', 'pr-card__pricing', pricing));

      parent.insertBefore(card, els[0] || null);
      els.forEach(function(e) { if (e.parentNode) e.parentNode.removeChild(e); });
    });
  }
  function transformTables() {
    main.querySelectorAll('table').forEach(function (tbl) {
      if (tbl.closest('.pr-listicle-v2__tbl-wrap')) return;
      tbl.classList.add('pr-listicle-v2__tbl');
      var wrap = el('div', 'pr-listicle-v2__tbl-wrap');
      tbl.parentNode.insertBefore(wrap, tbl);
      wrap.appendChild(tbl);

      /* Style score column cells blue + bold */
      var headers = Array.from(tbl.querySelectorAll('th'));
      var scoreIdx = headers.findIndex(function (th) {
        return /^score$/i.test(th.textContent.trim());
      });
      tbl.querySelectorAll('tbody tr').forEach(function (row) {
        var cells = row.querySelectorAll('td');
        if (scoreIdx > -1 && cells[scoreIdx]) {
          cells[scoreIdx].classList.add('pr-listicle-v2__tbl-score');
        }
        /* PipeRocket row highlight */
        var nameCell = cells[1] || cells[0];
        if (nameCell && /piperocket/i.test(nameCell.textContent)) {
          row.classList.add('pr-listicle-v2__tbl-ours');
        }
      });
    });
  }
  function transformFAQ() { /* TODO */ }
  function buildSidebarTOC() {
    var tocNav = document.querySelector('[data-pr-agency-toc]');
    if (!tocNav) return;

    /* Find the h2 that introduces the ranking list (contains "pick" or "ranking" or "best") */
    var allH2 = Array.from(main.querySelectorAll('h2'));
    /* Find the h2 immediately before the first ranked h3 (starts with "1.") */
    var firstRankedH3 = Array.from(main.querySelectorAll('h3')).find(function (h) {
      return /^\s*1[\.\)]/.test(h.textContent);
    });
    var rankH2 = null;
    if (firstRankedH3) {
      var prev = firstRankedH3.previousElementSibling;
      while (prev) {
        if (prev.tagName === 'H2') { rankH2 = prev; break; }
        prev = prev.previousElementSibling;
      }
    }
    rankH2 = rankH2 || allH2[0];

    /* Collect h3s that follow rankH2 and precede the next h2, and start with a digit */
    var headings = [];
    if (rankH2) {
      var next = rankH2.nextElementSibling;
      while (next) {
        if (next.tagName === 'H2') break;
        if (next.tagName === 'H3' && /^\s*\d+[\.\)]/.test(next.textContent)) {
          headings.push(next);
        }
        next = next.nextElementSibling;
      }
    }
    if (!headings.length) return;

    var ol = document.createElement('ol');
    headings.forEach(function (h, i) {
      /* Ensure heading has an id we can link to */
      if (!h.id) {
        h.id = 'agency-' + (i + 1);
      }
      /* Extract just the agency name: strip leading "N. " and any "– Best for..." suffix */
      var raw = h.textContent.replace(/^\s*\d+[\.\)]\s*/, '').split(/\s*[–—-]\s*Best\s+for/i)[0].trim();
      var li = document.createElement('li');
      li.innerHTML = '<a href="#' + h.id + '"><span class="toc-num">' + (i + 1) + '.</span> ' + raw + '</a>';
      ol.appendChild(li);
    });
    tocNav.appendChild(ol);

    /* Highlight active item on scroll */
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var id = entry.target.id;
        tocNav.querySelectorAll('li').forEach(function (li) {
          li.classList.toggle('is-active', li.querySelector('a').getAttribute('href') === '#' + id);
        });
      });
    }, { rootMargin: '0px 0px -60% 0px', threshold: 0 });

    headings.forEach(function (h) { observer.observe(h); });
  }

  function buildMobileNav() { /* TODO */ }

  /* ─── Run ───────────────────────────────────────────────────── */
  function init() {
    transformTLDR();
    transformMethodology();
    transformQuickPicks();
    transformTables();
    buildSidebarTOC();
    transformAgencyCards();
    transformFAQ();
    buildMobileNav();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}());
