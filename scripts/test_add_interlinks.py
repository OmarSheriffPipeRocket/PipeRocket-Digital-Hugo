#!/usr/bin/env python3
"""Unit tests for add_interlinks.py — verifies R5a (word-450 floor),
R5d (per-paragraph dedupe), target dedupe, and protected-span handling.

Run: python scripts/test_add_interlinks.py
"""
import os, re, sys, tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import add_interlinks as ai


def fake_body(words_before=500, paragraphs=None):
    """Generate a body with `words_before` filler words, then any given paragraphs."""
    intro = " ".join(["word"] * words_before) + "\n\n"
    if paragraphs:
        intro += "\n\n".join(paragraphs)
    return intro


def write_md(tmpdir, slug, body):
    fm = '---\ntitle: "Test"\nslug: "%s"\n---\n' % slug
    p = Path(tmpdir) / f"{slug}.md"
    p.write_text(fm + body, encoding="utf-8")
    return p


def run_with_link_map(link_map, body, skip_faq=False, word_gate=ai.WORD_GATE,
                      source_type="blogs"):
    """Process a single file with a custom link map, return (logged_entries, new_body)."""
    orig = ai.LINK_MAP
    ai.LINK_MAP = link_map
    try:
        with tempfile.TemporaryDirectory() as td:
            f = write_md(td, "test", body)
            new_content, log, err = ai.process_file(f, skip_faq=skip_faq, word_gate=word_gate,
                                                    source_type=source_type)
            if err:
                return [], None
            _, new_body = ai.split_frontmatter(new_content)
            return log, new_body
    finally:
        ai.LINK_MAP = orig


# ---------- TESTS ----------

def test_r5a_skips_before_w450():
    # word "PPC" appears at word 0 — must NOT be wrapped
    body = "PPC. " + (" ".join(["filler"] * 600))
    log, new = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")], body)
    assert log == [], f"R5a violation — wrapped at intro: {log}"
    assert "[PPC]" not in new, "should not have inserted link"
    print("✓ R5a: skips anchor before word 450")


def test_r5a_wraps_after_w450():
    # word "PPC" appears at word 0 AND at word 600 — should wrap the 600 one
    body = (" ".join(["filler"] * 500)) + " PPC. " + (" ".join(["tail"] * 50))
    log, new = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")], body)
    assert len(log) == 1, f"expected 1 wrap, got {log}"
    assert log[0]["word_pos"] >= ai.WORD_GATE, f"wrapped at w{log[0]['word_pos']}, expected ≥{ai.WORD_GATE}"
    assert "[PPC](/glossary/what-is-ppc/)" in new
    print(f"✓ R5a: wraps at word {log[0]['word_pos']} (≥450)")


def test_r5a_word_counting_uses_w_boundary():
    """Hyphenated terms like 'pay-per-click' count as 3 words, not 1.
    Verifies the \\b\\w+\\b counting (fix vs the WP applier's \\S+ counting).
    """
    # 150 instances of "pay-per-click" = 450 \w words exactly
    body = ("pay-per-click " * 150) + " PPC. " + " ".join(["tail"] * 50)
    log, new = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")], body)
    assert len(log) == 1, f"expected wrap, got {log}"
    assert log[0]["word_pos"] >= 450, f"word_pos={log[0]['word_pos']}"
    print(f"✓ R5a: \\b\\w+\\b counts 'pay-per-click' as 3 words (PPC landed at w{log[0]['word_pos']})")


def test_r5d_same_paragraph_blocked():
    """Two different targets in the same paragraph — only first should wrap."""
    pad = " ".join(["filler"] * 500)
    para = "Use the meta description and canonical tag together for clean SERPs."
    body = pad + "\n\n" + para
    link_map = [
        ("meta description", "/glossary/what-is-a-meta-description/", False, "P2"),
        ("canonical tag", "/glossary/what-is-a-canonical-tag/", False, "P2"),
    ]
    log, new = run_with_link_map(link_map, body)
    assert len(log) == 1, f"R5d violation — both wrapped in same paragraph: {log}"
    print(f"✓ R5d: blocks 2nd anchor in same paragraph (wrapped '{log[0]['anchor']}' only)")


def test_r5d_different_paragraphs_both_wrap():
    pad = " ".join(["filler"] * 500)
    body = pad + "\n\nFirst para mentions meta description here.\n\nSecond para mentions canonical tag here."
    link_map = [
        ("meta description", "/glossary/what-is-a-meta-description/", False, "P2"),
        ("canonical tag", "/glossary/what-is-a-canonical-tag/", False, "P2"),
    ]
    log, new = run_with_link_map(link_map, body)
    assert len(log) == 2, f"both should wrap (different paragraphs): {log}"
    print("✓ R5d: allows anchors in different paragraphs")


def test_target_dedupe_skips_already_linked():
    """If a target URL is already linked anywhere in the body, don't add another."""
    pad = " ".join(["filler"] * 500)
    body = (
        "Pre-existing [PPC link](/glossary/what-is-ppc/) at start.\n\n"
        + pad + "\n\nAnother PPC mention should NOT be wrapped."
    )
    log, _ = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")], body)
    assert log == [], f"should skip already-linked target, got {log}"
    print("✓ Target dedupe: skips already-linked URLs")


def test_protected_spans():
    """Don't wrap inside existing markdown links, code, or bare URLs."""
    pad = " ".join(["filler"] * 500)
    body = pad + "\n\n[Already linked PPC](/blogs/foo/) and `code PPC` and https://example.com/PPC must not match."
    log, new = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")], body)
    assert log == [], f"should not wrap inside protected spans: {log}"
    print("✓ Protected spans: skips inside links/code/URLs")


def test_faq_skip_off_by_default():
    """Default: don't skip FAQ section (per user override)."""
    pad = " ".join(["filler"] * 500)
    body = pad + "\n\n## Frequently Asked Questions\n\nThis paragraph mentions PPC."
    log, _ = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")], body, skip_faq=False)
    assert len(log) == 1, f"default should wrap inside FAQ: {log}"
    print("✓ FAQ skip: off by default (PPC wrapped inside FAQ section)")


def test_faq_skip_on_when_requested():
    pad = " ".join(["filler"] * 500)
    body = pad + "\n\n## Frequently Asked Questions\n\nThis paragraph mentions PPC."
    log, _ = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")], body, skip_faq=True)
    assert log == [], f"--skip-faq should block FAQ section: {log}"
    print("✓ FAQ skip: --skip-faq blocks FAQ-section anchors")


def test_conclusion_skip_on():
    pad = " ".join(["filler"] * 500)
    body = pad + "\n\n## Conclusion\n\nIn closing, our SEO approach wins."
    log, _ = run_with_link_map([("SEO", "/glossary/what-is-seo/", True, "P2")], body, skip_faq=True)
    assert log == [], f"Conclusion should be skipped under --skip-faq: {log}"
    print("✓ Conclusion skip: blocks anchors under ## Conclusion")


def test_per_type_word_gate():
    """Lower word gates (e.g. for glossary/list) allow earlier anchors."""
    body = "Intro mentions PPC at word 1. " + " ".join(["filler"] * 100)
    # blogs gate (w450) — should NOT wrap
    log_b, _ = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")], body, word_gate=450)
    assert log_b == [], f"w450 gate should block: {log_b}"
    # glossary/compare gate (w0) — should wrap
    log_g, new_g = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")], body, word_gate=0)
    assert len(log_g) == 1, f"w0 gate should wrap intro mention: {log_g}"
    print(f"✓ Per-type gate: w450 blocks, w0 allows (glossary/compare use w0)")


def test_flow_blog_to_glossary_allowed():
    """Rule 11 (user override): blog → glossary allowed."""
    body = " ".join(["filler"] * 460) + " PPC term."
    log, _ = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")],
                                body, source_type="blogs", word_gate=0)
    assert len(log) == 1, f"blog→glossary should be allowed: {log}"
    print("✓ Flow: blogs → glossary allowed (rule 11 override)")


def test_flow_compare_to_glossary_disallowed():
    """Compare as source: only same-type allowed. compare→glossary blocked."""
    body = "Compare body mentions PPC term and SEO term."
    log, _ = run_with_link_map([("PPC", "/glossary/what-is-ppc/", True, "P2")],
                                body, source_type="compare", word_gate=0)
    assert log == [], f"compare→glossary must be blocked: {log}"
    print("✓ Flow: compare → glossary blocked (not in allow-list)")


def test_flow_alternative_to_compare_allowed():
    """Rule 10: alternative → compare."""
    body = "We compared this in our KlientBoost vs review."
    log, _ = run_with_link_map(
        [("KlientBoost", "/compare/piperocket-digital-vs-klientboost/", False, "P0")],
        body, source_type="alternative", word_gate=0)
    assert len(log) == 1, f"alternative→compare should be allowed: {log}"
    print("✓ Flow: alternative → compare allowed (rule 10)")


def test_flow_alternative_to_blog_disallowed():
    """Alternative only → compare (rule 10) or self (rule 1). Not to blogs."""
    body = "Some prose mentioning PPC."
    log, _ = run_with_link_map([("PPC", "/blogs/saas-ppc/", True, "P0")],
                                body, source_type="alternative", word_gate=0)
    assert log == [], f"alternative→blog must be blocked: {log}"
    print("✓ Flow: alternative → blog blocked")


def test_flow_listicle_to_blog_after_5th_blocks_early():
    """Rule 6: listicle→blog only after 5th agency entry. Anchor before 5th must be skipped."""
    intro = "Intro mentions SaaS PPC here. " + " ".join(["filler"] * 250)
    body = intro + "\n\n### 1. Agency One\nA\n\n### 2. Agency Two\nB\n\n### 3. Agency Three\nC\n\n"
    log, _ = run_with_link_map([("SaaS PPC", "/blogs/saas-ppc/", False, "P0")],
                                body, source_type="list", word_gate=0)
    assert log == [], f"listicle→blog before 5th entry must be blocked: {log}"
    print("✓ Flow: listicle → blog before 5th entry blocked (rule 6)")


def test_flow_listicle_to_blog_after_5th_allows_late():
    body = (
        "Intro " + " ".join(["filler"] * 50) +
        "\n\n### 1. Agency One\nA\n\n### 2. Agency Two\nB\n\n### 3. Agency Three\nC"
        "\n\n### 4. Agency Four\nD\n\n### 5. Agency Five\nE\n\n"
        "After fifth entry we mention SaaS PPC for the first time."
    )
    log, _ = run_with_link_map([("SaaS PPC", "/blogs/saas-ppc/", False, "P0")],
                                body, source_type="list", word_gate=0)
    assert len(log) == 1, f"listicle→blog after 5th entry must wrap: {log}"
    print("✓ Flow: listicle → blog after 5th entry allowed (rule 6)")


def test_flow_listicle_to_service_no_5th_restriction():
    """Rule 8: listicle→service has no after-5th restriction — can link early."""
    body = "Early in the intro we mention our agency: saas-seo-agency.\n\n### 1. Foo\nbar"
    log, _ = run_with_link_map([("saas-seo-agency", "/saas-seo-agency/", False, "P0")],
                                body, source_type="list", word_gate=0)
    assert len(log) == 1, f"listicle→service should wrap regardless of position: {log}"
    print("✓ Flow: listicle → service no 5th-entry gate (rule 8)")


def test_self_link_suppression():
    """A page must never link to itself."""
    import os, tempfile
    body = "Intro mentions WebFX comparison topic. " + " ".join(["filler"] * 50)
    orig = ai.LINK_MAP
    ai.LINK_MAP = [("WebFX", "/compare/piperocket-digital-vs-webfx/", False, "P0")]
    try:
        with tempfile.TemporaryDirectory() as td:
            # Mimic Hugo content path: content/compare/<slug>.md
            cdir = os.path.join(td, "content", "compare")
            os.makedirs(cdir)
            f = ai.Path(cdir) / "piperocket-digital-vs-webfx.md"
            f.write_text('---\ntitle: "Self test"\n---\n' + body)
            new_content, log, err = ai.process_file(f, source_type="compare", word_gate=0)
            assert log == [], f"self-link must be suppressed: {log}"
    finally:
        ai.LINK_MAP = orig
    print("✓ Self-link: page never links to itself")


def test_flow_glossary_to_blog_allowed():
    body = "Glossary entry briefly mentions saas-ppc topic."
    log, _ = run_with_link_map([("saas-ppc", "/blogs/saas-ppc/", False, "P0")],
                                body, source_type="glossary", word_gate=0)
    assert len(log) == 1, f"glossary→blog should be allowed: {log}"
    print("✓ Flow: glossary → blog allowed (rule 2)")


def test_cluster_promotes_same_cluster_to_p0():
    """A P1-listed target in the same cluster as the source should be promoted to P0."""
    import os, tempfile
    body = "Mid-section mentions checklist topic. " + " ".join(["filler"] * 50)
    orig_map = ai.LINK_MAP
    orig_clusters = ai.CONTENT_CLUSTERS
    ai.LINK_MAP = [("checklist", "/blogs/saas-ppc-checklist/", False, "P1")]
    ai.CONTENT_CLUSTERS = {
        "/blogs/saas-ppc/": ("saas-ppc",),
        "/blogs/saas-ppc-checklist/": ("saas-ppc",),
    }
    try:
        with tempfile.TemporaryDirectory() as td:
            bdir = os.path.join(td, "content", "blogs")
            os.makedirs(bdir)
            f = ai.Path(bdir) / "saas-ppc.md"
            f.write_text('---\ntitle: "x"\n---\n' + body, encoding="utf-8")
            _, log, err = ai.process_file(f, source_type="blogs", word_gate=0)
        assert len(log) == 1, f"expected 1 wrap: {log}"
        assert log[0]["priority"] == "P0", f"same-cluster should bump to P0, got {log[0]['priority']}"
    finally:
        ai.LINK_MAP = orig_map
        ai.CONTENT_CLUSTERS = orig_clusters
    print("✓ Cluster: same-cluster target promoted P1 → P0")


def test_cluster_affinity_promotes_generic_to_p0():
    """A saas-seo blog linking to a generic `seo` glossary should bump to P0
    via CLUSTER_AFFINITY, even though clusters don't match directly."""
    import os, tempfile
    body = "Mid section mentions SEO topic. " + " ".join(["filler"] * 50)
    orig_map = ai.LINK_MAP
    orig_clusters = ai.CONTENT_CLUSTERS
    orig_aff = ai.CLUSTER_AFFINITY
    ai.LINK_MAP = [("SEO", "/glossary/what-is-seo/", True, "P2")]
    # Generic glossary entries now default to saas-seo (no separate "seo" cluster).
    # B2B sources reach it via affinity: b2b-seo affinity includes saas-seo.
    ai.CONTENT_CLUSTERS = {
        "/blogs/b2b-saas-seo/": ("b2b-seo",),
        "/glossary/what-is-seo/": ("saas-seo",),
    }
    ai.CLUSTER_AFFINITY = {"b2b-seo": {"b2b-seo", "saas-seo"}, "saas-seo": {"saas-seo"}}
    try:
        with tempfile.TemporaryDirectory() as td:
            bdir = os.path.join(td, "content", "blogs")
            os.makedirs(bdir)
            f = ai.Path(bdir) / "b2b-saas-seo.md"
            f.write_text('---\ntitle: "x"\n---\n' + body, encoding="utf-8")
            _, log, err = ai.process_file(f, source_type="blogs", word_gate=0)
        assert len(log) == 1, f"expected wrap: {log}"
        assert log[0]["priority"] == "P0", f"affinity should bump to P0, got {log[0]['priority']}"
    finally:
        ai.LINK_MAP = orig_map
        ai.CONTENT_CLUSTERS = orig_clusters
        ai.CLUSTER_AFFINITY = orig_aff
    print("✓ Cluster affinity: b2b-seo source + saas-seo glossary → P0")


def test_multi_cluster_membership():
    """A target in a multi-cluster entry (e.g. generic 'seo' glossary) should
    bump to P0 from any source cluster that overlaps."""
    import os, tempfile
    body = "Mid section mentions PPC topic. " + " ".join(["filler"] * 50)
    orig_map = ai.LINK_MAP
    orig_clusters = ai.CONTENT_CLUSTERS
    ai.LINK_MAP = [("PPC", "/glossary/what-is-ppc/", True, "P2")]
    # what-is-ppc is multi-cluster: relevant to both saas-ppc and b2b-ppc
    ai.CONTENT_CLUSTERS = {
        "/blogs/b2b-ppc/": ("b2b-ppc",),
        "/glossary/what-is-ppc/": ("saas-ppc", "b2b-ppc"),
    }
    try:
        with tempfile.TemporaryDirectory() as td:
            bdir = os.path.join(td, "content", "blogs")
            os.makedirs(bdir)
            f = ai.Path(bdir) / "b2b-ppc.md"
            f.write_text('---\ntitle: "x"\n---\n' + body, encoding="utf-8")
            _, log, err = ai.process_file(f, source_type="blogs", word_gate=0)
        assert len(log) == 1, f"expected 1 wrap: {log}"
        assert log[0]["priority"] == "P0", f"multi-cluster overlap should bump to P0, got {log[0]['priority']}"
    finally:
        ai.LINK_MAP = orig_map
        ai.CONTENT_CLUSTERS = orig_clusters
    print("✓ Cluster: multi-cluster glossary overlaps with source → P0")


def test_compare_bridge_listicle_inserts_after_section():
    """Listicle source + /compare/ target → bridge sentence after the agency section."""
    body = (
        "Intro " + " ".join(["filler"] * 50) +
        "\n\n### 1. A\nfoo\n\n### 2. B\nbar\n\n### 3. C\nbaz\n\n"
        "### 4. D\nqux\n\n### 5. E\nquux\n\n### 6. KlientBoost\nKlientBoost is solid.\n\n### 7. End\nlast"
    )
    log, new = run_with_link_map(
        [("KlientBoost", "/compare/piperocket-digital-vs-klientboost/", False, "P0")],
        body, source_type="list", word_gate=0,
    )
    # Should get TWO entries: existing-phrase wrap of "KlientBoost" AND a bridge sentence
    methods = [e.get("method") for e in log]
    assert "new_sentence" in methods, f"expected a new_sentence bridge, got: {methods}"
    assert "PipeRocket vs KlientBoost" in new or "[PipeRocket vs KlientBoost]" in new
    print("✓ Compare bridge: listicle inserts new sentence after agency section")


def test_compare_bridge_no_5th_entry_gate():
    """Rule 9 (listicle→compare) does NOT have an after-5th restriction —
    distinct from rules 6/7. Bridge should insert wherever the competitor
    section lives, even at #1."""
    body = (
        "Intro " + " ".join(["filler"] * 50) +
        "\n\n### 1. KlientBoost\nfoo bar\n\n### 2. B\nbaz"
    )
    log, _ = run_with_link_map(
        [("KlientBoost", "/compare/piperocket-digital-vs-klientboost/", False, "P0")],
        body, source_type="list", word_gate=0,
    )
    methods = [e.get("method") for e in log]
    assert "new_sentence" in methods, f"compare bridge should insert (no 5th-entry gate on rule 9): {methods}"
    print("✓ Compare bridge: no 5th-entry gate (rule 9 vs rules 6/7)")


def test_compare_bridge_alternative_page_card_structure():
    """Alternative page with numbered cards: bridge goes at section END
    (same positioning as listicles), not near first competitor mention."""
    body = (
        "Intro " + " ".join(["filler"] * 20) +
        "\n\n### 1. A\ntext\n\n### 2. KlientBoost\nKlientBoost detail line 1.\n\n"
        "More KlientBoost copy.\n\n"
        "**What Users Say**\nReviews go here.\n\n### 3. C\nnext card"
    )
    log, new = run_with_link_map(
        [("KlientBoost", "/compare/piperocket-digital-vs-klientboost/", False, "P0")],
        body, source_type="alternative", word_gate=0,
    )
    methods = [e.get("method") for e in log]
    assert "new_sentence" in methods, f"alt → compare bridge missing: {methods}"
    # The bridge should sit between "Reviews go here." and "### 3. C", not earlier
    bridge_idx = new.find("PipeRocket vs KlientBoost")
    third_card_idx = new.find("### 3.")
    second_card_idx = new.find("### 2.")
    assert second_card_idx < bridge_idx < third_card_idx, (
        f"bridge not at end of section 2: bridge={bridge_idx}, "
        f"sec2={second_card_idx}, sec3={third_card_idx}"
    )
    print("✓ Compare bridge: alt page uses end-of-section positioning (same as listicle)")


def test_compare_bridge_alternative_page_freeform_fallback():
    """If the alt page is freeform prose (no `### N.` cards), fall back to
    the first-mention paragraph anchor."""
    body = (
        "KlientBoost is one of the alternatives we cover. They focus on B2B SaaS.\n\n"
        "Their team has 50+ specialists."
    )
    log, _ = run_with_link_map(
        [("KlientBoost", "/compare/piperocket-digital-vs-klientboost/", False, "P0")],
        body, source_type="alternative", word_gate=0,
    )
    methods = [e.get("method") for e in log]
    assert "new_sentence" in methods, f"freeform-fallback bridge missing: {methods}"
    print("✓ Compare bridge: alt-page freeform fallback works when no `### N.` cards")


def test_alternative_bridge_into_alternative_page():
    """Alt page A linking to alt page B uses a new-sentence bridge with the
    `Considering {competitor}? See ...` template."""
    body = (
        "Some intro mentioning NoGood as one of our alternatives. "
        "They do paid + organic for SaaS.\n\n"
        "Their pricing starts at $5K."
    )
    log, new = run_with_link_map(
        [("NoGood", "/alternative/nogood-alternatives/", False, "P0")],
        body, source_type="alternative", word_gate=0,
    )
    methods = [e.get("method") for e in log]
    assert "new_sentence" in methods, f"alt → alt should bridge: {methods}"
    assert "[NoGood alternatives]" in new, f"alt-style anchor missing in body: {new[:200]}"
    print("✓ Alternative bridge: alt → alt uses 'NoGood alternatives' template")


def test_alternative_bridge_into_listicle_source():
    """Listicle that mentions NoGood in a numbered section should also bridge
    to /alternative/nogood-alternatives/ (if the flow is allowed)."""
    body = (
        "Intro " + " ".join(["filler"] * 50) +
        "\n\n### 1. A\n\n### 2. B\n\n### 3. C\n\n### 4. D\n\n### 5. E\n\n"
        "### 6. NoGood\nNoGood is solid."
    )
    # Add ("list","alternative") to ALLOWED_FLOWS temporarily to verify the
    # mechanism works (the user's stated rules don't include listicle→alt,
    # so this is a hypothetical — without the flow it stays blocked).
    orig_flows = ai.ALLOWED_FLOWS
    ai.ALLOWED_FLOWS = dict(orig_flows); ai.ALLOWED_FLOWS[("list","alternative")] = True
    try:
        log, _ = run_with_link_map(
            [("NoGood", "/alternative/nogood-alternatives/", False, "P0")],
            body, source_type="list", word_gate=0,
        )
        methods = [e.get("method") for e in log]
        assert "new_sentence" in methods, f"with flow allowed, bridge should fire: {methods}"
    finally:
        ai.ALLOWED_FLOWS = orig_flows
    print("✓ Alternative bridge: listicle → alt fires when flow is permitted")


def test_compare_bridge_dedupe_with_existing_link():
    """If the compare URL is already linked anywhere, don't add a bridge."""
    body = (
        "We covered this in [our compare](/compare/piperocket-digital-vs-klientboost/) earlier.\n\n"
        + " ".join(["filler"] * 50) +
        "\n\n### 1. A\n\n### 2. B\n\n### 3. C\n\n### 4. D\n\n### 5. E\n\n"
        "### 6. KlientBoost\nKlientBoost is solid."
    )
    log, _ = run_with_link_map(
        [("KlientBoost", "/compare/piperocket-digital-vs-klientboost/", False, "P0")],
        body, source_type="list", word_gate=0,
    )
    methods = [e.get("method") for e in log]
    assert "new_sentence" not in methods, "must not double-link compare URL"
    print("✓ Compare bridge: dedupes against pre-existing compare link")


def test_priority_ordering():
    """P0 beats P1 beats P2 when they compete for the same first-valid-position."""
    pad = " ".join(["filler"] * 500)
    body = pad + "\n\nWe wrote about saas seo recently."
    link_map = [
        ("saas seo", "/blogs/saas-seo/", False, "P0"),
        ("seo", "/glossary/what-is-seo/", False, "P2"),
    ]
    log, new = run_with_link_map(link_map, body)
    # Both targets eligible, but P0 longer-phrase claims first; P2 'seo' then
    # falls inside the wrapped P0 anchor (protected) so it's skipped.
    assert any(e["priority"] == "P0" for e in log), f"P0 should win: {log}"
    print(f"✓ Priority ordering: P0/longest claims slot first ({[e['anchor'] for e in log]})")


# ---------- RUN ALL ----------

if __name__ == "__main__":
    tests = [
        test_r5a_skips_before_w450,
        test_r5a_wraps_after_w450,
        test_r5a_word_counting_uses_w_boundary,
        test_r5d_same_paragraph_blocked,
        test_r5d_different_paragraphs_both_wrap,
        test_target_dedupe_skips_already_linked,
        test_protected_spans,
        test_faq_skip_off_by_default,
        test_faq_skip_on_when_requested,
        test_conclusion_skip_on,
        test_per_type_word_gate,
        test_flow_blog_to_glossary_allowed,
        test_flow_compare_to_glossary_disallowed,
        test_flow_alternative_to_compare_allowed,
        test_flow_alternative_to_blog_disallowed,
        test_flow_listicle_to_blog_after_5th_blocks_early,
        test_flow_listicle_to_blog_after_5th_allows_late,
        test_flow_listicle_to_service_no_5th_restriction,
        test_self_link_suppression,
        test_flow_glossary_to_blog_allowed,
        test_cluster_promotes_same_cluster_to_p0,
        test_cluster_affinity_promotes_generic_to_p0,
        test_multi_cluster_membership,
        test_compare_bridge_listicle_inserts_after_section,
        test_compare_bridge_no_5th_entry_gate,
        test_compare_bridge_alternative_page_card_structure,
        test_compare_bridge_alternative_page_freeform_fallback,
        test_alternative_bridge_into_alternative_page,
        test_alternative_bridge_into_listicle_source,
        test_compare_bridge_dedupe_with_existing_link,
        test_priority_ordering,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"✗ {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: EXCEPTION {type(e).__name__}: {e}")
            failed += 1
    print("\n" + ("=" * 60))
    if failed:
        print(f"FAILED: {failed} / {len(tests)} tests")
        sys.exit(1)
    print(f"ALL {len(tests)} TESTS PASSED")
