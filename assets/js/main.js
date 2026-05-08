// PipeRocket — minimal JS
// Each setup function runs independently; missing target elements are a no-op.

// Single rAF-throttled scroll manager — all scroll handlers register here
const scrollHandlers = [];
let scrollTicking = false;
const onWindowScroll = () => {
  if (scrollTicking) return;
  scrollTicking = true;
  requestAnimationFrame(() => {
    for (let i = 0; i < scrollHandlers.length; i++) scrollHandlers[i]();
    scrollTicking = false;
  });
};
const registerScroll = (fn) => {
  scrollHandlers.push(fn);
  fn();
};
window.addEventListener('scroll', onWindowScroll, { passive: true });

const setupMobileMenu = () => {
  const toggle = document.getElementById('prMenuToggle');
  const nav = document.querySelector('.pr-nav');
  if (!toggle || !nav) return;
  let savedScrollY = 0;
  const setOpen = (open) => {
    if (open) {
      savedScrollY = window.scrollY;
      document.body.style.top = `-${savedScrollY}px`;
    } else {
      document.body.style.top = '';
    }
    nav.classList.toggle('pr-nav--open', open);
    document.documentElement.classList.toggle('pr-nav-locked', open);
    document.body.classList.toggle('pr-nav-locked', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    if (!open) {
      window.scrollTo(0, savedScrollY);
    }
  };
  toggle.addEventListener('click', () => {
    setOpen(!nav.classList.contains('pr-nav--open'));
  });
  // Mobile-only: tap on Services/Resources label toggles its submenu
  nav.querySelectorAll('.pr-nav__item--mega').forEach((item) => {
    item.addEventListener('click', (e) => {
      // Don't intercept clicks on links inside the megamenu
      if (e.target.closest('a')) return;
      // Only behave as accordion in mobile (where drawer is open)
      if (!nav.classList.contains('pr-nav--open')) return;
      e.preventDefault();
      item.classList.toggle('is-open');
    });
  });
  // Close drawer on link click (mobile UX)
  nav.addEventListener('click', (e) => {
    if (e.target.tagName === 'A') setOpen(false);
  });
  // Close on escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && nav.classList.contains('pr-nav--open')) setOpen(false);
  });
};

const setupCounters = () => {
  const counters = document.querySelectorAll('[data-pr-counter]');
  if (counters.length === 0) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const formatValue = (value, decimals, prefix, suffix) =>
    `${prefix}${value.toFixed(decimals)}${suffix}`;

  const animate = (el) => {
    const target = parseFloat(el.dataset.target) || 0;
    const decimals = parseInt(el.dataset.decimals || '0', 10);
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    const duration = 1600;

    if (reduceMotion) {
      el.textContent = formatValue(target, decimals, prefix, suffix);
      return;
    }

    const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
      el.textContent = formatValue(target * eased, decimals, prefix, suffix);
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  if (!('IntersectionObserver' in window)) {
    counters.forEach(animate);
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animate(entry.target);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.4 }
  );
  counters.forEach((el) => observer.observe(el));
};

const setupAccordion = () => {
  document.querySelectorAll('.pr-accordion').forEach((group) => {
    const items = group.querySelectorAll('.pr-accordion__item');
    items.forEach((item) => {
      const summary = item.querySelector('summary');
      if (!summary) return;
      summary.addEventListener('click', (e) => {
        e.preventDefault();
        const isOpen = item.open;
        // Close all first, then open the clicked one if it was closed
        items.forEach(i => { i.open = false; });
        if (!isOpen) item.open = true;
      });
    });
  });
};

const setupStickyCta = () => {
  const cta = document.querySelector('[data-pr-sticky-cta]');
  if (!cta) return;

  const dismissedKey = 'pr-sticky-cta-dismissed';
  if (sessionStorage.getItem(dismissedKey)) {
    cta.remove();
    return;
  }

  cta.hidden = false;

  const onScroll = () => {
    cta.classList.toggle('pr-sticky-cta--visible', window.scrollY > 300);
  };
  registerScroll(onScroll);

  cta.querySelector('[data-pr-sticky-close]')?.addEventListener('click', () => {
    sessionStorage.setItem(dismissedKey, '1');
    cta.classList.remove('pr-sticky-cta--visible');
    setTimeout(() => cta.remove(), 300);
  });
};

const setupArticleUtils = () => {
  document.querySelectorAll('[data-pr-utils]').forEach((bar) => {
    const shareBtn = bar.querySelector('[data-pr-share]');
    const printBtn = bar.querySelector('[data-pr-print]');
    const downloadBtn = bar.querySelector('[data-pr-download]');

    shareBtn?.addEventListener('click', async () => {
      const data = { title: document.title, url: window.location.href };
      try {
        if (navigator.share) {
          await navigator.share(data);
          return;
        }
      } catch (_) { /* user cancelled */ }
      try {
        await navigator.clipboard.writeText(data.url);
        const label = shareBtn.querySelector('span');
        if (!label) return;
        const original = label.textContent;
        label.textContent = 'Copied';
        shareBtn.classList.add('pr-article-utils__btn--copied');
        setTimeout(() => {
          label.textContent = original;
          shareBtn.classList.remove('pr-article-utils__btn--copied');
        }, 1500);
      } catch (_) { /* clipboard blocked — silently noop */ }
    });

    printBtn?.addEventListener('click', () => window.print());
    downloadBtn?.addEventListener('click', () => window.print());
  });
};

const setupRailCollapsibles = () => {
  const items = document.querySelectorAll('.pr-article-rail__card--collapsible');
  if (items.length === 0) return;

  const sync = () => {
    const isDesktop = window.matchMedia('(min-width: 1024px)').matches;
    items.forEach((el) => {
      el.open = isDesktop;
    });
  };

  sync();
  window.addEventListener('resize', sync);
};

const setupGlossarySearch = () => {
  const wrap = document.querySelector('[data-pr-search]');
  if (!wrap) return;
  const input = wrap.querySelector('[data-pr-search-input]');
  const dropdown = wrap.querySelector('[data-pr-search-results]');
  const clearBtn = wrap.querySelector('[data-pr-search-clear]');
  const indexEl = document.getElementById('pr-search-index') || document.getElementById('pr-glossary-index');
  if (!input || !dropdown || !indexEl) return;

  let index = [];
  try { index = JSON.parse(indexEl.textContent); } catch (_) { return; }

  let activeIdx = -1;

  const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const escapeHtml = (s) => String(s || '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const highlight = (text, q) => escapeHtml(text).replace(new RegExp(escapeRegExp(q), 'gi'), (m) => `<mark>${m}</mark>`);

  const render = (items, q) => {
    if (items.length === 0) {
      dropdown.innerHTML = '<li class="pr-search__result pr-search__result--empty">No matches</li>';
    } else {
      dropdown.innerHTML = items.map((item, i) => `
        <li class="pr-search__result${i === activeIdx ? ' is-active' : ''}">
          <a href="${escapeHtml(item.url)}">
            <strong>${highlight(item.title, q)}</strong>
            ${item.definition ? `<span>${highlight(item.definition.slice(0, 100), q)}${item.definition.length > 100 ? '…' : ''}</span>` : ''}
          </a>
        </li>
      `).join('');
    }
    dropdown.hidden = false;
  };

  const search = () => {
    const q = input.value.trim().toLowerCase();
    clearBtn.hidden = q.length === 0;
    if (q.length < 2) {
      dropdown.hidden = true;
      activeIdx = -1;
      return;
    }
    const matches = index.filter((item) =>
      item.title.toLowerCase().includes(q) ||
      (item.definition && item.definition.toLowerCase().includes(q))
    ).slice(0, 8);
    activeIdx = -1;
    render(matches, q);
  };

  input.addEventListener('input', search);
  input.addEventListener('focus', () => { if (input.value.trim().length >= 2) search(); });

  input.addEventListener('keydown', (e) => {
    const items = dropdown.querySelectorAll('.pr-search__result:not(.pr-search__result--empty)');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeIdx = Math.min(items.length - 1, activeIdx + 1);
      items.forEach((el, i) => el.classList.toggle('is-active', i === activeIdx));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeIdx = Math.max(-1, activeIdx - 1);
      items.forEach((el, i) => el.classList.toggle('is-active', i === activeIdx));
    } else if (e.key === 'Enter' && activeIdx >= 0) {
      e.preventDefault();
      items[activeIdx].querySelector('a')?.click();
    } else if (e.key === 'Escape') {
      input.blur();
      dropdown.hidden = true;
    }
  });

  clearBtn.addEventListener('click', () => {
    input.value = '';
    dropdown.hidden = true;
    clearBtn.hidden = true;
    input.focus();
  });

  document.addEventListener('click', (e) => {
    if (!wrap.contains(e.target)) dropdown.hidden = true;
  });
};

const setupPageToc = () => {
  const tocNav = document.querySelector('[data-pr-page-toc]');
  if (!tocNav) return;
  if (!('IntersectionObserver' in window)) return;

  const links = [...tocNav.querySelectorAll('a[href^="#"]')];
  if (links.length === 0) return;

  const linkByHash = new Map(links.map((a) => [a.getAttribute('href'), a.parentElement]));
  const headings = links
    .map((a) => document.getElementById(a.getAttribute('href').slice(1)))
    .filter(Boolean);
  if (headings.length === 0) return;

  let active = null;
  const setActive = (li) => {
    if (active === li) return;
    if (active) active.classList.remove('is-active');
    active = li;
    if (active) active.classList.add('is-active');
  };

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => a.target.offsetTop - b.target.offsetTop);
      if (visible.length > 0) {
        const li = linkByHash.get('#' + visible[0].target.id);
        if (li) setActive(li);
      }
    },
    { rootMargin: '-80px 0px -65% 0px', threshold: 0 }
  );
  headings.forEach((h) => observer.observe(h));
};

const setupInlineRelated = () => {
  document.querySelectorAll('[data-pr-inline-related]').forEach((body) => {
    const raw = body.dataset.relatedLinks;
    if (!raw) return;
    let links = [];
    try { links = JSON.parse(raw); } catch (_) { return; }
    if (!Array.isArray(links) || links.length === 0) return;

    const section = document.createElement('section');
    section.className = 'pr-inline-related-block';
    section.innerHTML = `
      <h3 class="pr-inline-related-block__title">Related reads</h3>
      <div class="pr-inline-related-block__list">
        ${links.map((link) => `
          <a class="pr-inline-related-block__item" href="${link.url}">
            <strong>${link.title}</strong>
            ${link.description ? `<span>${link.description}</span>` : ''}
          </a>
        `).join('')}
      </div>
    `;
    body.appendChild(section);
  });
};

// Clamp long "On this page" TOCs and add a Show more / Show less toggle.
const setupTocCollapse = () => {
  const CLAMP_PX = 360;
  document.querySelectorAll('.pr-article-rail__card--collapsible').forEach((card) => {
    const nav = card.querySelector('nav.pr-article-rail__toc, nav');
    if (!nav) return;
    if (nav.scrollHeight <= CLAMP_PX + 24) return;

    nav.classList.add('pr-toc-clamp', 'is-clamped');

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pr-toc-clamp__toggle';
    btn.setAttribute('aria-expanded', 'false');

    const updateLabel = () => {
      const expanded = !nav.classList.contains('is-clamped');
      btn.textContent = expanded ? 'Show less' : 'Show more';
      btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    };
    updateLabel();

    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();   // don't bubble into <summary>/<details>
      nav.classList.toggle('is-clamped');
      updateLabel();
    });

    nav.insertAdjacentElement('afterend', btn);
  });
};

// Recognise the "ranking" markdown pattern produced by our listicles and
// decorate it so each agency block becomes a styled card.
const setupListicleRankings = () => {
  const body = document.querySelector('.pr-listicle__body');
  if (!body) return;

  // The migrated markdown uses "- 1. Item" which Goldmark parses into
  // <ul><li><ol start="N"><li>Item</li></ol></li></ul> — both the UL bullet
  // and the OL number render. Detect this pattern and hide the outer UL bullet.
  body.querySelectorAll('ul').forEach((ul) => {
    const items = [...ul.children].filter((c) => c.tagName === 'LI');
    if (items.length < 3) return;
    const nested = items.filter((li) => {
      const kids = [...li.children];
      return kids.length === 1 && kids[0].tagName === 'OL';
    }).length;
    const inlineNumbered = items.filter((li) =>
      /^\d+\.\s/.test(li.textContent.trim())
    ).length;
    if ((nested + inlineNumbered) / items.length > 0.8) {
      ul.classList.add('pr-list--manual-numbered');
    }
  });

  const RANK_HEADING = /^(\d+)\.\s+(.+)$/;
  const NUMBER_ONLY = /^\d{1,3}(\.\d+)?$/;
  const BREAKDOWN = /^[A-Za-z][^|]*\d+\/\d+\s*\|/;
  const PREFIXES = [
    ['Best for you if:', 'pr-rank__best-for'],
    ['Best suited for:', 'pr-rank__suited-for'],
    ['Not ideal for:', 'pr-rank__not-ideal'],
    ['Pricing:', 'pr-rank__pricing'],
  ];

  body.querySelectorAll('h3').forEach((h3) => {
    const m = h3.textContent.trim().match(RANK_HEADING);
    if (!m) return;
    const rankNum = m[1];
    const agency = m[2];

    h3.classList.add('pr-rank__h3');
    h3.dataset.rank = rankNum.padStart(2, '0');
    // Replace text with rank badge + name spans (for fine-grained styling)
    h3.innerHTML =
      `<span class="pr-rank__badge">${rankNum.padStart(2, '0')}</span>` +
      `<span class="pr-rank__title">${agency}</span>`;

    // Walk forward through siblings, classify until next h3/h2
    let n = h3.nextElementSibling;
    while (n && n.tagName !== 'H3' && n.tagName !== 'H2') {
      if (n.tagName === 'P') {
        const text = n.textContent.trim();
        if (NUMBER_ONLY.test(text)) {
          n.classList.add('pr-rank__score');
        } else if (BREAKDOWN.test(text)) {
          // Split into pill list
          const parts = text.split(/\s*\|\s*/).filter(Boolean);
          n.classList.add('pr-rank__breakdown');
          n.innerHTML = parts
            .map((p) => `<span class="pr-rank__metric">${p}</span>`)
            .join('');
        } else {
          for (const [prefix, cls] of PREFIXES) {
            if (text.startsWith(prefix)) {
              n.classList.add(cls);
              break;
            }
          }
        }
      }
      n = n.nextElementSibling;
    }
  });
};

// =========================================================
// Scroll reveal — fade-up on viewport entry. Applied to
// homepage section blocks and stagger-eligible card grids.
// Respects prefers-reduced-motion: skipped entirely.
// =========================================================
const setupReveals = () => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!('IntersectionObserver' in window)) return;

  // Only reveal whole sections on the homepage (body.page-home),
  // not on inner pages where the section is already in the viewport on load.
  const isHome = document.body.classList.contains('page-home');
  const selector = [
    // Whole sections — homepage only
    ...(isHome ? [
      'main > .pr-section:not(.pr-section--outcome):not(.pr-section--pov)',
      'main > .pr-section--tight:not(.pr-section--outcome):not(.pr-section--pov)',
      'main > .pr-section--dark:not(.pr-section--outcome):not(.pr-section--pov)',
      'main > .pr-cta-final',
      'main > .pr-certified',
    ] : []),
    // Card grids that benefit from stagger (all pages)
    '.pr-cases .pr-case',
    '.pr-approach .pr-approach__card',
    '.pr-pov .pr-pov__card',
    '.pr-twocol .pr-twocol__card',
    '.pr-features .pr-feature',
    '.pr-points .pr-point',
  ].join(',');

  const targets = document.querySelectorAll(selector);
  if (targets.length === 0) return;

  targets.forEach((el) => el.classList.add('pr-reveal'));

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
  );

  targets.forEach((el) => io.observe(el));
};

// Fade in the compare section intro paragraph on scroll
const setupCompareIntro = () => {
  const el = document.querySelector('.pr-compare__intro');
  if (!el) return;
  const io = new IntersectionObserver(
    ([entry]) => { if (entry.isIntersecting) { el.classList.add('is-revealed'); io.unobserve(el); } },
    { threshold: 0.2 }
  );
  io.observe(el);
};

// Reveal the certified-section stroke left-to-right on scroll
const setupStrokeReveal = () => {
  const stroke = document.querySelector('.pr-certified__stroke');
  const section = document.querySelector('.pr-certified');
  if (!stroke || !section) return;
  const io = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        stroke.classList.add('is-revealed');
        io.unobserve(section);
      }
    },
    { threshold: 0.2 }
  );
  io.observe(section);
};

// Scroll-based parallax animation for the car section
const setupParallax = () => {
  const section = document.querySelector('[data-parallax-section]');
  const car = document.querySelector('[data-parallax-car]');
  if (!section || !car) return;

  const handleScroll = () => {
    const rect = section.getBoundingClientRect();
    const sectionHeight = section.offsetHeight;
    const viewportHeight = window.innerHeight;

    // Calculate how far through the section we are (0 to 1)
    const scrollProgress = Math.max(0, Math.min(1,
      (viewportHeight - rect.top) / (viewportHeight + sectionHeight)
    ));

    const sectionWidth = section.offsetWidth;
    const startOffset = sectionWidth * -0.2;
    const endOffset   = sectionWidth * 0.45;
    const driveProgress = scrollProgress;
    const moveAmount = startOffset + driveProgress * (endOffset - startOffset);

    car.style.transform = `translateX(${moveAmount}px)`;
  };

  registerScroll(handleScroll);
};
// Scroll-based parallax for the SEO hero arrow — starts at CSS position, drifts toward search bar as user scrolls
const setupArrowParallax = () => {
  const arrow = document.querySelector('[data-arrow-parallax]');
  if (!arrow) return;
  const section = arrow.closest('.pr-hero');
  if (!section) return;

  const handleScroll = () => {
    const sectionHeight = section.offsetHeight;
    const progress = Math.max(0, Math.min(1, window.scrollY / (sectionHeight * 1.2)));

    const moveX = progress * -180;
    const moveY = progress * -120;
    arrow.style.transform = `translate(${moveX}px, ${moveY}px)`;
  };

  registerScroll(handleScroll);
};

// Scroll parallax for the CTA final section decorative elements
const setupCtaParallax = () => {
  const section = document.querySelector('.pr-cta-final');
  const mark  = document.querySelector('[data-cta-mark]');
  const phone = document.querySelector('[data-cta-phone]');
  if (!section || (!mark && !phone)) return;

  const handleScroll = () => {
    const rect = section.getBoundingClientRect();
    const sectionHeight = section.offsetHeight;
    const viewportHeight = window.innerHeight;
    const progress = Math.max(0, Math.min(1,
      (viewportHeight - rect.top) / (viewportHeight + sectionHeight)
    ));
    const offset = (progress - 0.5) * 120;
    if (mark)  mark.style.transform  = `translate(${offset * 0.6}px, ${-offset}px)`;
    if (phone) phone.style.transform = `translate(${-offset * 0.6}px, ${-offset}px)`;
  };

  registerScroll(handleScroll);
};

const setupOutcomeSection = () => {
  const section = document.querySelector('[data-outcome-section]');
  const rocket  = document.querySelector('[data-outcome-rocket]');
  if (!section) return;

  // Trigger underline animation for all instances when they enter view
  if ('IntersectionObserver' in window) {
    const underlineTargets = [
      ...document.querySelectorAll('.pr-underline-anim'),
      ...document.querySelectorAll('.pr-pov__underline-wrap'),
      ...document.querySelectorAll('.pr-outcome__underline-wrap')
    ];
    underlineTargets.forEach(el => {
      const obs = new IntersectionObserver((entries) => {
        entries.forEach(e => { if (e.isIntersecting) { el.classList.add('is-visible'); obs.unobserve(e.target); } });
      }, { threshold: 0.3 });
      obs.observe(el);
    });
  }

  // Scroll-based rocket rise — moves up-right in the direction the arrow points (~45°)
  if (!rocket) return;
  const handleScroll = () => {
    const rect = section.getBoundingClientRect();
    const progress = Math.max(0, Math.min(1,
      (window.innerHeight - rect.top) / (window.innerHeight + section.offsetHeight)
    ));
    const rise = progress * 200;
    rocket.style.transform = `translate(${rise * 2}px, ${-rise}px)`;
  };
  registerScroll(handleScroll);
};

const init = () => {
  setupMobileMenu();
  setupCounters();
  setupAccordion();
  setupStickyCta();
  setupRailCollapsibles();
  setupArticleUtils();
  setupGlossarySearch();
  setupInlineRelated();
  setupPageToc();
  setupTocCollapse();
  setupListicleRankings();
  setupStickyGlossarySearch();
  setupAlsoReadCallouts();
  setupCtaModal();
  setupStoriesFilter();
  setupReviewsFilter();
  setupClutchAccordion();
  setupReveals();
  setupCompareIntro();
  setupStrokeReveal();
  setupParallax();
  setupArrowParallax();
  setupCtaParallax();
  setupOutcomeSection();
  setupTestimonialDots();
  setupAiGridHeight();
};

// =========================================================
// AI section: lock image column to max accordion height
// =========================================================
const setupAiGridHeight = () => {
  const media = document.querySelector('.pr-ai-grid__media');
  const accordion = document.querySelector('.pr-ai-grid .pr-accordion');
  if (!media || !accordion) return;

  const items = accordion.querySelectorAll('.pr-accordion__item');
  let maxH = 0;

  // Measure height with each item open individually
  items.forEach(item => {
    items.forEach(i => i.removeAttribute('open'));
    item.setAttribute('open', '');
    maxH = Math.max(maxH, accordion.offsetHeight);
  });

  // Restore default (first item open)
  items.forEach(i => i.removeAttribute('open'));
  items[0].setAttribute('open', '');

  media.style.minHeight = maxH + 'px';
};

// =========================================================
// Testimonials dot pagination
// =========================================================
const setupTestimonialDots = () => {
  const track    = document.querySelector('[data-testimonials-track]');
  const dots     = document.querySelectorAll('[data-testimonial-dot]');
  if (!track || !dots.length) return;

  const activeImg   = '/images/dot-active.png';
  const inactiveImg = '/images/dot-inactive.png';
  const perPage = 3;

  let currentPage = 0;
  let direction = 1;
  const totalPages = dots.length;

  const cards = track.querySelectorAll('.pr-testimonial');

  const goToPage = (page) => {
    const card = cards[0];
    if (!card) return;
    const cardW = card.offsetWidth;
    const gap = parseInt(getComputedStyle(track).gap) || 10;
    const pageW = (cardW + gap) * perPage;
    track.style.transform = `translateX(-${page * pageW}px)`;

    dots.forEach((dot, i) => {
      const img = dot.querySelector('img');
      const isActive = i === page;
      dot.classList.toggle('pr-testimonials__dot--active', isActive);
      if (img) img.src = isActive ? activeImg : inactiveImg;
    });
  };

  dots.forEach(dot => {
    dot.addEventListener('click', () => {
      currentPage = parseInt(dot.dataset.testimonialDot, 10);
      direction = 1;
      goToPage(currentPage);
      resetAutoPlay();
    });
  });

  const advance = () => {
    const next = currentPage + direction;
    if (next >= totalPages || next < 0) {
      direction *= -1;
    }
    currentPage += direction;
    goToPage(currentPage);
  };

  let timer = setInterval(advance, 9000);

  const resetAutoPlay = () => {
    clearInterval(timer);
    timer = setInterval(advance, 9000);
  };

  goToPage(0);
};

// =========================================================
// Clutch reviews accordion + horizontal carousel — homepage
// (and reusable for other pages once approved).
// =========================================================
const setupClutchAccordion = () => {
  const toggles = document.querySelectorAll('[data-clutch-accordion-toggle]');
  if (!toggles.length) return;

  toggles.forEach((toggle) => {
    const panelId = toggle.getAttribute('aria-controls');
    const panel = panelId ? document.getElementById(panelId) : toggle.parentElement.querySelector('[data-clutch-accordion-panel]');
    if (!panel) return;

    toggle.addEventListener('click', () => {
      const expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expanded));
      panel.hidden = expanded;
    });

    // Carousel arrows
    const track = panel.querySelector('[data-carousel-track]');
    const prevBtn = panel.querySelector('[data-carousel-prev]');
    const nextBtn = panel.querySelector('[data-carousel-next]');
    if (!track || !prevBtn || !nextBtn) return;

    const scrollByCard = (dir) => {
      const card = track.querySelector('.pr-clutch-card');
      if (!card) return;
      const step = card.getBoundingClientRect().width + 16; // card width + gap
      track.scrollBy({ left: dir * step, behavior: 'smooth' });
    };
    prevBtn.addEventListener('click', () => scrollByCard(-1));
    nextBtn.addEventListener('click', () => scrollByCard(1));

    // Disable arrows at scroll extremes
    const updateArrows = () => {
      prevBtn.disabled = track.scrollLeft <= 4;
      nextBtn.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 4;
    };
    track.addEventListener('scroll', updateArrows, { passive: true });
    window.addEventListener('resize', updateArrows, { passive: true });
    // Initialize once panel becomes visible OR if open by default
    const observer = new MutationObserver(() => {
      if (!panel.hidden) requestAnimationFrame(updateArrows);
    });
    observer.observe(panel, { attributes: true, attributeFilter: ['hidden'] });
    // Run once on init for panels that start open (service pages)
    if (!panel.hidden) requestAnimationFrame(updateArrows);
  });
};

// Reusable filter wiring — pills toggle visibility of cards with matching data-services.
const wireFilter = ({ filter, grid, empty, cardSelector }) => {
  if (!filter || !grid) return;
  const cards = Array.from(grid.querySelectorAll(cardSelector));
  const apply = (value) => {
    let visible = 0;
    cards.forEach((card) => {
      const services = (card.dataset.services || '').split(',');
      const match = value === 'all' || services.includes(value);
      card.hidden = !match;
      if (match) visible++;
    });
    if (empty) empty.hidden = visible !== 0;
  };
  const setActive = (btn) => {
    filter.querySelectorAll('.pr-stories__pill').forEach((b) => b.classList.toggle('is-active', b === btn));
  };
  filter.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-filter]');
    if (!btn) return;
    setActive(btn);
    apply(btn.dataset.filter);
  });
  if (empty) {
    empty.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-filter]');
      if (!btn) return;
      const allBtn = filter.querySelector('[data-filter="all"]');
      if (allBtn) { setActive(allBtn); apply('all'); }
    });
  }
};

const setupReviewsFilter = () => {
  wireFilter({
    filter: document.querySelector('[data-reviews-filter]'),
    grid:   document.querySelector('[data-reviews-grid]'),
    empty:  document.querySelector('[data-reviews-empty]'),
    cardSelector: '.pr-review-card',
  });
};

// =========================================================
// /success-stories/ filter pills — toggle visibility of cards
// based on which service-tag pill is selected.
// =========================================================
const setupStoriesFilter = () => {
  const filter = document.querySelector('[data-stories-filter]');
  const grid = document.querySelector('[data-stories-grid]');
  const empty = document.querySelector('[data-stories-empty]');
  if (!filter || !grid) return;

  const cards = Array.from(grid.querySelectorAll('.pr-story-card'));

  const apply = (value) => {
    let visible = 0;
    cards.forEach((card) => {
      const services = (card.dataset.services || '').split(',');
      const match = value === 'all' || services.includes(value);
      card.hidden = !match;
      if (match) visible++;
    });
    if (empty) empty.hidden = visible !== 0;
  };

  const setActive = (btn) => {
    filter.querySelectorAll('.pr-stories__pill').forEach((b) => b.classList.toggle('is-active', b === btn));
  };

  filter.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-filter]');
    if (!btn) return;
    setActive(btn);
    apply(btn.dataset.filter);
  });

  // "Show all" button inside the empty state
  if (empty) {
    empty.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-filter]');
      if (!btn) return;
      const allBtn = filter.querySelector('[data-filter="all"]');
      if (allBtn) { setActive(allBtn); apply('all'); }
    });
  }
};

// =========================================================
// Free Funnel Audit modal — opens on CTA click, hosts the same HubSpot form
// used on /contact-us/. The HubSpot embed is loaded lazily on first open
// (so it doesn't fight with the page-level embed on /contact-us/).
// UTM params are pushed into the URL (replaceState) when the modal opens,
// so HubSpot's standard tracking picks them up.
// =========================================================
const setupCtaModal = () => {
  const modal = document.getElementById('prFunnelAuditModal');
  if (!modal) return;

  const portalId = modal.dataset.hsPortal;
  const formId = modal.dataset.hsForm;
  const region = modal.dataset.hsRegion || 'na1';
  const targetSelector = `#hsForm-modal-${formId}`;

  let lastFocused = null;
  let hsLoaded = false;

  const applyUtmParams = (ctaSource) => {
    const url = new URL(window.location.href);
    const p = url.searchParams;
    if (!p.get('utm_source'))   p.set('utm_source', 'site');
    if (!p.get('utm_medium'))   p.set('utm_medium', ctaSource || 'header_cta');
    if (!p.get('utm_campaign')) p.set('utm_campaign', 'free_funnel_audit');
    history.replaceState({}, '', url.toString());
  };

  // Load HubSpot embed script once (shared with any page-level embed).
  const ensureHubspotScript = () => new Promise((resolve) => {
    if (window.hbspt && window.hbspt.forms) return resolve();
    const existing = document.querySelector(`script[src*="js-${region}.hsforms.net/forms/embed/v2.js"]`);
    if (existing) {
      existing.addEventListener('load', resolve, { once: true });
      if (window.hbspt && window.hbspt.forms) resolve();
      return;
    }
    const s = document.createElement('script');
    s.src = `https://js-${region}.hsforms.net/forms/embed/v2.js`;
    s.charset = 'utf-8';
    s.onload = resolve;
    document.head.appendChild(s);
  });

  const renderHubspotForm = async () => {
    if (hsLoaded || !portalId || !formId) return;
    await ensureHubspotScript();
    // Wait one tick so window.hbspt is fully ready.
    await new Promise((r) => setTimeout(r, 0));
    if (!window.hbspt || !window.hbspt.forms) return;
    const cssRequired = ""
      + "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');"
      + "html,body{background:transparent !important;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif !important;color:#0D0D0D !important;margin:0 !important;padding:0 !important}"
      + ".hs-form,.hs-form fieldset{max-width:100% !important;width:100% !important}"
      + ".hs-form-field{margin-bottom:18px !important}"
      + ".hs-form-field>label,.hs-form-booleancheckbox-display>span{display:block !important;font-size:13px !important;font-weight:600 !important;color:#0D0D0D !important;margin:0 0 6px !important;letter-spacing:.005em}"
      + ".hs-form-required{color:#E63946 !important;margin-left:3px}"
      + ".hs-input,.hs-input.hs-fieldtype-intl-phone select{display:block !important;width:100% !important;box-sizing:border-box !important;background:#F6F6F1 !important;border:1.5px solid #D9D5C9 !important;border-radius:6px !important;padding:11px 14px !important;font-size:14.5px !important;font-family:inherit !important;color:#0D0D0D !important;line-height:1.45 !important;transition:border-color .15s,box-shadow .15s,background .15s !important;-webkit-appearance:none;appearance:none}"
      + "textarea.hs-input{min-height:110px;resize:vertical}"
      + ".hs-input:focus,.hs-input:focus-visible{outline:none !important;border-color:#0CC6F1 !important;background:#FFFFFF !important;box-shadow:0 0 0 3px rgba(12,198,241,.18) !important}"
      + ".hs-input::placeholder{color:#9A9A9A !important;opacity:1}"
      + ".inputs-list{list-style:none !important;padding:0 !important;margin:0 !important;display:flex !important;flex-direction:column !important;gap:8px}"
      + ".inputs-list .hs-form-radio,.inputs-list .hs-form-checkbox{margin:0 !important}"
      + ".inputs-list label{display:flex !important;align-items:center !important;gap:9px !important;padding:9px 12px !important;background:#F6F6F1 !important;border:1.5px solid #D9D5C9 !important;border-radius:6px !important;font-size:14px !important;font-weight:500 !important;color:#0D0D0D !important;cursor:pointer !important;transition:border-color .15s,background .15s !important}"
      + ".inputs-list label:hover{border-color:#0CC6F1 !important;background:rgba(12,198,241,.05) !important}"
      + ".inputs-list input[type=radio],.inputs-list input[type=checkbox]{accent-color:#0CC6F1 !important;width:16px !important;height:16px !important;margin:0 !important}"
      + ".hs-fieldtype-intl-phone .input{display:flex !important;gap:8px !important}"
      + ".hs-fieldtype-intl-phone .hs-input{flex:1 !important}"
      + ".hs-error-msgs,.hs-error-msg{list-style:none !important;padding:0 !important;margin:6px 0 0 !important;color:#C0392B !important;font-size:12.5px !important;font-weight:500}"
      + ".legal-consent-container,.hs-richtext{font-size:12.5px !important;color:#6B6B6B !important;line-height:1.55 !important;margin:8px 0 !important}"
      + ".hs-button,input[type=submit].hs-button{display:inline-flex !important;align-items:center !important;justify-content:center !important;background:#0CC6F1 !important;color:#0D0D0D !important;border:0 !important;padding:13px 26px !important;border-radius:6px !important;font-family:inherit !important;font-size:15px !important;font-weight:700 !important;letter-spacing:.005em;cursor:pointer !important;box-shadow:0 4px 14px rgba(12,198,241,.25) !important;transition:background .15s,transform .12s,box-shadow .2s !important;width:auto !important;margin-top:6px}"
      + ".hs-button:hover,input[type=submit].hs-button:hover{background:#09B3DA !important;transform:translateY(-1px) !important;box-shadow:0 6px 18px rgba(12,198,241,.35) !important}"
      + ".hs-button:focus-visible{outline:3px solid rgba(12,198,241,.4) !important;outline-offset:2px}"
      + ".submitted-message{background:rgba(12,198,241,.08) !important;border-left:3px solid #0CC6F1 !important;border-radius:4px !important;padding:18px !important;color:#0D0D0D !important;font-size:14.5px !important;line-height:1.6}"
      + ".hs-form-field .input{margin:0 !important}";
    window.hbspt.forms.create({
      region,
      portalId,
      formId,
      target: targetSelector,
      cssRequired,
    });
    hsLoaded = true;
  };

  const open = (ctaSource) => {
    applyUtmParams(ctaSource);
    lastFocused = document.activeElement;
    modal.hidden = false;
    document.body.classList.add('pr-modal-open');
    renderHubspotForm();
  };

  const close = () => {
    modal.hidden = true;
    document.body.classList.remove('pr-modal-open');
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  };

  document.querySelectorAll('[data-modal-trigger="funnel-audit"]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      open(btn.dataset.ctaSource || 'header_cta');
    });
  });

  modal.querySelectorAll('[data-modal-close]').forEach((el) => {
    el.addEventListener('click', close);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.hidden) close();
  });
};

// Detect "**Also read:** [link](url)" paragraphs and style them as
// inline callouts so they read as clickable cards, not body copy.
const setupAlsoReadCallouts = () => {
  const bodies = document.querySelectorAll('.pr-blog__body, .pr-listicle__body, .pr-glossary__body');
  bodies.forEach((body) => {
    body.querySelectorAll('p').forEach((p) => {
      const first = p.firstElementChild;
      if (!first || first.tagName !== 'STRONG') return;
      const label = first.textContent.trim().replace(/[:：]\s*$/, '').toLowerCase();
      if (label === 'also read' || label === 'related' || label === 'read next' || label === 'related read') {
        if (p.querySelector('a')) p.classList.add('pr-also-read');
      }
    });
  });
};

// Toggle .is-stuck on the glossary search bar when it pins to the header.
const setupStickyGlossarySearch = () => {
  const search = document.querySelector('.pr-glossary__search-top');
  if (!search) return;
  // Sentinel element placed just above the search bar; when it leaves the
  // viewport (scrolls under the header), we know the search has stuck.
  const sentinel = document.createElement('div');
  sentinel.style.cssText = 'position:absolute;height:1px;width:1px;';
  search.before(sentinel);
  const io = new IntersectionObserver(
    ([entry]) => search.classList.toggle('is-stuck', !entry.isIntersecting),
    { rootMargin: '-72px 0px 0px 0px', threshold: 0 }
  );
  io.observe(sentinel);
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
