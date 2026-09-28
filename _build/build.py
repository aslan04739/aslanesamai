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
from i18n import (AIOSEO, AIOSEO_ARTICLES, AIOSEO_ARTICLES_EN, AIOSEO_BY_LANG, AIOSEO_TOOLS_BY_LANG, EDUCATION, EXPERIENCE,  # noqa: E402
                  GITHUB, LANGS, META, SKILLS, STREAMLIT, TOOL_URL_EN, TOOLS, T)
from md import to_markdown  # noqa: E402
from services import SERVICES as SERVICE_DEFS, UI as SVC_UI  # noqa: E402

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
MEDIUM = "https://medium.com/@samaiaslane7"
AIOSEO_PROFILE = "https://aioseo.fr/aslane-samai-consultant-seo-technique-expert-geo/"
AIOSEO_PROFILE_EN = "https://aioseo.fr/en/aslane-samai-technical-seo-geo-expert/"
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
    body = re.sub(r"<img\b[^>]*>", _sized_img, (SRC / "content" / path).read_text(encoding="utf-8"))
    if "<!-- chart:aioseo -->" in body:
        body = (body.replace("<!-- stats:aioseo -->", aioseo_stats_html()).replace("<!-- chart:aioseo -->", aioseo_chart())
                .replace("<!-- genai:aioseo -->", aioseo_genai_html() if AIO.get("genai") else "")
                .replace("<!-- milestones:aioseo -->", aioseo_milestones()))
    return body


# ---------------------------------------------------------------- aioseo.fr case study (numbers from _build/aioseo_stats.json)
AIO = json.loads((SRC / "aioseo_stats.json").read_text()) if (SRC / "aioseo_stats.json").exists() else None


def _month_label(m, short=True):
    y, mo = m.split("-")
    return f"{MONTHS['en'][int(mo) - 1][:3]} {y[2:] if short else y}"


def aioseo_stats_html():
    mon = [m for m in AIO["monthly"] if m["month"] not in (AIO["first_day"][:7],)]
    first, best = mon[0], max(mon, key=lambda m: m["impressions"])
    best_pos = min((m for m in mon if m["impressions"] > 5000), key=lambda m: m["position"])
    tot_i = sum(m["impressions"] for m in AIO["monthly"])
    tot_c = sum(m["clicks"] for m in AIO["monthly"])
    l90 = AIO["last90"]
    cards = [
        (f"{best['impressions'] / first['impressions']:.0f}×", f"monthly impressions, {first['impressions']:,} ({_month_label(first['month'], False)}) to {best['impressions']:,} ({_month_label(best['month'], False)})"),
        (f"{first['position']:.0f} → {best_pos['position']:.0f}", f"average position, {_month_label(first['month'], False)} to {_month_label(best_pos['month'], False)}"),
        (f"{tot_i / 1000:.0f}k", f"impressions and {tot_c:,} clicks since launch"),
        (f"{l90['queries_with_impressions']:,}", f"queries and {l90['pages_with_impressions']} pages with impressions in the last 90 days"),
        (f"{l90['en_click_share'] * 100:.0f}%", "of clicks go to the English versions (last 90 days)"),
        (f"{l90['nonbrand_click_share'] * 100:.0f}%", "of query clicks are non-brand (last 90 days)"),
    ]
    items = "".join(f"<div><b>{v}</b><span>{e(t)}</span></div>" for v, t in cards)
    return f'<div class="case-stats">{items}</div><p class="case-source">Source: Google Search Console, {AIO["first_day"]} to {AIO["last_day"]}.</p>'


def aioseo_chart():
    mon = [m for m in AIO["monthly"] if m["month"] != AIO["first_day"][:7]]  # launch month has a single day
    W, H, L, R, T, B = 720, 300, 56, 44, 20, 36
    iw, ih = W - L - R, H - T - B
    maxi = max(m["impressions"] for m in mon)
    top = 10000 * -(-maxi // 10000)
    bw = iw / len(mon)
    bars, labels, pts = [], [], []
    for i, m in enumerate(mon):
        h = ih * m["impressions"] / top
        x = L + i * bw
        bars.append(f'<rect class="ch-bar" x="{x + bw * .18:.1f}" y="{T + ih - h:.1f}" width="{bw * .64:.1f}" height="{h:.1f}"><title>{_month_label(m["month"], False)}: {m["impressions"]:,} impressions, average position {m["position"]}</title></rect>')
        if i % 3 == 0 or i == len(mon) - 1:
            labels.append(f'<text class="ch-x" x="{x + bw / 2:.1f}" y="{H - 12}" text-anchor="middle">{_month_label(m["month"])}</text>')
        py = T + ih * (m["position"] - 1) / 49  # position 1 at the top, 50 at the bottom
        pts.append(f"{x + bw / 2:.1f},{py:.1f}")
    grid = ""
    for k in range(5):
        v = top * k / 4
        y = T + ih - ih * k / 4
        grid += f'<line class="ch-grid" x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}"/><text class="ch-y" x="{L - 8}" y="{y + 4:.1f}" text-anchor="end">{v / 1000:.0f}k</text>'
    for pos in (1, 10, 25, 50):
        y = T + ih * (pos - 1) / 49
        grid += f'<text class="ch-y2" x="{W - R + 8}" y="{y + 4:.1f}">{pos}</text>'
    line = f'<polyline class="ch-line" points="{" ".join(pts)}"/>' + "".join(f'<circle class="ch-dot" cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="3"/>' for p in pts)
    rows = "".join(f"<tr><td>{_month_label(m['month'], False)}</td><td>{m['impressions']:,}</td><td>{m['position']}</td></tr>" for m in mon)
    return f"""<figure class="case-chart">
<svg viewBox="0 0 {W} {H}" role="img" aria-label="aioseo.fr: monthly Google impressions (bars) and average position (line), {_month_label(mon[0]['month'], False)} to {_month_label(mon[-1]['month'], False)}">{grid}{''.join(bars)}{line}{''.join(labels)}</svg>
<figcaption><span class="lg lg-bar"></span>Monthly impressions (left axis) <span class="lg lg-line"></span>Average position (right axis, 1 at the top). September 2026 runs to the 27th.</figcaption>
<details><summary>Show the data</summary><table><thead><tr><th>Month</th><th>Impressions</th><th>Avg. position</th></tr></thead><tbody>{rows}</tbody></table></details>
</figure>"""


GENAI_TOP_PAGES = [  # most visible pages in AI Overviews / AI Mode (public articles)
    ("Generative AI report in Google Search Console: how to analyze it", "https://aioseo.fr/en/google-search-console-generative-ai-report-how-to-analyze-it/"),
    ("Top 10 GEO tools to track your AI position (English and French versions)", "https://aioseo.fr/en/top-10-tools-geo-to-track-your-position-ia-2025/"),
    ("Comment connaître son positionnement sur Google AI Mode et AI Overviews ?", "https://aioseo.fr/comment-connaitre-son-positionnement-sur-ai-mode/"),
    ("Google AI Overviews arrives in France", "https://aioseo.fr/en/en-google-ai-overviews-arrive-en-france/"),
]


def _day_label(d):
    y, m, day = d.split("-")
    return f"{MONTHS['en'][int(m) - 1]} {int(day)}, {y}"


def aioseo_genai_html():
    g = AIO["genai"]
    full = [m for m in g["monthly"] if not m["partial"] and m["month"] != g["last_day"][:7]]
    shares = [m["share_of_site"] * 100 for m in full]
    fc = ", ".join(f"{c['country']} {c['share'] * 100:.0f}%" for c in g["top_countries"][:2])
    cards = [
        (f"{g['impressions']:,}", f"impressions in AI Overviews and AI Mode, {_day_label(g['first_day'])} to {_day_label(g['last_day'])}"),
        (f"{min(shares):.0f}–{max(shares):.0f}%", f"of all the site's Google impressions each month ({_month_label(full[0]['month'], False)} to {_month_label(full[-1]['month'], False)})"),
        (f"{g['daily_avg_last_week'] / g['daily_avg_first_week']:.1f}×", f"daily AI impressions, about {g['daily_avg_first_week']} a day in the first week to {g['daily_avg_last_week']} in the last"),
        (f"{g['pages']}", "pages shown in AI answers"),
        (f"{g['countries']}", f"countries ({fc})"),
        (f"{g['en_share'] * 100:.0f}%", "of AI impressions go to the English versions"),
    ]
    stats = "".join(f"<div><b>{v}</b><span>{e(t)}</span></div>" for v, t in cards)
    wk = g["weekly"]
    W, H, L, R, T, B = 720, 220, 56, 16, 16, 34
    iw, ih = W - L - R, H - T - B
    top = 500 * -(-max(w["impressions"] for w in wk) // 500)
    bw = iw / len(wk)
    bars = "".join(
        f'<rect class="ch-bar ch-bar-ai" x="{L + i * bw + bw * .18:.1f}" y="{T + ih - ih * w["impressions"] / top:.1f}" width="{bw * .64:.1f}" height="{ih * w["impressions"] / top:.1f}"><title>Week of {_day_label(w["week"])}: {w["impressions"]:,} impressions</title></rect>'
        for i, w in enumerate(wk))
    labels = "".join(f'<text class="ch-x" x="{L + i * bw + bw / 2:.1f}" y="{H - 10}" text-anchor="middle">{MONTHS["en"][int(w["week"][5:7]) - 1][:3]} {int(w["week"][8:])}</text>'
                     for i, w in enumerate(wk) if i % 4 == 0 or (i == len(wk) - 1 and i % 4 > 2))
    grid = "".join(f'<line class="ch-grid" x1="{L}" x2="{W - R}" y1="{T + ih - ih * k / 4:.1f}" y2="{T + ih - ih * k / 4:.1f}"/><text class="ch-y" x="{L - 8}" y="{T + ih - ih * k / 4 + 4:.1f}" text-anchor="end">{top * k / 4:,.0f}</text>' for k in range(5))
    rows = "".join(f"<tr><td>{_day_label(w['week'])}</td><td>{w['impressions']:,}</td></tr>" for w in wk)
    tops = "".join(f'<li><a href="{u}" target="_blank" rel="noopener">{e(x)}</a></li>' for x, u in GENAI_TOP_PAGES)
    return f"""<div class="case-stats">{stats}</div>
<figure class="case-chart">
<svg viewBox="0 0 {W} {H}" role="img" aria-label="aioseo.fr: weekly impressions in Google AI Overviews and AI Mode">{grid}{bars}{labels}</svg>
<figcaption><span class="lg lg-bar lg-ai"></span>Weekly impressions in AI Overviews and AI Mode (full weeks, Monday to Sunday).</figcaption>
<details><summary>Show the data</summary><table><thead><tr><th>Week of</th><th>AI impressions</th></tr></thead><tbody>{rows}</tbody></table></details>
</figure>
<p>The pages most often shown in AI answers are the practical, reference-style ones:</p>
<ul>{tops}</ul>
<p class="case-source">Source: Google Search Console, generative AI features report, {g['first_day']} to {g['last_day']}.</p>"""


def aioseo_cover():
    """Card / social image for the case study: the impressions curve on the site's green."""
    mon = [m for m in AIO["monthly"] if m["month"] != AIO["first_day"][:7]]
    W, H = 1200, 630
    maxi = max(m["impressions"] for m in mon)
    bw = 1000 / len(mon)
    bars = "".join(f'<rect x="{100 + i * bw + bw * .15:.1f}" y="{560 - 330 * m["impressions"] / maxi:.1f}" width="{bw * .7:.1f}" height="{330 * m["impressions"] / maxi:.1f}" rx="6" fill="#e3ece5" opacity="{.35 + .65 * m["impressions"] / maxi:.2f}"/>' for i, m in enumerate(mon))
    first, best = mon[0], max(mon, key=lambda m: m["impressions"])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#1f4d3a"/>
<text x="100" y="130" font-family="Georgia, serif" font-size="72" fill="#f6f3ec">aioseo.fr</text>
<text x="100" y="185" font-family="Helvetica, Arial, sans-serif" font-size="30" fill="#cfe0d5">SEO &amp; GEO case study · {best['impressions'] / first['impressions']:.0f}× monthly Google impressions</text>
{bars}</svg>"""
    write("assets/case-aioseo.svg", svg)


def aioseo_milestones():
    by = {m["month"]: m for m in AIO["monthly"]}
    g = lambda k: by.get(k, {"clicks": 0, "impressions": 0, "position": 0})  # noqa: E731
    items = [
        ("December 2025", f"First 100-click month; average position improved to {g('2025-12')['position']:.0f}, from {g('2025-11')['position']:.0f} the month before."),
        ("February 2026", f"{g('2026-02')['impressions']:,} impressions in a month, three times January."),
        ("April – June 2026", f"Average position around {g('2026-04')['position']:.0f}, from about 40 a year earlier."),
        ("June – July 2026", f"Best months for clicks ({g('2026-06')['clicks']} and {g('2026-07')['clicks']}), driven by the AI Overviews France coverage."),
        ("August – September 2026", f"Record impressions ({g('2026-08')['impressions']:,} in August) while click-through rates fell after AI Overviews launched in France: the zero-click shift the blog documents."),
    ]
    return '<ol class="milestones">' + "".join(f"<li><b>{w}</b><span>{t}</span></li>" for w, t in items) + "</ol>"


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
# Services come from _build/services.py (one page per language; English keeps the historical URLs)
SERVICES = [d["paths"]["en"] for d in SERVICE_DEFS]
SVC_BY_PATH = {d["paths"][l]: d for d in SERVICE_DEFS for l in LANGS}
for _d in SERVICE_DEFS:  # metadata used by llms.txt, the sitemap and listings
    PAGES[_d["paths"]["en"]] = {**PAGES.get(_d["paths"]["en"], {}), "path": _d["paths"]["en"], "title": _d["en"]["title"], "h1": _d["en"]["h1"],
                                "description": _d["en"]["desc"], "jsonld": [], "cover": None, "lead": ""}
CASES, _ = ordered("cases_order")
LABELS = {it["path"]: clean_text(it["label"]) for k in ("blog_order", "services_order", "cases_order", "home_blog") for it in data[k]}


# ---------------------------------------------------------------- structured data
def person_node(full=False):
    node = {"@type": "Person", "@id": PERSON_ID, "name": "Aslane Samai", "alternateName": "Samai Aslane", "url": f"{SITE}/",
            "image": OG_DEFAULT, "jobTitle": "SEO / GEO consultant", "sameAs": [LINKEDIN, MEDIUM, GITHUB, AIOSEO_PROFILE, AIOSEO_PROFILE_EN]}
    if full:
        node.update({
            "description": ("Aslane Samai is an SEO and GEO (generative engine optimization) consultant based in Paris, France. He helps businesses "
                            "get found on Google and cited in AI answers such as ChatGPT, Gemini and Google AI Overviews, through technical SEO "
                            "audits, data analysis and content. He previously worked for a year as an SEO & GEO consultant at Eskimoz, "
                            "and writes aioseo.fr, a blog about AI search in French and English."),
            "email": f"mailto:{EMAIL}", "telephone": PHONE,
            "address": {"@type": "PostalAddress", "addressLocality": "Paris", "addressRegion": "Île-de-France", "postalCode": "75000", "addressCountry": "FR"},
            "knowsAbout": KNOWS_ABOUT, "knowsLanguage": ["fr", "en"],
            "hasOccupation": {"@type": "Occupation", "name": "SEO / GEO consultant", "occupationLocation": {"@type": "City", "name": "Paris"},
                              "skills": ", ".join(strip_tags(x) for x in T["en"]["skills_seo_items"] + SKILLS["skills_tools"] + SKILLS["skills_data"][:2] + SKILLS["skills_viz"])},
            "alumniOf": [{"@type": "CollegeOrUniversity", "name": school} for school, *_ in EDUCATION],
            "hasCredential": [{"@type": "EducationalOccupationalCredential", "name": f"{t} certification", "credentialCategory": "certificate",
                               "recognizedBy": {"@type": "Organization", "name": o.split(" · ")[0], **({"url": u} if u else {})}} for t, o, u in CERTS],
            "subjectOf": {"@type": "WebSite", "name": "AIO SEO · Good GEO is good SEO!", "url": AIOSEO, "inLanguage": ["fr", "en"], "author": {"@id": PERSON_ID}},
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


SUN = '<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6 6 6M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/></svg>'
MOON = '<svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.2A8.5 8.5 0 1 1 9.8 3.5a6.8 6.8 0 0 0 10.7 10.7Z"/></svg>'


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
    <div class="header-tools">
      <nav class="nav" aria-label="Main">{links}{switch}{cta}</nav>
      <button class="theme-toggle" type="button" aria-label="{t['theme']}" title="{t['theme']}">{SUN}{MOON}</button>
      <details class="menu"><summary aria-label="{t['menu']}"><span></span></summary><nav aria-label="Mobile">{links}{switch}{cta}</nav></details>
    </div>
  </div>
</header>"""


def footer(lang):
    t = T[lang]
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="cols">
      <div class="f-about"><a class="brand" href="/{lang}/">Aslane Samai<span>.</span></a><p>{t['footer_tagline']}</p></div>
      <div><h4>{t['footer_explore']}</h4><ul><li><a href="/{lang}/services.html">{t['nav_services']}</a></li><li><a href="/{lang}/ressources.html">{t['nav_cases']}</a></li><li><a href="/{lang}/blog.html">{t['nav_blog']}</a></li><li><a href="/{lang}/#testimonials">{t['footer_testimonials']}</a></li><li>{ext(AIOSEO_BY_LANG[lang], "aioseo.fr")}</li></ul></div>
      <div><h4>{t['footer_contact']}</h4><ul><li><a href="mailto:{EMAIL}">{EMAIL}</a></li><li><a href="/{lang}/#contact">{t['footer_book']}</a></li></ul></div>
      <div><h4>{t['footer_follow']}</h4><ul><li><a href="{LINKEDIN}" rel="me noopener" target="_blank">LinkedIn</a></li><li><a href="{GITHUB}" rel="me noopener" target="_blank">GitHub</a></li><li><a href="{MEDIUM}" rel="me noopener" target="_blank">Medium</a></li></ul></div>
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
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{e(og_image)}">
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="Aslane Samai · Blog" href="{SITE}/feed.xml">
<link rel="me" href="{LINKEDIN}">
<link rel="preload" href="/assets/fonts/fraunces-normal-latin.woff2" as="font" type="font/woff2" crossorigin>{fonts}{pre}
<script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
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
            f'<h3 lang="{plang}" dir="ltr">{e(LABELS.get(path) or p["h1"])}</h3><p lang="{plang}" dir="ltr">{e(clip(p["description"], 150))}</p></div></a>')


def case_card(path, lang="en"):
    p = PAGES[path]
    t = T[lang]
    raw = p.get("card_image") or p.get("cover") or first_image(path)  # card_image: a logo for the card only, not shown on the page
    cover = img(raw, 720)
    frame = "thumb" if (raw or "").startswith("/assets/case-") else "thumb logo"  # generated covers are full-bleed, client logos sit on white
    thumb = f'<div class="{frame}"><img src="{e(cover)}" alt=""{dims(raw, 720)} loading="lazy" decoding="async"></div>' if cover else ""
    return (f'<a class="card card-media reveal" href="{url_of(path)}" hreflang="en">{thumb}<div class="body"><span class="tag">{t["case_tag"]}{badge(lang)}</span>'
            f'<h3 lang="en" dir="ltr">{e(p["h1"])}</h3><p lang="en" dir="ltr">{e(clip(p["description"], 140))}</p><span class="foot">{t["case_read"]}</span></div></a>')


def service_card(path, lang, i=None):
    t = T[lang]
    d = SVC_BY_PATH[path]
    name, text = d[lang]["card"]
    num = f'<span class="num">0{i}</span>' if i else ""
    return f'<a class="card reveal" href="{url_of(d["paths"][lang])}">{num}<h3>{name}</h3><p>{text}</p><span class="foot">{t["learn_more"]}</span></a>'


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


def period(lang, start, end):
    """'2025-09', '2026' / None -> 'Sep 2025 – 2026' in the page language (None = present)."""
    t = T[lang]
    def one(d):
        if d is None:
            return t["present"]
        y, _, m = d.partition("-")
        return f"{t['months'][int(m) - 1]} {y}" if m else y
    return f"{one(start)} – {one(end)}"


def logo_tile(logo, name, tile="light", cls="xp-logo"):
    if not logo:
        return f'<span class="{cls} {cls}-light"><span class="initials-mark" aria-hidden="true">{e(name[:5])}</span></span>'
    return f'<span class="{cls} {cls}-{tile}"><img src="/assets/logos/{logo}" alt="{e(name)} logo" loading="lazy" decoding="async"></span>'


def experience_section(lang):
    t = T[lang]
    rows = []
    for org, url, start, end, key, logo, tile in EXPERIENCE:
        role, text = t[key]
        name = ext(url, e(org)) if url else e(org)
        rows.append(f'<li class="xp reveal"><div class="xp-when"><bdi>{period(lang, start, end)}</bdi></div><div class="xp-body">{logo_tile(logo, org, tile)}<div><h3>{name}</h3><p class="xp-role">{role}</p><p>{text}</p></div></div></li>')
    edu = "".join(
        f'<li>{logo_tile(logo, school, "light", "edu-logo")}<div><b>{e(school)}</b>{f" · {e(deg)}" if deg else ""}<span><bdi>{period(lang, start, end)}</bdi> · {t[key]}</span></div></li>'
        for school, deg, start, end, key, logo in EDUCATION)
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
        items = t[key + "_items"] if items is None else items
        chips = "".join(f"<li>{x}</li>" for x in items)
        groups.append(f'<div class="skill-group reveal"><h3>{t[key]}</h3><ul class="chips">{chips}</ul></div>')
    tools = "".join(
        f'<a class="card tool reveal" href="{e(u)}" target="_blank" rel="noopener"><h3 dir="ltr">{e(name)}</h3><p>{t[key]}</p><span class="foot">{t["tools_open"]}</span></a>'
        for name, u, key in ((n, TOOL_URL_EN.get(k, u) if lang == "en" else u, k) for n, u, k in TOOLS))
    intro = t["tools_intro"].format(link=ext(AIOSEO_TOOLS_BY_LANG[lang], "aioseo.fr"))
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
    <p class="section-more">{ext(AIOSEO_TOOLS_BY_LANG[lang], t['tools_all'], 'more')} · {ext(STREAMLIT, 'Streamlit', 'more')} · {ext(GITHUB, 'GitHub', 'more')}</p>
  </div>
</section>"""


def aioseo_section(lang):
    t = T[lang]
    alang = "en" if lang == "en" else "fr"
    arts = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener" hreflang="{alang}" lang="{alang}">{e(x)}</a></li>'
                   for x, u in (AIOSEO_ARTICLES_EN if lang == "en" else AIOSEO_ARTICLES))
    note = f'<span class="lang-badge">{t["aioseo_note"]}</span>' if t["aioseo_note"] else ""
    return f"""<section class="section" id="aioseo">
  <div class="wrap">
    <div class="aioseo reveal">
      <div>
        <p class="eyebrow">{t['aioseo_eyebrow']}</p>
        <h2>{t['aioseo_h2']}</h2>
        <p>{t['aioseo_text']}</p>
        {ext(AIOSEO_BY_LANG[lang], t['aioseo_cta'] + ' →', 'btn btn-primary')}
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
    more_posts = "".join(f'<a href="{url_of(p)}" hreflang="en"><h3 lang="en" dir="ltr">{e(LABELS.get(p) or PAGES[p]["h1"])}</h3><span>{fmt_date(post_date(PAGES[p]), lang)}</span></a>' for p in BLOG[3:8])
    certs_html = "".join(f'<div class="cert reveal"><b dir="ltr">{x}</b><span>{ext(u, o) if u else o}</span></div>' for x, o, u in CERTS)
    faq_html = "".join(f'<details class="faq-item reveal"><summary><h3>{e(q)}</h3></summary><div><p>{a}</p></div></details>' for q, a in t["faq"])
    about = [t["about_p1"],
             t["about_p2"].format(eskimoz=ext("https://www.eskimoz.fr", "Eskimoz")),
             t["about_p3"].format(vfaw=ext("https://www.vfaw-ngo.org", "Voices For Animal Welfare"), aio=ext("https://developers.google.com/search/docs/appearance/ai-overviews", "Google AI Overviews")),
             t["about_p4"].format(aioseo=ext(AIOSEO_BY_LANG[lang], "aioseo.fr"))]
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
                    {"@type": "Offer", "itemOffered": {"@type": "Service", "name": d[lang]["card"][0], "url": canonical(d["paths"][lang])}} for d in SERVICE_DEFS]}},
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
    <div class="grid grid-3">{services}</div>
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
        <li>{ext(AIOSEO_BY_LANG[lang], "aioseo.fr")}</li>
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
        items, grid = [d["paths"][lang] for d in SERVICE_DEFS], f'<div class="grid grid-3">{"".join(service_card(p, lang, i) for i, p in enumerate(SERVICES, 1))}</div>'
    else:
        items, grid = CASES, f'<div class="grid grid-3">{"".join(case_card(p, lang) for p in CASES)}</div>'
    body = f"""<section class="page-head"><div class="wrap"><p class="eyebrow">{eyebrow}</p><h1>{e(h1)}</h1><p class="lead">{e(lead)}</p></div></section>
<section style="padding-bottom:0"><div class="wrap">{grid}</div></section>
{cta_band(lang)}"""
    ld = graph(person_node(), website_node(),
               {"@type": "CollectionPage", "@id": canonical(path) + "#webpage", "url": canonical(path), "name": h1, "description": description, "inLanguage": lang,
                "isPartOf": {"@id": WEBSITE_ID}, "author": {"@id": PERSON_ID},
                "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i, "url": canonical(q), "name": SVC_BY_PATH[q][lang]["h1"] if q in SVC_BY_PATH else PAGES[q]["h1"]} for i, q in enumerate(items, 1)]}},
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


def _excerpt(x):
    return f"…{x}" if x.rstrip().endswith((".", "!", "?")) else f"…{x}…"


def find_testimonial(name, excerpt):
    """(quote paragraphs, name, role, language) for a testimonial, verbatim; an excerpt is shown with ellipses."""
    f = TESTI["featured"]
    if name == f["name"]:
        return ([_excerpt(excerpt) if excerpt else f["excerpt"][0]], f["name"], f"{f['role']}, {f['company']}", "fr")
    q = next(x for x in TESTI["items"] if x["name"] == name)
    paras = [_excerpt(excerpt)] if excerpt else [clean_text(x) for x in q["quote"]]
    return (paras, q["name"], q["role"], lang_of(" ".join(q["quote"])))


def service_body(lang, d):
    """The service content (without hero), also used for llms-full.txt."""
    t, u, c = T[lang], SVC_UI[lang], d[lang]
    incl = "".join(f'<div class="card incl reveal"><span class="num">0{i}</span><h3>{x}</h3><p>{y}</p></div>' for i, (x, y) in enumerate(c["incl"], 1))
    steps = "".join(f'<li class="reveal"><span class="step-n">{i}</span><div><h3>{x}</h3><p>{y}</p></div></li>' for i, (x, y) in enumerate(u["steps"], 1))
    deliver = "".join(f"<li>{x}</li>" for x in c["deliver"])
    tools = "".join(f'<li dir="ltr">{e(x)}</li>' for x in d["tools"])
    paras, name, role, qlang = find_testimonial(*d["testimonial"])
    quote = f"""<figure class="svc-quote reveal"><blockquote lang="{qlang}" dir="ltr">{''.join(f'<p>{e(x)}</p>' for x in paras)}</blockquote><figcaption><b>{e(name)}</b> · <span>{e(role)}</span></figcaption></figure>"""
    cases = "".join(case_card(q, lang) for q in d["cases"])
    gallery = ""
    if d.get("gallery"):
        gallery = f"""<section class="section"><div class="wrap"><div class="section-head"><h2>{u['gallery_h2']}</h2></div>
<div class="gallery">{''.join(f'<figure class="reveal"><img src="{e(img(src, 900))}" alt="{e(cap[lang])}" loading="lazy" decoding="async"{dims(src, 900)}><figcaption>{cap[lang]} · Tableau</figcaption></figure>' for src, cap in d["gallery"])}</div></div></section>"""
    faq = "".join(f'<details class="faq-item reveal"><summary><h3>{e(q)}</h3></summary><div><p>{a}</p></div></details>' for q, a in c["faq"])
    return f"""<section class="section"><div class="wrap about"><div><h2>{u['why_h2']}</h2></div><div class="prose-lg">{''.join(f'<p>{x}</p>' for x in c['why'])}</div></div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>{u['incl_h2']}</h2></div><div class="grid grid-3">{incl}</div></div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>{u['steps_h2']}</h2></div><ol class="steps">{steps}</ol></div></section>
<section class="section"><div class="wrap svc-cols">
  <div><h2>{u['deliver_h2']}</h2><ul class="checklist">{deliver}</ul></div>
  <div><h2>{u['tools_h2']}</h2><ul class="chips">{tools}</ul></div>
</div></section>
{gallery}
<section class="section"><div class="wrap"><div class="section-head"><h2>{u['proof_h2']}</h2></div>{quote}<div class="grid grid-3" style="margin-top:20px">{cases}</div></div></section>
<section class="section"><div class="wrap faq"><div><h2>{u['faq_h2']}</h2></div><div class="faq-list">{faq}</div></div></section>"""


def build_service(lang, d):
    t, u, c = T[lang], SVC_UI[lang], d[lang]
    path = d["paths"][lang]
    alternates = {l: url_of(d["paths"][l]) for l in LANGS} | {"x-default": url_of(d["paths"]["en"])}
    crumbs = (f'<nav class="crumbs" aria-label="Breadcrumb"><a href="/{lang}/">{t["home_crumb"]}</a><span aria-hidden="true">/</span>'
              f'<a href="/{lang}/services.html">{t["nav_services"]}</a></nav>')
    facts = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in ((u["for"], c["for"]), (u["deliverable"], c["deliverable"]), (u["languages"], u["lang_value"])))
    others = "".join(service_card(o["paths"]["en"], lang) for o in SERVICE_DEFS if o is not d)
    body = f"""<section class="svc-hero"><div class="wrap">
  {crumbs}
  <p class="eyebrow">{u['eyebrow']}</p>
  <h1>{e(c['h1'])}</h1>
  <p class="lead">{c['lead']}</p>
  <div class="actions"><a class="btn btn-primary" href="/{lang}/#contact">{t['hero_cta']}</a><a class="btn btn-ghost" href="/{lang}/ressources.html">{u['cta2']}</a></div>
  <dl class="svc-facts">{facts}</dl>
</div></section>
{service_body(lang, d)}
{cta_band(lang)}
<section class="related"><div class="wrap"><div class="section-head"><h2>{u['others_h2']}</h2></div><div class="grid grid-2">{others}</div></div></section>"""
    url = canonical(path)
    ld = graph(person_node(), website_node(),
               {"@type": "Service", "@id": url + "#service", "url": url, "name": c["h1"], "description": c["desc"], "serviceType": d["service_type"],
                "provider": {"@id": PERSON_ID}, "areaServed": ["FR", "Worldwide"], "availableLanguage": ["fr", "en"], "inLanguage": lang},
               {"@type": "FAQPage", "@id": url + "#faq", "inLanguage": lang,
                "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}} for q, a in c["faq"]]},
               breadcrumbs([(t["home_crumb"], f"/{lang}/"), (t["nav_services"], f"/{lang}/services.html"), (c["h1"], url_of(path))]))
    write(path, layout(path, title=title_with_brand(c["title"]), description=c["desc"], body=body, lang=lang, active="services", jsonld=[ld], alternates=alternates))


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
    write("index.html", layout("index.html", title="Aslane Samai · SEO & GEO Consultant · EN / FR / AR", description=T["en"]["home_desc"], body=body, lang="en", jsonld=[ld],
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
    for d in SERVICE_DEFS:
        alts = {l: url_of(d["paths"][l]) for l in LANGS} | {"x-default": url_of(d["paths"]["en"])}
        urls += "".join(entry(d["paths"][l], "0.9", alts) for l in LANGS)
    urls += "".join(entry(p, "0.8") for p in CASES + BLOG)
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
    xp = "\n".join(f"  - {org} ({period('en', start, end)}): {strip_tags(t[key][0])}. {strip_tags(t[key][1])}" for org, _, start, end, key, _, _ in EXPERIENCE)
    edu = "\n".join(f"  - {school}{f', {deg}' if deg else ''} ({period('en', start, end)}): {t[key]}" for school, deg, start, end, key, _ in EDUCATION)
    tools = "\n".join(f"  - [{name}]({u}): {t[key]}" for name, u, key in TOOLS)
    skills = "; ".join(strip_tags(", ".join(T["en"][k + "_items"] if v is None else v)) for k, v in SKILLS.items())
    return f"""Key facts:

- Name: Aslane Samai (also written Samai Aslane)
- Role: SEO / GEO consultant, based in Paris, France; works in French and English
- Experience:
{xp}
- Education:
{edu}
- Skills and tools: {skills}
- Certifications: Google Data Analytics (Google / Coursera), SQL (CoRise), Technical SEO (Blue Array), SEO Manager (Blue Array)
- Tools built (free to use):
{tools}
- Also writes: [aioseo.fr]({AIOSEO}) (English: {AIOSEO_BY_LANG["en"]}), "AIO SEO · Good GEO is good SEO!", a blog about GEO and AI search in French and English (Google AI Overviews, AI Mode, query fan-out, GEO tools)
- Contact: {EMAIL} · book a 30-minute call to start an SEO / GEO audit: {CALENDLY}
- Profiles: LinkedIn {LINKEDIN} · GitHub {GITHUB} · Medium {MEDIUM}"""


INTRO = ("> Aslane Samai is an SEO and GEO (generative engine optimization) consultant based in Paris, France. He helps businesses get found on "
         "Google and cited in AI answers (ChatGPT, Gemini, Google AI Overviews) through technical SEO audits, data analysis and content. "
         "He writes aioseo.fr, a blog about AI search in French and English.")


def build_llms():
    def line(q):
        return f"- [{clean_text(PAGES[q]['h1'])}]({canonical(q)}): {clean_text(PAGES[q]['description'])}"
    lines = [f"# {SITE_NAME}", "", INTRO, "", facts_md(), "",
             "## Site versions", "",
             *[f"- [{META[l]['name']}]({canonical(f'{l}/index.html')}): {T[l]['home_title']}" for l in LANGS], "",
             "## Services", "", *[line(q) for q in SERVICES], "",
             "## Case studies", "", *[line(q) for q in CASES], "",
             "## Blog", "", *[line(q) for q in BLOG], "",
             "## AIO SEO (aioseo.fr, English and French)", "", *[f"- [{x}]({u})" for x, u in AIOSEO_ARTICLES_EN], *[f"- [{x}]({u}) (French)" for x, u in AIOSEO_ARTICLES], "",
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
        body = service_body("en", SVC_BY_PATH[q]) if q in SVC_BY_PATH else content(q)
        full.append(f"---\n\n## {clean_text(p['h1'])}\n\n{meta}\n\n{to_markdown(body, SITE)}")
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
        if path not in SVC_BY_PATH:
            build_page(path)
    for d in SERVICE_DEFS:
        for lang in LANGS:
            build_service(lang, d)
    build_404()
    build_redirects()
    build_sitemap()
    build_llms()
    build_feed()
    if AIO:
        aioseo_cover()
    print(f"built {len(LANGS) * 4 + len(PAGES) - len(SERVICES) + len(SERVICES) * len(LANGS) + 2} pages ({', '.join(LANGS)}) · blog {len(BLOG)} · services {len(SERVICES)} · cases {len(CASES)} · redirects {len(REDIRECTS)}")
