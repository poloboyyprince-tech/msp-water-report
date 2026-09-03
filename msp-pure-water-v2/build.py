#!/usr/bin/env python3
"""MSP Pure Water — static site generator.

Components are Python functions (Header, Hero, SystemCard, GHLCalendar, ...).
Content lives in src/data/*.json, business facts in src/config/site.json and
every GoHighLevel setting in src/config/ghl.config.js. Run:  python3 build.py
Output: dist/ (clean URLs: dist/<slug>/index.html).
"""
import json, os, re, shutil, html, datetime, argparse
ROOT = os.path.dirname(os.path.abspath(__file__))
ARGS = argparse.ArgumentParser(description="Build the MSP Pure Water site")
ARGS.add_argument("--out", default="dist", help="output directory (default dist)")
ARGS.add_argument("--base", default="", help="URL prefix when hosting under a subpath, e.g. /preview")
ARGS.add_argument("--staging", action="store_true", help="noindex every page and disallow crawling (staging copies)")
OPT = ARGS.parse_args()
BASEPATH = OPT.base.rstrip("/")
SRC, DIST = os.path.join(ROOT, "src"), os.path.join(ROOT, OPT.out)
def J(p): return json.load(open(os.path.join(SRC, p), encoding="utf-8"))
SITE = J("config/site.json"); SYS = J("data/systems.json"); PROBLEMS = J("data/problems.json")
FAQ = J("data/faq.json"); CITIES = J("data/cities.json"); REVIEWS = J("data/reviews.json"); REGIONS = J("data/regions.json"); COMPONENTS = J("data/components.json")
FOOTER_CITIES = CITIES[:20]
LEGAL = J("data/legal-source.json") if os.path.exists(os.path.join(SRC, "data/legal-source.json")) else {}
SYSTEMS = {s["id"]: s for s in SYS["systems"]}
BY_CAT = {c["id"]: [s for s in SYS["systems"] if s["category"] == c["id"]] for c in SYS["categories"]}
PHONE, TEL = SITE["phone_display"], SITE["phone_tel"]
BASE = SITE["domain"]
HAS_VIDEO = os.path.exists(os.path.join(SRC, "video/hero.mp4"))
HAS_POSTER = os.path.exists(os.path.join(SRC, "img/hero-poster.jpg"))
def has_img(n): return os.path.exists(os.path.join(SRC, "img", n))
def e(s): return html.escape(str(s), quote=True)
def money(n): return "${:,}".format(n)
def sys_href(s):
    return "/systems/%s/" % s["id"]
def cat_href(s):
    return {"city": "/city-water-filtration/", "well": "/well-water-filtration/", "ro": "/reverse-osmosis/", "addon": "/well-water-filtration/"}[s["category"]] + "#" + s["id"]

# ---------------------------------------------------------------- icons
ICON = {
 "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.9 2z"/></svg>',
 "cal": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
 "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>',
 "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
 "down": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M6 13l6 6 6-6"/></svg>',
 "chev": '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>',
 "plus": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
 "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
 "x": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>',
 "star": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/></svg>',
 "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M12 2 4 5.5v6C4 16.5 7.4 20.6 12 22c4.6-1.4 8-5.5 8-10.5v-6z"/><path d="m9 12 2 2 4-4"/></svg>',
 "tag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L2 12V2h10l8.6 8.6a2 2 0 0 1 0 2.8z"/><circle cx="7" cy="7" r="1.5"/></svg>',
 "wrench": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.7 6.3a4 4 0 0 0 5 5L22 9l-2-2-2 2-2-2 2-2-2-2-2.3 2.3zM3 21l8.5-8.5"/></svg>',
 "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>',
 "drop": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.5S5 10 5 14.5a7 7 0 0 0 14 0C19 10 12 2.5 12 2.5z"/></svg>',
 "layers": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5M3 17.5l9 5 9-5"/></svg>',
 "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
 "eye": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
 "well": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 21h16M6 21V9l6-5 6 5v12M9 21v-6h6v6"/></svg>',
 "city": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18M5 21V7l5-3v17M10 21V11l5-3v13M15 21V9l4 2v10"/></svg>',
 "glass": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h12l-1.5 17a2 2 0 0 1-2 1.8h-5a2 2 0 0 1-2-1.8zM7 10h10"/></svg>',
 "snow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M12 2v20M2 12h20M5 5l14 14M19 5 5 19"/></svg>',
}

# ---------------------------------------------------------------- shell
NAV = [
 ("Systems", None, [("City Water Systems", "/city-water-filtration/"), ("Well Water Systems", "/well-water-filtration/"), ("Reverse Osmosis", "/reverse-osmosis/"), ("Compare Systems", "/compare-systems/")]),
 ("Pricing", "/pricing/", None),
 ("Water Problems", None, [(p["nav"], "/water-problems/%s/" % p["id"]) for p in PROBLEMS if p.get("page")]),
 ("Service Areas", "/service-areas/", None),
 ("Why MSP", "/about/", None),
 ("FAQ", "/faq/", None),
]
def brand(cls=""):
    return ('<a class="brand %s" href="/" aria-label="MSP Pure Water home"><img src="/assets/img/logo.png" width="161" height="214" alt="MSP Pure Water shield logo">'
            '<span class="brand-word">MSP Pure Water<small>Twin Cities &middot; Greater Minnesota</small></span></a>') % cls
def announce():
    return ('<div class="announce" role="region" aria-label="Announcement"><a href="/best-price-guarantee/" data-bpg><strong>Best Price Guarantee</strong> &nbsp;&mdash;&nbsp; comparable system, lower installed quote? We\'ll beat it.</a>'
            '<button class="x" aria-label="Dismiss announcement">&times;</button></div>')
def header(over_hero=False):
    items = []
    for label, href, sub in NAV:
        if sub:
            items.append('<li><button type="button" aria-haspopup="true" aria-expanded="false">%s %s</button><div class="sub" data-open="false"><div class="sub-inner">%s</div></div></li>' % (
                label, ICON["chev"], "".join('<a href="%s">%s</a>' % (h, e(l)) for l, h in sub)))
        else:
            items.append('<li><a href="%s">%s</a></li>' % (href, label))
    m = []
    for label, href, sub in NAV:
        if sub:
            m.append('<div class="mgroup">%s</div><div class="sublist">%s</div>' % (label, "".join('<a href="%s">%s</a>' % (h, e(l)) for l, h in sub)))
        else:
            m.append('<a href="%s">%s</a>' % (href, label))
    return ('<a class="skip" href="#main">Skip to content</a>' + announce() +
      '<header class="header %s"><div class="container header-inner">%s<ul class="nav" aria-label="Primary">%s</ul>'
      '<div class="header-cta"><a class="header-phone" href="tel:%s">%s %s</a><a class="btn btn-gold" href="/schedule/">Schedule Online</a>'
      '<button class="burger" aria-label="Open menu" aria-expanded="false" aria-controls="mnav">%s</button></div></div></header>'
      '<nav class="mnav" id="mnav" data-open="false" aria-label="Mobile"><div class="mnav-top">%s<button class="x" aria-label="Close menu">%s</button></div>%s'
      '<div class="mnav-actions"><a class="btn btn-gold btn-lg" href="/schedule/">Schedule Online</a><a class="btn btn-outline btn-lg" href="/find-my-system/">Find My System</a><a class="btn btn-outline btn-lg" href="tel:%s">%s Call %s</a></div></nav>'
      '<div class="mbar" aria-label="Quick actions"><a class="call" href="tel:%s">%s Call</a><a class="sched" href="/schedule/">%s Schedule</a></div>') % (
        "over-hero" if over_hero else "", brand(), "".join(items), TEL, ICON["phone"], PHONE, ICON["menu"], brand(), ICON["x"], "".join(m), TEL, ICON["phone"], PHONE, TEL, ICON["phone"], ICON["cal"])
def footer():
    cities = " ".join('<a href="/service-areas/%s/">Water Filtration %s</a>' % (c["slug"], e(c["city"])) for c in FOOTER_CITIES) + ' <a href="/service-areas/">+ %d more cities</a>' % (len(CITIES) - len(FOOTER_CITIES))
    return ('<footer class="footer"><div class="container"><div class="footer-grid"><div>%s<p style="margin-top:1rem;max-width:36ch">Whole-home filtration, softening, well-water treatment and reverse osmosis for the Twin Cities and Greater Minnesota.</p>'
      '<a class="fphone" href="tel:%s" style="text-decoration:none;display:block">%s</a><p>%s &middot; Call or text<br>%s</p><p><a href="mailto:%s">%s</a></p></div>'
      '<div><h4>Systems</h4><ul><li><a href="/city-water-filtration/">City Water Systems</a></li><li><a href="/well-water-filtration/">Well Water Systems</a></li><li><a href="/reverse-osmosis/">Reverse Osmosis</a></li><li><a href="/compare-systems/">Compare Systems</a></li><li><a href="/pricing/">Pricing</a></li></ul></div>'
      '<div><h4>Learn</h4><ul>%s<li><a href="/faq/">FAQ</a></li></ul></div>'
      '<div><h4>Company</h4><ul><li><a href="/about/">About &amp; Why MSP</a></li><li><a href="/best-price-guarantee/">Best Price Guarantee</a></li><li><a href="/service-areas/">Service Areas</a></li><li><a href="/schedule/">Schedule Online</a></li><li><a href="/find-my-system/">Find My System</a></li><li><a href="/contact/">Contact</a></li></ul></div></div>'
      '<div class="footer-cities">Serving %s</div>'
      '<div class="footer-bottom"><span>&copy; <span data-year></span> MSP Pure Water. All rights reserved. Serving Minneapolis, St. Paul &amp; Greater Minnesota.</span><ul><li><a href="/privacy/">Privacy</a></li><li><a href="/terms/">Terms</a></li><li><a href="/accessibility/">Accessibility</a></li></ul></div></div></footer>') % (
        brand(), TEL, PHONE, SITE["hours"], SITE["service_area"], SITE["email"], SITE["email"],
        "".join('<li><a href="/water-problems/%s/">%s</a></li>' % (p["id"], e(p["nav"])) for p in PROBLEMS if p.get("page")), cities)

def local_business():
    return {"@context": "https://schema.org", "@type": "LocalBusiness", "@id": BASE + "/#business", "name": SITE["name"], "url": BASE + "/", "telephone": TEL, "email": SITE["email"],
            "image": BASE + SITE["og_image"], "logo": BASE + "/assets/img/logo.png", "description": SITE["description"], "priceRange": "$799 - $5,999",
            "areaServed": [{"@type": "City", "name": c["city"] + ", MN"} for c in CITIES] + [{"@type": "State", "name": "Minnesota"}],
            "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], "opens": "00:00", "closes": "23:59"}],
            "sameAs": [SITE["google_reviews_url"]]}

def page(slug, title, desc, body, over_hero=False, schema=None, noindex=False, canonical=None):
    path = "/" if slug == "" else "/%s/" % slug
    can = canonical or (BASE + path)
    ld = [local_business()] + (schema or [])
    jsonld = "".join('<script type="application/ld+json">%s</script>' % json.dumps(s, ensure_ascii=False) for s in ld)
    head = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
      '<title>%s</title><meta name="description" content="%s"><link rel="canonical" href="%s">%s'
      '<meta property="og:type" content="website"><meta property="og:site_name" content="MSP Pure Water"><meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s"><meta property="og:image" content="%s">'
      '<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0B1426">'
      '<link rel="icon" href="/assets/img/favicon.png" type="image/png"><link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">'
      '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
      '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=DM+Sans:wght@400;500;600;700&display=swap">'
      '<link rel="stylesheet" href="/assets/css/site.css">%s'
      '<script src="/assets/js/ghl.config.js"></script><script defer src="/assets/js/tracking.js"></script><script defer src="/assets/js/ghl-adapter.js"></script><script defer src="/assets/js/find-my-system.js"></script><script defer src="/assets/js/ui.js"></script>'
      '</head><body>') % (e(title), e(desc), can, '<meta name="robots" content="noindex,nofollow">' if (noindex or OPT.staging) else "", e(title), e(desc), can, BASE + SITE["og_image"],
      ('<link rel="preload" as="image" href="/assets/img/hero-poster.jpg">' if (slug == "" and HAS_POSTER) else "") + jsonld)
    out = head + header(over_hero) + '<main id="main">' + headings_title_case(body) + "</main>" + footer() + "</body></html>"
    return rebase(out)

SMALL = {"a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "by", "for", "with", "per", "vs", "nor", "but", "into", "from", "as"}
KEEP = {"MSP", "RO", "GPM", "GPD", "UV", "TDS", "HW800", "AlkaPro", "FAQ", "MN", "St.", "AIO", "ProValve", "USA", "NSF"}
def title_case(text):
    words = text.split(" "); out = []
    for i, w in enumerate(words):
        if not w: out.append(w); continue
        core = w.strip(".,:;!?()\"'“”‘’")
        if w.startswith("&") or core in KEEP or (core.isupper() and len(core) > 1) or any(ch.isdigit() for ch in core): out.append(w); continue
        lw = w.lower()
        prev_end = i > 0 and words[i - 1] and words[i - 1][-1] in ".:!?"
        if i > 0 and lw.strip(".,:;!?") in SMALL and not prev_end: out.append(lw); continue
        # capitalize first alpha char, keep the rest (handles “quotes”, hyphens: capitalize after hyphen too)
        chars = list(w); done = False
        for j, ch in enumerate(chars):
            if ch.isalpha() and not done: chars[j] = ch.upper(); done = True
            elif ch == "-" and j + 1 < len(chars) and chars[j + 1].isalpha(): chars[j + 1] = chars[j + 1].upper()
        out.append("".join(chars))
    return " ".join(out)
def headings_title_case(html_):
    def fix(m):
        inner = re.sub(r'>([^<]+)<', lambda n: ">" + title_case(n.group(1)) + "<", ">" + m.group(2) + "<")[1:-1]
        return m.group(1) + inner + m.group(3)
    return re.sub(r'(<h[1-3]\b[^>]*>)(.*?)(</h[1-3]>)', fix, html_, flags=re.S)

def rebase(s):
    """Prefix root-relative URLs when the site is hosted under a subpath (staging)."""
    if not BASEPATH: return s
    s = re.sub(r'((?:href|src|poster|action)=")/(?!/)', r'\1' + BASEPATH + '/', s)
    s = re.sub(r'(srcset=")([^"]+)', lambda m: m.group(1) + re.sub(r'(^|,\s*)/(?!/)', lambda n: n.group(1) + BASEPATH + '/', m.group(2)), s)
    s = s.replace('<meta name="robots" content="noindex,nofollow">', '')
    return s.replace('<meta charset="utf-8">', '<meta charset="utf-8"><meta name="robots" content="noindex,nofollow">')

# ---------------------------------------------------------------- components
def rating_badge(dark=True):
    return ('<a class="rating" href="%s" target="_blank" rel="noopener" style="text-decoration:none"><span class="g">G</span><span class="stars" aria-hidden="true">★★★★★</span><span>%s</span></a>') % (SITE["google_reviews_url"], SITE["rating_line"])

def phero(kicker, h1, lead, crumbs=None, subnav=None, extra=""):
    c = '<div class="crumbs"><a href="/">Home</a> / %s</div>' % crumbs if crumbs else ""
    sn = ('<div class="subnav">' + "".join('<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if cur else "", l) for l, h, cur in subnav) + "</div>") if subnav else ""
    if extra: sn += '<div class="pill-row">%s</div>' % extra; extra = ""
    media = ('<div class="phero-media" aria-hidden="true"><video autoplay muted loop playsinline preload="metadata" poster="/assets/img/hero-poster.jpg" tabindex="-1"><source src="/assets/video/hero-mobile.mp4" type="video/mp4"></video></div>' if HAS_VIDEO else '<div class="phero-media" aria-hidden="true"><img src="/assets/img/hero-poster.jpg" alt=""></div>')
    return '<section class="phero">%s<div class="container"><div class="grid-hero"><div>%s<p class="kicker">%s</p><h1>%s</h1><p class="lead">%s</p>%s</div><div>%s</div></div></div></section>' % (media, c, kicker, h1, lead, sn, extra)

def hero():
    video = ""
    if HAS_VIDEO:
        mobile = '<source src="/assets/video/hero-mobile.mp4" type="video/mp4" media="(max-width: 768px)">' if os.path.exists(os.path.join(SRC, "video/hero-mobile.mp4")) else ""
        webm = '<source src="/assets/video/hero.webm" type="video/webm">' if os.path.exists(os.path.join(SRC, "video/hero.webm")) else ""
        video = ('<video autoplay muted loop playsinline preload="metadata" poster="/assets/img/hero-poster.jpg" aria-hidden="true" tabindex="-1">%s%s<source src="/assets/video/hero.mp4" type="video/mp4"></video>' % (mobile, webm))
    else:
        video = '<img src="/assets/img/%s" alt="" fetchpriority="high">' % ("hero-poster.jpg" if HAS_POSTER else "system-whole-home.v5.webp")
    return ('<section class="hero" id="top"><div class="hero-media" data-parallax="30">%s</div>%s'
      '<div class="container hero-inner"><div class="hero-promo reveal"><b>Included</b> Reverse osmosis drinking-water system with every whole-home system</div>'
      '<h1 class="reveal">Better water.<br><em>Throughout your entire home.</em></h1>'
      '<p class="lead reveal reveal-d1">Whole-home filtration, softening, well-water treatment and reverse osmosis for the Twin Cities. Published prices, professional installation, and a phone consultation you can book online tonight.</p>'
      '<div class="hero-actions reveal reveal-d2"><a class="btn btn-gold btn-lg" href="/find-my-system/">Find My System %s</a><a class="btn btn-outline btn-lg" href="/schedule/">Schedule Online</a></div>'
      '<div class="hero-meta reveal reveal-d3">%s<a href="tel:%s">%s %s</a><span>Open 24 hours</span></div></div>'
      '<div class="hero-side reveal reveal-d2"><div class="stat"><b>%s</b><span>Whole-home systems from</span></div><div class="stat"><b>28 GPM</b><span>Whole-home flow rate</span></div><div class="stat"><b>48,000</b><span>Grain softening capacity</span></div></div></section>'
      '<div class="trust"><div class="container trust-inner"><span>%s Five-star rated on Google</span><span>%s Free phone consultation</span><span>%s Best Price Guarantee</span><span>%s Professional installation</span><span>%s Twin Cities &amp; Greater Minnesota</span></div></div>') % (
        video, '<button class="video-toggle" type="button">Pause video</button>' if HAS_VIDEO else "", ICON["arrow"], rating_badge(), TEL, ICON["phone"], PHONE, money(2999),
        ICON["star"], ICON["phone"], ICON["tag"], ICON["wrench"], ICON["pin"])

def source_cards():
    cards = [
      ("01", "city", "City Water", ["Hardness", "Chlorine / chloramine", "Scale", "Taste & odor"], "/city-water-filtration/", {"water_source": "City Water"}, "Explore city water systems"),
      ("02", "well", "Well Water", ["Hardness", "Iron", "Sulfur odor", "Staining", "Sediment"], "/well-water-filtration/", {"water_source": "Well Water", "system_interest": "Well Water Treatment"}, "Explore well water systems"),
      ("03", "glass", "Drinking Water", ["Taste", "Dissolved solids", "Bottled-water replacement", "Reverse osmosis"], "/reverse-osmosis/", {"system_interest": "Reverse Osmosis"}, "Explore drinking water systems"),
    ]
    out = ""
    for n, ic, t, items, href, intake, go in cards:
        out += ('<a class="source reveal" href="%s" data-intake=\'%s\' data-intake-via="water_source_selector"><span class="source-icon">%s</span><span class="num">%s</span><h3>%s</h3><ul>%s</ul><span class="go">%s %s</span></a>') % (
            href, json.dumps(intake), ICON[ic], n, t, "".join("<li>%s</li>" % i for i in items), go, ICON["arrow"])
    return ('<section class="section" id="start"><div class="container"><div class="grid grid-2" style="align-items:end;margin-bottom:2.5rem"><div><p class="kicker">Step one</p><h2>Start with your water.</h2></div><p class="lead">Every home is different. Pick your water source to see the systems built for it, with prices, specs and online scheduling on every page. Your choice carries into Find My System so you never repeat yourself.</p></div>'
            '<div class="source-cards">%s</div><p class="center" style="margin-top:2rem">Want the numbers first? <a class="link" href="/pricing/">See transparent pricing for every system.</a></p></div></section>') % out

def explorer():
    data = {}
    for p in PROBLEMS:
        data[p["id"]] = {"label": p["label"], "tag": p["tag"], "cause": p["cause"], "approach": p["approach"], "interest": p["interest"],
                         "href": "/water-problems/%s/" % p["id"] if p.get("page") else "",
                         "systems": [{"name": SYSTEMS[s]["short"], "price": "{:,}".format(SYSTEMS[s]["price"]), "href": sys_href(SYSTEMS[s])} for s in p["systems"]]}
    chips = "".join('<li><button type="button" class="chip" role="tab" data-id="%s" aria-selected="false">%s</button></li>' % (p["id"], e(p["label"])) for p in PROBLEMS)
    return ('<section class="section cream" id="problems"><div class="container"><p class="kicker">What\'s wrong with my water?</p><div class="grid grid-2" style="align-items:end;margin-bottom:2rem"><h2>Pick the symptom. We\'ll show the cause and the fix.</h2><p class="lead">Water problems have specific causes and specific treatments. Nothing here is a one-size-fits-all box.</p></div>'
            '<div class="explorer" data-explorer><ul class="chips" role="tablist" aria-label="Water problems">%s</ul><div class="explorer-panel" role="tabpanel" aria-live="polite"></div></div>'
            '<script type="application/json" id="explorer-data">%s</script></div></section>') % (chips, json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))

def system_card(s, compact=False):
    img = s["image"]; img640 = img.replace(".webp", "-640.webp")
    badge = '<span class="badge">%s</span>' % e(s["badge"]) if s.get("badge") else ""
    pre = '<span class="pre">%s</span>' % s["price_prefix"] if s.get("price_prefix") else ""
    incl = "".join("<li>%s<span>%s</span></li>" % (ICON["check"], e(i)) for i in s["included"][:3])
    promo = ('<div class="promo-line">%s RO drinking system included</div>' % ICON["drop"] if s["category"] in ("city", "well") else "") + ('<div class="promo-line nsf-line">%s Every component NSF certified</div>' % ICON["shield"] if s.get("nsf") else "")
    return ('<article class="syscard reveal" id="%s"><div class="syscard-media"><img src="/assets/img/%s" srcset="/assets/img/%s 640w, /assets/img/%s 1024w" sizes="(max-width:640px) 90vw, 400px" width="1024" height="1280" loading="lazy" alt="%s"></div>'
            '<div class="syscard-body">%s<h3>%s</h3><div class="price">%s%s<small>installed</small></div>%s<p class="for">%s</p><ul class="tags">%s</ul><ul class="incl">%s</ul>'
            '<div class="syscard-actions"><a class="btn btn-gold" href="/schedule/?system=%s" data-intake=\'%s\' data-intake-via="system_card">Schedule</a><a class="btn btn-outline on-light" href="%s">%s</a></div></div></article>') % (
        s["id"] + ("-card" if compact else ""), img, img640, img, e(s["image_alt"]), badge, e(s["name"]), pre, money(s["price"]), promo, e(s["for"]),
        "".join("<li>%s</li>" % e(p) for p in s["problems"]), incl, s["id"], json.dumps({"system_interest": {"city": "Whole Home Filtration", "well": "Well Water Treatment", "ro": "Reverse Osmosis", "addon": "Well Water Treatment"}[s["category"]], "water_source": {"city": "City Water", "well": "Well Water"}.get(s["category"], "")}),
        sys_href(s), "Configure")

def systems_home():
    blocks = ""
    for c in SYS["categories"]:
        if c["id"] == "addon": continue
        blocks += '<div style="margin-bottom:3rem"><div class="grid grid-2" style="align-items:end;margin-bottom:1.25rem"><h3 style="margin:0">%s</h3><p class="muted" style="margin:0">%s</p></div><div class="grid grid-3">%s</div></div>' % (
            e(c["label"]), e(c["intro"]), "".join(system_card(s, compact=True) for s in BY_CAT[c["id"]]))
    addons = "".join('<div class="pricing-row"><div><b>%s</b><small>%s</small></div><div class="price" style="font-size:1.6rem">+%s</div><a class="btn btn-sm btn-outline on-light" href="/well-water-filtration/#%s">Details</a></div>' % (e(s["name"]), e(s["for"]), money(s["price"]), s["id"]) for s in BY_CAT["addon"])
    return ('<section class="section" id="pricing" data-view-event="pricing_viewed"><div class="container"><div class="grid grid-2" style="align-items:end;margin-bottom:2.5rem"><div><p class="kicker">Systems &amp; transparent pricing</p><h2>Know what you\'re buying before anyone enters your home.</h2></div><p class="lead">Every price is published. No quote games, no three-hour presentation. %s</p></div>%s'
            '<div style="max-width:820px"><h3>Optional add-ons</h3>%s</div><p style="margin-top:1.5rem" class="muted">%s %s</p><div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1.5rem"><a class="btn btn-navy" href="/pricing/">Full pricing</a><a class="btn btn-outline on-light" href="/compare-systems/">Compare systems side by side</a></div></div></section>') % (
        e(SYS["promo"]["ro_included"]), blocks, addons, e(SYS["promo"]["financing"]), e(SYS["promo"]["travel"]))

def best_price(section=True):
    inner = ('<div class="bpg-grid"><div><p class="kicker">Best Price Guarantee</p><h2>Find a Lower Quote on a Comparable System. We\'ll Beat It.</h2><p class="lead">%s</p><div style="display:flex;gap:.9rem;flex-wrap:wrap;margin-top:1.5rem"><a class="btn btn-gold btn-lg" href="/find-my-system/?inquiry=best-price" data-bpg data-intake=\'{"inquiry_type":"Best Price Guarantee Inquiry"}\' data-intake-via="bpg">Claim Your Best Price</a><a class="btn btn-outline btn-lg" href="/pricing/">See our prices</a></div></div>'
             '<div class="bpg-terms"><p><b>How it works</b></p><p>Send us the competing written quote. We compare equipment, capacity and installation scope. If it\'s comparable and lower, we beat it, and you get priority booking on the schedule.</p></div></div>') % e(SITE["best_price_guarantee"])
    return '<section class="section dark bpg" id="best-price"><span class="big" aria-hidden="true">BEAT IT</span><div class="container">%s</div></section>' % inner if section else inner

def approach():
    rows = [("Hard Water", "Scale, spots, buildup on fixtures and appliances.", "10% Crosslinked Resin", "Ion exchange removes the calcium and magnesium responsible for hardness."),
            ("Chlorine / Chloramine", "Taste, odor and municipal disinfectant.", "Jacobi Catalytic Carbon Tank", "Selected specifically because it treats chloramine as well as free chlorine."),
            ("Well Iron & Sulfur", "Staining, metallic taste, rotten-egg odor.", "Oxidation + Filtration", "Air oxidation for iron and manganese; hydrogen peroxide injection for sulfur odor and heavy iron."),
            ("Drinking Water", "Dissolved solids and unwanted taste.", "Reverse Osmosis", "A dedicated under-sink membrane system for the water you drink and cook with.")]
    cells = "".join('<div class="reveal"><span class="step">Problem</span><div class="prob">%s</div><p>%s</p><span class="arrow">%s</span><span class="step">Correct treatment</span><div class="sol">%s</div><p>%s</p></div>' % (a, b, ICON["down"], c, d) for a, b, c, d in rows)
    return '<section class="section"><div class="container"><p class="kicker">The MSP approach</p><div class="grid grid-2" style="align-items:end;margin-bottom:2rem"><h2>Problem. Cause. Correct treatment.</h2><p class="lead">We match equipment to the water problem you actually have. Not a generic box for every house on the street.</p></div><div class="approach">%s</div></div></section>' % cells

def before_after():
    items = [("scale", "Scale-covered faucet", "Clean fixture", "Hard Water & Scale", "Softened water stops new scale from forming. Fixtures stay clean between cleanings."),
             ("dishes", "Spotty glassware", "Clear glassware", "Spots on Dishes", "No hardness minerals left behind when the water dries."),
             ("iron", "Iron-stained sink", "Stain-free sink", "Iron Staining", "Oxidation and filtration remove iron before it ever reaches your fixtures."),
             ("bottles", "Bottled-water clutter", "Dedicated RO faucet", "Drinking Water", "Purified water at its own kitchen faucet. No cases to carry, no bottles to recycle.")]
    cards = ""
    for key, b, a, t, p in items:
        bi = '<img src="/assets/img/ba-%s-before.webp" alt="%s" loading="lazy">' % (key, e(b)) if has_img("ba-%s-before.webp" % key) else ""
        ai = '<img src="/assets/img/ba-%s-after.webp" alt="%s" loading="lazy">' % (key, e(a)) if has_img("ba-%s-after.webp" % key) else ""
        cards += '<div class="ba-card reveal"><div class="pair"><div class="before">%s<span>Before</span></div><div class="after">%s<span>After</span></div></div><p><b>%s</b>%s</p></div>' % (bi, ai, t, p)
    return '<section class="section cream"><div class="container"><p class="kicker">The difference you notice</p><div class="grid grid-2" style="align-items:end;margin-bottom:2rem"><h2>Real changes around the house. No lab coats required.</h2><p class="lead">We don\'t sell test-tube theatrics. These are the everyday results homeowners describe after installation.</p></div><div class="ba">%s</div></div></section>' % cards

def why():
    rows = [("tag", "Transparent pricing", "Every system price is published. You can budget before you book."), ("layers", "Water-specific systems", "City and well water get different equipment because they have different problems."),
            ("cal", "Phone consultations", "Pick a time online and we call you. In-home presentations available on request. No deposit to reserve."), ("wrench", "Professional installation", "Connected to your main line, configured for your water, walked through before we leave."),
            ("pin", "Local Minnesota service", "Based in the Twin Cities and serving Greater Minnesota. You reach the person who does the work."), ("shield", "Warranty & Best Price Guarantee", "Lifetime warranty on whole-home and RO systems, and we beat any comparable lower quote.")]
    return '<section class="section dark"><div class="container"><p class="kicker">Why MSP Pure Water</p><h2 style="max-width:20ch">The modern alternative to the in-home sales pitch.</h2><div class="why" style="margin-top:2.5rem">%s</div></div></section>' % "".join(
        '<div class="reveal"><span class="ico">%s</span><h3>%s</h3><p>%s</p></div>' % (ICON[i], t, p) for i, t, p in rows)

def process():
    steps = [("01", "Identify your water source", "City or well. If you pay a water bill, it's city water.", ""), ("02", "Find your system", "Match your symptoms to the right equipment, with prices shown.", ""),
             ("03", "Schedule a phone consultation", "Pick a time online. We call you, confirm the system and price, and set your install date.", "Instant confirmation"), ("04", "Professional installation", "We connect, configure and walk you through the system.", ""), ("05", "Enjoy better water", "Every faucet, shower and appliance runs on treated water.", "")]
    return '<section class="section"><div class="container"><p class="kicker">The process</p><h2 style="max-width:20ch">Better water without the runaround.</h2><div class="process" style="margin-top:2.5rem">%s</div></div></section>' % "".join(
        '<div class="reveal"><div class="n">%s</div><h3>%s</h3><p>%s</p>%s</div>' % (n, t, p, '<span class="ghl">%s</span>' % g if g else "") for n, t, p, g in steps)

def reviews():
    cards = "".join('<article class="review reveal"><blockquote>%s</blockquote><footer><b>%s</b> &middot; %s</footer></article>' % (e(r["quote"]), e(r["name"]), e(r["meta"])) for r in REVIEWS["testimonials"])
    return ('<section class="section cream" id="reviews"><div class="container"><p class="kicker">What homeowners say</p><div class="grid grid-2" style="align-items:end;margin-bottom:2rem"><h2>Twin Cities homeowners agree.</h2><div class="rating-card"><div class="big">%s</div><div class="stars" aria-hidden="true">★★★★★</div><small>Five stars on Google &middot; <a href="%s" target="_blank" rel="noopener" style="color:#fff">Read our reviews</a></small></div></div><div class="reviews">%s</div></div></section>') % (
        SITE["google_rating"], SITE["google_reviews_url"], cards)

def minnesota():
    items = [("snow", "Hard groundwater is the default here", "Minnesota groundwater is generally hard. That's why softening is the foundation of most Twin Cities systems."),
             ("city", "City water is disinfected", "Municipal utilities in the Twin Cities use chlorine or chloramine. Catalytic carbon is chosen because it treats both."),
             ("well", "Wells bring iron and manganese", "Both occur naturally in Minnesota groundwater. They need oxidation and filtration, not just a softener."),
             ("clock", "Installed by a local team", "Twin Cities based, open 24 hours, serving Greater Minnesota. Travel fees may apply beyond 35 miles from Minneapolis.")]
    media = ('<img src="/assets/img/mn-home.webp" alt="A Minnesota home in winter at dusk" loading="lazy" width="1024" height="1280">' if has_img("mn-home.webp") else "")
    return ('<section class="section mn"><div class="container mn-grid"><div><p class="kicker">Built for Minnesota water</p><h2>Systems sized for the water under your feet, not a national average.</h2><p class="lead">Water in Minnesota has a personality: hard, often iron-rich, and disinfected on the way to city taps. Our two system lines exist because of it.</p><ul class="mn-list" style="margin-top:2rem">%s</ul>'
            '<p style="margin-top:1.5rem"><a class="link" href="https://www.health.state.mn.us/communities/environment/water/index.html" target="_blank" rel="noopener">Minnesota Department of Health: water and health resources</a></p></div><div class="mn-media reveal" data-parallax="24">%s</div></div></section>') % (
        "".join('<li>%s<div><b>%s</b><p>%s</p></div></li>' % (ICON[i], t, p) for i, t, p in items), media)

def service_area_block():
    lis = "".join('<li><a class="%s" href="/service-areas/%s/">%s</a></li>' % ("core" if c.get("core") else "", c["slug"], e(c["city"])) for c in FOOTER_CITIES)
    return '<section class="section"><div class="container"><p class="kicker">Service area</p><div class="grid grid-2" style="align-items:end;margin-bottom:2rem"><h2>Minneapolis, St. Paul and the whole metro.</h2><p class="lead">Twenty of the %d Twin Cities communities we serve, plus Greater Minnesota. <a class="link" href="/service-areas/">See every city and region</a></p></div><ul class="areas">%s</ul></div></section>' % (len(CITIES), lis)

def faq_block(items, heading="Questions homeowners ask", kicker="FAQ", more=True):
    d = "".join('<details><summary>%s %s</summary><div class="a">%s</div></details>' % (e(q["q"]), ICON["plus"], e(q["a"])) for q in items)
    return '<section class="section cream"><div class="container"><div class="center"><p class="kicker">%s</p><h2>%s</h2></div><div class="faq" style="margin-top:2rem">%s</div>%s</div></section>' % (kicker, heading, d, '<p class="center" style="margin-top:2rem"><a class="btn btn-outline on-light" href="/faq/">All questions</a></p>' if more else "")

def final_cta():
    return ('<section class="section dark final"><div class="container"><h2><span>Your water.</span><span>Your system.</span><span class="g">Your schedule.</span></h2><div class="final-actions"><a class="btn btn-gold btn-lg" href="/find-my-system/">Find My System</a><a class="btn btn-outline btn-lg" href="/schedule/">Schedule Online</a><a class="phone" href="tel:%s">%s</a></div></div></section>') % (TEL, PHONE)

def ghl_calendar(title="Choose your appointment time"):
    return ('<div class="dev-banner"></div><div class="ghl-wrap" data-ghl-calendar data-phone="%s" data-tel="%s" aria-label="%s"></div>') % (PHONE, TEL, title)

def marquee():
    items = ["Best Price Guarantee", "Reverse osmosis included", "Transparent pricing", "Online scheduling", "Iron & sulfur treatment", "Professional installation", "Twin Cities & Greater Minnesota"]
    track = "".join("<span>%s</span>" % i for i in items)
    return '<div class="marquee" aria-hidden="true"><div class="marquee-track">%s%s</div></div>' % (track, track)

# ---------------------------------------------------------------- pages
def home():
    body = hero() + source_cards() + explorer() + systems_home() + best_price() + approach() + before_after() + why() + process() + reviews() + minnesota() + service_area_block() + faq_block(FAQ[:6]) + final_cta()
    return page("", "Water Filtration, Softening & Reverse Osmosis | Twin Cities | MSP Pure Water", SITE["description"], body, over_hero=True)

def sysdetail(s):
    img = s["image"]
    intake = json.dumps({"system_interest": {"city": "Whole Home Filtration", "well": "Well Water Treatment", "ro": "Reverse Osmosis", "addon": "Well Water Treatment"}[s["category"]], "water_source": {"city": "City Water", "well": "Well Water"}.get(s["category"], "")})
    badge = '<span class="badge" style="position:static;display:inline-block;margin-bottom:.75rem">%s</span>' % e(s["badge"]) if s.get("badge") else ""
    note = '<p class="note">%s</p>' % e(s["note"]) if s.get("note") else ""
    stages = ('<div class="detail-block"><h4>Treatment stages</h4><ol class="stages">%s</ol></div>' % "".join('<li><span class="n">%s</span><div><b>%s</b><p>%s</p></div></li>' % (st["n"], e(st["title"]), e(st["text"])) for st in s["stages"])) if s["stages"] else ""
    specs = ('<table class="specs"><tbody>%s</tbody></table>' % "".join("<tr><th>%s</th><td>%s</td></tr>" % (e(k), e(v)) for k, v in s["specs"])) if s["specs"] else '<p class="note">%s</p>' % e(s.get("specs_note", ""))
    incl = "".join("<li>%s<span>%s</span></li>" % (ICON["check"], e(i)) for i in s["included"])
    warranty = '<p class="muted" style="font-size:.9rem;margin-top:.75rem">Warranty: %s. Exact terms reviewed at your consultation.</p>' % e(s["warranty"]) if s.get("warranty") else ""
    return ('<article class="sysdetail section-tight" id="%s"><div class="sysdetail-media reveal"><img src="/assets/img/%s" width="1024" height="1024" loading="lazy" alt="%s"></div><div>'
            '%s<h2 style="font-size:clamp(1.9rem,3.4vw,2.8rem)">%s</h2><div class="price" style="margin-bottom:1rem">%s%s<small>installed</small></div><p class="lead">%s</p><ul class="tags" style="margin-bottom:1.5rem">%s</ul>%s%s'
            '<div class="detail-block"><h4>Verified specifications</h4>%s</div><div class="detail-block"><h4>What\'s included</h4><ul class="incl">%s</ul>%s</div>'
            '<div class="detail-block" style="display:flex;gap:.75rem;flex-wrap:wrap"><a class="btn btn-gold btn-lg" href="%s" data-intake=\'%s\'>Configure &amp; schedule</a><a class="btn btn-outline on-light btn-lg" href="/compare-systems/">Compare</a><a class="btn btn-outline on-light btn-lg" href="/find-my-system/">Not sure? Find my system</a></div></div></article>') % (
        s["id"], img, e(s["image_alt"]), badge, e(s["name"]), s.get("price_prefix", ""), money(s["price"]), e(s["for"]), "".join("<li>%s</li>" % e(p) for p in s["problems"]), note, stages, specs, incl, warranty, sys_href(s), intake)

SYS_SUBNAV = lambda cur: [("City Water", "/city-water-filtration/", cur == "city"), ("Well Water", "/well-water-filtration/", cur == "well"), ("Drinking Water / RO", "/reverse-osmosis/", cur == "ro"), ("Compare", "/compare-systems/", cur == "compare"), ("Pricing", "/pricing/", cur == "pricing")]

def service_schema(name, desc, systems):
    return {"@context": "https://schema.org", "@type": "Service", "name": name, "description": desc, "provider": {"@id": BASE + "/#business"}, "areaServed": {"@type": "State", "name": "Minnesota"},
            "hasOfferCatalog": {"@type": "OfferCatalog", "name": name, "itemListElement": [{"@type": "Offer", "name": s["name"], "price": s["price"], "priceCurrency": "USD", "url": BASE + sys_href(s)} for s in systems]}}

def system_page(cat, slug, title, desc, h1, lead, concerns, extra_sections=""):
    systems = BY_CAT[cat]
    body = phero({"city": "City water solutions", "well": "Well water solutions", "ro": "Drinking water"}[cat], h1, lead, crumbs="Systems", subnav=SYS_SUBNAV(cat),
                 extra='<div class="hero-promo"><b>Included</b> RO drinking system with every whole-home system</div>' if cat != "ro" else "")
    body += marquee()
    body += '<section class="section-tight"><div class="container">' + carousel(systems, {"city": "City water systems", "well": "Well water systems", "ro": "Drinking water systems"}[cat]) + "</div></section>"
    if cat == "well":
        body += '<section class="section-tight cream" id="add-ons"><div class="container"><p class="kicker">Recommended for well water</p><h2>Protection add-ons</h2><div class="grid grid-2" style="margin-top:1.5rem">' + "".join(system_card(s) for s in BY_CAT["addon"]) + "</div></div></section>"
    body += extra_sections
    body += '<section class="section"><div class="container"><p class="kicker">Common concerns</p><h2 style="max-width:22ch">%s</h2><div class="grid grid-3" style="margin-top:2rem">%s</div></div></section>' % (concerns[0], "".join('<div class="reveal"><h3 style="font-size:1.35rem">%s</h3><p class="muted">%s</p></div>' % (t, p) for t, p in concerns[1]))
    body += best_price() + faq_block([q for q in FAQ if any(k in q["q"].lower() for k in {"city": ["cost", "filtration and softening", "every faucet", "salt", "pressure"], "well": ["well", "cost", "maintenance", "tested", "warranty"], "ro": ["reverse osmosis", "tank", "every faucet", "cost"]}[cat])][:5]) + final_cta()
    return page(slug, title, desc, body, schema=[service_schema(h1, desc, systems)])

def city_page():
    return system_page("city", "city-water-filtration", "City Water Filtration & Softening Systems | Twin Cities | MSP Pure Water",
        "Whole-home water filtration and softening for Minneapolis, St. Paul and Twin Cities homes on municipal water. Published prices from $2,999, RO included.",
        "City water filtration systems for Twin Cities homes", "Municipal water is treated and safe, but it typically arrives hard and disinfected with chlorine or chloramine. These systems soften and filter every tap in the house.",
        ("What's in Twin Cities city water", [("Hardness", "Minnesota groundwater is generally hard. Calcium and magnesium cause scale on fixtures, water heaters and appliances."), ("Chlorine and chloramine", "Twin Cities utilities use disinfectants including chloramine. They affect taste and odor and call for catalytic carbon."), ("Dissolved solids", "Minerals that affect drinking-water taste. Point-of-use reverse osmosis handles them at the kitchen sink.")]))

def well_page():
    return system_page("well", "well-water-filtration", "Well Water Filtration, Iron & Sulfur Treatment | Minnesota | MSP Pure Water",
        "Chemical-free well water treatment for iron, sulfur odor, manganese and hardness in Minnesota. Dual tank systems from $4,499 with RO included.",
        "Well water filtration systems for Minnesota homes", "Private wells in Minnesota commonly carry iron, manganese and hardness, and in some areas hydrogen sulfide. Final configuration is confirmed from your water test.",
        ("What's in Minnesota well water", [("Iron and manganese", "Both occur naturally in Minnesota groundwater. They stain fixtures and laundry and need oxidation plus filtration."), ("Hydrogen sulfide", "The rotten-egg smell. Oxidation converts it into a filterable form."), ("Sediment and microorganisms", "A pre-system sediment filter protects your equipment; a UV purifier adds a disinfection barrier after filtration.")]))

def ro_page():
    extra = ('<section class="section cream"><div class="container two-col"><div><p class="kicker">What reverse osmosis does</p><h2>A finer barrier for the water you drink.</h2><p>Reverse osmosis pushes water through a semipermeable membrane under pressure. Water molecules pass; a broad range of dissolved solids is rejected and sent to drain. The treated water goes to its own faucet at the kitchen sink.</p><p>RO is a point-of-use method. It treats one location for drinking and cooking, not the whole house, which is why we pair it with whole-home filtration or softening and include it free with every whole-home system.</p></div>'
             '<div class="founder"><blockquote>Tank or tankless, the RO faucet is the one your family will use fifty times a day.</blockquote><p class="muted" style="color:rgba(255,255,255,.7)">Both configurations are $799 on their own and included free with any whole-home system.</p></div></div></section>')
    return system_page("ro", "reverse-osmosis", "Reverse Osmosis Drinking Water Systems | Twin Cities | MSP Pure Water",
        "Tank or tankless reverse osmosis installed at your kitchen sink in the Twin Cities. $799, or included free with any MSP Pure Water whole-home system.",
        "Reverse osmosis systems for Twin Cities homes", "Point-of-use reverse osmosis produces a treated drinking-water stream at a dedicated kitchen faucet. Tank or tankless, professionally installed, and included free with any whole-home system.",
        ("Drinking-water questions we hear most", [("Taste", "Residual chlorine, hardness and dissolved solids all affect taste. RO plus remineralization is the fix most homeowners notice first."), ("Bottled water", "A dedicated faucet replaces the cases, the clutter and the recycling."), ("Well water", "On a well, RO adds a second barrier for drinking water after whole-home treatment handles iron and hardness.")]), extra)

def compare_page():
    cols = [SYSTEMS[i] for i in ["whole-home-softener", "dual-tank-city", "salt-free", "dual-tank-well", "iron-sulfur"]]
    def row(label, fn): return "<tr><th>%s</th>%s</tr>" % (label, "".join("<td>%s</td>" % fn(s) for s in cols))
    yes = '<span class="yes">%s Yes</span>' % ICON["check"]; no = '<span class="no">—</span>'
    tbl = ('<table class="compare"><thead><tr><th>Compare</th>%s</tr></thead><tbody>' % "".join("<th>%s</th>" % e(s["short"]) for s in cols) +
        row("Water source", lambda s: "City water" if s["category"] == "city" else "Well water") +
        row("Installed price", lambda s: '<span class="cprice">%s</span>' % money(s["price"])) +
        row("Softens (ion exchange)", lambda s: yes if s["id"] != "salt-free" else '<span class="no">Salt-free conditioning only</span>') +
        row("Chlorine / chloramine", lambda s: yes if s["category"] == "city" else '<span class="no">Not typical on wells</span>') +
        row("Iron, sulfur, manganese", lambda s: yes if s["category"] == "well" else no) +
        row("Treatment", lambda s: "Air oxidation (chemical-free)" if s["id"] == "dual-tank-well" else "Peroxide injection + carbon" if s["id"] == "iron-sulfur" else "Carbon + salt-free conditioner" if s["id"] == "salt-free" else "Carbon + softening, two tanks" if s["id"] == "dual-tank-city" else "Carbon + softening, one tank") +
        row("Softening capacity", lambda s: dict(s["specs"]).get("Softening capacity", "Sized at consultation")) +
        row("System flow", lambda s: dict(s["specs"]).get("System flow rate", "Sized at consultation")) +
        row("RO drinking system", lambda s: '<span class="yes">Included free</span>') +
        row("Warranty", lambda s: s.get("warranty", "—")) +
        row("Best for", lambda s: e(s["for"])) +
        '</tbody><tfoot><tr><td></td>%s</tr></tfoot></table>' % "".join('<td><a class="btn btn-sm btn-gold" href="%s">Configure</a> <a class="btn btn-sm btn-outline on-light" href="/schedule/?system=%s">Schedule</a></td>' % (sys_href(s), s["id"]) for s in cols))
    body = phero("Compare systems", "Every whole-home system, side by side.", "Same facts we use in the consultation. Add-ons and reverse osmosis options are listed below the table.", crumbs="Systems", subnav=SYS_SUBNAV("compare"))
    body += '<section class="section" data-view-event="system_comparison_used"><div class="container"><div class="tablewrap">%s</div><p class="muted" style="margin-top:1rem;font-size:.9rem">Well-water configuration is confirmed from your water test during the phone consultation. %s</p></div></section>' % (tbl, e(SYS["promo"]["travel"]))
    body += '<section class="section cream"><div class="container"><h2>Drinking water &amp; add-ons</h2><div class="grid grid-4" style="margin-top:1.5rem">%s</div></div></section>' % "".join(system_card(s) for s in BY_CAT["ro"] + BY_CAT["addon"])
    body += best_price() + final_cta()
    return page("compare-systems", "Compare Water Filtration Systems & Prices | MSP Pure Water", "Side-by-side comparison of MSP Pure Water whole-home city and well systems: treatment, capacity, flow, price and what's included.", body)

def pricing_page():
    body = phero("No mystery pricing", "See every price before you schedule.", "No in-home presentation required to find out what the equipment costs. " + SYS["promo"]["ro_included"], crumbs="Pricing", subnav=SYS_SUBNAV("pricing"))
    body += '<section class="section" data-view-event="pricing_viewed"><div class="container">'
    for c in SYS["categories"]:
        rows = "".join('<div class="pricing-row"><div><b>%s</b>%s<small>%s</small></div><div class="price">%s%s</div><a class="btn btn-sm btn-navy" href="/schedule/?system=%s">Schedule</a></div>' % (
            e(s["name"]), ' <span class="badge" style="position:static;display:inline-block;margin-left:.5rem">%s</span>' % e(s["badge"]) if s.get("badge") and c["id"] != "ro" else "", e(s["for"]), s.get("price_prefix", ""), money(s["price"]), s["id"]) for s in BY_CAT[c["id"]]).replace('href="/schedule/?system=', 'href="/systems/').replace('">Schedule</a>', '/">Configure</a>')
        body += '<div class="pricing-cat"><header><h2 style="margin:0">%s</h2><p>%s</p></header>%s<p style="margin-top:1rem"><a class="link" href="%s">Explore %s</a></p></div>' % (e(c["label"]), e(c["intro"]), rows, {"city": "/city-water-filtration/", "well": "/well-water-filtration/", "ro": "/reverse-osmosis/", "addon": "/well-water-filtration/#add-ons"}[c["id"]], e(c["label"].lower()))
    body += '<p class="note">%s %s</p></div></section>' % (e(SYS["promo"]["financing"]), e(SYS["promo"]["travel"]))
    body += best_price() + faq_block([q for q in FAQ if "cost" in q["q"].lower() or "guarantee" in q["q"].lower() or "warranty" in q["q"].lower()]) + final_cta()
    return page("pricing", "Transparent Pricing for Water Filtration Systems | MSP Pure Water", "Every MSP Pure Water system price published: whole-home from $2,999, well systems from $4,499, reverse osmosis $799. RO included with every whole-home system.", body)

def problems_hub():
    cards = "".join('<a class="source reveal" href="%s" data-intake=\'%s\' data-intake-via="problems_hub"><span class="num">%s</span><h3 style="font-size:1.5rem">%s</h3><p class="muted" style="margin:0">%s</p><span class="go">%s %s</span></a>' % (
        "/water-problems/%s/" % p["id"] if p.get("page") else "/#problem-%s" % p["id"], json.dumps({"water_problems": [p["label"]], "system_interest": p["interest"]}), e(p["tag"]), e(p["label"]), e(p["cause"][:140] + ("…" if len(p["cause"]) > 140 else "")), "Read more" if p.get("page") else "Explore", ICON["arrow"]) for p in PROBLEMS)
    body = phero("Water problems", "What's wrong with my water?", "Every symptom has a cause and a correct treatment. Pick yours.", crumbs="Water Problems") + '<section class="section"><div class="container"><div class="grid grid-3">%s</div></div></section>' % cards + final_cta()
    return page("water-problems", "Common Water Problems in Minnesota Homes | MSP Pure Water", "Hard water, chlorine, iron, sulfur odor, manganese and drinking-water concerns: causes and the correct treatment for each.", body)

def problem_page(p):
    systems = [SYSTEMS[s] for s in p["systems"]]
    others = [q for q in PROBLEMS if q.get("page") and q["id"] != p["id"]]
    body = phero(p["tag"] + " water", p["label"] if p["id"] != "chlorine-chloramine" else "Chlorine & Chloramine", p["cause"], crumbs='<a href="/water-problems/">Water Problems</a>')
    body += ('<section class="section"><div class="container two-col"><div><p class="kicker">How MSP approaches it</p><h2>The correct treatment, not a generic box.</h2><p class="lead">%s</p><div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1.5rem"><a class="btn btn-gold btn-lg" href="/find-my-system/" data-intake=\'%s\' data-intake-via="problem_page">Find my system</a><a class="btn btn-outline on-light btn-lg" href="/schedule/">Schedule online</a></div></div>'
             '<div class="founder"><p class="kicker">Which system category may apply</p>%s</div></div></section>') % (e(p["approach"]), json.dumps({"water_problems": [p["label"]], "system_interest": p["interest"]}), "".join('<a href="%s" style="color:#fff;text-decoration:none;display:flex;justify-content:space-between;gap:1rem;padding:.8rem 0;border-bottom:1px solid var(--line-dark)"><b>%s</b><span class="serif" style="font-size:1.3rem;color:var(--gold-300)">%s%s</span></a>' % (sys_href(s), e(s["name"]), s.get("price_prefix", ""), money(s["price"])) for s in systems))
    body += '<section class="section cream"><div class="container"><p class="kicker">Systems for this problem</p><div class="grid grid-3">%s</div></div></section>' % "".join(system_card(s) for s in systems[:3])
    body += '<section class="section"><div class="container"><p class="kicker">Other problems</p><ul class="chips">%s</ul></div></section>' % "".join('<li><a class="chip" href="/water-problems/%s/" style="text-decoration:none;display:inline-block">%s</a></li>' % (q["id"], e(q["nav"])) for q in others)
    body += final_cta()
    return page("water-problems/" + p["id"], p["seo_title"], p["seo_desc"], body)

def configurator(s):
    """SystemConfigurator: options -> live total -> Schedule CTA. Presentation only; JS in ui.js."""
    groups = ""
    for g in s.get("options", []):
        if g["type"] == "single":
            groups += '<div class="cfg-group"><span>%s</span>%s</div>' % (e(g["label"]), "".join(
                '<label class="opt"><span class="lab"><input type="radio" name="cfg-%s" value="%d"%s> %s</span><span class="add%s">%s</span></label>' % (
                    g["key"], i, " checked" if i == 0 else "", e(c["label"]), " inc" if c.get("inc") else "", "Included" if c.get("inc") else "+" + money(c["add"])) for i, c in enumerate(g["choices"])))
        else:
            groups += '<div class="cfg-group"><label class="opt"><span class="lab"><input type="checkbox" name="cfg-%s"%s> %s%s</span><span class="add">+%s</span></label></div>' % (
                g["key"], " checked" if g.get("rec") else "", e(g["label"]), ' <span class="rec">Recommended</span>' if g.get("rec") else "", money(g["add"]))
    cfg = {"id": s["id"], "name": s["short"], "price": s["price"], "options": s.get("options", []), "interest": {"city": "Whole Home Filtration", "well": "Well Water Treatment", "ro": "Reverse Osmosis", "addon": "Well Water Treatment"}[s["category"]], "water_source": {"city": "City Water", "well": "Well Water"}.get(s["category"], "")}
    incl = "".join("<li>%s<span>%s</span></li>" % (ICON["check"], e(i)) for i in s["included"])
    return ('<div class="buybox" data-configurator><script type="application/json">%s</script>%s<h1>%s</h1><div class="price">%s%s<small>installed</small></div>%s<p class="fine">%s</p>%s'
            '<ul class="incl">%s</ul><div class="total"><div><b data-total>%s</b><div style="font-size:.8rem;color:var(--muted)" data-config-line></div></div><span>installed price</span></div>'
            '<div class="cta"><a class="btn btn-gold btn-lg btn-block" href="/schedule/?system=%s" data-cta>Schedule installation</a><a class="btn btn-outline on-light btn-block" href="/find-my-system/">Not sure? Find my system</a></div>'
            '<div class="trust-mini"><span>%s No deposit</span><span>%s Best Price Guarantee</span><span>%s Phone consultation first</span></div>'
            '<p class="fine">%s</p></div>') % (
        json.dumps(cfg).replace("</", "<\\/"), '<span class="badge" style="position:static;display:inline-block">%s</span>' % e(s["badge"]) if s.get("badge") else "", e(s["name"]), s.get("price_prefix", ""), money(s["price"]), nsf_badge(True) if s.get("nsf") else "", e(s["for"]), groups, incl, money(s["price"]), s["id"],
        ICON["check"], ICON["tag"], ICON["phone"], e(SYS["promo"]["financing"] + " " + SYS["promo"]["travel"]))

def slide(s, i, n):
    stages = ('<ol class="stages steps-row">%s</ol>' % "".join('<li><span class="n">%s</span><div><b>%s</b><p>%s</p></div></li>' % (st["n"], e(st["title"]), e(st["text"])) for st in s["stages"])) if s["stages"] else ""
    specs = ('<table class="specs compact"><tbody>%s</tbody></table>' % "".join("<tr><th>%s</th><td>%s</td></tr>" % (e(k), e(v)) for k, v in s["specs"][:5])) if s["specs"] else '<p class="note">%s</p>' % e(s.get("specs_note", ""))
    badge = '<span class="badge">%s</span>' % e(s["badge"]) if s.get("badge") else ""
    intake = json.dumps({"system_interest": {"city": "Whole Home Filtration", "well": "Well Water Treatment", "ro": "Reverse Osmosis", "addon": "Well Water Treatment"}[s["category"]], "water_source": {"city": "City Water", "well": "Well Water"}.get(s["category"], "")})
    return ('<article class="slide" id="%s" data-active="%s" role="tabpanel" aria-label="%s"><div class="slide-media"><img src="/assets/img/%s" srcset="/assets/img/%s 640w, /assets/img/%s 1024w" sizes="(max-width:860px) 90vw, 560px" width="1024" height="1280" loading="%s" alt="%s"></div>'
            '<div class="slide-body"><div>%s<h3>%s</h3><div class="price">%s%s<small>installed</small></div><div class="pills">%s</div></div><p style="margin:0;color:var(--muted)">%s</p><ul class="tags">%s</ul>'
            '<div class="slide-cols"><div><h4>Why it leads the industry</h4>%s</div><div><h4>Verified specifications</h4>%s</div></div>'
            '<div class="slide-actions"><a class="btn btn-gold" href="%s" data-intake=\'%s\'>Configure &amp; schedule</a><a class="btn btn-outline on-light" href="%s">Full details</a>%s</div></div>'
            '<div class="slide-steps"><h4>How it works</h4>%s</div></article>') % (
        s["id"], "true" if i == 0 else "false", e(s["name"]), s["image"], s["image"].replace(".webp", "-640.webp"), s["image"], "eager" if i == 0 else "lazy", e(s["image_alt"]),
        badge, e(s["name"]), s.get("price_prefix", ""), money(s["price"]), nsf_badge(True) if s.get("nsf") else "", e(s.get("what_it_does") or s["for"]), "".join("<li>%s</li>" % e(p) for p in s["problems"]), leads_list(s), specs, sys_href(s), intake, sys_href(s),
        '<span class="promo-line">%s RO drinking system included</span>' % ICON["drop"] if s["category"] in ("city", "well") else "", stages)

def carousel(systems, label):
    n = len(systems)
    dots = "".join('<button type="button" role="tab" aria-selected="%s" data-slide="%d">%s</button>' % ("true" if i == 0 else "false", i, e(s["short"])) for i, s in enumerate(systems))
    return ('<div class="carousel" data-carousel><div class="carousel-head"><div class="carousel-dots" role="tablist" aria-label="%s">%s</div><div class="carousel-nav"><button type="button" data-prev aria-label="Previous system">%s</button><span class="count"><span data-current>1</span> / %d</span><button type="button" data-next aria-label="Next system">%s</button></div></div>%s</div>') % (
        e(label), dots, ICON["arrow"].replace('<svg', '<svg style="transform:rotate(180deg)"'), n, ICON["arrow"], "".join(slide(s, i, n) for i, s in enumerate(systems)))

NSF_ICON = '<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="30" fill="#0A5AA8"/><circle cx="32" cy="32" r="23" fill="none" stroke="#fff" stroke-width="2.5"/><text x="32" y="38" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="18" fill="#fff">NSF</text></svg>'
def nsf_badge(small=False):
    return '<span class="pill pill-nsf">%s Every component NSF certified</span>' % NSF_ICON

def leads_list(s):
    if not s.get("leads"): return ""
    return '<ul class="leads">%s</ul>' % "".join("<li>%s<span>%s</span></li>" % (ICON["check"], e(l)) for l in s["leads"])

def components_section(s):
    ids = s.get("components") or []
    if not ids: return ""
    cards = ""
    for cid in ids:
        c = COMPONENTS[cid]
        cards += ('<article class="comp reveal"><span class="kicker">%s</span><h3>%s</h3><dl><div><dt>What it is</dt><dd>%s</dd></div><div><dt>What it does</dt><dd>%s</dd></div><div><dt>Why it matters</dt><dd>%s</dd></div></dl><ul class="comp-stats">%s</ul></article>') % (
            e(c["kicker"]), e(c["name"]), e(c["what"]), e(c["does"]), e(c["value"]), "".join("<li><b>%s</b><span>%s</span></li>" % (e(v), e(k)) for k, v in c["stats"]))
    return ('<section class="section" id="inside"><div class="container"><div class="grid grid-2" style="align-items:end;margin-bottom:2rem"><div><p class="kicker">Inside the system</p><h2>Every component, and why we chose it.</h2></div><p class="lead">No mystery boxes. These are the exact parts in the %s, what each one does to your water, and the value it adds over what most companies install.</p></div><div class="comp-grid">%s</div></div></section>') % (e(s["short"]), cards)

def product_page(s):
    cat = {"city": "City water", "well": "Well water", "ro": "Drinking water", "addon": "Well water add-on"}[s["category"]]
    cat_link = {"city": "/city-water-filtration/", "well": "/well-water-filtration/", "ro": "/reverse-osmosis/", "addon": "/well-water-filtration/#add-ons"}[s["category"]]
    pills = ('<span class="pill">%s Reverse osmosis drinking-water system included</span>' % ICON["check"] if s["category"] in ("city", "well") else "") + (nsf_badge() if s.get("nsf") else "")
    # option chips (configurator)
    groups = ""
    for g in s.get("options", []):
        if g["type"] == "single":
            groups += '<div class="cfg-group" data-group><span>%s <em data-choice>— %s</em></span><div class="chips">%s</div></div>' % (e(g["label"]), e(g["choices"][0]["label"]), "".join(
                '<label class="chipopt"><input type="radio" name="cfg-%s" value="%d"%s><span>%s</span></label>' % (g["key"], i, " checked" if i == 0 else "", e(c["label"]) + ("" if c.get("inc") else " +" + money(c["add"]))) for i, c in enumerate(g["choices"])))
        else:
            groups += '<div class="cfg-group" data-group><span>%s <em data-choice>— %s</em></span><div class="chips"><label class="chipopt"><input type="checkbox" name="cfg-%s"%s><span>%s +%s</span></label></div></div>' % (
                e(g["label"]), "Yes" if g.get("rec") else "No", g["key"], " checked" if g.get("rec") else "", "Add" if not g.get("rec") else "Included in quote", money(g["add"]))
    cfg = {"id": s["id"], "name": s["short"], "price": s["price"], "options": s.get("options", []), "interest": {"city": "Whole Home Filtration", "well": "Well Water Treatment", "ro": "Reverse Osmosis", "addon": "Well Water Treatment"}[s["category"]], "water_source": {"city": "City Water", "well": "Well Water"}.get(s["category"], "")}
    trust = '<ul class="trust-row"><li>%s<span>Best Price Guarantee</span></li><li>%s<span>Professional install</span></li><li>%s<span>NSF certified components</span></li><li>%s<span>Lifetime warranty</span></li></ul>' % (ICON["tag"], ICON["wrench"], NSF_ICON, ICON["shield"])
    desc_lines = "".join("<p><b>%s:</b> %s</p>" % (e(a), e(b)) for a, b in s.get("description_lines", []))
    spec_line = " | ".join("%s %s" % (v, k.lower()) for k, v in s["specs"][:5]) if s["specs"] else ""
    accordions = ('<div class="acc"><details open><summary>Description %s</summary><div class="acc-body"><p>%s</p>%s%s</div></details>'
                  '<details><summary>Installation &amp; Scheduling %s</summary><div class="acc-body"><p>Pick a time online and we call you for a free phone consultation. We confirm your selections, your water and every detail, then set an installation date. Most whole-home systems are installed in a single visit, connected to your main water line, configured for your water and walked through with you before we leave. In-home presentations are available on request. %s</p></div></details>'
                  '<details><summary>Warranty &amp; Guarantee %s</summary><div class="acc-body"><p>%s We go through the exact terms with you on the phone before anything is installed. Best Price Guarantee: find a lower quote on comparable equipment and installation and we\'ll beat it, with priority booking.</p></div></details></div>') % (
        ICON["chev"], e(s.get("what_it_does") or s["for"]), desc_lines, ('<p class="spec-line"><b>Specs:</b> %s</p>' % e(spec_line)) if spec_line else "", ICON["chev"], e(SYS["promo"]["travel"]), ICON["chev"], ("Lifetime warranty on the system." if s.get("warranty") else "Warranty details reviewed at your consultation."))
    buy = ('<div class="buy" data-configurator><script type="application/json">%s</script><h1>%s</h1><div class="pills">%s</div><div class="price">%s%s</div><div class="price-note">Professional installation included</div>%s'
           '<a class="btn btn-gold btn-lg btn-block" href="/schedule/?system=%s" data-cta>Schedule Online</a><p class="or">or call or text <a href="tel:%s">%s</a></p><p class="fine center">We\'ll confirm your selections and every detail before your install date.</p>%s%s</div>') % (
        json.dumps(cfg).replace("</", "<\\/"), e(s["name"]), pills, s.get("price_prefix", ""), money(s["price"]), groups, s["id"], TEL, PHONE, trust, accordions)
    hero = ('<section class="section-tight"><div class="container"><div class="crumbs" style="font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:1.25rem"><a href="/">Home</a> / <a href="%s">%s systems</a> / %s</div>'
            '<div class="pdp"><div class="pdp-media"><img src="/assets/img/%s" width="1024" height="1024" alt="%s" fetchpriority="high"></div>%s</div></div></section>') % (cat_link, cat, e(s["short"]), s["image"], e(s["image_alt"]), buy)
    # Inside the system stepper
    inside = ""
    if s.get("aspects"):
        steps = ""
        for i, a in enumerate(s["aspects"]):
            steps += ('<div class="aspect" data-active="%s"><span class="kicker">%s</span><div class="crossed">%s</div><h3>%s</h3><p>%s</p><div class="stat-boxes">%s</div></div>') % (
                "true" if i == 0 else "false", e(a["kicker"]), e(a["crossed"]), e(a["headline"]), e(a["body"]), "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v)) for k, v in a["stats"]))
        callouts = "".join('<span class="callout" style="left:%d%%;top:%d%%">%s</span>' % (c["x"], c["y"], e(c["label"])) for c in s.get("callouts", []))
        n = len(s["aspects"])
        inside = ('<section class="section dark inside" id="inside"><div class="container"><div class="center"><p class="kicker">What we use &amp; why it matters</p><h2>Inside the System</h2>%s</div>'
                  '<div class="stepper" data-stepper><div class="aspects">%s<div class="step-nav"><button type="button" data-prev aria-label="Previous">%s</button><span class="count"><span data-current>1</span> of %d</span><button type="button" data-next aria-label="Next">%s</button></div>'
                  '<div class="step-cta"><a class="btn btn-gold" href="/schedule/?system=%s">Schedule this system</a><a class="btn btn-outline" href="tel:%s">Call %s</a></div></div>'
                  '<div class="callout-media"><img src="/assets/img/%s" width="1024" height="1024" loading="lazy" alt="%s">%s%s</div></div></div></section>') % (
            nsf_badge() if s.get("nsf") else "", steps, ICON["arrow"].replace('<svg', '<svg style="transform:rotate(180deg)"'), n, ICON["arrow"], s["id"], TEL, PHONE, s["image"], e(s["image_alt"]), callouts, ('<span class="callout-nsf">%s</span>' % NSF_ICON) if s.get("nsf") else "")
    related = [x for x in SYS["systems"] if x["category"] == s["category"] and x["id"] != s["id"]][:3] or [SYSTEMS["ro-tankless"]]
    body = hero + inside
    body += '<section class="section cream"><div class="container"><p class="kicker">Compare</p><h2>Other %s options</h2><div class="grid grid-3" style="margin-top:1.5rem">%s</div><p style="margin-top:1.5rem"><a class="link" href="/compare-systems/">Full side-by-side comparison</a></p></div></section>' % (cat.lower(), "".join(system_card(x) for x in related))
    body += faq_block([q for q in FAQ if any(k in q["q"].lower() for k in {"city": ["come to my home", "cost", "filtration and softening", "salt", "pressure"], "well": ["come to my home", "well", "tested", "maintenance", "warranty"], "ro": ["come to my home", "reverse osmosis", "tank", "every faucet"], "addon": ["come to my home", "sediment", "uv", "well"]}[s["category"]])][:4]) + final_cta()
    schema = {"@context": "https://schema.org", "@type": "Product", "name": s["name"], "description": s.get("what_it_does") or s["for"], "image": BASE + "/assets/img/" + s["image"], "brand": {"@type": "Brand", "name": "MSP Pure Water"},
              "offers": {"@type": "Offer", "price": s["price"], "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": BASE + sys_href(s), "seller": {"@id": BASE + "/#business"}}}
    return page("systems/" + s["id"], "%s | %s%s Installed | MSP Pure Water" % (s["name"], s.get("price_prefix", ""), money(s["price"])), "%s %s installed in the Twin Cities. %s Configure your options and schedule online." % (s["name"], money(s["price"]), s["for"]), body, schema=[schema])

def areas_hub():
    counties = []
    for c in CITIES:
        if c["county"] not in counties: counties.append(c["county"])
    groups = ""
    for co in counties:
        cs = [c for c in CITIES if c["county"] == co]
        groups += '<div class="county reveal"><h3>%s <small>%d communities</small></h3><ul class="areas">%s</ul></div>' % (e(co), len(cs), "".join('<li><a class="%s" href="/service-areas/%s/">%s</a></li>' % ("core" if c.get("core") else "", c["slug"], e(c["city"])) for c in cs))
    regions = "".join('<div><b>%s</b><p>%s</p></div>' % (e(r["region"]), e(", ".join(r["cities"]))) for r in REGIONS["greater"])
    body = phero("Coverage", "Serving Minneapolis, St. Paul &amp; Greater Minnesota", "Whole-home filtration, softening, well-water treatment and reverse osmosis across the entire Twin Cities metro, with installs throughout Greater Minnesota. Consultations happen by phone, so distance never delays a recommendation.", crumbs="Service Areas",
                 extra='<div class="hero-promo"><b>%d</b> metro communities &middot; %d counties</div>' % (len(CITIES), len(counties)))
    body += ('<section class="section"><div class="container"><div class="grid grid-2" style="align-items:end"><div><p class="kicker">How coverage works</p><h2>Phone first. Then one visit to install.</h2></div><p class="lead">Every consultation starts as a scheduled phone call, wherever you live, with in-home presentations available on request. Travel fees apply only beyond 35 miles from Minneapolis.</p></div>'
             '<div class="coverage"><div><b>Twin Cities metro</b><p>Hennepin, Ramsey, Dakota, Anoka, Washington, Scott and Carver counties, plus the growing suburbs in Wright, Sherburne, Isanti and Chisago.</p></div><div><b>Greater Minnesota</b><p>Regular installs from St. Cloud to Rochester to Duluth. Travel fees may apply beyond 35 miles from Minneapolis; we quote them on the call.</p></div><div><b>City or well, anywhere</b><p>Metro homes are mostly on municipal water; outer suburbs and Greater Minnesota lean on private wells. We carry both system lines.</p></div></div></div></section>')
    body += '<section class="section cream"><div class="container"><p class="kicker">Twin Cities metro</p><h2 style="margin-bottom:2rem">Communities we serve, by county</h2>%s</div></section>' % groups
    body += ('<section class="section mn"><div class="container mn-grid"><div><p class="kicker">Greater Minnesota</p><h2>Outside the metro? We still come to you.</h2><p class="lead">These are the regions we install in most often. Not listed? Call or text and we\'ll tell you right away.</p><div class="region-list" style="margin-top:2rem">%s</div><div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:2rem"><a class="btn btn-gold btn-lg" href="/schedule/">Schedule a phone consultation</a><a class="btn btn-outline btn-lg" href="tel:%s">%s Call or text %s</a></div></div><div class="mn-media reveal" data-parallax="24">%s</div></div></section>') % (
        regions, TEL, ICON["phone"], PHONE, '<img src="/assets/img/mn-home.webp" alt="A Minnesota home in winter at dusk" loading="lazy" width="1024" height="1280">' if has_img("mn-home.webp") else "")
    body += process() + final_cta()
    return page("service-areas", "Service Areas | Water Filtration Across the Twin Cities & Minnesota | MSP Pure Water", "MSP Pure Water serves %d Twin Cities communities across %d counties plus Greater Minnesota with water filtration, softening, well treatment and RO installation." % (len(CITIES), len(counties)), body)

def city_page_for(c):
    name = c["city"]
    nearby = [x for x in CITIES if x["county"] == c["county"] and x["slug"] != c["slug"]][:6]
    body = phero(c["county"] + " &middot; Minnesota", "Water filtration in %s" % e(name), "Whole-home filtration, water softening, well-water treatment and reverse osmosis for %s homeowners, with published prices and online scheduling." % e(name), crumbs='<a href="/service-areas/">Service Areas</a>')
    body += ('<section class="section"><div class="container two-col"><div><p class="kicker">Local, transparent, professional</p><h2>Systems for %s homes, priced up front.</h2><p>Whether your %s home is on municipal water or a private well, we start with the water problem and match the equipment to it. Every system price is published, the reverse osmosis drinking-water system is included, and you can book an appointment online.</p>'
             '<p>Want to know exactly what\'s in your water? City customers can request the annual Consumer Confidence Report from their water utility; well owners should have a current water test. We go over either one with you on the phone.</p>'
             '<div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1.5rem"><a class="btn btn-gold btn-lg" href="/find-my-system/">Find My System</a><a class="btn btn-outline on-light btn-lg" href="/schedule/">Schedule Online</a></div></div>'
             '<div class="founder"><p class="kicker">Popular in %s</p>%s</div></div></section>') % (e(name), e(name), e(name), "".join('<a href="%s" style="color:#fff;text-decoration:none;display:flex;justify-content:space-between;gap:1rem;padding:.8rem 0;border-bottom:1px solid var(--line-dark)"><b>%s</b><span class="serif" style="font-size:1.3rem;color:var(--gold-300)">%s</span></a>' % (sys_href(s), e(s["short"]), money(s["price"])) for s in [SYSTEMS["whole-home-softener"], SYSTEMS["dual-tank-well"], SYSTEMS["ro-tankless"]]))
    body += '<section class="section cream"><div class="container"><div class="grid grid-3">%s</div></div></section>' % "".join(system_card(SYSTEMS[i]) for i in ["whole-home-softener", "dual-tank-well", "ro-tankless"])
    if nearby: body += '<section class="section"><div class="container"><p class="kicker">Nearby</p><ul class="chips">%s</ul></div></section>' % "".join('<li><a class="chip" style="text-decoration:none;display:inline-block" href="/service-areas/%s/">%s</a></li>' % (x["slug"], e(x["city"])) for x in nearby)
    body += final_cta()
    schema = {"@context": "https://schema.org", "@type": "Service", "name": "Water filtration in %s, MN" % name, "provider": {"@id": BASE + "/#business"}, "areaServed": {"@type": "City", "name": name + ", MN"}, "serviceType": "Water filtration, water softening, well water treatment, reverse osmosis installation"}
    return page("service-areas/" + c["slug"], "Water Filtration %s MN | Softening, Well & RO | MSP Pure Water" % name, "Whole-home water filtration, softening, well-water treatment and reverse osmosis in %s, Minnesota. Published prices from $2,999, RO included, schedule online." % name, body, schema=[schema])

def about_page():
    body = phero("Minneapolis, St. Paul & Greater Minnesota", "Why MSP Pure Water", "Better water for Minnesota homes: honestly assessed, fairly priced, installed cleanly, and backed personally.", crumbs="Why MSP")
    body += ('<section class="section"><div class="container founder-grid"><div class="portrait reveal"><img src="/assets/img/founder-prince.webp" srcset="/assets/img/founder-prince-480.webp 480w, /assets/img/founder-prince.webp 960w" sizes="(max-width:860px) 90vw, 420px" width="960" height="1200" alt="Prince, founder and CEO of MSP Pure Water"><div class="cap">Founder &amp; CEO<b>Prince</b></div></div><div><p class="kicker">Meet the founder</p><h2>Prince</h2><p>Being from Minnesota himself, Prince understands how important water quality is here. From hard-water buildup to the long-term wear it puts on plumbing, fixtures and appliances, homeowners deserve solutions that prevent problems before they become expensive repairs.</p>'
             '<p>He started MSP Pure Water because he was tired of seeing overpriced water solutions, with homeowners quoted thousands more than the work was worth for the same equipment. The company exists to make water treatment affordable without cutting a corner on quality.</p>'
             '<p>When you work with MSP Pure Water, you work with Prince directly. Every recommendation and every install runs through him personally. That accountability is not a selling point. It is just how the business operates.</p></div>'
             '<div class="founder" style="margin-top:1.5rem"><blockquote>We run the same systems we install. We\'re not selling you something we wouldn\'t put in our own house.</blockquote><div class="stat-row"><div><b>%s</b><span>Stars on Google</span></div><div><b>Phone</b><span>Consultations, in-home on request</span></div><div><b>24 h</b><span>Open every day</span></div><div><b>$2,999</b><span>Whole-home from</span></div></div></div></div></div></section>') % (SITE["google_rating"])
    body += why()
    std = [("Free phone assessment first", "We go over your water and your home on the phone before we recommend anything. In-home presentations are available on request."), ("Honest recommendation", "The right system for your home and budget, not the most expensive option on the list."), ("Clean installation", "Professional work and a full walkthrough of how your system works before we leave."), ("Same-day response", "Call or text and we get back to you the same day with real answers."), ("No oversell, ever", "We recommend only what makes sense for your home and your water profile."), ("Local and personally accountable", "When you call, you reach someone who knows the job. Not a dispatcher, not a call center.")]
    body += '<section class="section cream"><div class="container"><p class="kicker">Our standards</p><h2 style="max-width:20ch">You can rely on the quality and professionalism of our work.</h2><div class="grid grid-3" style="margin-top:2rem">%s</div></div></section>' % "".join('<div class="reveal"><h3 style="font-size:1.35rem">%s</h3><p class="muted">%s</p></div>' % (t, p) for t, p in std)
    body += reviews() + process() + final_cta()
    return page("about", "About MSP Pure Water | Why Twin Cities Homeowners Choose Us", "Meet Prince, founder of MSP Pure Water, and see why Twin Cities homeowners choose transparent pricing, water-specific systems and professional installation.", body)

def faq_page():
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in FAQ]}
    body = phero("Questions", "Frequently asked questions", "Straight answers about softening, filtration, reverse osmosis and well-water treatment.", crumbs="FAQ")
    body += faq_block(FAQ, heading="Everything homeowners ask us", more=False).replace('class="section cream"', 'class="section"')
    body += '<section class="section cream"><div class="container center"><h2>Still have a question?</h2><p class="lead">Call or text any time. We answer 24 hours a day.</p><div style="display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap"><a class="btn btn-navy btn-lg" href="tel:%s">%s %s</a><a class="btn btn-gold btn-lg" href="/schedule/">Schedule Online</a></div></div></section>' % (TEL, ICON["phone"], PHONE)
    return page("faq", "FAQ | Water Filtration, Softening & RO Questions | MSP Pure Water", "Answers to the questions Twin Cities homeowners ask about water softening, filtration, reverse osmosis, well water, maintenance, warranty and scheduling.", body, schema=[schema])

def schedule_page():
    steps = [("01", "Choose a time", "Pick any open slot on the calendar below. No deposit to reserve."), ("02", "We call you", "At your chosen time, on the number you give us. Instant confirmation and a reminder before the call."), ("03", "The phone consultation", "We go over your water and your home, recommend the right system at its published price, and answer every question. Prefer to meet in person? In-home presentations are available on request."), ("04", "Installation day", "We set the date on the call. Most systems are installed in a single visit, then walked through with you.")]
    body = phero("Schedule online", "Book your phone consultation.", "Choose a time and we call you. Everything before installation happens over the phone: your water, the right system, the price, and your install date.", crumbs="Schedule",
                 extra='<div class="hero-promo"><b>Free</b> Phone consultation &middot; in-home presentations on request</div>')
    body += ('<section class="section"><div class="container"><div class="grid" style="grid-template-columns:minmax(0,1.5fr) minmax(280px,.8fr);gap:clamp(24px,4vw,56px)"><div><div class="config-summary" data-config-summary><b>You\'re scheduling</b><div class="cs-line"></div><a href="#" data-clear-config style="font-size:.8rem">Not this system? Clear it</a></div>%s<div data-lead-summary class="summary-box" hidden></div></div>'
             '<aside><p class="kicker">What happens</p><div class="process" style="grid-template-columns:1fr;gap:1.25rem">%s</div><div class="note" style="margin-top:1.5rem">Prefer to talk? Call or text <a href="tel:%s"><b>%s</b></a>. Open 24 hours.</div></aside></div></div></section>') % (
        ghl_calendar(), "".join('<div><div class="n" style="font-size:2rem">%s</div><h3 style="font-size:1.2rem">%s</h3><p>%s</p></div>' % (n, t, p) for n, t, p in steps), TEL, PHONE)
    body += '<div data-booked-inline hidden class="container"><div class="confirm section-tight"><div class="check">%s</div><h2>You\'re scheduled.</h2><p class="lead">Check your email or phone for the confirmation. We\'ll call you at your chosen time.</p></div></div>' % ICON["check"]
    body += faq_block([q for q in FAQ if any(k in q["q"].lower() for k in ["schedule", "long does", "tested", "cost"])][:4]) + final_cta()
    return page("schedule", "Schedule Online | Book a Free Phone Consultation | MSP Pure Water", "Book your free MSP Pure Water phone consultation online. Pick a time, we call you, no home visit. Twin Cities and Greater Minnesota.", body)

def fms_page():
    body = phero("Find my system", "Tell us about your water. We'll match the system.", "Five quick steps. Your answers go straight to our team, then you can pick an appointment time.", crumbs="Find My System")
    body += '<section class="section-tight"><div class="container"><div class="dev-banner"></div><div data-fms aria-live="polite"></div><p class="center muted" style="margin-top:1.5rem;font-size:.9rem">Rather talk? Call or text <a href="tel:%s"><b>%s</b></a>.</p></div></section>' % (TEL, PHONE)
    body += process()
    return page("find-my-system", "Find My System | Match Your Water to the Right Treatment | MSP Pure Water", "Answer five quick questions about your water and MSP Pure Water will recommend the right whole-home, well or reverse osmosis system.", body)

def thank_you_page():
    body = ('<section class="phero"><div class="container confirm"><div class="check">%s</div><h1>We received your information.</h1><p class="lead">Thanks, <span data-lead-name>there</span>. Our team has your details. Pick a time for your phone consultation now and skip the phone tag.</p></div></section>'
            '<section class="section"><div class="container"><div class="center"><p class="kicker">Next step</p><h2>Choose a time for your call</h2></div><div data-lead-summary class="summary-box" style="max-width:720px;margin:1rem auto 1.5rem" hidden></div>%s'
            '<p class="center muted" style="margin-top:1.5rem">Or call or text <a href="tel:%s"><b>%s</b></a>. Open 24 hours.</p></div></section>') % (ICON["check"], ghl_calendar(), TEL, PHONE)
    return page("thank-you", "We Received Your Information | MSP Pure Water", "Your Find My System request has been received. Choose your consultation time.", body, noindex=True)

def booked_page():
    body = ('<section class="phero"><div class="container confirm" data-booked><div class="check">%s</div><h1 data-booked-name>You\'re scheduled.</h1><p class="lead">Your phone consultation is on the calendar. We\'ll call you at that time. A confirmation is on its way to your phone and email.</p>'
            '<dl><div><dt>Date</dt><dd data-booked-date>See your confirmation</dd></div><div><dt>Time</dt><dd data-booked-time>See your confirmation</dd></div><div><dt>Questions</dt><dd><a href="tel:%s" style="text-decoration:none">%s</a></dd></div></dl></div></section>'
            '<section class="section"><div class="container confirm"><h2>What happens next</h2><ol class="steps-list"><li>You\'ll get a reminder before the call. Need to change it? Use the link in your confirmation or call us.</li><li>On the call we go over your water, recommend the right system at its published price, and answer your questions.</li><li>If you decide to go ahead, we set the installation date right then. Most installs happen in a single visit.</li></ol>'
            '<div style="display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;margin-top:1.5rem"><a class="btn btn-navy" href="/pricing/">Review pricing</a><a class="btn btn-outline on-light" href="/compare-systems/">Compare systems</a></div></div></section>') % (ICON["check"], TEL, PHONE)
    return page("booked", "You're Scheduled | MSP Pure Water", "Your MSP Pure Water consultation is booked.", body, noindex=True)

def bpg_page():
    body = phero("Best Price Guarantee", "Comparable system. Lower installed quote. We'll beat it.", SITE["best_price_guarantee"], crumbs="Best Price Guarantee")
    body += ('<section class="section"><div class="container two-col"><div><p class="kicker">How it works</p><h2>Three steps, no haggling.</h2><ol class="steps-list" style="margin:0"><li><b>Get your quote.</b> Any written quote from another company for comparable equipment and installation.</li><li><b>Send it to us.</b> Use the form below or text a photo of it to %s.</li><li><b>We beat it.</b> If it\'s comparable, we beat the price and move you to priority booking.</li></ol></div>'
             '<div class="founder"><p class="kicker">What counts as comparable</p><p>Same water source (city or well), similar softening capacity and flow rating, similar treatment stages, professional installation included. We\'ll tell you plainly if a quote isn\'t comparable and why.</p></div></div></section>') % PHONE
    body += '<section class="section cream" id="claim"><div class="container"><div class="center"><p class="kicker">Claim your best price</p><h2>Start with your water and we\'ll take it from there.</h2></div><div class="dev-banner"></div><div data-fms data-start="0" style="margin-top:2rem"></div><script>try{sessionStorage.setItem("msp_intake",JSON.stringify(Object.assign(JSON.parse(sessionStorage.getItem("msp_intake")||"{}"),{inquiry_type:"Best Price Guarantee Inquiry"})))}catch(e){}</script></div></section>'
    body += final_cta()
    return page("best-price-guarantee", "Best Price Guarantee | MSP Pure Water", "Find a lower quote on a comparable water treatment system and installation and MSP Pure Water will beat it, with priority booking.", body)

def contact_page():
    body = phero("Contact", "Call, text or schedule. We answer 24 hours.", "The fastest ways to reach MSP Pure Water.", crumbs="Contact")
    body += ('<section class="section"><div class="container grid grid-3"><div class="review"><h3>Call or text</h3><a class="fphone" style="font-family:var(--font-display);font-size:1.8rem;text-decoration:none" href="tel:%s">%s</a><p class="muted">Open 24 hours, every day.</p></div><div class="review"><h3>Email</h3><a class="link" href="mailto:%s">%s</a><p class="muted">Same-day response.</p></div><div class="review"><h3>Schedule online</h3><p class="muted">Pick a time and we call you. In-home presentations on request.</p><a class="btn btn-gold" href="/schedule/">Schedule Online</a></div></div></section>') % (TEL, PHONE, SITE["email"], SITE["email"])
    body += '<section class="section cream"><div class="container"><div class="center"><p class="kicker">Or start here</p><h2>Find my system</h2></div><div class="dev-banner"></div><div data-fms style="margin-top:2rem"></div></div></section>' + final_cta()
    return page("contact", "Contact MSP Pure Water | (952) 952-6206", "Call or text MSP Pure Water at (952) 952-6206, open 24 hours, or schedule your water consultation online.", body)

def legal_page(slug, title, key, fallback):
    txt = LEGAL.get(key, "")
    paras = []
    if txt:
        for line in txt.split("\n"):
            line = line.strip()
            if not line or line.lower().startswith("privacy policy") and slug == "privacy" and not paras: continue
            if line.startswith("[H"): paras.append("<h2>%s</h2>" % e(line.split("] ", 1)[1]))
            elif line.startswith("- "): paras.append("<li>%s</li>" % e(line[2:]))
            else: paras.append("<p>%s</p>" % e(line))
    body = phero("Legal", title, "", crumbs=title) + '<section class="section"><div class="container prose">%s</div></section>' % ("".join(paras) if paras else fallback)
    return page(slug, "%s | MSP Pure Water" % title, "%s for msppurewaterco.com." % title, body)

def accessibility_page():
    body = phero("Accessibility", "Accessibility statement", "MSP Pure Water is committed to a website every homeowner can use.", crumbs="Accessibility")
    body += ('<section class="section"><div class="container prose"><p>We build this site to the WCAG 2.1 AA guidelines: semantic headings, keyboard-navigable menus and forms, visible focus states, descriptive alt text, strong color contrast and respect for your reduced-motion preference (the hero video does not autoplay when reduced motion is on).</p>'
             '<p>The scheduling calendar and intake form are provided by our CRM partner inside a labeled, keyboard-reachable frame. If any part of the site is difficult to use, call or text <a href="tel:%s">%s</a> or email <a href="mailto:%s">%s</a> and we will help you directly and fix the issue.</p></div></section>') % (TEL, PHONE, SITE["email"], SITE["email"])
    return page("accessibility", "Accessibility | MSP Pure Water", "MSP Pure Water accessibility statement and how to get help using this website.", body)

def notfound_page():
    body = '<section class="section notfound"><div class="container"><p class="kicker">404</p><h1>That page isn\'t here.</h1><p class="lead">Try one of these instead.</p><div style="display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;margin-top:1rem"><a class="btn btn-gold" href="/find-my-system/">Find My System</a><a class="btn btn-navy" href="/pricing/">Pricing</a><a class="btn btn-outline on-light" href="/schedule/">Schedule Online</a></div></div></section>'
    return page("404", "Page Not Found | MSP Pure Water", "Page not found.", body, noindex=True)

# ---------------------------------------------------------------- build
def write(path, content):
    full = os.path.join(DIST, path); os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f: f.write(content)

def main():
    if os.path.exists(DIST): shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copytree(os.path.join(SRC, "img"), os.path.join(DIST, "assets/img"))
    shutil.copytree(os.path.join(SRC, "css"), os.path.join(DIST, "assets/css"))
    shutil.copytree(os.path.join(SRC, "js"), os.path.join(DIST, "assets/js"))
    shutil.copy(os.path.join(SRC, "config/ghl.config.js"), os.path.join(DIST, "assets/js/ghl.config.js"))
    if BASEPATH:  # scripts navigate/link with root-relative paths; rewrite them for subpath hosting
        for jsn in os.listdir(os.path.join(DIST, "assets/js")):
            jp = os.path.join(DIST, "assets/js", jsn); js = open(jp, encoding="utf-8").read()
            js = re.sub(r'(["\'])/(thank-you|schedule|privacy|find-my-system|assets)/', lambda m: m.group(1) + BASEPATH + "/" + m.group(2) + "/", js)
            js = js.replace('href=\\"/schedule/\\"', 'href=\\"' + BASEPATH + '/schedule/\\"').replace('href="/schedule/"', 'href="' + BASEPATH + '/schedule/"').replace('href=\\"/privacy/\\"', 'href=\\"' + BASEPATH + '/privacy/\\"')
            open(jp, "w", encoding="utf-8").write(js)
    if os.path.isdir(os.path.join(SRC, "video")): shutil.copytree(os.path.join(SRC, "video"), os.path.join(DIST, "assets/video"))
    pages = {"": home(), "city-water-filtration": city_page(), "well-water-filtration": well_page(), "reverse-osmosis": ro_page(), "compare-systems": compare_page(), "pricing": pricing_page(),
             "water-problems": problems_hub(), "service-areas": areas_hub(), "about": about_page(), "faq": faq_page(), "schedule": schedule_page(), "find-my-system": fms_page(),
             "thank-you": thank_you_page(), "booked": booked_page(), "best-price-guarantee": bpg_page(), "contact": contact_page(),
             "privacy": legal_page("privacy", "Privacy Policy", "privacy", "<p>Privacy policy content pending.</p>"), "terms": legal_page("terms", "Terms of Service", "terms", "<p>Terms content pending.</p>"),
             "accessibility": accessibility_page()}
    for p in PROBLEMS:
        if p.get("page"): pages["water-problems/" + p["id"]] = problem_page(p)
    for c in CITIES: pages["service-areas/" + c["slug"]] = city_page_for(c)
    for s in SYS["systems"]: pages["systems/" + s["id"]] = product_page(s)
    noindex = {"thank-you", "booked"}
    for slug, html_ in pages.items():
        write(("index.html" if slug == "" else slug + "/index.html"), html_)
    write("404.html", notfound_page())
    today = datetime.date.today().isoformat()
    urls = "".join("<url><loc>%s/%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>" % (BASE, (slug + "/") if slug else "", today, "weekly" if slug in ("", "pricing") else "monthly", "1.0" if slug == "" else "0.8" if "/" not in slug else "0.6") for slug in pages if slug not in noindex)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % urls)
    write("robots.txt", ("User-agent: *\nDisallow: /\n" if OPT.staging else "User-agent: *\nAllow: /\nDisallow: /thank-you/\nDisallow: /booked/\nSitemap: %s/sitemap.xml\n" % BASE))
    # Redirects for legacy Amboras routes (Netlify/Cloudflare _redirects syntax; mirror in host config if different)
    write("_redirects", "\n".join([
        "/iron-sulfur-removal  /well-water-filtration/  301", "/iron-sulfur-removal/  /well-water-filtration/  301",
        "/uv-water-purification  /well-water-filtration/#uv-purifier  301", "/uv-water-purification/  /well-water-filtration/#uv-purifier  301",
        "/products  /pricing/  301", "/products/  /pricing/  301",
        "/products/complete-home-softener-filtration-system  /systems/whole-home-softener/  301",
        "/products/dual-tank-system-for-well-water  /systems/dual-tank-well/  301",
        "/products/reverse-osmosis-system  /systems/ro-tankless/  301",
        "/home  /  301", "/services  /pricing/  301", "/privacy-policy  /privacy/  301", "/tos  /terms/  301",
        "/*  /404.html  404"]) + "\n")
    write("_headers", "/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: SAMEORIGIN\n  Referrer-Policy: strict-origin-when-cross-origin\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n")
    print("Built %d pages -> %s" % (len(pages) + 1, DIST))

if __name__ == "__main__": main()
