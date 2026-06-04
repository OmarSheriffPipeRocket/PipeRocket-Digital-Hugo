// PurgeCSS — strips unused selectors from Hugo's fingerprinted CSS bundle
// to fix the render-blocking-CSS and unused-CSS Lighthouse audits.
//
// Runs after Hugo. Hugo emits the minified CSS at
//   public/css/main.min.<fingerprint>.css
// and references it from every page. PurgeCSS rewrites that file in place,
// keeping the same filename so the HTML references stay valid.

module.exports = {
  // Scan the rendered HTML so we see the actual class names Hugo emits,
  // including markdown-generated ones. Also scan source layouts/JS for
  // safety (Hugo public/ does not include source maps).
  content: [
    'public/**/*.html',
    'public/**/*.js',
    'layouts/**/*.html',
    'assets/js/**/*.js',
  ],

  // Target ONLY the main fingerprinted bundle Hugo writes to /public/css/.
  // It is loaded WITHOUT an integrity attribute, so rewriting it in place is
  // safe. Every other CSS file (listicle, blog-v2, compare, glossary, …) is
  // loaded WITH a Subresource-Integrity hash computed by Hugo — purging those
  // in place changes their bytes, breaks the SRI hash, and the browser then
  // silently refuses to apply them (banner/layout renders unstyled). So the
  // glob must stay scoped to main.min.*.css only.
  css: ['public/css/main.min.*.css'],

  // Default extractor splits on whitespace; this one also keeps class names
  // that contain ':' (Tailwind-like) and standard BEM separators.
  defaultExtractor: (content) => content.match(/[A-Za-z0-9_:/-]+/g) || [],

  // Output to the same path (in-place overwrite via the directory).
  output: 'public/css/',

  // Selectors that must never be removed — these are added at runtime by
  // assets/js/main.js (IntersectionObserver, modal/menu toggles, typewriter
  // reveal) or rendered by markdown content the build doesn't statically
  // know about.
  safelist: {
    standard: [
      // Body-level state classes
      'page-home',
      'pr-modal-open',
      'pr-nav-locked',

      // Header / nav
      'pr-nav--open',

      // Sticky CTA
      'pr-sticky-cta--visible',

      // Reveal animations + intersection observer toggles
      'pr-reveal',
      'is-active',
      'is-clamped',
      'is-expanded',
      'is-open',
      'is-revealed',
      'is-stuck',
      'is-typing',
      'is-visible',

      // About letter typewriter (each character span)
      'pr-letter-ch',

      // Article utilities (copy-link button)
      'pr-article-utils__btn--copied',
      'pr-also-read',

      // Listicle rank table
      'pr-rank__best-for--ours',
      'pr-rank__breakdown',
      'pr-rank__h3',
      'pr-rank__score',

      // Misc dynamic
      'pr-list--manual-numbered',
      'pr-testimonials__dot--active',
      'pr-toc-clamp',
    ],
    // Keep anything matching these patterns. Useful for markdown-rendered
    // HTML (e.g. Chroma syntax highlighting) and any class whose suffix is
    // computed at runtime.
    greedy: [
      /^chroma/,    // Chroma code-block highlighting tokens
      /^highlight/, // Hugo highlight wrapper
      /^hljs/,      // legacy highlight.js if any imported snippets use it
    ],
    // Always keep these pseudo states/attributes.
    deep: [
      /^pr-modal/,  // modal classes can be toggled by JS we may add later
    ],
  },
};
