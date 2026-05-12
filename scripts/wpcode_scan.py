"""Detect WPCode / custom-HTML embeds inside post body only (not footer/header)."""
import re
import urllib.request

URLS = [
    "https://piperocket.digital/blogs/b2b-content-marketing-guide/",
    "https://piperocket.digital/blogs/b2b-demand-generation-guide/",
    "https://piperocket.digital/blogs/b2b-inbound-marketing-guide/",
    "https://piperocket.digital/blogs/b2b-lead-generation/",
    "https://piperocket.digital/blogs/b2b-linkedin-marketing-guide/",
    "https://piperocket.digital/blogs/b2b-marketing/",
    "https://piperocket.digital/blogs/b2b-saas-seo/",
    "https://piperocket.digital/blogs/fintech-seo-guide/",
    "https://piperocket.digital/blogs/how-to-conduct-a-saas-ppc-audit/",
    "https://piperocket.digital/blogs/how-to-do-saas-content-audit/",
    "https://piperocket.digital/blogs/how-to-do-saas-seo-competitor-analysis/",
    "https://piperocket.digital/blogs/how-to-do-saas-seo-keyword-research/",
    "https://piperocket.digital/blogs/how-to-rank-on-chatgpt/",
    "https://piperocket.digital/blogs/how-to-run-google-ads-for-saas/",
    "https://piperocket.digital/blogs/how-to-run-linkedin-retargeting-ads/",
    "https://piperocket.digital/blogs/how-to-write-saas-comparison-pages-for-seo/",
    "https://piperocket.digital/blogs/how-to-write-saas-google-ads-copy/",
    "https://piperocket.digital/blogs/how-to-write-saas-seo-content-with-ai/",
    "https://piperocket.digital/blogs/optimize-saas-landing-pages-for-seo/",
    "https://piperocket.digital/blogs/saas-content-marketing-guide/",
    "https://piperocket.digital/blogs/saas-google-ads-mistakes-to-avoid/",
    "https://piperocket.digital/blogs/saas-linkedin-ads-mistakes-to-avoid/",
    "https://piperocket.digital/blogs/saas-ppc-checklist/",
    "https://piperocket.digital/blogs/saas-ppc/",
    "https://piperocket.digital/blogs/saas-seo-checklist/",
]


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "audit/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode(errors="ignore")
    except Exception:
        return ""


def body_only(html):
    """Slice content between <h1> (post title) and related-articles section."""
    h1 = html.find("<h1")
    if h1 < 0:
        return ""
    end = html.find("related-articles", h1)
    if end < 0:
        end = html.find("<footer", h1)
    if end < 0:
        end = len(html)
    return html[h1:end]


def scan(url):
    html = fetch(url)
    if not html:
        return None
    body = body_only(html)
    return {
        "url": url,
        "size": len(body),
        "wpcode_class": len(re.findall(r'class="[^"]*wpcode[^"]*"', body, re.I)),
        "wpcode_id": len(re.findall(r'\bid="wpcode_-?\d+"', body, re.I)),
        "wpcode_comment": len(re.findall(r"<!--\s*WPCode", body, re.I)),
        "wpcode_shortcode_leaked": len(re.findall(r"\[wpcode[^]]*\]", body, re.I)),
        "iframes_in_body": len(re.findall(r"<iframe", body, re.I)),
        "forms_in_body": len(re.findall(r"<form", body, re.I)),
        "inline_scripts_in_body": len(re.findall(r"<script(?![^>]*\bsrc=)", body, re.I)),
        "html_blocks_data_attr": len(re.findall(r"<div[^>]+data-[a-z]+=", body, re.I)),
        "leaked_shortcodes": re.findall(r"\[\w[\w_]+[^]]*\]", body)[:5],
    }


def main():
    rows = []
    for u in URLS:
        r = scan(u)
        if r:
            rows.append(r)

    print(f"\n{'URL':<70}  {'wpc':>4}  {'iframe':>7}  {'form':>5}  {'<script':>8}  {'data':>5}  leaked-shortcodes")
    print("-" * 150)
    suspicious = []
    for r in rows:
        wpc = r["wpcode_class"] + r["wpcode_id"] + r["wpcode_comment"] + r["wpcode_shortcode_leaked"]
        short = r["url"].replace("https://piperocket.digital", "")
        signal = wpc + r["iframes_in_body"] + r["forms_in_body"] + r["inline_scripts_in_body"]
        marker = "*" if signal else " "
        sc = ",".join(r["leaked_shortcodes"]) if r["leaked_shortcodes"] else ""
        print(f"{marker} {short:<68}  {wpc:>4}  {r['iframes_in_body']:>7}  {r['forms_in_body']:>5}  {r['inline_scripts_in_body']:>8}  {r['html_blocks_data_attr']:>5}  {sc}")
        if signal:
            suspicious.append((r["url"], wpc, r["iframes_in_body"], r["forms_in_body"], r["inline_scripts_in_body"]))

    print(f"\n=== Suspicious (has custom HTML inside post body) ===")
    for u, w, i, f, s in suspicious:
        bits = []
        if w: bits.append(f"wpcode={w}")
        if i: bits.append(f"iframe={i}")
        if f: bits.append(f"form={f}")
        if s: bits.append(f"inline-script={s}")
        print(f"  {u}  [{' '.join(bits)}]")


if __name__ == "__main__":
    main()
