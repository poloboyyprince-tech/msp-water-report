import re, os, json, importlib.util
spec = importlib.util.spec_from_file_location("b", os.path.join(os.path.dirname(os.path.abspath(__file__)),"build.py"))
# build.py runs on import (writes the 12 pages) - that's fine/idempotent
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

SRC, OUT = b.SRC, b.OUT
RAW = open(f"{SRC}/pages/about.html", encoding="utf-8").read()
H0, H1 = RAW.find("<header"), RAW.find("</header>")+9
F0, F1 = RAW.find("<footer"), RAW.find("</footer>")+9
HEADER_RAW, FOOTER_RAW = RAW[H0:H1], RAW[F0:F1]

EY   = 'text-[11px] tracking-[0.35em] uppercase text-accent font-semibold mb-3'
H1C  = 'text-4xl lg:text-5xl font-heading font-bold text-foreground mb-4'
LEAD = 'text-muted-foreground text-lg max-w-2xl mx-auto'
H2C  = 'text-2xl font-heading font-bold text-foreground mb-3'
H3C  = 'font-heading font-bold text-foreground mb-1'
SUB  = 'text-xs text-muted-foreground'
BODY = 'text-muted-foreground leading-relaxed mb-4'
CARD = 'glass-card-hover rounded-xl p-5'
CTA  = 'inline-block bg-accent hover:bg-accent/90 text-accent-foreground font-heading font-semibold tracking-widest uppercase text-sm px-10 py-4 rounded-lg transition-all'
CTA2 = 'inline-block border border-accent/50 hover:bg-accent/10 text-foreground font-heading font-semibold tracking-widest uppercase text-sm px-8 py-4 rounded-lg transition-all'
WRAP = 'min-h-screen bg-background pt-36 lg:pt-72 pb-32 lg:pb-16'

def page(slug, title, desc, main):
    p = b.prefix_for(slug)
    header = b.clean(HEADER_RAW, slug); footer = b.clean(FOOTER_RAW, slug)
    links = "".join(
        f'<a href="{p}{h}.html" class="py-3 border-b border-accent/10 text-foreground hover:text-accent transition-colors font-heading tracking-widest uppercase text-sm">{t}</a>'
        for t,h in b.NAVLINKS)
    html = b.SHELL.format(title=title, desc=desc, p=p,
        core=header + main + footer,
        drawer=b.DRAWER.format(links=links, p=p), cookie=b.COOKIE)
    path = os.path.join(OUT, f"{slug}.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path,"w",encoding="utf-8").write(html)
    return slug

SYSTEMS = [("City Water Systems","city-water-filtration","Hardness, chlorine and chloramine, taste, odor and scale on city water."),
           ("Well Water Systems","well-water-filtration","Hardness, iron, sulfur odor, staining and sediment on private wells."),
           ("Drinking Water / RO","reverse-osmosis","Under-sink reverse osmosis — included free with every whole-home system.")]

INCLUDED = [("Reverse osmosis included free","A dedicated under-sink RO system comes with every whole-home system."),
            ("Transparent pricing","See system prices online before anyone comes to your home."),
            ("Best price guarantee","Bring a comparable quote on equipment and installation and we'll beat it."),
            ("Professional installation","Equipment is connected to your home water line and configured for your water."),
            ("Online scheduling","Reserve a 10–12 AM or 2–4 PM arrival window online."),
            ("Systems matched to your water","City and well water are treated differently — you get the right approach.")]

STEPS = [("01","Choose Your System","Start with City Water or Well Water and compare transparent pricing."),
         ("02","Schedule Online","Pick an available date and a 10–12 AM or 2–4 PM arrival window."),
         ("03","We Install","Your equipment is connected to the appropriate water line and configured."),
         ("04","Enjoy the Difference","Your home's water runs through treatment before reaching your fixtures.")]

def city_main(slug, city, desc, p):
    cards = "".join(f'<a href="{p}{h}.html" class="{CARD} block"><h2 class="{H3C}">{t}</h2><p class="{SUB}">{d}</p></a>' for t,h,d in SYSTEMS)
    inc = "".join(f'<div class="{CARD}"><h3 class="{H3C}">{t}</h3><p class="{SUB}">{d}</p></div>' for t,d in INCLUDED)
    steps = "".join(f'<div class="{CARD}"><p class="text-accent font-heading text-2xl mb-2">{n}</p><h3 class="{H3C}">{t}</h3><p class="{SUB}">{d}</p></div>' for n,t,d in STEPS)
    return f'''<main class="min-h-screen"><div class="{WRAP}"><div class="container-custom max-w-5xl">
<div class="text-center mb-14"><p class="{EY}">Service Area</p>
<h1 class="{H1C}">Water Filtration in {city}, MN</h1>
<p class="{LEAD}">{desc} Whole-home filtration, softening, and reverse osmosis installed by MSP Pure Water — with transparent pricing and online scheduling.</p>
<p class="text-muted-foreground text-sm mt-3">Serving {city} and the surrounding Twin Cities metro. Travel fees may apply beyond 35 miles from Minneapolis.</p></div>
<p class="text-center text-[11px] tracking-[0.3em] uppercase text-muted-foreground/70 mb-6">Systems we install in {city}</p>
<div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-16">{cards}</div>
<h2 class="{H2C} text-center">What every {city} installation includes</h2>
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-16">{inc}</div>
<h2 class="{H2C} text-center">How it works</h2>
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-16">{steps}</div>
<div class="text-center"><h2 class="{H2C}">Ready for better water in {city}?</h2>
<p class="{LEAD} mb-8">See transparent pricing first, then reserve an installation window online.</p>
<div class="flex flex-wrap gap-4 justify-center"><a href="{p}schedule.html" class="{CTA}">Schedule Online</a><a href="{p}pricing.html" class="{CTA2}">See Pricing</a></div>
<p class="text-muted-foreground text-sm mt-8">Or call or text <a href="tel:9529526206" class="text-accent">952-952-6206</a></p>
<p class="mt-10"><a href="{p}service-areas.html" class="text-xs tracking-[0.25em] uppercase text-muted-foreground/70 hover:text-accent transition-colors">&#8592; All service areas</a></p></div>
</div></div></main>'''

built=[]
cities = json.load(open(f"{SRC}/cities.json"))
for slug, c in cities.items():
    s=f"service-areas/{slug}"; p=b.prefix_for(s)
    built.append(page(s, f"Water Filtration {c['city']} MN | Softening & RO | MSP Pure Water",
        f"{c['desc']} Whole-home water filtration, softening and reverse osmosis installation in {c['city']}, Minnesota. Transparent pricing and online scheduling.",
        city_main(slug, c['city'], c['desc'], p)))

# ---- UV purification -------------------------------------------------------
UVF=[("Inactivates bacteria and viruses","UV light disrupts the DNA of microorganisms so they cannot reproduce or cause illness."),
     ("No chemicals, no taste change","UV adds nothing to the water — no chlorine, no aftertaste, no by-products."),
     ("Continuous treatment","Water is treated as it passes the lamp, whenever a fixture is opened."),
     ("Best paired with pre-filtration","UV needs clear water. Sediment, iron and hardness are treated upstream so light reaches the water."),
     ("Common on private wells","Wells are not disinfected by a municipality, so UV is a frequent final stage on well systems."),
     ("Annual lamp replacement","The lamp is replaced about once a year to keep output at full strength.")]
uv_cards="".join(f'<div class="{CARD}"><h3 class="{H3C}">{t}</h3><p class="{SUB}">{d}</p></div>' for t,d in UVF)
uv_main=f'''<main class="min-h-screen"><div class="{WRAP}"><div class="container-custom max-w-4xl">
<div class="text-center mb-14"><p class="{EY}">Whole-Home Treatment</p>
<h1 class="{H1C}">UV Water Purification</h1>
<p class="{LEAD}">Ultraviolet purification is the final stage on many well-water systems — it inactivates bacteria and viruses without adding a single chemical to your water.</p></div>
<h2 class="{H2C}">How UV purification works</h2>
<p class="{BODY}">Water passes through a chamber containing an ultraviolet lamp. The UV light penetrates microorganisms and disrupts their DNA, so bacteria and viruses can no longer reproduce or cause infection. Nothing is added to the water and nothing is left behind — the water tastes exactly the same going out as it did coming in.</p>
<p class="{BODY}">Because UV works with light, the water has to be clear for it to be effective. Sediment, iron, and hardness are handled by filtration and softening upstream, so the UV lamp gets a clean, clear stream to treat. UV does not remove sediment, dissolved minerals, or chemical contaminants — it is a disinfection stage, not a replacement for filtration.</p>
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 my-12">{uv_cards}</div>
<h2 class="{H2C}">Is UV right for your home?</h2>
<p class="{BODY}">UV is most common on private wells, which are not disinfected by a municipal utility. If your water has tested positive for coliform bacteria, or you simply want a final barrier on a well system, UV is the standard solution. On city water, the municipality already disinfects, so UV is usually unnecessary — carbon filtration for chlorine and chloramine is the more relevant stage.</p>
<p class="{BODY}">We'll look at your water and tell you honestly whether UV belongs on your system.</p>
<div class="text-center mt-14"><div class="flex flex-wrap gap-4 justify-center"><a href="schedule.html" class="{CTA}">Schedule Online</a><a href="well-water-filtration.html" class="{CTA2}">Well Water Systems</a></div>
<p class="text-muted-foreground text-sm mt-8">Questions? Call or text <a href="tel:9529526206" class="text-accent">952-952-6206</a></p></div>
</div></div></main>'''
built.append(page("uv-water-purification","UV Water Purification Systems Twin Cities MN | MSP Pure Water",
 "Ultraviolet water purification for Twin Cities homes and private wells. Chemical-free disinfection that inactivates bacteria and viruses. Transparent pricing.", uv_main))

# ---- Accessibility ---------------------------------------------------------
acc_main=f'''<main class="min-h-screen"><div class="{WRAP}"><div class="container-custom max-w-3xl">
<div class="mb-12"><p class="{EY}">Commitment</p><h1 class="{H1C}">Accessibility Statement</h1>
<p class="text-muted-foreground text-lg">MSP Pure Water is committed to making this website usable by everyone, including people who use assistive technology.</p></div>
<h2 class="{H2C}">Our goal</h2>
<p class="{BODY}">We aim to meet the Web Content Accessibility Guidelines (WCAG) 2.1 at Level AA. These guidelines explain how to make web content more accessible to people with visual, hearing, motor, and cognitive disabilities.</p>
<h2 class="{H2C}">What we do</h2>
<p class="{BODY}">We work to provide meaningful text alternatives for images, sufficient colour contrast between text and background, keyboard access to interactive elements such as menus and expandable questions, clear and consistent page structure with proper headings, and a layout that adapts to phones, tablets, and desktop screens.</p>
<h2 class="{H2C}">Ongoing work</h2>
<p class="{BODY}">Accessibility is not a one-time project. We review the site as we add pages and features, and we correct issues as we find them. Some older content may not yet meet every guideline.</p>
<h2 class="{H2C}">Tell us about a problem</h2>
<p class="{BODY}">If you have trouble using any part of this site, we want to hear about it. Call or text us at <a href="tel:9529526206" class="text-accent">952-952-6206</a> and describe the page and the problem. We will help you get the information you need and work to fix the issue.</p>
<p class="{BODY}">If you would rather not use the website at all, that is completely fine — call or text and we will walk you through systems, pricing, and scheduling directly.</p>
<div class="text-center mt-14"><a href="schedule.html" class="{CTA}">Schedule Online</a></div>
</div></div></main>'''
built.append(page("accessibility","Accessibility Statement | MSP Pure Water",
 "MSP Pure Water's commitment to an accessible website, our WCAG 2.1 AA goal, and how to report an accessibility problem.", acc_main))

print(f"{len(built)} new pages generated")
