import re, html
TOKEN = re.compile(r'(<!--.*?-->|<script\b.*?</script\s*>|<style\b.*?</style\s*>|<noscript\b[^>]*>|</noscript>|<![^>]*>|<[^>]+>)', re.S | re.I)
ATTRS = ('alt', 'title', 'aria-label', 'placeholder', 'data-label', 'value')
ATTR_RE = re.compile(r'(\s(?:%s)=")([^"]*)(")' % '|'.join(ATTRS), re.I)
META_RE = re.compile(r'<meta\s[^>]*(?:name|property)="(?:description|og:title|og:description|twitter:title|twitter:description|dcterms\.title|dcterms\.description)"[^>]*>', re.I)
def norm(s):
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()
def is_text(s):
    n = norm(s)
    return bool(n) and re.search(r'[A-Za-z]', n)
def split(doc):
    return TOKEN.split(doc)
