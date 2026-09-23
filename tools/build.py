# -*- coding: utf-8 -*-
"""Build translated pages from the raw "Save page as – complete" downloads.

Only text content is changed; markup, classes, styles and scripts are kept.
"""
import html, json, os, re, shutil, sys, urllib.parse
from tok import split, norm, is_text, ATTR_RE, META_RE
from trans import T, SKIP, RAW

RAW_DIR, OUT = sys.argv[1], sys.argv[2]
BM = "https://www.britishmuseum.org"
PAGES = [
    ("Galleries _ British Museum", "index.html", "galleries_files"),
    ("Enlightenment _ British Museum", "enlightenment.html", "enlightenment_files"),
    ("Africa _ British Museum", "africa.html", "africa_files"),
]
LOCAL_LINKS = {
    BM + "/collection/galleries/enlightenment": "enlightenment.html",
    BM + "/collection/galleries/africa": "africa.html",
}
# Tracking / cookie-consent scripts that only make sense on britishmuseum.org
DROP_FILES = {"gtm.js", "state.js", "consent-sdk-2.3.js", "uc.js",
              "saved_resource.html", "saved_resource(1).html", "bc-v4.min.html"}

missing = {}


def tr(text):
    """Translate one raw text segment, keeping its surrounding whitespace."""
    if not is_text(text):
        return text
    key = norm(text)
    if key in SKIP:
        return text
    if key not in T:
        missing[key] = missing.get(key, 0) + 1
        return text
    m = re.match(r'^(?:\s|&nbsp;|&#160;)*', text)
    lead = m.group(0)
    rest = text[len(lead):]
    t = re.search(r'(?:\s|&nbsp;|&#160;)*$', rest).group(0)
    return lead + html.escape(T[key], quote=False) + t


def tr_fragment(h):
    """Translate text nodes inside an (unescaped) HTML fragment."""
    parts = split(h)
    for i in range(0, len(parts), 2):
        parts[i] = tr(parts[i])
    return "".join(parts)


def tr_attr_value(v):
    key = norm(v)
    if key in SKIP or not is_text(v) or v.startswith(("http", "/")):
        return v
    if key not in T:
        missing[key] = missing.get(key, 0) + 1
        return v
    return html.escape(T[key], quote=True)


def fix_tag(tag):
    if tag.lower().startswith(("<script", "<style", "<!--", "<!")):
        return tag
    tag = ATTR_RE.sub(lambda m: m.group(1) + (m.group(2) if 'value=' in m.group(1).lower() else tr_attr_value(m.group(2))) + m.group(3), tag)
    if META_RE.match(tag):
        tag = re.sub(r'(content=")([^"]*)(")', lambda m: m.group(1) + tr_attr_value(m.group(2)) + m.group(3), tag)
    # lightbox captions
    tag = re.sub(r'( data-description=")([^"]*)(")',
                 lambda m: m.group(1) + html.escape(tr_fragment(html.unescape(m.group(2))), quote=True) + m.group(3), tag)

    def swipe(m):
        items = json.loads(html.unescape(m.group(2)))
        for it in items:
            for k in ("title", "caption"):
                if it.get(k):
                    it[k] = tr_fragment(it[k])
        return m.group(1) + html.escape(json.dumps(items, ensure_ascii=False), quote=True) + m.group(3)
    tag = re.sub(r'( data-photo-swipe-items=")([^"]*)(")', swipe, tag)
    return tag


def localise_images(doc, folder):
    """Point responsive-image attributes at the locally saved copy when there is one."""
    local_re = re.compile(r'\ssrc="(\./%s/[^"]+)"' % re.escape(folder))

    def fix_img(tag, local):
        # srcset treats spaces/commas as separators, so percent-encode the path
        local = urllib.parse.quote(html.unescape(local), safe="/.")
        for attr in ("srcset", "data-srcset", "data-src"):
            tag = re.sub(r'(\s%s=")[^"]*(")' % attr, lambda m: m.group(1) + local + m.group(2), tag)
        return tag

    def picture(m):
        block = m.group(0)
        loc = local_re.search(block)
        if not loc:
            return block
        return re.sub(r'<(?:img|source)\b[^>]*>', lambda t: fix_img(t.group(0), loc.group(1)), block)
    doc = re.sub(r'<picture\b.*?</picture>', picture, doc, flags=re.S)

    def img(m):
        tag = m.group(0)
        loc = local_re.search(tag)
        return fix_img(tag, loc.group(1)) if loc else tag
    return re.sub(r'<img\b[^>]*>', img, doc)


def absolutise(text):
    """Root-relative britishmuseum.org URLs would break on GitHub Pages."""
    return re.sub(r'(?<=["(,\s;])/(?=(?:sites|themes|collection|files)/)', BM + '/', text)


def build(src_name, out_name, folder):
    raw_folder = src_name + "_files"
    doc = open(os.path.join(RAW_DIR, src_name + ".html"), encoding="utf-8").read()

    # --- assets: rename folder, drop browser ".下载" suffix
    doc = doc.replace("./" + raw_folder + "/", "./" + folder + "/")
    doc = doc.replace(".下载\"", "\"")
    dst = os.path.join(OUT, folder)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(dst)
    for f in os.listdir(os.path.join(RAW_DIR, raw_folder)):
        clean = f.replace(".#U4e0b#U8f7d", "").replace(".下载", "")
        if clean in DROP_FILES:
            continue
        shutil.copy(os.path.join(RAW_DIR, raw_folder, f), os.path.join(dst, clean))

    # --- disable analytics / cookie banner that belong to the original domain
    for s in DROP_FILES:
        doc = re.sub(r'<script[^>]*src="\./%s/%s"[^>]*>\s*</script>' % (re.escape(folder), re.escape(s)),
                     '', doc)
    # hidden iframes the Cookiebot script injected before the page was saved
    doc = re.sub(r'<iframe class="CybotCookiebot[^"]*"[^>]*>.*?</iframe>', '', doc, flags=re.S)
    doc = re.sub(r'(<!-- Google Tag Manager -->)(.*?)(<!-- End Google Tag Manager -->)',
                 lambda m: m.group(1) + "<!-- disabled on this translated copy:" + m.group(2).replace("--", "- -") + "-->" + m.group(3),
                 doc, count=1, flags=re.S)
    doc = re.sub(r'(<!-- Google Tag Manager \(noscript\) -->)(.*?)(<!-- End Google Tag Manager \(noscript\) -->)',
                 lambda m: m.group(1) + "<!--" + m.group(2).replace("--", "- -") + "-->" + m.group(3),
                 doc, count=1, flags=re.S)

    # Cookiebot loader (uc.js is not kept, so the tag would only 404)
    doc = re.sub(r'<script id="Cookiebot"[^>]*>\s*</script>', '', doc)

    # --- images & root-relative URLs
    doc = localise_images(doc, folder)
    doc = absolutise(doc)
    for css in os.listdir(dst):
        if css.endswith(".css"):
            p = os.path.join(dst, css)
            c = open(p, encoding="utf-8").read()
            c = re.sub(r'url\((["\']?)/(?!/)', lambda m: 'url(' + m.group(1) + BM + '/', c)
            open(p, "w", encoding="utf-8").write(c)

    # --- links to the two translated room pages
    def link(m):
        url = m.group(2)
        base, frag = (url.split("#", 1) + [""])[:2]
        if base.rstrip("/") in LOCAL_LINKS:
            url = LOCAL_LINKS[base.rstrip("/")] + ("#" + frag if frag else "")
        return m.group(1) + url + m.group(3)
    doc = re.sub(r'(<a\b[^>]*?\shref=")([^"]*)(")', link, doc)

    # --- language + text
    doc = doc.replace('<html lang="en"', '<html lang="zh-CN"', 1)
    for a, b in RAW:
        doc = doc.replace(a, b)
    parts = split(doc)
    for i, p in enumerate(parts):
        parts[i] = tr(p) if i % 2 == 0 else fix_tag(p)
    doc = "".join(parts)
    open(os.path.join(OUT, out_name), "w", encoding="utf-8").write(doc)


for p in PAGES:
    build(*p)
if missing:
    print("UNTRANSLATED:")
    for k, v in missing.items():
        print("  %r x%d" % (k, v))
