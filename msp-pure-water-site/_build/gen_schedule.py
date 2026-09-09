import os, json, importlib.util
spec=importlib.util.spec_from_file_location("b",os.path.join(os.path.dirname(os.path.abspath(__file__)),"build.py"))
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
OUT=b.OUT
RAW=open(f"{b.SRC}/pages/about.html",encoding="utf-8").read()
HEADER=b.clean(RAW[RAW.find("<header"):RAW.find("</header>")+9],"schedule")
FOOTER=b.clean(RAW[RAW.find("<footer"):RAW.find("</footer>")+9],"schedule")

SYSTEMS={
 "city":[("Whole Home Water Filtration and Softening System","$2,999"),
         ("Dual Tank Whole Home Water Filtration System","$3,999"),
         ("Whole Home Complete Salt-Free Filtration System","$4,499"),
         ("Tank RO Only","$799"),("Tankless RO Only","$799")],
 "well":[("Dual Tank Well Water Whole Home Filtration System","$4,499"),
         ("Iron and Sulfur Treatment System","$5,999"),
         ("Tank RO Only","$799"),("Tankless RO Only","$799")]}
CARD='glass-card-hover rounded-xl p-5 text-left w-full'
main=f'''<main class="min-h-screen"><div class="min-h-screen bg-background pt-36 lg:pt-72 pb-32 lg:pb-16">
<div class="container-custom max-w-3xl">
<div class="text-center mb-10"><p class="text-[11px] tracking-[0.35em] uppercase text-accent font-semibold mb-3">MSP Pure Water</p>
<h1 class="text-4xl lg:text-5xl font-heading font-bold text-foreground mb-4">Schedule Your Installation</h1>
<p class="text-muted-foreground text-lg">No deposit required. Select a system, pick a time, and we will confirm.</p></div>

<ol id="sched-steps" class="flex items-center justify-center gap-2 mb-10 text-[10px] tracking-[0.2em] uppercase"></ol>

<section data-step="1"><h2 class="text-xl font-heading font-bold text-foreground mb-5 text-center">What type of water do you have?</h2>
<div class="grid sm:grid-cols-2 gap-4">
<button type="button" class="{CARD}" data-water="city"><h3 class="font-heading font-bold text-foreground mb-1">City Water</h3><p class="text-xs text-muted-foreground">Municipal / treated water supply</p></button>
<button type="button" class="{CARD}" data-water="well"><h3 class="font-heading font-bold text-foreground mb-1">Well Water</h3><p class="text-xs text-muted-foreground">Private well on your property</p></button>
</div></section>

<section data-step="2" hidden><h2 class="text-xl font-heading font-bold text-foreground mb-5 text-center">Choose your system</h2>
<div id="sys-list" class="grid gap-3"></div>
<button type="button" data-back="1" class="mt-6 text-xs tracking-[0.25em] uppercase text-muted-foreground hover:text-accent transition-colors">&#8592; Back</button></section>

<section data-step="3" hidden><h2 class="text-xl font-heading font-bold text-foreground mb-5 text-center">Pick a date and arrival window</h2>
<div class="glass-card-hover rounded-xl p-6 space-y-5">
<label class="block"><span class="text-xs uppercase tracking-widest font-semibold text-foreground">Preferred date</span>
<input type="date" id="sched-date" class="mt-2 w-full bg-transparent border border-accent/30 rounded-lg px-4 py-3 text-foreground"/></label>
<div><span class="text-xs uppercase tracking-widest font-semibold text-foreground">Arrival window</span>
<div class="flex flex-wrap gap-2 mt-2">
<button type="button" class="win-btn px-4 py-2.5 text-sm border border-border rounded-md hover:border-accent/60 transition-all" data-window="10–12 AM">10–12 AM</button>
<button type="button" class="win-btn px-4 py-2.5 text-sm border border-border rounded-md hover:border-accent/60 transition-all" data-window="2–4 PM">2–4 PM</button>
</div></div></div>
<div class="flex gap-3 mt-6"><button type="button" data-back="2" class="text-xs tracking-[0.25em] uppercase text-muted-foreground hover:text-accent transition-colors">&#8592; Back</button>
<button type="button" id="to-4" class="ml-auto bg-accent hover:bg-accent/90 text-accent-foreground text-sm font-semibold tracking-widest uppercase px-8 py-3 rounded-lg transition-all">Continue</button></div></section>

<section data-step="4" hidden><h2 class="text-xl font-heading font-bold text-foreground mb-5 text-center">Your details</h2>
<div class="glass-card-hover rounded-xl p-6 grid gap-4">
<label class="block"><span class="text-xs uppercase tracking-widest font-semibold text-foreground">Name</span><input id="f-name" class="mt-2 w-full bg-transparent border border-accent/30 rounded-lg px-4 py-3 text-foreground"/></label>
<label class="block"><span class="text-xs uppercase tracking-widest font-semibold text-foreground">Phone</span><input id="f-phone" type="tel" class="mt-2 w-full bg-transparent border border-accent/30 rounded-lg px-4 py-3 text-foreground"/></label>
<label class="block"><span class="text-xs uppercase tracking-widest font-semibold text-foreground">Service address</span><input id="f-addr" class="mt-2 w-full bg-transparent border border-accent/30 rounded-lg px-4 py-3 text-foreground"/></label>
</div>
<div class="flex gap-3 mt-6"><button type="button" data-back="3" class="text-xs tracking-[0.25em] uppercase text-muted-foreground hover:text-accent transition-colors">&#8592; Back</button>
<button type="button" id="to-5" class="ml-auto bg-accent hover:bg-accent/90 text-accent-foreground text-sm font-semibold tracking-widest uppercase px-8 py-3 rounded-lg transition-all">Review request</button></div></section>

<section data-step="5" hidden><h2 class="text-xl font-heading font-bold text-foreground mb-5 text-center">Confirm your request</h2>
<div class="glass-card-hover rounded-xl p-6"><dl id="summary" class="grid gap-3 text-sm"></dl></div>
<div class="glass-card-hover rounded-xl p-6 mt-4 text-center">
<p class="text-sm text-muted-foreground mb-4">Send your request and we&#8217;ll confirm your window.</p>
<div class="flex flex-wrap gap-3 justify-center">
<a id="send-sms" href="#" class="bg-accent hover:bg-accent/90 text-accent-foreground text-sm font-semibold tracking-widest uppercase px-8 py-4 rounded-lg transition-all">Text this request</a>
<a id="send-mail" href="#" class="border border-accent/50 hover:bg-accent/10 text-foreground text-sm font-semibold tracking-widest uppercase px-8 py-4 rounded-lg transition-all">Email this request</a></div>
<p class="text-sm text-muted-foreground mt-6">Or call <a href="tel:9529526206" class="text-accent font-semibold">952-952-6206</a></p></div>
<button type="button" data-back="4" class="mt-6 text-xs tracking-[0.25em] uppercase text-muted-foreground hover:text-accent transition-colors">&#8592; Back</button></section>

<p class="text-center text-sm text-muted-foreground mt-10">Questions? Call <a href="tel:9529526206" class="text-accent">952-952-6206</a></p>
</div></div>
<script id="sched-data" type="application/json">{json.dumps(SYSTEMS)}</script></main>'''

links="".join(f'<a href="{h}.html" class="py-3 border-b border-accent/10 text-foreground hover:text-accent transition-colors font-heading tracking-widest uppercase text-sm">{t}</a>' for t,h in b.NAVLINKS)
out=b.SHELL.format(title="Schedule Your Installation | MSP Pure Water",
 desc="Book your whole-home water filtration or reverse osmosis installation. Pick your system, date, and a 10–12 AM or 2–4 PM arrival window.",
 p="",core=HEADER+main+FOOTER,drawer=b.DRAWER.format(links=links,p=""),cookie=b.COOKIE)
open(os.path.join(OUT,"schedule.html"),"w",encoding="utf-8").write(out)
print("schedule.html rebuilt:",len(out),"bytes")
