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

/* ─────────────────────────────────────────────────────────────
   Interactive checklist ({{< checklist >}} shortcode)
   Tickable items with a live progress meter, saved state in
   localStorage, a Reset button, and Download-as-PDF that prints a
   clean, branded document (PipeRocket logo + only the checklist +
   CTA) via a hidden iframe, so the surrounding page never prints.
   ───────────────────────────────────────────────────────────── */
(function () {
  'use strict';

  var widgets = document.querySelectorAll('[data-pr-checklist]');
  if (!widgets.length) return;

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* Build a standalone, branded checklist document and print just that
     via a hidden iframe. Reflects the current ticked state. */
  function printChecklist(root) {
    var titleEl = root.querySelector('.pr-checklist__title');
    var subEl   = root.querySelector('.pr-checklist__sub');
    var ctaEl   = root.querySelector('.pr-checklist__cta-text');
    var title   = titleEl ? titleEl.textContent : 'Checklist';
    var sub     = subEl ? subEl.textContent : '';
    var cta     = ctaEl ? ctaEl.textContent : '';
    var origin  = window.location.origin;

    var groups = '';
    Array.prototype.forEach.call(root.querySelectorAll('.pr-checklist__group'), function (g) {
      var gt = g.querySelector('.pr-checklist__group-title');
      var items = '';
      Array.prototype.forEach.call(g.querySelectorAll('.pr-checklist__item'), function (it) {
        var input = it.querySelector('input');
        var label = it.querySelector('label');
        var done  = input && input.checked;
        items += '<li class="' + (done ? 'done' : '') + '"><span class="bx">' + (done ? '✓' : '') +
                 '</span><span class="tx">' + esc(label ? label.textContent : '') + '</span></li>';
      });
      groups += '<h2>' + esc(gt ? gt.textContent : '') + '</h2><ul class="cl">' + items + '</ul>';
    });

    var css =
      '*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact;}' +
      'body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#0D0D0D;margin:0;padding:28px 32px;}' +
      '.hd{display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #0D0D0D;padding-bottom:12px;margin-bottom:18px;}' +
      '.hd img{height:26px;width:auto;}' +
      '.hd .src{font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:#6B6B6B;}' +
      'h1{font-size:22px;line-height:1.2;margin:0 0 6px;}' +
      '.sub{font-size:12px;color:#6B6B6B;margin:0 0 16px;max-width:640px;line-height:1.5;}' +
      'h2{font-size:14px;margin:16px 0 8px;padding-bottom:5px;border-bottom:1px solid #D9D5C9;}' +
      'ul.cl{list-style:none;margin:0;padding:0;}' +
      'ul.cl li{display:flex;align-items:flex-start;gap:9px;padding:5px 0;font-size:12.5px;line-height:1.4;page-break-inside:avoid;break-inside:avoid;}' +
      'ul.cl li .bx{flex:0 0 auto;width:14px;height:14px;border:1.5px solid #0D0D0D;border-radius:3px;text-align:center;line-height:11px;font-size:11px;color:#0CC6F1;font-weight:700;margin-top:1px;}' +
      'ul.cl li.done .tx{color:#6B6B6B;text-decoration:line-through;}' +
      '.cta{margin-top:22px;border:1px solid #0D0D0D;border-radius:8px;padding:14px 16px;page-break-inside:avoid;}' +
      '.cta strong{display:block;font-size:13px;margin-bottom:4px;}' +
      '.cta p{margin:0;font-size:12px;color:#333;line-height:1.5;}' +
      '@page{margin:14mm;}';

    var html =
      '<!doctype html><html><head><meta charset="utf-8"><title>' + esc(title) + '</title><style>' + css + '</style></head><body>' +
      '<header class="hd"><img src="' + origin + '/images/piperocket-logo.svg" alt="PipeRocket"><span class="src">piperocket.digital</span></header>' +
      '<h1>' + esc(title) + '</h1>' +
      (sub ? '<p class="sub">' + esc(sub) + '</p>' : '') +
      groups +
      (cta ? '<div class="cta"><strong>Work with PipeRocket</strong><p>' + esc(cta) + '</p><p>piperocket.digital/contact-us</p></div>' : '') +
      '</body></html>';

    var iframe = document.createElement('iframe');
    iframe.setAttribute('aria-hidden', 'true');
    iframe.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;visibility:hidden;';
    document.body.appendChild(iframe);

    var win = iframe.contentWindow;
    var doc = win.document;
    doc.open();
    doc.write(html);
    doc.close();

    var fired = false;
    function fire() {
      if (fired) return;
      fired = true;
      try { win.focus(); win.print(); } catch (e) { /* ignore */ }
      /* Remove the iframe well after the dialog is done with it. */
      win.onafterprint = function () { if (iframe.parentNode) iframe.parentNode.removeChild(iframe); };
      setTimeout(function () { if (iframe.parentNode) iframe.parentNode.removeChild(iframe); }, 60000);
    }

    /* Wait for the logo to load so it renders in the PDF; fall back on a timer. */
    var img = doc.querySelector('img');
    if (img && !img.complete) {
      img.addEventListener('load', fire);
      img.addEventListener('error', fire);
      setTimeout(fire, 1500);
    } else {
      setTimeout(fire, 200);
    }
  }

  /* Lazy-load ExcelJS only when a user actually exports, so it never touches
     page-load performance. Self-hosted at /js/exceljs.min.js. */
  var _exceljsPromise = null;
  function loadExcelJS() {
    if (window.ExcelJS) return Promise.resolve(window.ExcelJS);
    if (_exceljsPromise) return _exceljsPromise;
    _exceljsPromise = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = '/js/exceljs.min.js';
      s.async = true;
      s.onload = function () { window.ExcelJS ? resolve(window.ExcelJS) : reject(new Error('ExcelJS not found')); };
      s.onerror = function () { _exceljsPromise = null; reject(new Error('Failed to load ExcelJS')); };
      document.head.appendChild(s);
    });
    return _exceljsPromise;
  }

  /* Download the checklist as a native .xlsx (branded, logo top-left,
     reflects ticked state) built with ExcelJS. */
  function exportExcel(root, btn) {
    var title = (root.querySelector('.pr-checklist__title') || {}).textContent || 'Checklist';
    var sub   = (root.querySelector('.pr-checklist__sub') || {}).textContent || '';
    var cta   = (root.querySelector('.pr-checklist__cta-text') || {}).textContent || '';
    var logo  = root.getAttribute('data-logo') || '';
    var id    = root.getAttribute('data-checklist-id') || 'checklist';
    var origLabel = btn ? btn.innerHTML : '';
    if (btn) { btn.disabled = true; }

    loadExcelJS().then(function (ExcelJS) {
      var wb = new ExcelJS.Workbook();
      wb.creator = 'PipeRocket Digital';
      var ws = wb.addWorksheet('Checklist', { views: [{ showGridLines: false }] });
      ws.columns = [{ width: 72 }, { width: 10 }];

      // Deterministic row cursor so nothing overlaps and every band lines up.
      var R = 0;
      function estH(text, cpl, lineH, min) {
        var lines = Math.max(1, Math.ceil((text || '').length / cpl));
        return Math.max(min || 15, lines * lineH + 4);
      }
      // Full-width band: merge A:B, wrap, so long text stays inside the table edge.
      function band(text, font, height, fill) {
        R += 1;
        var row = ws.getRow(R);
        row.getCell(1).value = text;
        ws.mergeCells(R, 1, R, 2);
        row.getCell(1).font = font;
        row.getCell(1).alignment = { wrapText: true, vertical: 'middle' };
        if (fill) { row.getCell(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: fill } }; }
        if (height) { row.height = height; }
        return row;
      }

      // Row 1: logo only (reserved so it never overlaps the text below).
      if (logo) {
        var b64 = logo.indexOf(',') >= 0 ? logo.split(',')[1] : logo;
        var imgId = wb.addImage({ base64: b64, extension: 'png' });
        ws.addImage(imgId, { tl: { col: 0, row: 0 }, ext: { width: 150, height: 24 } });
      }
      R += 1; ws.getRow(R).height = 22;

      band('piperocket.digital', { size: 10, color: { argb: 'FF6B6B6B' } }, 16);
      band(title, { bold: true, size: 14, color: { argb: 'FF0D0D0D' } }, estH(title, 55, 18, 22));
      if (sub) { band(sub, { size: 10, italic: true, color: { argb: 'FF6B6B6B' } }, estH(sub, 92, 14, 16)); }
      R += 1; ws.getRow(R).height = 6; // spacer

      // Header row (Task | Done)
      R += 1;
      var rHdr = ws.getRow(R); rHdr.height = 18;
      rHdr.getCell(1).value = 'Task';
      rHdr.getCell(2).value = 'Done';
      rHdr.eachCell(function (c) {
        c.font = { bold: true, color: { argb: 'FFFFFFFF' } };
        c.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF0D0D0D' } };
        c.alignment = { vertical: 'middle' };
      });
      rHdr.getCell(2).alignment = { horizontal: 'center', vertical: 'middle' };

      Array.prototype.forEach.call(root.querySelectorAll('.pr-checklist__group'), function (g) {
        var gt = (g.querySelector('.pr-checklist__group-title') || {}).textContent || '';
        // Group title as a full-width band so the fill spans cleanly.
        band(gt, { bold: true, size: 11, color: { argb: 'FF0D0D0D' } }, 18, 'FFF1EFE7');
        Array.prototype.forEach.call(g.querySelectorAll('.pr-checklist__item'), function (it) {
          var input = it.querySelector('input');
          var lbl = (it.querySelector('label') || {}).textContent || '';
          var checked = !!(input && input.checked);
          R += 1;
          var ri = ws.getRow(R);
          ri.getCell(1).value = lbl;
          ri.getCell(2).value = checked ? '✓' : '';
          ri.getCell(1).alignment = { wrapText: true, vertical: 'top' };
          ri.getCell(2).alignment = { horizontal: 'center', vertical: 'top' };
          if (checked) { ri.getCell(2).font = { bold: true, color: { argb: 'FF217346' } }; }
        });
      });

      if (cta) {
        R += 1; ws.getRow(R).height = 6; // spacer
        band(cta + '  piperocket.digital/contact-us',
             { size: 10, color: { argb: 'FF333333' } },
             estH(cta, 90, 14, 20), 'FFF1EFE7');
      }

      return wb.xlsx.writeBuffer();
    }).then(function (buf) {
      var blob = new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = id + '-checklist.xlsx';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      if (btn) { btn.disabled = false; btn.innerHTML = origLabel; }
    }).catch(function (e) {
      if (btn) { btn.disabled = false; btn.innerHTML = origLabel; }
      console.error('Excel export failed:', e);
    });
  }

  Array.prototype.forEach.call(widgets, function (root) {
    var id       = root.getAttribute('data-checklist-id') || 'default';
    var total    = parseInt(root.getAttribute('data-total'), 10) || 0;
    var boxes    = Array.prototype.slice.call(root.querySelectorAll('[data-checklist-item]'));
    var fill     = root.querySelector('[data-checklist-fill]');
    var count    = root.querySelector('[data-checklist-count]');
    var dlBtn    = root.querySelector('[data-checklist-download]');
    var xlBtn    = root.querySelector('[data-checklist-excel]');
    var resetBtn = root.querySelector('[data-checklist-reset]');
    var storeKey = 'pr-checklist:' + id;

    /* localStorage can throw (private mode / disabled) — degrade gracefully. */
    function load() {
      try { return JSON.parse(localStorage.getItem(storeKey)) || {}; }
      catch (e) { return {}; }
    }
    function save(state) {
      try { localStorage.setItem(storeKey, JSON.stringify(state)); }
      catch (e) { /* ignore */ }
    }

    function update() {
      var done = 0;
      boxes.forEach(function (b) { if (b.checked) done++; });
      if (count) count.textContent = done;
      if (fill)  fill.style.width = (total ? (done / total) * 100 : 0) + '%';
    }

    /* Restore saved state (keyed by each box's id). */
    var state = load();
    boxes.forEach(function (b) {
      if (state[b.id]) b.checked = true;
      b.addEventListener('change', function () {
        var s = load();
        if (b.checked) { s[b.id] = 1; } else { delete s[b.id]; }
        save(s);
        update();
      });
    });
    update();

    /* Reset — clear ticks + saved state. */
    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        boxes.forEach(function (b) { b.checked = false; });
        save({});
        update();
      });
    }

    /* Download as PDF — print a clean branded doc (logo + checklist + CTA). */
    if (dlBtn) {
      dlBtn.addEventListener('click', function () { printChecklist(root); });
    }
    /* Download as Excel — branded workbook (logo top-left + checklist + CTA). */
    if (xlBtn) {
      xlBtn.addEventListener('click', function () { exportExcel(root, xlBtn); });
    }
  });
}());
