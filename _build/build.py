"""Static site generator for aslanesamai.com (stdlib only).

    python3 _build/build.py

Sources (edit these, then rebuild; never edit generated files by hand):
  _build/site.json          page metadata extracted from the original site
  _build/seo.json           per-page <title> / description / h1 / canonical overrides
  _build/content/<path>     article, case study and service bodies (original language)
  _build/testimonials.json  testimonials, quoted verbatim
  _build/i18n.py            interface and home-page copy in English, French and Arabic
  _build/imgsize.json       image dimensions (refresh with _build/measure_images.py)

Output: /en/, /fr/, /ar/ (home, services, case studies, blog), a language chooser at /,
the articles at their original URLs, sitemap.xml, feed.xml, robots.txt, llms.txt, llms-full.txt,
404.html and redirect stubs for retired URLs.
"""
import datetime as dt
import hashlib
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n import (AIOSEO, AIOSEO_ARTICLES, AIOSEO_TOOLS, EDUCATION, EXPERIENCE, GITHUB, LANGS, META, SKILLS, STREAMLIT,  # noqa: E402
                  TOOLS, T)
from md import to_markdown  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_build"
SITE = "https://aslanesamai.com"
SITE_NAME = "Aslane Samai"
PORTRAIT = "/assets/portrait.webp"
OG_DEFAULT = f"{SITE}/aslanesamai.png"
CALENDLY = "https://calendly.com/samaiaslane/free-seo-audit"
EMAIL = "contact@aslanesamai.com"
PHONE = "+33651630813"
LINKEDIN = "https://www.linkedin.com/in/aslane-samai"
X_URL = "https://x.com/this_is_aslan"
MEDIUM = "https://medium.com/@samaiaslane7"
AIOSEO_PROFILE = "https://aioseo.fr/aslane-samai-consultant-seo-technique-expert-geo/"
TODAY = dt.date.today().isoformat()
PERSON_ID = f"{SITE}/#person"
WEBSITE_ID = f"{SITE}/#website"

data = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
PAGES = data["pages"]
SEO = {k: v for k, v in json.loads((SRC / "seo.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}
for _path, _o in SEO.items():
    PAGES[_path].update({k: v for k, v in _o.items() if k in ("title", "description", "h1", "canonical")})
TESTI = json.loads((SRC / "testimonials.json").read_text(encoding="utf-8"))
IMGSIZE = json.loads((SRC / "imgsize.json").read_text()) if (SRC / "imgsize.json").exists() else {}
CSS_V = hashlib.sha1((ROOT / "assets/site.css").read_bytes() + (ROOT / "assets/site.js").read_bytes()).hexdigest()[:8]

KNOWS_ABOUT = ["Search engine optimization", "Generative engine optimization", "Technical SEO", "Google AI Overviews", "Google AI Mode",
               "Google Search Console", "Bing Webmaster Tools", "Core Web Vitals", "Structured data", "Semantic SEO", "Netlinking",
               "SEO content writing", "Data analysis", "SQL", "Python", "Data visualization", "Tableau", "Looker Studio"]
CERTS = [("Google Data Analytics", "Google · Coursera", None), ("SQL", "CoRise", None), ("Technical SEO", "Blue Array", "https://www.bluearray.co.uk/"),
         ("SEO Manager", "Blue Array", "https://www.bluearray.co.uk/")]
SERVICE_KEYS = {
    "services/seo-the-driving-force-behind-my-passion.html": "svc_seo",
    "services/data-analysis.html": "svc_data",
    "services/data-visualization.html": "svc_viz",
    "services/seo-content-writing.html": "svc_content",
}
SERVICE_LD = {  # from the original service pages' markup (prices as published there)
    "services/seo-the-driving-force-behind-my-passion.html": ("SEO (Search Engine Optimization) Services", "Comprehensive SEO services including on-page, off-page, and technical optimization.", "Search Engine Optimization", 200, "per month"),
    "services/data-analysis.html": ("Data Analysis", "Professional data analysis services using SQL, Python, and more.", "Data Analysis", 200, "per project"),
    "services/data-visualization.html": ("Data Visualization Services", "Professional data visualization services using Tableau and other tools.", "Data Visualization", 200, "per project"),
    "services/seo-content-writing.html": ("Content Writing", "Professional content writing services in both French and English.", "Writing", 50, "per article"),
}
LISTINGS = {"services.html": "services", "ressources.html": "ressources", "blog.html": "blog"}
REDIRECTS = {  # retired URLs -> current page
    "ressources/seo-case-study.html": "ressources/seo-case-study-interfast.html",
    "ressources/radco-seo-case-study.html": "ressources/seo-case-study-radco.html",
    "services.html": "en/services.html",
    "ressources.html": "en/ressources.html",
    "blog.html": "en/blog.html",
}

e = lambda s: html.escape(s or "", quote=True)  # noqa: E731
GENERIC_TITLES = {"my blog", "read my blog", ""}
FR_WORDS = re.compile(r"\b(le|la|les|des|une|est|pour|avec|dans|sur|nous|vous|qui|que|pas|sont|du|au|et)\b", re.I)
EN_WORDS = re.compile(r"\b(the|and|is|for|with|in|on|we|you|who|that|not|are|of|to|a)\b", re.I)


def lang_of(text):
    return "fr" if len(FR_WORDS.findall(text)) > len(EN_WORDS.findall(text)) else "en"


def clean_text(s):
    return re.sub(r"\s+([.,;:!?])(?=\s|$)", r"\1", re.sub(r"\s+", " ", s)).strip()


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def img(url, width=None):
    """Sirv images can be resized on the fly; local ones are served as is."""
    if url and width and "sirv.com" in url and "?" not in url:
        return f"{url}?w={width}"
    return url


def dims(url, max_w=None):
    """width/height attributes for an image, scaled down to max_w when it is served resized."""
    size = IMGSIZE.get(url)
    if not size:
        return ""
    w, h = size
    if max_w and w > max_w and "sirv.com" in url:
        w, h = max_w, round(h * max_w / w)
    return f' width="{w}" height="{h}"'


def _sized_img(m):
    tag = m.group(0)
    src = re.search(r'\bsrc="([^"]+)"', tag)
    if not src:
        return tag
    url = html.unescape(src.group(1))
    size = IMGSIZE.get(url)
    if size and "width=" not in tag:
        w, h = size
        if w > 1400 and "sirv.com" in url:  # serve at 2x the reading column, not the original screenshot size
            w, h = 1400, round(h * 1400 / w)
            tag = tag.replace(src.group(0), f'src="{e(img(url, 1400))}"')
        tag = tag.replace("<img", f'<img width="{w}" height="{h}"', 1)
    if "loading=" not in tag:
        tag = tag.replace("<img", '<img loading="lazy" decoding="async"', 1)
    return tag


def content(path):
    return re.sub(r"<img\b[^>]*>", _sized_img, (SRC / "content" / path).read_text(encoding="utf-8"))


def first_image(path):
    m = re.search(r'<img[^>]*\bsrc="([^"]+)"', (SRC / "content" / path).read_text(encoding="utf-8"))
    return m.group(1) if m else None


def page_title(p):
    t = clean_text(p["title"]).rstrip("<").strip()
    return p["h1"] if t.lower() in GENERIC_TITLES else t


def title_with_brand(t):
    return t if "Aslane Samai" in t or len(t) + 15 > 62 else f"{t} · Aslane Samai"


def post_date(p):
    return p.get("date_published") or p.get("added")


MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "ar": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
}


def fmt_date(d, lang="en"):
    if not d:
        return ""
    y, m, day = map(int, d.split("-"))
    return f"{MONTHS[lang][m - 1]} {day}, {y}" if lang == "en" else f"{day} {MONTHS[lang][m - 1]} {y}"


def url_of(path):
    if path == "index.html":
        return "/"
    if path.endswith("/index.html"):
        return "/" + path[: -len("index.html")]
    return "/" + path


def canonical(path):
    return SITE + url_of(path)


def clip(s, n):
    s = clean_text(s)
    return s if len(s) <= n else s[: s.rfind(" ", 0, n)].rstrip(",;:") + "…"


def initials(name):
    return "".join(w[0] for w in name.split()[:2]).upper()


def ext(url, text, cls=""):
    return f'<a{f" class={chr(34)}{cls}{chr(34)}" if cls else ""} href="{e(url)}" target="_blank" rel="noopener">{text}</a>'


# ---------------------------------------------------------------- collections
def ordered(order_key):
    seen, out = set(), []
    for it in data[order_key]:
        if it["path"] in PAGES and it["path"] not in seen:
            seen.add(it["path"])
            out.append(it["path"])
    return out, seen


BLOG, _seen = ordered("blog_order")
BLOG += sorted((p for p in PAGES if p.startswith("blog/") and p not in _seen), key=lambda p: post_date(PAGES[p]) or "", reverse=True)
SERVICES, _ = ordered("services_order")
CASES, _ = ordered("cases_order")
LABELS = {it["path"]: clean_text(it["label"]) for k in ("blog_order", "services_order", "cases_order", "home_blog") for it in data[k]}


# ---------------------------------------------------------------- structured data
def person_node(full=False):
    node = {"@type": "Person", "@id": PERSON_ID, "name": "Aslane Samai", "alternateName": "Samai Aslane", "url": f"{SITE}/",
            "image": OG_DEFAULT, "jobTitle": "SEO / GEO consultant", "sameAs": [LINKEDIN, X_URL, MEDIUM, GITHUB, AIOSEO_PROFILE]}
    if full:
        node.update({
            "description": ("Aslane Samai is an SEO and GEO (generative engine optimization) consultant based in Paris, France. He helps businesses "
                            "get found on Google and cited in AI answers such as ChatGPT, Gemini and Google AI Overviews, through technical SEO "
                            "audits, data analysis and content. He previously worked for a year as an SEO & GEO consultant at Eskimoz, "
                            "and writes aioseo.fr, a French-language blog about AI search."),
            "email": f"mailto:{EMAIL}", "telephone": PHONE,
            "address": {"@type": "PostalAddress", "addressLocality": "Paris", "addressRegion": "Île-de-France", "postalCode": "75000", "addressCountry": "FR"},
            "knowsAbout": KNOWS_ABOUT, "knowsLanguage": ["fr", "en"],
            "hasOccupation": {"@type": "Occupation", "name": "SEO / GEO consultant", "occupationLocation": {"@type": "City", "name": "Paris"},
                              "skills": ", ".join(strip_tags(x) for x in T["en"]["skills_seo_items"] + SKILLS["skills_tools"] + SKILLS["skills_data"][:2] + SKILLS["skills_viz"])},
            "alumniOf": [{"@type": "CollegeOrUniversity", "name": school} for school, _, _, _ in EDUCATION],
            "hasCredential": [{"@type": "EducationalOccupationalCredential", "name": f"{t} certification", "credentialCategory": "certificate",
                               "recognizedBy": {"@type": "Organization", "name": o.split(" · ")[0], **({"url": u} if u else {})}} for t, o, u in CERTS],
            "subjectOf": {"@type": "WebSite", "name": "AIO SEO · Good GEO is good SEO!", "url": AIOSEO, "inLanguage": "fr", "author": {"@id": PERSON_ID}},
        })
    return node


def website_node():
    return {"@type": "WebSite", "@id": WEBSITE_ID, "url": f"{SITE}/", "name": SITE_NAME, "inLanguage": LANGS, "publisher": {"@id": PERSON_ID}}


def graph(*nodes):
    return json.dumps({"@context": "https://schema.org", "@graph": [n for n in nodes if n]}, ensure_ascii=False)


def breadcrumbs(items):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items, 1)]}


def image_obj(url):
    if not url:
        return OG_DEFAULT
    size = IMGSIZE.get(url)
    return {"@type": "ImageObject", "url": url if url.startswith("http") else SITE + url, **({"width": size[0], "height": size[1]} if size else {})}


# ---------------------------------------------------------------- layout
def lang_switch(lang, alternates):
    links = "".join(
        f'<a href="{alternates.get(l, f"/{l}/")}" hreflang="{l}" lang="{l}" data-lang="{l}"{" aria-current=true" if l == lang else ""}>{META[l]["short"]}</a>'
        for l in LANGS)
    return f'<div class="langs" role="navigation" aria-label="{T[lang]["lang_label"]}">{links}</div>'


def header(lang, active, alternates):
    t = T[lang]
    items = [(t["nav_services"], f"/{lang}/services.html", "services"), (t["nav_experience"], f"/{lang}/#experience", "experience"),
             (t["nav_cases"], f"/{lang}/ressources.html", "ressources"), (t["nav_blog"], f"/{lang}/blog.html", "blog"), (t["nav_contact"], f"/{lang}/#contact", "contact")]
    links = "".join(f'<a href="{h}"{" aria-current=\"page\"" if a == active else ""}>{x}</a>' for x, h, a in items)
    cta = f'<a class="btn btn-primary" href="/{lang}/#contact">{t["nav_cta"]}</a>'
    switch = lang_switch(lang, alternates)
    return f"""<header class="site-header" id="top">
  <div class="wrap">
    <a class="brand" href="/{lang}/" aria-label="Aslane Samai">Aslane Samai<span>.</span></a>
    <nav class="nav" aria-label="Main">{links}{switch}{cta}</nav>
    <details class="menu"><summary aria-label="{t['menu']}"><span></span></summary><nav aria-label="Mobile">{links}{switch}{cta}</nav></details>
  </div>
</header>"""


def footer(lang):
    t = T[lang]
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="cols">
      <div class="f-about"><a class="brand" href="/{lang}/">Aslane Samai<span>.</span></a><p>{t['footer_tagline']}</p></div>
      <div><h4>{t['footer_explore']}</h4><ul><li><a href="/{lang}/services.html">{t['nav_services']}</a></li><li><a href="/{lang}/ressources.html">{t['nav_cases']}</a></li><li><a href="/{lang}/blog.html">{t['nav_blog']}</a></li><li><a href="/{lang}/#testimonials">{t['footer_testimonials']}</a></li><li>{ext(AIOSEO, "aioseo.fr")}</li></ul></div>
      <div><h4>{t['footer_contact']}</h4><ul><li><a href="mailto:{EMAIL}">{EMAIL}</a></li><li><a href="/{lang}/#contact">{t['footer_book']}</a></li></ul></div>
      <div><h4>{t['footer_follow']}</h4><ul><li><a href="{LINKEDIN}" rel="me noopener" target="_blank">LinkedIn</a></li><li><a href="{X_URL}" rel="me noopener" target="_blank">X / Twitter</a></li><li><a href="{GITHUB}" rel="me noopener" target="_blank">GitHub</a></li><li><a href="{MEDIUM}" rel="me noopener" target="_blank">Medium</a></li></ul></div>
    </div>
    <div class="legal"><span>© {dt.date.today().year} Aslane Samai</span><a href="/privacy-policy.html">{t['footer_privacy']}</a></div>
  </div>
</footer>"""


def layout(path, *, title, description, body, lang="en", ui=None, active="", og_type="website", og_image=None, jsonld=(), preload_portrait=False,
           noindex=False, canonical_path=None, published=None, alternates=None):
    """lang: language of the page content; ui: language of the navigation (defaults to lang, English for other languages)."""
    ui = ui or (lang if lang in LANGS else "en")
    og_image = og_image or OG_DEFAULT
    if og_image.startswith("/"):
        og_image = SITE + og_image
    desc = e(clean_text(strip_tags(description)))
    ld = "".join(f'\n<script type="application/ld+json">{j}</script>' for j in jsonld)
    pre = f'\n<link rel="preload" as="image" href="{PORTRAIT}" type="image/webp">' if preload_portrait else ""
    robots = '\n<meta name="robots" content="noindex">' if noindex else ""
    canon = "" if noindex else f'\n<link rel="canonical" href="{canonical(canonical_path or path)}">'
    hreflang = ""
    if alternates:
        hreflang = "".join(f'\n<link rel="alternate" hreflang="{l}" href="{SITE}{u}">' for l, u in alternates.items())
        hreflang += f'\n<link rel="alternate" hreflang="x-default" href="{SITE}{alternates.get("x-default", alternates["en"])}">'
    article = f'\n<meta property="article:published_time" content="{published}">\n<meta property="article:author" content="{SITE}/">' if published else ""
    locale = META.get(lang, META["en"])["locale"]
    og_alt = "".join(f'\n<meta property="og:locale:alternate" content="{META[l]["locale"]}">' for l in (alternates or {}) if l in META and l != lang)
    fonts = ('\n<link rel="preload" href="/assets/fonts/ibm-plex-sans-arabic-400-arabic.woff2" as="font" type="font/woff2" crossorigin>'
             if lang == "ar" else '\n<link rel="preload" href="/assets/fonts/inter-normal-latin.woff2" as="font" type="font/woff2" crossorigin>')
    return f"""<!doctype html>
<html lang="{lang}" dir="{META.get(lang, META['en'])['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{desc}">
<meta name="author" content="Aslane Samai">{robots}{canon}{hreflang}
<meta name="theme-color" content="#f6f3ec" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121311" media="(prefers-color-scheme: dark)">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical(canonical_path or path)}">
<meta property="og:locale" content="{locale}">{og_alt}{article}
<meta property="og:image" content="{e(og_image)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@this_is_aslan">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{e(og_image)}">
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="Aslane Samai · Blog" href="{SITE}/feed.xml">
<link rel="me" href="{LINKEDIN}">
<link rel="me" href="{X_URL}">
<link rel="preload" href="/assets/fonts/fraunces-normal-latin.woff2" as="font" type="font/woff2" crossorigin>{fonts}{pre}
<link rel="stylesheet" href="/assets/site.css?v={CSS_V}">
<script src="/assets/site.js?v={CSS_V}" defer></script>{ld}
</head>
<body>
<a class="skip" href="#main">{T[ui]['skip']}</a>
{header(ui, active, alternates or {})}
<main id="main"{f' lang="{lang}"' if lang != ui else ""}>
{body}
</main>
{footer(ui)}
</body>
</html>
"""


def write(rel, text):
    (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / rel).write_text(text, encoding="utf-8")


def alternates_for(page):
    """page: 'index.html' or a listing file name -> {lang: url} for the three language versions."""
    alts = {l: url_of(f"{l}/{page}") for l in LANGS}
    alts["x-default"] = "/" if page == "index.html" else alts["en"]
    return alts


# ---------------------------------------------------------------- components
def cta_band(lang):
    t = T[lang]
    return f"""<section class="section"><div class="wrap"><div class="cta-band reveal"><div><h2>{t['cta_h']}</h2><p>{t['cta_p']}</p></div><a class="btn btn-primary" href="/{lang}/#contact">{t['cta_b']}</a></div></div></section>"""


def badge(lang, page_lang="en"):
    return "" if lang == page_lang else f'<span class="lang-badge">{T[lang]["in_english"]}</span>'


def post_card(path, lang="en", width=720):
    p = PAGES[path]
    plang = lang_of(p["h1"] + " " + p["description"])
    cover = img(p.get("cover"), width)
    thumb = f'<div class="thumb"><img src="{e(cover)}" alt=""{dims(p.get("cover"), width)} loading="lazy" decoding="async"></div>' if cover else ""
    return (f'<a class="card card-media reveal" href="{url_of(path)}" hreflang="{plang}">{thumb}<div class="body"><span class="tag">{fmt_date(post_date(p), lang)}{badge(lang, plang)}</span>'
            f'<h3 lang="{plang}">{e(LABELS.get(path) or p["h1"])}</h3><p lang="{plang}">{e(clip(p["description"], 150))}</p></div></a>')


def case_card(path, lang="en"):
    p = PAGES[path]
    t = T[lang]
    raw = p.get("cover") or first_image(path)
    cover = img(raw, 720)
    thumb = f'<div class="thumb logo"><img src="{e(cover)}" alt=""{dims(raw, 720)} loading="lazy" decoding="async"></div>' if cover else ""
    return (f'<a class="card card-media reveal" href="{url_of(path)}" hreflang="en">{thumb}<div class="body"><span class="tag">{t["case_tag"]}{badge(lang)}</span>'
            f'<h3 lang="en">{e(LABELS.get(path) or p["h1"])}</h3><p lang="en">{e(clip(p["description"], 140))}</p><span class="foot">{t["case_read"]}</span></div></a>')


def service_card(path, lang, i=None):
    t = T[lang]
    name, text = t[SERVICE_KEYS[path]]
    num = f'<span class="num">0{i}</span>' if i else ""
    return f'<a class="card reveal" href="{url_of(path)}" hreflang="en">{num}<h3>{name}</h3><p>{text}</p><span class="foot">{t["learn_more"]}{badge(lang)}</span></a>'


def testimonials_section(lang):
    t = T[lang]
    f = TESTI["featured"]
    excerpt = "".join(f"<p>{e(x)}</p>" for x in f["excerpt"])
    letter = "".join(f"<p>{e(x)}</p>" for x in f["letter"])
    company = ext(f["link"], e(f["company"])) if f.get("link") else e(f["company"])
    featured = f"""<figure class="featured-quote reveal">
  <div class="mark" aria-hidden="true">“</div>
  <div>
    <blockquote lang="fr" dir="ltr">{excerpt}</blockquote>
    <figcaption class="who"><span class="initials" aria-hidden="true">{initials(f['name'])}</span><div><b>{e(f['name'])}</b><span lang="fr">{e(f['role'])}, {company}</span></div></figcaption>
    <details class="letter"><summary>{t['letter_summary']}</summary>
      <div class="letter-body" lang="fr" dir="ltr">{letter}<p class="meta">{e(f['name'])}, {e(f['role'])}, {e(f['company'])} · {e(f.get('place') or '')}, {e(f['date'])}</p></div>
    </details>
  </div>
</figure>"""
    cards = []
    for q in TESTI["items"]:
        quote = "".join(f"<p>{e(clean_text(x))}</p>" for x in q["quote"])
        role = e(q["role"])
        if q.get("link"):
            role += " · " + ext(q["link"], t["website"])
        photo = (f'<img src="{e(img(q["photo"], 96))}" alt="{e(q["name"])}" width="48" height="48" loading="lazy" decoding="async">' if q.get("photo")
                 else f'<span class="initials">{initials(q["name"])}</span>')
        ql = lang_of(" ".join(q["quote"]))
        cards.append(f'<figure class="quote reveal"><blockquote lang="{ql}" dir="ltr">{quote}</blockquote><figcaption>{photo}<div><b>{e(q["name"])}</b><span>{role}</span></div></figcaption></figure>')
    return f"""<section class="section" id="testimonials">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">{t['testi_eyebrow']}</p><h2>{t['testi_h2']}</h2></div><p>{t['testi_sub']}</p></div>
    {featured}
    <div class="quotes">{''.join(cards)}</div>
  </div>
</section>"""


def experience_section(lang):
    t = T[lang]
    rows = []
    for org, url, dates, key in EXPERIENCE:
        role, text = t[key]
        name = ext(url, e(org)) if url else e(org)
        rows.append(f'<li class="xp reveal"><div class="xp-when"><bdi dir="ltr">{dates or ""}</bdi></div><div><h3>{name}</h3><p class="xp-role">{role}</p><p>{text}</p></div></li>')
    edu = "".join(
        f'<li><b>{e(school)}</b>{f" · {e(deg)}" if deg else ""}<span><bdi dir="ltr">{dates}</bdi> · {t[key]}</span></li>' for school, deg, dates, key in EDUCATION)
    return f"""<section class="section" id="experience">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">{t['xp_eyebrow']}</p><h2>{t['xp_h2']}</h2></div><p>{t['xp_intro']}</p></div>
    <ol class="timeline">{''.join(rows)}</ol>
    <div class="edu reveal"><h3>{t['edu_h3']}</h3><ul>{edu}</ul></div>
  </div>
</section>"""


def skills_section(lang):
    t = T[lang]
    groups = []
    for key, items in SKILLS.items():
        items = t["skills_seo_items"] if items is None else items
        chips = "".join(f"<li>{x}</li>" for x in items)
        groups.append(f'<div class="skill-group reveal"><h3>{t[key]}</h3><ul class="chips">{chips}</ul></div>')
    tools = "".join(
        f'<a class="card tool reveal" href="{e(u)}" target="_blank" rel="noopener"><h3 dir="ltr">{e(name)}</h3><p>{t[key]}</p><span class="foot">{t["tools_open"]}</span></a>'
        for name, u, key in TOOLS)
    intro = t["tools_intro"].format(link=ext(AIOSEO_TOOLS, "aioseo.fr"))
    return f"""<section class="section" id="skills">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">{t['skills_eyebrow']}</p><h2>{t['skills_h2']}</h2></div><p>{t['skills_intro']}</p></div>
    <div class="skills">{''.join(groups)}</div>
  </div>
</section>

<section class="section" id="tools">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">{t['tools_eyebrow']}</p><h2>{t['tools_h2']}</h2></div><p>{intro}</p></div>
    <div class="grid grid-3">{tools}</div>
    <p class="section-more">{ext(AIOSEO_TOOLS, t['tools_all'], 'more')} · {ext(STREAMLIT, 'Streamlit', 'more')} · {ext(GITHUB, 'GitHub', 'more')}</p>
  </div>
</section>"""


def aioseo_section(lang):
    t = T[lang]
    arts = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener" hreflang="fr" lang="fr">{e(x)}</a></li>' for x, u in AIOSEO_ARTICLES)
    note = f'<span class="lang-badge">{t["aioseo_note"]}</span>' if t["aioseo_note"] else ""
    return f"""<section class="section" id="aioseo">
  <div class="wrap">
    <div class="aioseo reveal">
      <div>
        <p class="eyebrow">{t['aioseo_eyebrow']}</p>
        <h2>{t['aioseo_h2']}</h2>
        <p>{t['aioseo_text']}</p>
        {ext(AIOSEO, t['aioseo_cta'] + ' →', 'btn btn-primary')}
      </div>
      <div><ul class="aioseo-list">{arts}</ul>{note}</div>
    </div>
  </div>
</section>"""


# ---------------------------------------------------------------- pages
def build_home(lang):
    t = T[lang]
    path = f"{lang}/index.html"
    services = "".join(service_card(p, lang, i) for i, p in enumerate(SERVICES, 1))
    cases = "".join(case_card(p, lang) for p in CASES[:3])
    posts = "".join(post_card(p, lang) for p in BLOG[:3])
    more_posts = "".join(f'<a href="{url_of(p)}" hreflang="en"><h3 lang="en">{e(LABELS.get(p) or PAGES[p]["h1"])}</h3><span>{fmt_date(post_date(PAGES[p]), lang)}</span></a>' for p in BLOG[3:8])
    certs_html = "".join(f'<div class="cert reveal"><b dir="ltr">{x}</b><span>{ext(u, o) if u else o}</span></div>' for x, o, u in CERTS)
    faq_html = "".join(f'<details class="faq-item reveal"><summary><h3>{e(q)}</h3></summary><div><p>{a}</p></div></details>' for q, a in t["faq"])
    about = [t["about_p1"],
             t["about_p2"].format(eskimoz=ext("https://www.eskimoz.fr", "Eskimoz")),
             t["about_p3"].format(vfaw=ext("https://www.vfaw-ngo.org", "Voices For Animal Welfare"), aio=ext("https://developers.google.com/search/docs/appearance/ai-overviews", "Google AI Overviews")),
             t["about_p4"].format(aioseo=ext(AIOSEO, "aioseo.fr"))]
    home_url = canonical(path)
    ld = graph(person_node(full=True), website_node(),
               {"@type": "ProfilePage", "@id": home_url + "#webpage", "url": home_url, "name": t["home_title"], "description": t["home_desc"],
                "isPartOf": {"@id": WEBSITE_ID}, "mainEntity": {"@id": PERSON_ID}, "about": {"@id": PERSON_ID},
                "primaryImageOfPage": image_obj("/aslanesamai.png"), "inLanguage": lang},
               {"@type": "ProfessionalService", "@id": f"{SITE}/#service", "name": "Aslane Samai · SEO / GEO consulting", "url": f"{SITE}/", "image": OG_DEFAULT,
                "founder": {"@id": PERSON_ID}, "email": EMAIL, "telephone": PHONE, "areaServed": ["FR", "Worldwide"],
                "address": {"@type": "PostalAddress", "addressLocality": "Paris", "addressCountry": "FR"}, "knowsAbout": KNOWS_ABOUT, "sameAs": [LINKEDIN],
                "availableLanguage": ["fr", "en"],
                "hasOfferCatalog": {"@type": "OfferCatalog", "name": t["nav_services"], "itemListElement": [
                    {"@type": "Offer", "itemOffered": {"@type": "Service", "name": t[SERVICE_KEYS[q]][0], "url": canonical(q)}} for q in SERVICES]}},
               {"@type": "FAQPage", "@id": home_url + "#faq", "inLanguage": lang, "mainEntity": [
                   {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}} for q, a in t["faq"]]})
    body = f"""<section class="hero">
  <div class="wrap">
    <div>
      <p class="eyebrow">{t['hero_eyebrow']}</p>
      <h1>{t['hero_h1']}</h1>
      <p class="lead">{t['hero_lead']}</p>
      <div class="actions"><a class="btn btn-primary" href="#contact">{t['hero_cta']}</a><a class="btn btn-ghost" href="/{lang}/ressources.html">{t['hero_cta2']}</a></div>
    </div>
    <figure class="portrait"><img src="{PORTRAIT}" alt="{t['portrait_alt']}" width="560" height="560" fetchpriority="high"><figcaption><i></i>{t['hero_badge']}</figcaption></figure>
  </div>
</section>

<section class="section" id="about">
  <div class="wrap about">
    <div><p class="eyebrow">{t['about_eyebrow']}</p><h2>{t['about_h2']}</h2></div>
    <div class="prose-lg">
      {''.join(f'<p>{x}</p>' for x in about)}
      <div class="facts"><div><b dir="ltr">SEO + GEO</b><span>{t['fact_1']}</span></div><div><b>{len(BLOG)}</b><span>{t['fact_2']}</span></div><div><b>{len(CERTS)}</b><span>{t['fact_3']}</span></div></div>
    </div>
  </div>
</section>

<section class="section" id="services">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">{t['services_eyebrow']}</p><h2>{t['services_h2']}</h2></div><a class="more" href="/{lang}/services.html">{t['services_all']}</a></div>
    <div class="grid grid-4">{services}</div>
  </div>
</section>

{experience_section(lang)}

{skills_section(lang)}

{testimonials_section(lang)}

<section class="section" id="case-studies">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">{t['cases_eyebrow']}</p><h2>{t['cases_h2']}</h2></div><a class="more" href="/{lang}/ressources.html">{t['cases_all']}</a></div>
    <div class="grid grid-3">{cases}</div>
  </div>
</section>

{aioseo_section(lang)}

<section class="section" id="blog">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">{t['blog_eyebrow']}</p><h2>{t['blog_h2']}</h2></div><a class="more" href="/{lang}/blog.html">{t['blog_all']}</a></div>
    <div class="grid grid-3">{posts}</div>
    <div class="list" style="margin-top:40px">{more_posts}</div>
  </div>
</section>

<section class="section" id="certifications">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">{t['certs_eyebrow']}</p><h2>{t['certs_h2']}</h2></div><p>{t['certs_sub']}</p></div>
    <div class="certs">{certs_html}</div>
  </div>
</section>

<section class="section" id="faq">
  <div class="wrap faq">
    <div><p class="eyebrow">{t['faq_eyebrow']}</p><h2>{t['faq_h2']}</h2></div>
    <div class="faq-list">{faq_html}</div>
  </div>
</section>

<section class="section" id="contact">
  <div class="wrap contact">
    <div>
      <p class="eyebrow">{t['contact_eyebrow']}</p>
      <h2>{t['contact_h2']}</h2>
      <p class="lead">{t['contact_lead']}</p>
      <ul>
        <li><a href="mailto:{EMAIL}" dir="ltr">{EMAIL}</a></li>
        <li><a href="{LINKEDIN}" target="_blank" rel="me noopener">LinkedIn</a></li>
        <li><a href="{X_URL}" target="_blank" rel="me noopener">X / Twitter</a></li>
        <li>{ext(AIOSEO, "aioseo.fr")}</li>
      </ul>
    </div>
    <div class="calendly-frame"><div class="calendly-inline-widget" data-url="{CALENDLY}?hide_gdpr_banner=1" data-lazy><div class="calendly-placeholder"><a class="btn btn-ghost" href="{CALENDLY}" target="_blank" rel="noopener">{t['open_calendar']}</a></div></div></div>
  </div>
</section>"""
    write(path, layout(path, title=t["home_title"], description=t["home_desc"], body=body, lang=lang, jsonld=[ld], preload_portrait=True,
                       alternates=alternates_for("index.html")))


def build_listing(lang, page):
    t = T[lang]
    section = LISTINGS[page]
    path = f"{lang}/{page}"
    key = {"services": "services_page", "ressources": "cases_page", "blog": "blog_page"}[section]
    title, description, h1, lead = t[key]
    eyebrow = {"services": t["services_eyebrow"], "ressources": t["cases_eyebrow"], "blog": t["blog_eyebrow"]}[section]
    if section == "blog":
        items, grid = BLOG, f'<div class="grid grid-3">{"".join(post_card(p, lang) for p in BLOG)}</div>'
    elif section == "services":
        items, grid = SERVICES, f'<div class="grid grid-2">{"".join(service_card(p, lang, i) for i, p in enumerate(SERVICES, 1))}</div>'
    else:
        items, grid = CASES, f'<div class="grid grid-3">{"".join(case_card(p, lang) for p in CASES)}</div>'
    body = f"""<section class="page-head"><div class="wrap"><p class="eyebrow">{eyebrow}</p><h1>{e(h1)}</h1><p class="lead">{e(lead)}</p></div></section>
<section style="padding-bottom:0"><div class="wrap">{grid}</div></section>
{cta_band(lang)}"""
    ld = graph(person_node(), website_node(),
               {"@type": "CollectionPage", "@id": canonical(path) + "#webpage", "url": canonical(path), "name": h1, "description": description, "inLanguage": lang,
                "isPartOf": {"@id": WEBSITE_ID}, "author": {"@id": PERSON_ID},
                "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i, "url": canonical(q), "name": PAGES[q]["h1"]} for i, q in enumerate(items, 1)]}},
               breadcrumbs([(t["home_crumb"], f"/{lang}/"), (eyebrow, url_of(path))]))
    write(path, layout(path, title=title, description=description, body=body, lang=lang, active=section, jsonld=[ld], alternates=alternates_for(page)))


def build_page(path):
    p = PAGES[path]
    body_html = content(path)
    lang = lang_of(p["h1"] + " " + re.sub(r"<[^>]+>", " ", body_html)[:4000])
    t = T[lang]
    section = path.split("/")[0] if "/" in path else ""
    crumbs_map = {"blog": (t["nav_blog"], f"/{lang}/blog.html"), "services": (t["nav_services"], f"/{lang}/services.html"), "ressources": (t["nav_cases"], f"/{lang}/ressources.html")}
    is_post = section == "blog"
    date = post_date(p) if is_post else None
    crumbs = f'<nav class="crumbs" aria-label="Breadcrumb"><a href="/{lang}/">{t["home_crumb"]}</a><span aria-hidden="true">/</span>'
    if section in crumbs_map:
        crumbs += f'<a href="{crumbs_map[section][1]}">{crumbs_map[section][0]}</a>'
    crumbs += "</nav>"
    byline = (f'<div class="byline"><img src="/assets/portrait-sm.webp" alt="" width="40" height="40"><div><b>Aslane Samai</b><br>{fmt_date(date, lang) if date else "SEO / GEO consultant"}</div></div>'
              if section else "")
    lead = f'<p class="lead">{e(p["lead"])}</p>' if p.get("lead") and path != "privacy-policy.html" else ""
    cover = f'<figure class="cover"><img src="{e(img(p["cover"], 1600))}" alt=""{dims(p["cover"], 1600)} fetchpriority="high"></figure>' if p.get("cover") and path != "privacy-policy.html" else ""
    author = ""
    if section in ("blog", "ressources"):
        author = f'<aside class="author-box"><img src="/assets/portrait-sm.webp" alt="" width="72" height="72" loading="lazy"><p><b>Aslane Samai</b><br>{t["footer_tagline"]} <a href="/{lang}/#contact">{t["nav_contact"]}</a>.</p></aside>'
    related = ""
    pool = {"blog": BLOG, "ressources": CASES, "services": SERVICES}.get(section)
    if pool:
        idx = pool.index(path) if path in pool else -1
        others = [q for q in pool[idx + 1:] + pool[:max(idx, 0)] if q != path][:3]
        if others:
            card = {"blog": post_card, "ressources": case_card, "services": service_card}[section]
            heading = {"blog": "Keep reading", "ressources": "More case studies", "services": "Other services"}[section] if lang == "en" else {"blog": "À lire aussi", "ressources": "Autres études de cas", "services": "Autres services"}[section]
            related = f'<section class="related"><div class="wrap"><div class="section-head"><h2>{heading}</h2></div><div class="grid grid-3">{"".join(card(q, lang) for q in others)}</div></div></section>'
    canon_path = p.get("canonical") or path
    url = canonical(canon_path)
    words = len(re.sub(r"<[^>]+>", " ", body_html).split())
    node = {"@id": url + "#webpage", "url": url, "headline": p["h1"], "name": p["h1"], "description": clean_text(p["description"]),
            "inLanguage": lang, "isPartOf": {"@id": WEBSITE_ID}, "author": {"@id": PERSON_ID}, "publisher": {"@id": PERSON_ID}}
    if is_post:
        node.update({"@type": "BlogPosting", "mainEntityOfPage": url, "datePublished": date, "image": image_obj(p.get("cover")), "wordCount": words})
    elif section == "ressources":
        node.update({"@type": "Article", "articleSection": "SEO case study", "mainEntityOfPage": url, "image": image_obj(p.get("cover") or first_image(path)),
                     "wordCount": words, **({"datePublished": p["added"]} if p.get("added") else {})})
    elif section == "services" and path in SERVICE_LD:
        name, desc_, stype, price, unit = SERVICE_LD[path]
        node = {"@type": "Service", "@id": url + "#service", "url": url, "name": name, "description": desc_, "serviceType": stype,
                "provider": {"@id": PERSON_ID}, "areaServed": ["FR", "Worldwide"],
                "offers": {"@type": "Offer", "url": url, "priceCurrency": "USD", "description": f"Starting at ${price} {unit}",
                           "priceSpecification": {"@type": "PriceSpecification", "minPrice": price, "priceCurrency": "USD"}}}
    else:
        node["@type"] = "WebPage"
    crumb_items = [(t["home_crumb"], f"/{lang}/")] + ([crumbs_map[section]] if section in crumbs_map else []) + [(p["h1"], url_of(canon_path))]
    jsonld = [graph(person_node(), website_node(), node, breadcrumbs(crumb_items))]
    body = f"""<article>
<header class="article-head"><div class="wrap"><div class="inner">{crumbs}<h1>{e(p['h1'])}</h1>{lead}{byline}</div></div></header>
{cover}
<div class="prose">
{body_html}
</div>
{author}
</article>
{related}
{cta_band(lang)}"""
    og_image = p.get("og_image") or (img(p["cover"], 1200) if p.get("cover") else None)
    write(path, layout(path, title=title_with_brand(page_title(p)), description=p["description"] or p["h1"], body=body, lang=lang, active=section,
                       og_type="article" if is_post else "website", og_image=og_image, jsonld=jsonld, canonical_path=canon_path, published=date))


def build_root():
    """/ : language chooser (x-default). Sends visitors to their saved or browser language; search engines see the three versions."""
    alts = alternates_for("index.html")
    cards = "".join(
        f'<a class="lang-card" href="/{l}/" hreflang="{l}" lang="{l}" dir="{META[l]["dir"]}" data-lang="{l}"><b>{META[l]["name"]}</b><span>{T[l]["home_title"]}</span></a>'
        for l in LANGS)
    body = f"""<section class="chooser"><div class="wrap">
  <img src="{PORTRAIT}" alt="Portrait of Aslane Samai" width="120" height="120">
  <h1>Aslane Samai</h1>
  <p class="lead">SEO / GEO consultant · Consultant SEO / GEO · مستشار SEO / GEO</p>
  <div class="lang-cards">{cards}</div>
</div></section>
<script>
(function () {{
  var pick = null;
  try {{ pick = localStorage.getItem("lang"); }} catch (e) {{}}
  if (!pick) {{
    var prefs = (navigator.languages || [navigator.language || "en"]).map(function (l) {{ return String(l).slice(0, 2).toLowerCase(); }});
    for (var i = 0; i < prefs.length && !pick; i++) if (["en", "fr", "ar"].indexOf(prefs[i]) > -1) pick = prefs[i];
  }}
  location.replace("/" + (pick || "en") + "/" + location.hash);
}})();
</script>"""
    ld = graph(person_node(full=True), website_node())
    write("index.html", layout("index.html", title="Aslane Samai, SEO / GEO consultant", description=T["en"]["home_desc"], body=body, lang="en", jsonld=[ld],
                               alternates=alts))


def build_404():
    langs = " · ".join(f'<a href="/{l}/" lang="{l}">{META[l]["name"]}</a>' for l in LANGS)
    body = f"""<section class="page-head"><div class="wrap"><p class="eyebrow">Error 404</p><h1>This page wandered off.</h1><p class="lead">The link may be old or mistyped. Here are a few good places to start instead.</p>
<div class="actions" style="display:flex;gap:12px;flex-wrap:wrap;margin-top:32px"><a class="btn btn-primary" href="/en/">Home</a><a class="btn btn-ghost" href="/en/blog.html">Blog</a><a class="btn btn-ghost" href="/en/services.html">Services</a></div>
<p style="margin-top:28px">{langs}</p></div></section>"""
    write("404.html", layout("404.html", title="Page not found · Aslane Samai", description="This page could not be found.", body=body, noindex=True))


def build_redirects():
    for old, new in REDIRECTS.items():
        write(old, f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Moved</title>
<link rel="canonical" href="{canonical(new)}"><meta name="robots" content="noindex, follow">
<meta http-equiv="refresh" content="0; url={url_of(new)}"></head>
<body><p>This page has moved to <a href="{url_of(new)}">{canonical(new)}</a>.</p></body></html>
""")


# ---------------------------------------------------------------- sitemap, robots, feeds, llms.txt
def build_sitemap():
    def entry(path, prio, alts=None):
        links = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{u}"/>' for l, u in (alts or {}).items())
        return f"  <url>\n    <loc>{canonical(path)}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <priority>{prio}</priority>{links}\n  </url>\n"
    urls = ""
    for page, prio in [("index.html", "1.0"), ("services.html", "0.9"), ("ressources.html", "0.9"), ("blog.html", "0.9")]:
        alts = alternates_for(page)
        for l in LANGS:
            urls += entry(f"{l}/{page}", prio, alts)
    urls += "".join(entry(p, "0.8") for p in SERVICES + CASES + BLOG)
    urls += entry("privacy-policy.html", "0.3")
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n{urls}</urlset>\n')
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User",
            "Google-Extended", "Applebot-Extended", "Bingbot", "Googlebot", "CCBot", "Meta-ExternalAgent", "MistralAI-User", "DuckAssistBot"]
    robots = "# Search engines and AI assistants are welcome: this site wants to be read, cited and linked.\n"
    robots += "".join(f"User-agent: {b}\n" for b in bots) + "Allow: /\n\n"
    robots += f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"
    write("robots.txt", robots)


def facts_md():
    t = T["en"]
    xp = "\n".join(f"  - {org}{f' ({dates})' if dates else ''}: {strip_tags(t[key][0])}. {strip_tags(t[key][1])}" for org, _, dates, key in EXPERIENCE)
    edu = "\n".join(f"  - {school}{f', {deg}' if deg else ''} ({dates}): {t[key]}" for school, deg, dates, key in EDUCATION)
    tools = "\n".join(f"  - [{name}]({u}): {t[key]}" for name, u, key in TOOLS)
    skills = "; ".join(strip_tags(", ".join(T["en"]["skills_seo_items"] if v is None else v)) for v in SKILLS.values())
    return f"""Key facts:

- Name: Aslane Samai (also written Samai Aslane)
- Role: SEO / GEO consultant, based in Paris, France; works in French and English
- Experience:
{xp}
- Education:
{edu}
- Skills and tools: {skills}
- Certifications: Google Data Analytics (Google / Coursera), SQL (CoRise), Technical SEO (Blue Array), SEO Manager (Blue Array)
- Tools built (free):
{tools}
- Also writes: [aioseo.fr]({AIOSEO}), "AIO SEO · Good GEO is good SEO!", a French-language blog about GEO and AI search (Google AI Overviews, AI Mode, query fan-out, GEO tools)
- Contact: {EMAIL} · free 30-minute SEO audit call: {CALENDLY}
- Profiles: LinkedIn {LINKEDIN} · X {X_URL} · GitHub {GITHUB} · Medium {MEDIUM}"""


INTRO = ("> Aslane Samai is an SEO and GEO (generative engine optimization) consultant based in Paris, France. He helps businesses get found on "
         "Google and cited in AI answers (ChatGPT, Gemini, Google AI Overviews) through technical SEO audits, data analysis and content. "
         "He writes aioseo.fr, a French blog about AI search.")


def build_llms():
    def line(q):
        return f"- [{clean_text(PAGES[q]['h1'])}]({canonical(q)}): {clean_text(PAGES[q]['description'])}"
    lines = [f"# {SITE_NAME}", "", INTRO, "", facts_md(), "",
             "## Site versions", "",
             *[f"- [{META[l]['name']}]({canonical(f'{l}/index.html')}): {T[l]['home_title']}" for l in LANGS], "",
             "## Services", "", *[line(q) for q in SERVICES], "",
             "## Case studies", "", *[line(q) for q in CASES], "",
             "## Blog", "", *[line(q) for q in BLOG], "",
             "## AIO SEO (French articles on aioseo.fr)", "", *[f"- [{x}]({u})" for x, u in AIOSEO_ARTICLES], "",
             "## Optional", "",
             f"- [Full text of every page]({SITE}/llms-full.txt): services, case studies and articles in Markdown",
             f"- [Privacy policy]({canonical('privacy-policy.html')})"]
    write("llms.txt", "\n".join(lines) + "\n")

    f = TESTI["featured"]
    testimonials = "\n\n".join(f"> {clean_text(' '.join(q['quote']))}\n>\n> — {q['name']}, {q['role']}" for q in TESTI["items"])
    full = [f"# {SITE_NAME}: full site content", INTRO, facts_md(), "## About", strip_tags(T["en"]["about_p1"]),
            "## Frequently asked questions", *[f"### {q}\n\n{strip_tags(a)}" for q, a in T["en"]["faq"]],
            "## Testimonials", f"### Recommendation letter from {f['name']}, {f['role']}, {f['company']} ({f['date']})\n\n" + "\n\n".join(f["letter"]), testimonials]
    for q in SERVICES + CASES + BLOG:
        p = PAGES[q]
        meta = f"URL: {canonical(q)}" + (f" · Published: {post_date(p)}" if q.startswith("blog/") and post_date(p) else "")
        full.append(f"---\n\n## {clean_text(p['h1'])}\n\n{meta}\n\n{to_markdown(content(q), SITE)}")
    write("llms-full.txt", "\n\n".join(full) + "\n")


def build_feed():
    def rfc822(d):
        return dt.datetime.strptime(d, "%Y-%m-%d").strftime("%a, %d %b %Y 12:00:00 +0000")
    posts = sorted((q for q in BLOG if post_date(PAGES[q])), key=lambda q: post_date(PAGES[q]), reverse=True)
    items = "".join(f"""  <item>
    <title>{e(PAGES[q]['h1'])}</title>
    <link>{canonical(q)}</link>
    <guid isPermaLink="true">{canonical(q)}</guid>
    <pubDate>{rfc822(post_date(PAGES[q]))}</pubDate>
    <dc:creator>Aslane Samai</dc:creator>
    <description>{e(clean_text(PAGES[q]['description']))}</description>
  </item>
""" for q in posts)
    write("feed.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <title>Aslane Samai · Blog</title>
  <link>{SITE}/en/blog.html</link>
  <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>Notes on SEO, GEO, AI search and the web by Aslane Samai, SEO / GEO consultant in Paris.</description>
  <language>en</language>
  <lastBuildDate>{rfc822(TODAY)}</lastBuildDate>
{items}</channel>
</rss>
""")


if __name__ == "__main__":
    for lang in LANGS:
        build_home(lang)
        for page in LISTINGS:
            build_listing(lang, page)
    build_root()
    for path in PAGES:
        build_page(path)
    build_404()
    build_redirects()
    build_sitemap()
    build_llms()
    build_feed()
    print(f"built {len(LANGS) * 4 + len(PAGES) + 2} pages ({', '.join(LANGS)}) · blog {len(BLOG)} · services {len(SERVICES)} · cases {len(CASES)} · redirects {len(REDIRECTS)}")
