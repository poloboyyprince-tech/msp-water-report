import re, os, shutil, urllib.parse, glob

SRC = os.path.dirname(os.path.abspath(__file__))
OUT = "/Users/princeonyemeh-sea/Claude/Water Report/msp-pure-water-site"

REAL = {  # slug -> mirrored file
 "":"home","about":"about","city-water-filtration":"city-water-filtration","faq":"faq",
 "iron-sulfur-removal":"iron-sulfur-removal","pricing":"pricing","privacy":"privacy",
 "reverse-osmosis":"reverse-osmosis","schedule":"schedule","service-areas":"service-areas",
 "terms":"terms","well-water-filtration":"well-water-filtration",
 "contact":"contact","products":"products",
 "products/complete-home-softener-filtration-system":"products_complete-home-softener-filtration-system",
 "products/dual-tank-system-for-well-water":"products_dual-tank-system-for-well-water",
 "products/reverse-osmosis-system":"products_reverse-osmosis-system",
}

def slug_to_path(slug):
    return "index.html" if slug=="" else f"{slug}.html" if "/" not in slug else f"{slug}.html"

def prefix_for(slug):
    return "../" * slug.count("/")

def rewrite_links(html, slug):
    p = prefix_for(slug)
    def repl(m):
        href = m.group(1)
        if href.startswith(("http","tel:","mailto:","#")): return m.group(0)
        frag = query = ""
        if "#" in href: href, frag = href.split("#",1); frag = "#"+frag
        if "?" in href: href, query = href.split("?",1); query = "?"+query
        h = href.strip("/")
        target = "index.html" if h=="" else f"{h}.html"
        return f'href="{p}{target}{query}{frag}"'
    return re.sub(r'href="(/[^"]*|/)"', repl, html)

def rewrite_images(html, slug):
    p = prefix_for(slug)
    # srcset entries and src attrs pointing at /_next/image?url=...
    def one(m):
        raw = m.group(0)
        u = re.search(r'url=([^&"\s]+)', raw)
        if not u: return raw
        dec = urllib.parse.unquote(urllib.parse.unquote(u.group(1)))
        ident = dec.rsplit("/",1)[-1]
        return f"{p}assets/img/{ident}"
    html = re.sub(r'/_next/image\?url=[^"\s]+', one, html)
    # collapse now-identical srcset candidates -> keep plain src only
    html = re.sub(r'\s+(?:image)?[sS]rcSet="[^"]*"', '', html)
    html = re.sub(r'\s+imageSizes="[^"]*"', '', html)
    return html

def clean(html, slug):
    html = rewrite_images(html, slug)
    html = rewrite_links(html, slug)
    html = re.sub(r'\s+(?:data-precedence|fetchPriority|decoding)="[^"]*"', '', html)
    return html

def extract(fname, slug):
    s = open(os.path.join(SRC,"pages",fname+".html"), encoding="utf-8").read()
    t = re.search(r"<title>(.*?)</title>", s)
    d = re.search(r'name="description" content="(.*?)"', s)
    i, j = s.find("<header"), s.find("</footer>")
    core = s[i:j+9] if i!=-1 and j!=-1 else ""
    return (t.group(1) if t else "MSP Pure Water",
            d.group(1) if d else "", clean(core, slug))

EXTRA_CSS = """

/* ------------------------------------------------------------------ *
 * Utilities used by the static recreation that were not present in    *
 * the original compiled Tailwind build (it only emitted classes the   *
 * original markup used). Without these the mobile drawer backdrop is  *
 * transparent and has no width, which overlays the page.              *
 * ------------------------------------------------------------------ */
.duration-400 { transition-duration: 400ms; }
.z-\\[100\\] { z-index: 100; }
.z-\\[110\\] { z-index: 110; }
.bg-black\\/70 { background-color: rgb(0 0 0 / 0.7); }
.w-\\[86\\%\\] { width: 86%; }
.border-l { border-left-width: 1px; border-left-style: solid; }
.pb-10 { padding-bottom: 2.5rem; }
.bottom-4 { bottom: 1rem; }
.max-h-full { max-height: 100%; }
.my-12 { margin-top: 3rem; margin-bottom: 3rem; }
.bg-card { background-color: hsl(var(--background)); }
@media (min-width: 640px) {
  .sm\\:w-\\[380px\\] { width: 380px; }
}
"""

SHELL = """<!DOCTYPE html>
<html lang="en" class="cinzel_678e8667-module__0ZDGPG__variable josefin_sans_fddc297d-module__ZAnm5a__variable">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<meta name="description" content="{desc}"/>
<link rel="stylesheet" href="{p}assets/site.css"/>
<link rel="icon" href="{p}assets/img/01KZECZB5BP4J74H0CP611B03K.webp"/>
</head>
<body>
{core}
{drawer}
{cookie}
<script src="{p}assets/site.js" defer></script>
</body>
</html>
"""

DRAWER = """<div id="mobile-drawer" class="fixed inset-0 z-[100] hidden">
  <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" data-drawer-close></div>
  <nav class="absolute right-0 top-0 h-full w-[86%] max-w-sm bg-background border-l border-accent/25 overflow-y-auto animate-slide-in-right">
    <div class="flex items-center justify-between px-6 h-20 border-b border-accent/20">
      <span class="font-heading tracking-[0.2em] text-accent text-sm uppercase">Menu</span>
      <button class="w-10 h-10 rounded-lg border border-accent/50 text-accent" aria-label="Close menu" data-drawer-close>&#10005;</button>
    </div>
    <div class="px-6 py-6 flex flex-col gap-1">{links}</div>
    <div class="px-6 pb-10 pt-4 border-t border-accent/20 mt-4">
      <a href="tel:9529526206" class="block text-accent font-heading tracking-widest text-lg">952-952-6206</a>
      <a href="{p}schedule.html" class="mt-4 block text-center bg-accent text-accent-foreground font-heading font-semibold tracking-widest uppercase text-sm px-6 py-4 rounded-lg">Schedule Online</a>
    </div>
  </nav>
</div>"""

NAVLINKS = [("City Water Systems","city-water-filtration"),("Well Water Systems","well-water-filtration"),
 ("Reverse Osmosis","reverse-osmosis"),("Iron &amp; Sulfur Removal","iron-sulfur-removal"),
 ("UV Purification","uv-water-purification"),("Pricing","pricing"),("Service Areas","service-areas"),
 ("About","about"),("FAQ","faq")]

COOKIE = """<div id="cookie-banner" class="fixed bottom-4 right-4 left-4 sm:left-auto sm:w-[380px] z-[110] hidden">
  <div class="bg-card border border-accent/30 rounded-xl p-5 shadow-2xl">
    <p class="font-heading text-foreground text-sm mb-2">We value your privacy</p>
    <p class="text-xs text-muted-foreground leading-relaxed mb-4">We use cookies to understand how visitors interact with our store. No personal data is shared with third parties.</p>
    <div class="flex gap-2">
      <button data-cookie="accept" class="flex-1 bg-accent text-accent-foreground text-xs font-semibold tracking-widest uppercase py-2.5 rounded-lg">Accept</button>
      <button data-cookie="decline" class="flex-1 border border-accent/40 text-foreground text-xs font-semibold tracking-widest uppercase py-2.5 rounded-lg">Decline</button>
    </div>
  </div>
</div>"""

def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(f"{OUT}/assets/img", exist_ok=True)
    os.makedirs(f"{OUT}/assets/fonts", exist_ok=True)
    for f in glob.glob(f"{SRC}/assets/img/*.webp"): shutil.copy(f, f"{OUT}/assets/img/")
    for f in glob.glob(f"{SRC}/assets/fonts/*.woff2"): shutil.copy(f, f"{OUT}/assets/fonts/")
    if os.path.exists(f"{SRC}/site.js"): shutil.copy(f"{SRC}/site.js", f"{OUT}/assets/site.js")

    css = open(f"{SRC}/app.css", encoding="utf-8").read()
    css = re.sub(r'url\("\.\./media/([^"]+)"\)', r'url("fonts/\1")', css)
    open(f"{OUT}/assets/site.css","w",encoding="utf-8").write(css + EXTRA_CSS)

    built = []
    for slug, fname in REAL.items():
        title, desc, core = extract(fname, slug)
        p = prefix_for(slug)
        links = "".join(
            f'<a href="{p}{h}.html" class="py-3 border-b border-accent/10 text-foreground hover:text-accent transition-colors font-heading tracking-widest uppercase text-sm">{t}</a>'
            for t,h in NAVLINKS)
        out = SHELL.format(title=title, desc=desc, core=core, p=p,
                           drawer=DRAWER.format(links=links,p=p), cookie=COOKIE)
        path = os.path.join(OUT, slug_to_path(slug))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path,"w",encoding="utf-8").write(out)
        built.append((slug or "/", len(out)))

    for s,n in built: print(f"  {s:28} {n:>7,} bytes")
    print(f"\n{len(built)} existing pages converted")


if __name__ == "__main__":
    main()
