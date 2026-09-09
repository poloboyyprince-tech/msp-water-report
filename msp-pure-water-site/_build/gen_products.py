import re, os, json, html, importlib.util
spec=importlib.util.spec_from_file_location("b",os.path.join(os.path.dirname(os.path.abspath(__file__)),"build.py"))
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
SRC,OUT=b.SRC,b.OUT
cat=json.load(open(f"{SRC}/catalog.json")); asp=json.load(open(f"{SRC}/aspects.json"))
RAW=open(f"{SRC}/pages/about.html",encoding="utf-8").read()
HEADER_RAW=RAW[RAW.find("<header"):RAW.find("</header>")+9]
FOOTER_RAW=RAW[RAW.find("<footer"):RAW.find("</footer>")+9]

NSF=('<svg viewBox="0 0 64 64" class="w-7 h-7 flex-shrink-0" role="img" aria-label="NSF Certified">'
 '<circle cx="32" cy="32" r="31" fill="hsl(var(--nsf))"></circle>'
 '<circle cx="32" cy="32" r="27.5" fill="none" stroke="hsl(var(--nsf-foreground))" stroke-width="1.6"></circle>'
 '<text x="32" y="38.5" text-anchor="middle" fill="hsl(var(--nsf-foreground))" font-family="Arial, Helvetica, sans-serif" font-weight="800" font-size="19" letter-spacing="0.5">NSF</text></svg>')
TRUST=[("Best Price Guarantee",'<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"></path>'),
 ("Professional Install",'<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"></path>'),
 ("NSF Certified Components",None),
 ("Lifetime Warranty",'<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"></path><path d="m9 12 2 2 4-4"></path>')]
def icon(p): return ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
  'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5" aria-hidden="true">'+p+'</svg>')
CHEV=('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-muted-foreground transition-transform duration-200" aria-hidden="true"><path d="m6 9 6 6 6-6"></path></svg>')

SYS={"reverse-osmosis-system":"tankRO","complete-home-softener-filtration-system":"standard","dual-tank-system-for-well-water":"dualWell"}

def acc(title, inner, open_=False):
    return (f'<div class="border-b last:border-0"><button class="flex w-full items-center justify-between py-4 text-left">'
            f'<span class="text-sm font-medium">{title}</span>{CHEV}</button>'
            f'<div class="overflow-hidden transition-all duration-200 max-h-0">'
            f'<div class="text-sm text-muted-foreground leading-relaxed pb-4">{inner}</div></div></div>')

INSTALL=('<ul class="space-y-2"><li>Professionally installed by MSP Pure Water — nothing is shipped to you</li>'
 '<li>Pick your install date and arrival window when you schedule</li>'
 '<li>Your included reverse osmosis system (tank or tankless) is confirmed before install day</li>'
 '<li>Serving Minneapolis, St. Paul &amp; Greater Minnesota — call 952-952-6206 with any questions</li></ul>')
WARRANTY=('<ul class="space-y-2"><li>Lifetime warranty on the system</li><li>NSF-certified media</li>'
 '<li>Best Price Guarantee — find a lower quote on a comparable system and we’ll beat it</li></ul>')

def product_main(handle, p, a, pre=''):
    img=a['image']; alt=html.escape(a['alt'] or p['title'])
    price=p['price']; sysq=SYS.get(handle,'standard')
    # option selectors
    opts=""
    for oi,o in enumerate(p['options']):
        vals="".join(
            f'<button type="button" data-opt="{oi}" data-val="{html.escape(v)}" class="variant-btn min-w-[48px] px-4 py-2.5 text-sm border rounded-md transition-all '
            +('border-accent bg-accent text-accent-foreground font-semibold' if vi==0 else 'border-border hover:border-accent/60')+f'">{html.escape(v)}</button>'
            for vi,v in enumerate(o['values']))
        opts+=(f'<div><h3 class="text-xs uppercase tracking-widest font-semibold mb-3">{html.escape(o["title"])}'
               f'<span class="ml-2 normal-case tracking-normal font-normal text-muted-foreground">&#8212; <span data-optlabel="{oi}">{html.escape(o["values"][0])}</span></span></h3>'
               f'<div class="flex flex-wrap gap-2">{vals}</div></div>')
    trust="".join(
        f'<div class="text-center"><span class="flex h-7 items-center justify-center mb-1.5">{NSF if pth is None else icon(pth)}</span>'
        f'<p class="text-xs text-muted-foreground">{lbl}</p></div>' for lbl,pth in TRUST)
    accs=""
    if len(re.sub(r'<[^>]+>','',p['description']).strip())>0:
        accs+=acc("Description",p['description'])
    accs+=acc("Installation &amp; Scheduling",INSTALL)+acc("Warranty &amp; Guarantee",WARRANTY)
    # inside the system
    aspects=""
    for x in a['aspects']:
        stats="".join(f'<div><p class="text-[10px] tracking-[0.2em] uppercase text-muted-foreground/70">{html.escape(l)}</p>'
                      f'<p class="font-heading font-bold text-foreground">{html.escape(v)}</p></div>' for l,v in x['stats'])
        aspects+=(f'<div class="glass-card-hover rounded-xl p-6"><p class="text-[10px] tracking-[0.3em] uppercase text-accent font-semibold mb-2">{html.escape(x["kicker"])}</p>'
          f'<p class="text-xs text-muted-foreground/60 line-through mb-1">{html.escape(x["crossed"])}</p>'
          f'<h3 class="text-xl font-heading font-bold text-foreground mb-3">{html.escape(x["headline"])}</h3>'
          f'<p class="text-sm text-muted-foreground leading-relaxed mb-4">{html.escape(x["body"])}</p>'
          f'<div class="grid grid-cols-2 gap-3 pt-3 border-t border-accent/15">{stats}</div></div>')
    vmap=json.dumps({v['title']:v['price'] for v in p['variants']})
    return f'''<main class="min-h-screen"><div class="border-b pt-36 lg:pt-72"><div class="container-custom py-3">
<nav class="flex items-center gap-2 text-xs text-muted-foreground"><a class="hover:text-foreground transition-colors" href="{pre}index.html">Home</a>
<span>&#8250;</span><a class="hover:text-foreground transition-colors" href="{pre}products.html">Shop</a><span>&#8250;</span>
<span class="text-foreground">{html.escape(p['title'])}</span></nav></div></div>
<div class="container-custom py-8 lg:py-12" data-variants='{vmap}'>
<div class="grid gap-10 lg:gap-16 md:grid-cols-[2fr_3fr]">
<div class="md:sticky md:top-40 md:self-start"><div class="relative w-full max-w-md mx-auto aspect-[3/4]">
<img alt="{alt}" class="object-contain w-full h-full" src="{pre}assets/img/{img}"/></div></div>
<div class="md:sticky md:top-24 md:self-start space-y-6">
<div><h1 class="text-h2 font-heading font-semibold">{html.escape(p['title'])}</h1>
<div class="flex flex-wrap items-center gap-2.5 mt-4"><p class="inline-flex items-center gap-2.5 text-[10px] tracking-[0.25em] uppercase text-foreground/80 font-semibold border border-accent/30 bg-accent/5 rounded-full pl-1.5 pr-4 min-h-[40px] py-1">{NSF}Every component NSF certified</p></div></div>
<div class="space-y-6"><div><p class="text-3xl font-heading font-bold text-accent" data-price>{price}</p>
<p class="text-xs text-muted-foreground mt-1 uppercase tracking-widest">Professional installation included</p></div>
{opts}
<div class="space-y-4"><a class="w-full flex items-center justify-center text-center bg-accent hover:bg-accent/90 text-accent-foreground text-sm font-semibold tracking-widest uppercase py-4 px-6 rounded-lg transition-all duration-300" href="{pre}schedule.html?system={sysq}">Schedule Online</a>
<p class="text-center text-sm text-muted-foreground">or call or text <a href="tel:9529526206" class="text-accent font-semibold hover:underline">952-952-6206</a></p></div>
<p class="text-sm text-foreground/70 leading-relaxed text-center">We&#8217;ll confirm your selections and every detail before your install date.</p></div>
<div class="grid grid-cols-2 sm:grid-cols-4 gap-4 py-6 border-t">{trust}</div>
<div class="border-t">{accs}</div></div></div></div>
<section class="relative overflow-hidden border-t border-accent/15 bg-[#060d1f]"><div class="pointer-events-none absolute inset-0">
<div class="absolute -top-32 left-1/4 w-[500px] h-[500px] rounded-full bg-accent/10 blur-[140px]"></div>
<div class="absolute bottom-0 right-0 w-[400px] h-[400px] rounded-full bg-[hsl(220,80%,30%)]/25 blur-[120px]"></div></div>
<div class="container-custom relative pt-8 pb-16 lg:pt-10 lg:pb-24">
<p class="text-[10px] tracking-[0.3em] uppercase text-accent font-semibold text-center mb-2">What We Use &amp; Why It Matters</p>
<h2 class="text-2xl lg:text-4xl font-heading font-bold text-center text-foreground mb-8">Inside The System</h2>
<div class="grid grid-cols-1 md:grid-cols-2 gap-5">{aspects}</div></div></section></main>'''

def write(slug,title,desc,main):
    p=b.prefix_for(slug)
    links="".join(f'<a href="{p}{h}.html" class="py-3 border-b border-accent/10 text-foreground hover:text-accent transition-colors font-heading tracking-widest uppercase text-sm">{t}</a>' for t,h in b.NAVLINKS)
    out=b.SHELL.format(title=title,desc=desc,p=p,core=b.clean(HEADER_RAW,slug)+main+b.clean(FOOTER_RAW,slug),
                       drawer=b.DRAWER.format(links=links,p=p),cookie=b.COOKIE)
    path=os.path.join(OUT,f"{slug}.html"); os.makedirs(os.path.dirname(path),exist_ok=True)
    open(path,"w",encoding="utf-8").write(out)

n=0
for h,p in cat.items():
    a=asp.get(h,{'image':'01KZEG7K6BWVXTG1WGHKGGH5MF.webp','alt':p['title'],'aspects':[]})
    plain=re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',p['description'])).strip()
    h_slug=f"products/{h}"
    write(h_slug,f"{p['title']} — {p['price']} | MSP Pure Water",
          (plain[:155] if plain else f"{p['title']} from MSP Pure Water — {p['price']}, professional installation included. NSF certified, lifetime warranty, Twin Cities."),
          product_main(h,p,a,b.prefix_for(h_slug))); n+=1

cards="".join(
 f'<a href="products/{h}.html" class="glass-card-hover rounded-xl p-6 block"><div class="aspect-[3/4] mb-5 flex items-center justify-center">'
 f'<img src="assets/img/{asp.get(h,{}).get("image","01KZEG7K6BWVXTG1WGHKGGH5MF.webp")}" alt="{html.escape(cat[h]["title"])}" class="object-contain max-h-full"/></div>'
 f'<h2 class="font-heading font-bold text-foreground mb-1">{html.escape(cat[h]["title"])}</h2>'
 f'<p class="text-2xl font-heading font-bold text-accent mb-1">{cat[h]["price"]}</p>'
 f'<p class="text-xs text-muted-foreground">Professional installation included</p></a>'
 for h in ["complete-home-softener-filtration-system","dual-tank-system-for-well-water","reverse-osmosis-system"])
write("products","Shop Water Filtration Systems — Transparent Pricing | MSP Pure Water",
 "Whole-home water softening and filtration, dual-tank well water systems, and reverse osmosis. Transparent pricing with professional installation included.",
 f'''<main class="min-h-screen"><div class="min-h-screen bg-background pt-36 lg:pt-72 pb-32 lg:pb-16"><div class="container-custom max-w-5xl">
<div class="text-center mb-14"><p class="text-[11px] tracking-[0.35em] uppercase text-accent font-semibold mb-3">Shop</p>
<h1 class="text-4xl lg:text-5xl font-heading font-bold text-foreground mb-4">Systems &amp; Transparent Pricing</h1>
<p class="text-muted-foreground text-lg max-w-2xl mx-auto">Every price includes professional installation. Reverse osmosis is included free with every whole-home system.</p></div>
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">{cards}</div>
<div class="text-center mt-14"><a href="schedule.html" class="inline-block bg-accent hover:bg-accent/90 text-accent-foreground font-heading font-semibold tracking-widest uppercase text-sm px-10 py-4 rounded-lg transition-all">Schedule Online</a></div>
</div></div></main>'''); n+=1
print(f"{n} product pages rebuilt with real content")
