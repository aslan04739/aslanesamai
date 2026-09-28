"""Static site generator for aslanesamai.com (stdlib only).

    python3 _build/build.py

Reads _build/site.json (page metadata), _build/content/<path>.html (article bodies) and
_build/testimonials.json, and writes every public page at the repository root, keeping the
existing URLs. Edit the sources, then rebuild; don't edit the generated .html files by hand.
"""
import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_build"
SITE = "https://aslanesamai.com"
SITE_NAME = "Aslane Samai"
PORTRAIT = "/assets/portrait.webp"
OG_DEFAULT = f"{SITE}/aslanesamai.png"
CALENDLY = "https://calendly.com/samaiaslane/free-seo-audit"
EMAIL = "contact@aslanesamai.com"
LINKEDIN = "https://www.linkedin.com/in/aslane-samai"
X_URL = "https://x.com/this_is_aslan"
MEDIUM = "https://medium.com/@samaiaslane7"
TODAY = dt.date.today().isoformat()

data = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
PAGES = data["pages"]
TESTI = json.loads((SRC / "testimonials.json").read_text(encoding="utf-8"))
CSS_V = hashlib.sha1((ROOT / "assets/site.css").read_bytes() + (ROOT / "assets/site.js").read_bytes()).hexdigest()[:8]

e = lambda s: html.escape(s or "", quote=True)  # noqa: E731
GENERIC_TITLES = {"my blog", "read my blog", ""}

FR_WORDS = re.compile(r"\b(le|la|les|des|une|est|pour|avec|dans|sur|nous|vous|qui|que|pas|sont|du|au|et)\b", re.I)
EN_WORDS = re.compile(r"\b(the|and|is|for|with|in|on|we|you|who|that|not|are|of|to|a)\b", re.I)


def lang_of(text):
    return "fr" if len(FR_WORDS.findall(text)) > len(EN_WORDS.findall(text)) else "en"


def clean_text(s):
    return re.sub(r"\s+([.,;:!?])(?=\s|$)", r"\1", re.sub(r"\s+", " ", s)).strip()


def img(url, width=None):
    """Sirv images can be resized on the fly; local ones are served as is."""
    if url and width and "sirv.com" in url and "?" not in url:
        return f"{url}?w={width}"
    return url


def content(path):
    body = (SRC / "content" / path).read_text(encoding="utf-8")
    body = body.replace("/blog/aslan04739/aslanesamai/images/", "/images/")  # broken absolute path from an old build
    body = re.sub(r"<img\b(?![^>]*\bloading=)", '<img loading="lazy" decoding="async"', body)
    return body


def page_title(p):
    t = clean_text(p["title"]).rstrip("<").strip()
    return p["h1"] if t.lower() in GENERIC_TITLES else t


def post_date(p):
    return p.get("date_published") or p.get("added")


def fmt_date(d, lang="en"):
    if not d:
        return ""
    y, m, day = map(int, d.split("-"))
    months = (["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
              if lang == "fr" else ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
    return f"{day} {months[m - 1]} {y}" if lang == "fr" else f"{months[m - 1]} {day}, {y}"


def url_of(path):
    return "/" if path == "index.html" else "/" + path


def canonical(path):
    return SITE + url_of(path)


# ---------------------------------------------------------------- collections
def ordered(order_key, prefix):
    seen, out = set(), []
    for it in data[order_key]:
        if it["path"] in PAGES and it["path"] not in seen:
            seen.add(it["path"])
            out.append(it["path"])
    return out, seen


BLOG, seen = ordered("blog_order", "blog/")
extra = sorted((p for p in PAGES if p.startswith("blog/") and p not in seen), key=lambda p: post_date(PAGES[p]) or "", reverse=True)
BLOG = BLOG + extra
SERVICES, _ = ordered("services_order", "services/")
CASES, _ = ordered("cases_order", "ressources/")
LABELS = {it["path"]: clean_text(it["label"]) for k in ("blog_order", "services_order", "cases_order", "home_blog") for it in data[k]}
SERVICE_SHORT = {
    "services/seo-the-driving-force-behind-my-passion.html": ("Search Engine Optimization", "Audits, technical SEO, on-page and off-page work that makes search engines, and now AI answers, understand and recommend your site."),
    "services/data-analysis.html": ("Data analytics", "SQL and Python to find where traffic is won or lost, and which fixes will actually move the numbers."),
    "services/data-visualization.html": ("Data visualization", "Clear dashboards and charts that turn search data into decisions your whole team can follow."),
    "services/seo-content-writing.html": ("Content writing", "Search-led content that answers real questions, ranks, and gets cited by generative engines."),
}


# ---------------------------------------------------------------- layout
def header(active):
    items = [("Services", "/services.html", "services"), ("Case studies", "/ressources.html", "ressources"), ("Blog", "/blog.html", "blog"), ("Contact", "/#contact", "contact")]
    links = "".join(f'<a href="{h}"{" aria-current=\"page\"" if a == active else ""}>{t}</a>' for t, h, a in items)
    cta = f'<a class="btn btn-primary" href="/#contact">Free SEO audit</a>'
    return f"""<header class="site-header" id="top">
  <div class="wrap">
    <a class="brand" href="/" aria-label="Aslane Samai, home">Aslane Samai<span>.</span></a>
    <nav class="nav" aria-label="Main">{links}{cta}</nav>
    <details class="menu"><summary aria-label="Menu"><span></span></summary><nav aria-label="Mobile">{links}{cta}</nav></details>
  </div>
</header>"""


def footer():
    year = dt.date.today().year
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="cols">
      <div class="f-about"><a class="brand" href="/">Aslane Samai<span>.</span></a><p>SEO &amp; GEO consultant based in Paris. I help businesses get found on Google and cited by AI answers.</p></div>
      <div><h4>Explore</h4><ul><li><a href="/services.html">Services</a></li><li><a href="/ressources.html">Case studies</a></li><li><a href="/blog.html">Blog</a></li><li><a href="/#testimonials">Testimonials</a></li></ul></div>
      <div><h4>Contact</h4><ul><li><a href="mailto:{EMAIL}">{EMAIL}</a></li><li><a href="/#contact">Book a free audit</a></li></ul></div>
      <div><h4>Follow</h4><ul><li><a href="{LINKEDIN}" rel="me noopener" target="_blank">LinkedIn</a></li><li><a href="{X_URL}" rel="me noopener" target="_blank">X / Twitter</a></li><li><a href="{MEDIUM}" rel="me noopener" target="_blank">Medium</a></li></ul></div>
    </div>
    <div class="legal"><span>© {year} Aslane Samai</span><a href="/privacy-policy.html">Privacy policy</a></div>
  </div>
</footer>"""


def layout(path, *, title, description, body, active="", lang="en", og_type="website", og_image=None, jsonld=(), preload_portrait=False, noindex=False):
    og_image = og_image or OG_DEFAULT
    if og_image.startswith("/"):
        og_image = SITE + og_image
    ld = "".join(f'\n<script type="application/ld+json">{j}</script>' for j in jsonld)
    pre = f'\n<link rel="preload" as="image" href="{PORTRAIT}" type="image/webp">' if preload_portrait else ""
    robots = '\n<meta name="robots" content="noindex">' if noindex else ""
    canon = "" if noindex else f'\n<link rel="canonical" href="{canonical(path)}">'
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(clean_text(description))}">
<meta name="author" content="Aslane Samai">{robots}{canon}
<meta name="theme-color" content="#f6f3ec" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121311" media="(prefers-color-scheme: dark)">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(clean_text(description))}">
<meta property="og:url" content="{canonical(path)}">
<meta property="og:image" content="{e(og_image)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@this_is_aslan">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(clean_text(description))}">
<meta name="twitter:image" content="{e(og_image)}">
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/fraunces-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/inter-normal-latin.woff2" as="font" type="font/woff2" crossorigin>{pre}
<link rel="stylesheet" href="/assets/site.css?v={CSS_V}">
<script src="/assets/site.js?v={CSS_V}" defer></script>{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{header(active)}
<main id="main">
{body}
</main>
{footer()}
</body>
</html>
"""


def cta_band(lang="en"):
    if lang == "fr":
        h, p, b = "Et si on regardait votre site ensemble ?", "30 minutes, gratuitement : je vous montre ce qui freine votre visibilité sur Google et dans les réponses des IA.", "Réserver un audit gratuit"
    else:
        h, p, b = "Want to know what's holding your site back?", "A free 30-minute audit call: what's blocking your visibility on Google and in AI answers, and what to fix first.", "Book a free audit"
    return f"""<section class="section"><div class="wrap"><div class="cta-band reveal"><div><h2>{h}</h2><p>{p}</p></div><a class="btn btn-primary" href="/#contact">{b}</a></div></div></section>"""


def post_card(path, width=720):
    p = PAGES[path]
    lang = lang_of(p["h1"] + " " + p["description"])
    cover = img(p.get("cover"), width)
    thumb = f'<div class="thumb"><img src="{e(cover)}" alt="" loading="lazy" decoding="async"></div>' if cover else ""
    return f"""<a class="card card-media" href="{url_of(path)}">{thumb}<div class="body"><span class="tag">{fmt_date(post_date(p), lang)}</span><h3>{e(LABELS.get(path) or p['h1'])}</h3><p>{e(clip(p['description'], 150))}</p></div></a>"""


def clip(s, n):
    s = clean_text(s)
    return s if len(s) <= n else s[: s.rfind(" ", 0, n)].rstrip(",;:") + "…"


def initials(name):
    return "".join(w[0] for w in name.split()[:2]).upper()


# ---------------------------------------------------------------- testimonials
def testimonials_section():
    f = TESTI["featured"]
    excerpt = "".join(f"<p>{e(x)}</p>" for x in f["excerpt"])
    letter = "".join(f"<p>{e(x)}</p>" for x in f["letter"])
    company = f'<a href="{e(f["link"])}" target="_blank" rel="noopener">{e(f["company"])}</a>' if f.get("link") else e(f["company"])
    featured = f"""<figure class="featured-quote reveal" lang="fr">
  <div class="mark" aria-hidden="true">“</div>
  <div>
    <blockquote>{excerpt}</blockquote>
    <figcaption class="who"><span class="initials" aria-hidden="true">{initials(f['name'])}</span><div><b>{e(f['name'])}</b><span>{e(f['role'])}, {company}</span></div></figcaption>
    <details class="letter"><summary>Lire la lettre de recommandation complète</summary>
      <div class="letter-body">{letter}<p class="meta">{e(f['name'])}, {e(f['role'])}, {e(f['company'])} · {e(f.get('place') or '')}, {e(f['date'])}</p></div>
    </details>
  </div>
</figure>"""
    cards = []
    for t in TESTI["items"]:
        quote = "".join(f"<p>{e(clean_text(q))}</p>" for q in t["quote"])
        role = e(t["role"])
        if t.get("link"):
            role += f' · <a href="{e(t["link"])}" target="_blank" rel="noopener">website</a>'
        photo = f'<img src="{e(img(t["photo"], 96))}" alt="{e(t["name"])}" width="48" height="48" loading="lazy" decoding="async">' if t.get("photo") else f'<span class="initials">{initials(t["name"])}</span>'
        tl = lang_of(" ".join(t["quote"]))
        cards.append(f"""<figure class="quote reveal" lang="{tl}"><blockquote>{quote}</blockquote><figcaption>{photo}<div><b>{e(t['name'])}</b><span>{role}</span></div></figcaption></figure>""")
    return f"""<section class="section" id="testimonials">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">Testimonials</p><h2>What people I've worked with say</h2></div><p>Clients, managers and teammates, in their own words.</p></div>
    {featured}
    <div class="quotes">{''.join(cards)}</div>
  </div>
</section>"""


# ---------------------------------------------------------------- pages
def build_home():
    services = "".join(
        f'<a class="card reveal" href="{url_of(p)}"><span class="num">0{i}</span><h3>{e(SERVICE_SHORT[p][0])}</h3><p>{e(SERVICE_SHORT[p][1])}</p><span class="foot">Learn more</span></a>'
        for i, p in enumerate(SERVICES, 1))
    cases = "".join(case_card(p) for p in CASES[:3])
    posts = "".join(post_card(p) for p in BLOG[:3])
    more_posts = "".join(f'<a href="{url_of(p)}"><h3>{e(LABELS.get(p) or PAGES[p]["h1"])}</h3><span>{fmt_date(post_date(PAGES[p]))}</span></a>' for p in BLOG[3:8])
    certs = [("Google Data Analytics", "Google · Coursera", None), ("SQL", "CoRise", None), ("Technical SEO", "Blue Array", "https://www.bluearray.co.uk/"), ("SEO Manager", "Blue Array", "https://www.bluearray.co.uk/")]
    certs_html = "".join(f'<div class="cert reveal"><b>{t}</b><span>{f"<a href={chr(34)}{u}{chr(34)} target=_blank rel=noopener>{o}</a>" if u else o}</span></div>' for t, o, u in certs)
    desc = "As an SEO professional, my goal is to help businesses succeed online. I offer a range of services, including SEO audits, technical optimization, on-page and off-page SEO, content creation, and backlink acquisition."
    person = json.dumps({
        "@context": "https://schema.org", "@type": "Person", "name": "Samai Aslane", "alternateName": "Aslane Samai",
        "jobTitle": "SEO / GEO consultant", "url": f"{SITE}/", "image": OG_DEFAULT, "email": EMAIL, "telephone": "+33651630813",
        "address": {"@type": "PostalAddress", "streetAddress": "Paris, ile de France", "addressLocality": "Paris", "addressRegion": "Paris", "postalCode": "75000", "addressCountry": "FR"},
        "alumniOf": [], "sameAs": [LINKEDIN, MEDIUM, X_URL],
        "hasCredential": [{"@type": "EducationalOccupationalCredential", "name": f"{t} certification", "recognizedBy": {"@type": "Organization", "name": o.split(" · ")[0]}} for t, o, _ in certs],
    }, ensure_ascii=False, indent=1)
    person = person.replace('"alumniOf": [],\n ', "")
    website = json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": f"{SITE}/"})
    body = f"""<section class="hero">
  <div class="wrap">
    <div>
      <p class="eyebrow">SEO &amp; GEO consultant · Paris</p>
      <h1>Aslane Samai, your <em>SEO / GEO</em> consultant</h1>
      <p class="lead">I help businesses get found: on Google, and in the answers of ChatGPT, Gemini and AI Overviews. Technical audits, data-driven strategy and content that earns its place.</p>
      <div class="actions"><a class="btn btn-primary" href="#contact">Book a free SEO audit</a><a class="btn btn-ghost" href="/ressources.html">See case studies</a></div>
    </div>
    <figure class="portrait"><img src="{PORTRAIT}" alt="Portrait of Aslane Samai" width="600" height="635" fetchpriority="high"><figcaption><i></i>Based in Paris</figcaption></figure>
  </div>
</section>

<section class="section" id="about">
  <div class="wrap about">
    <div><p class="eyebrow">About</p><h2>Let me tell you about me</h2></div>
    <div class="prose-lg">
      <p>{desc}</p>
      <p>I previously worked as an <strong>SEO &amp; GEO consultant at <a href="https://www.eskimoz.fr" target="_blank" rel="noopener">Eskimoz</a></strong>, one of France's leading SEO agencies, where I spent a year on technical audits, traffic and performance analysis, and SEO / GEO strategy for large accounts such as Sunelia, Manpower, Engie My Power and Riverly.</p>
      <p>I'm also assisting <a href="https://www.vfaw-ngo.org" target="_blank" rel="noopener">Voices For Animal Welfare</a> with launching their new website and improving its SEO performance, and exploring the impact of <a href="https://developers.google.com/search/docs/appearance/ai-overviews" target="_blank" rel="noopener">Google AI Overviews</a> on search visibility.</p>
      <div class="facts"><div><b>SEO + GEO</b><span>Search engines and generative engines</span></div><div><b>{len(BLOG)}</b><span>Articles on the blog</span></div><div><b>4</b><span>Professional certifications</span></div></div>
    </div>
  </div>
</section>

<section class="section" id="services">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">Services</p><h2>Here's everything I do</h2></div><a class="more" href="/services.html">All services</a></div>
    <div class="grid grid-4">{services}</div>
  </div>
</section>

{testimonials_section()}

<section class="section" id="case-studies">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">Case studies</p><h2>Real results for real clients</h2></div><a class="more" href="/ressources.html">All case studies</a></div>
    <div class="grid grid-3">{cases}</div>
  </div>
</section>

<section class="section" id="blog">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">Blog</p><h2>Notes on SEO, AI search and the web</h2></div><a class="more" href="/blog.html">All articles</a></div>
    <div class="grid grid-3">{posts}</div>
    <div class="list" style="margin-top:40px">{more_posts}</div>
  </div>
</section>

<section class="section" id="certifications">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">Certifications</p><h2>Humble brag</h2></div><p>Certifications don't always reflect what someone knows, but these come from authoritative organizations.</p></div>
    <div class="certs">{certs_html}</div>
  </div>
</section>

<section class="section" id="contact">
  <div class="wrap contact">
    <div>
      <p class="eyebrow">Contact</p>
      <h2>Let's get your site found.</h2>
      <p class="lead">Pick a slot for a free 30-minute SEO audit, or write to me directly.</p>
      <ul>
        <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
        <li><a href="{LINKEDIN}" target="_blank" rel="me noopener">LinkedIn</a></li>
        <li><a href="{X_URL}" target="_blank" rel="me noopener">X / Twitter</a></li>
      </ul>
    </div>
    <div class="calendly-frame"><div class="calendly-inline-widget" data-url="{CALENDLY}?hide_gdpr_banner=1" data-lazy><div class="calendly-placeholder"><a class="btn btn-ghost" href="{CALENDLY}" target="_blank" rel="noopener">Open the booking calendar</a></div></div></div>
  </div>
</section>"""
    write("index.html", layout("index.html", title="Aslane Samai, SEO / GEO consultant", description=desc, body=body, jsonld=[person, website], preload_portrait=True))


def first_image(path):
    m = re.search(r'<img[^>]*\bsrc="([^"]+)"', (SRC / "content" / path).read_text(encoding="utf-8"))
    return m.group(1) if m else None


def case_card(path):
    p = PAGES[path]
    cover = img(p.get("cover") or first_image(path), 720)
    thumb = f'<div class="thumb logo"><img src="{e(cover)}" alt="" loading="lazy" decoding="async"></div>' if cover else ""
    return f'<a class="card card-media reveal" href="{url_of(path)}">{thumb}<div class="body"><span class="tag">Case study</span><h3>{e(LABELS.get(path) or p["h1"])}</h3><p>{e(clip(p["description"], 140))}</p><span class="foot">Read the case study</span></div></a>'


def build_index(path, *, active, eyebrow, h1, lead, title, description, grid):
    body = f"""<section class="page-head"><div class="wrap"><p class="eyebrow">{eyebrow}</p><h1>{e(h1)}</h1><p class="lead">{e(lead)}</p></div></section>
<section style="padding-bottom:0"><div class="wrap">{grid}</div></section>
{cta_band()}"""
    write(path, layout(path, title=title, description=description, body=body, active=active))


def build_listings():
    build_index("blog.html", active="blog", eyebrow="Blog", h1="Read my blog", lead="For SEO tips, tricks, tools, and more: news decoded, experiments, and resources for beginners.",
                title="Blog · SEO tips, tricks and tools · Aslane Samai",
                description=PAGES_OLD_DESC["blog.html"], grid=f'<div class="grid grid-3">{"".join(post_card(p) for p in BLOG)}</div>')
    grid = "".join(
        f'<a class="card reveal" href="{url_of(p)}"><span class="num">0{i}</span><h3>{e(SERVICE_SHORT[p][0])}</h3><p>{e(SERVICE_SHORT[p][1])}</p><span class="foot">Learn more</span></a>'
        for i, p in enumerate(SERVICES, 1))
    build_index("services.html", active="services", eyebrow="Services", h1="Here's everything I do", lead="From technical SEO and generative engine optimization to data analysis, visualization and content: everything that gets a site found, and keeps it there.",
                title="Services · SEO, GEO, data analysis and content · Aslane Samai", description=PAGES_OLD_DESC["services.html"], grid=f'<div class="grid grid-2">{grid}</div>')
    build_index("ressources.html", active="ressources", eyebrow="Case studies", h1="Real SEO success stories from my clients", lead="How personalized strategies and focused work turned invisible websites into ones that rank.",
                title="SEO case studies · Real success stories · Aslane Samai", description=PAGES_OLD_DESC["ressources.html"], grid=f'<div class="grid grid-3">{"".join(case_card(p) for p in CASES)}</div>')


def build_page(path):
    p = PAGES[path]
    body_html = content(path)
    lang = lang_of(p["h1"] + " " + re.sub(r"<[^>]+>", " ", body_html)[:4000])
    section = path.split("/")[0] if "/" in path else ""
    crumbs_map = {"blog": ("Blog", "/blog.html"), "services": ("Services", "/services.html"), "ressources": ("Case studies", "/ressources.html")}
    is_post = section == "blog"
    title = page_title(p)
    date = post_date(p) if is_post else None
    crumbs = '<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span>'
    if section in crumbs_map:
        crumbs += f'<a href="{crumbs_map[section][1]}">{crumbs_map[section][0]}</a>'
    crumbs += "</nav>"
    byline = f'<div class="byline"><img src="/assets/portrait-sm.webp" alt="" width="40" height="40"><div><b>Aslane Samai</b><br>{fmt_date(date, lang) if date else "SEO / GEO consultant"}</div></div>' if section != "" else ""
    lead = f'<p class="lead">{e(p["lead"])}</p>' if p.get("lead") and path != "privacy-policy.html" else ""
    cover = f'<figure class="cover"><img src="{e(img(p["cover"], 1600))}" alt="" fetchpriority="high"></figure>' if p.get("cover") and path != "privacy-policy.html" else ""
    author = ""
    if section in ("blog", "ressources"):
        bio = ("Consultant SEO &amp; GEO à Paris. J'aide les entreprises à être trouvées sur Google et citées par les IA." if lang == "fr"
               else "SEO &amp; GEO consultant in Paris. I help businesses get found on Google and cited by AI answers.")
        author = f'<aside class="author-box"><img src="/assets/portrait-sm.webp" alt="" width="72" height="72" loading="lazy"><p><b>Aslane Samai</b><br>{bio} <a href="/#contact">{"Me contacter" if lang == "fr" else "Get in touch"}</a>.</p></aside>'
    related = ""
    pool = {"blog": BLOG, "ressources": CASES, "services": SERVICES}.get(section)
    if pool:
        idx = pool.index(path) if path in pool else -1
        others = [q for q in pool[idx + 1:] + pool[:max(idx, 0)] if q != path][:3]
        if others:
            card = post_card if section == "blog" else case_card if section == "ressources" else (lambda q: f'<a class="card" href="{url_of(q)}"><h3>{e(SERVICE_SHORT[q][0])}</h3><p>{e(SERVICE_SHORT[q][1])}</p><span class="foot">Learn more</span></a>')
            heading = {"blog": "Keep reading", "ressources": "More case studies", "services": "Other services"}[section]
            related = f'<section class="related"><div class="wrap"><div class="section-head"><h2>{heading}</h2></div><div class="grid grid-3">{"".join(card(q) for q in others)}</div></div></section>'
    jsonld = list(p.get("jsonld") or [])
    if is_post and not any('"BlogPosting"' in j or '"Article"' in j for j in jsonld):
        jsonld.append(json.dumps({"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["h1"], "description": clean_text(p["description"]),
                                  "datePublished": date, "image": p.get("cover") if (p.get("cover") or "").startswith("http") else (SITE + p["cover"] if p.get("cover") else OG_DEFAULT),
                                  "author": {"@type": "Person", "name": "Aslane Samai", "url": f"{SITE}/"}, "mainEntityOfPage": canonical(path), "inLanguage": lang}, ensure_ascii=False))
    trail = [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"}]
    if section in crumbs_map:
        trail.append({"@type": "ListItem", "position": 2, "name": crumbs_map[section][0], "item": SITE + crumbs_map[section][1]})
    trail.append({"@type": "ListItem", "position": len(trail) + 1, "name": p["h1"], "item": canonical(path)})
    jsonld.append(json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": trail}, ensure_ascii=False))
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
    write(path, layout(path, title=title, description=p["description"] or p["h1"], body=body, active=section, lang=lang,
                       og_type="article" if is_post else "website", og_image=og_image, jsonld=jsonld))


def build_404():
    body = f"""<section class="page-head"><div class="wrap"><p class="eyebrow">Error 404</p><h1>This page wandered off.</h1><p class="lead">The link may be old or mistyped. Here are a few good places to start instead.</p>
<div class="actions" style="display:flex;gap:12px;flex-wrap:wrap;margin-top:32px"><a class="btn btn-primary" href="/">Home</a><a class="btn btn-ghost" href="/blog.html">Blog</a><a class="btn btn-ghost" href="/services.html">Services</a></div></div></section>"""
    write("404.html", layout("404.html", title="Page not found · Aslane Samai", description="This page could not be found.", body=body, noindex=True))


def build_sitemap():
    entries = [("index.html", "1.0"), ("services.html", "0.9"), ("ressources.html", "0.9"), ("blog.html", "0.9")]
    entries += [(p, "0.8") for p in SERVICES + CASES + BLOG]
    entries += [("privacy-policy.html", "0.3")]
    urls = "".join(f"  <url>\n    <loc>{canonical(p)}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <priority>{pr}</priority>\n  </url>\n" for p, pr in entries)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")


def write(rel, text):
    (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / rel).write_text(text, encoding="utf-8")


PAGES_OLD_DESC = {
    "blog.html": "Expert SEO insights, tips, and strategies to boost your website's visibility. Stay informed with the latest SEO news, updates, and industry trends. Optimize your online presence and achieve higher search rankings.",
    "services.html": "Discover my SEO-related services. From copywriting and data analysis to data visualization.",
    "ressources.html": "Dive into real-life SEO success stories from my clients. Discover how personalized strategies and dedicated efforts transformed their online presence and drove exceptional results.",
}

if __name__ == "__main__":
    build_home()
    build_listings()
    for path in PAGES:
        build_page(path)
    build_404()
    build_sitemap()
    print(f"built {len(PAGES) + 5} pages · blog {len(BLOG)} · services {len(SERVICES)} · cases {len(CASES)}")
