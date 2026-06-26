#!/usr/bin/env python3
"""Static-site generator for the MSP Pure Water educational report.

Reuses the exact (tested) report logic in water_report/ to pre-render one fast
HTML page per Twin Cities city, plus a landing page with a city/ZIP search.
Output is pure static files in docs/ — host on any CDN (GitHub Pages, Render
static, Netlify…). No server, no cold start, free, instant.

Run:  python3 build_static.py
"""
import html
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from water_report import knowledge_base as kb

# Custom domain for GitHub Pages (written to docs/CNAME so it survives rebuilds).
CUSTOM_DOMAIN = "reports.msppurewaterco.com"
DOCS = os.path.join(HERE, "docs")
REPORTS = os.path.join(DOCS, "reports")
os.makedirs(REPORTS, exist_ok=True)
# Copy the brand logo into the published site so rebuilds always carry it.
_logo_src = os.path.join(HERE, "assets", "logo.png")
if os.path.exists(_logo_src):
    os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
    shutil.copyfile(_logo_src, os.path.join(DOCS, "assets", "logo.png"))
CONFIG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
CO = CONFIG["company"]

# Brand site + phone, used to make the report's header/footer match msppurewaterco.com.
SITE = "https://msppurewaterco.com"
PHONE_DIGITS = re.sub(r"[^0-9]", "", CO["phone"])
PHONE_FMT = (f"({PHONE_DIGITS[0:3]}) {PHONE_DIGITS[3:6]} {PHONE_DIGITS[6:10]}"
             if len(PHONE_DIGITS) == 10 else CO["phone"])
PHONE_ICON = ('<svg class="pico" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">'
              '<path d="M497.39 361.8l-112-48a24 24 0 0 0-28 6.9l-49.6 60.6A370.66 370.66 0 0 1 130.6 '
              '204.11l60.6-49.6a23.94 23.94 0 0 0 6.9-28l-48-112A24.16 24.16 0 0 0 122.6.61l-104 24A24 '
              '24 0 0 0 0 48c0 256.5 207.9 464 464 464a24 24 0 0 0 23.4-18.6l24-104a24.29 24.29 0 0 0-14.01-27.6z"/></svg>')

LOGO_SVG = (
    '<svg width="56" height="61" viewBox="0 0 92 100" xmlns="http://www.w3.org/2000/svg" aria-label="MSP Pure Water"><g>'
    '<path d="M46,6 C41,10 27,15 15,20 C13,28 13,40 13,50 C13,64 22,73 46,82 C70,73 79,64 79,50 C79,40 79,28 77,20 C65,15 51,10 46,6 Z" fill="#C9A24B"/>'
    '<path d="M46,6 C41,10 27,15 15,20 C13,28 13,40 13,50 C13,64 22,73 46,82 C70,73 79,64 79,50 C79,40 79,28 77,20 C65,15 51,10 46,6 Z" fill="#13243B" transform="translate(46,44) scale(0.93) translate(-46,-44)"/>'
    '<path d="M46,6 C41,10 27,15 15,20 C13,28 13,40 13,50 C13,64 22,73 46,82 C70,73 79,64 79,50 C79,40 79,28 77,20 C65,15 51,10 46,6 Z" fill="none" stroke="#C9A24B" stroke-width="1" transform="translate(46,44) scale(0.84) translate(-46,-44)"/>'
    '<path d="M46,22 C51,32 58,40 58,48 C58,56 53,60 46,60 C39,60 34,56 34,48 C34,40 41,32 46,22 Z" fill="#0C1A2C" stroke="#C9A24B" stroke-width="1.8"/>'
    '<path d="M40,42 C36,45 36,51 39,55" fill="none" stroke="#DEC07A" stroke-width="1.1"/>'
    '<rect x="22" y="72" width="48" height="18" rx="2" fill="#13243B" stroke="#C9A24B" stroke-width="1.3"/>'
    '<text x="46" y="86" text-anchor="middle" font-family="Georgia, serif" font-weight="700" font-size="13" fill="#C9A24B" letter-spacing="1">MSP</text>'
    '</g></svg>'
)

CSS = """
:root{--navy:#162038;--navy2:#0e1830;--navy3:#2a3a5a;--gold:#C9A84C;--goldl:#E2C97E;
--cream:#FAF7F2;--ink:#1c1c1c;--grey:#6b6b6b;--line:#E7E3DC;--good:#2E8B57;--elev:#C98A2B;--concern:#B23B3B;--maxw:1120px;}
*{box-sizing:border-box}
body{margin:0;font-family:'DM Sans',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--cream);font-size:17px;line-height:1.65;}
a{color:var(--navy)}
.topbar{background:#fff;color:var(--navy);padding:16px 24px;border-bottom:none}
.topbar .wrap{max-width:var(--maxw);margin:0 auto;display:flex;align-items:center;gap:30px}
.topbar .brand{display:flex;align-items:center;text-decoration:none}
.topbar .logo{height:90px;width:auto;display:block}
.topbar .nav{margin-left:auto;display:flex;gap:38px;align-items:center}
.topbar .nav a{font-family:'DM Sans',sans-serif;color:var(--navy);text-decoration:none;font-size:21px;font-weight:400}
.topbar .nav a:hover{color:var(--gold)}
.topbar .callbox{text-align:center;text-decoration:none;line-height:1.35;margin-left:52px}
.topbar .callbox .pico{width:17px;height:17px;fill:#DE3B3B;vertical-align:-2px;margin-right:7px}
.topbar .callbox .ct{display:block;color:var(--navy);font-family:'DM Sans',sans-serif;font-weight:500;font-size:20px}
.topbar .callbox .cn{display:block;color:var(--navy);font-family:'DM Sans',sans-serif;font-weight:500;font-size:20px}
main{max-width:var(--maxw);margin:44px auto 64px;padding:0 24px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:none;padding:38px 40px;margin-bottom:30px}
.card h2{font-family:'Montserrat',sans-serif;color:var(--navy);margin:0 0 12px;font-size:29px;font-weight:700;letter-spacing:-.5px;line-height:1.2}
.kick{font-size:13px;font-weight:700;letter-spacing:1.5px;color:var(--gold);text-transform:uppercase;margin:0 0 8px}
.lead{color:var(--grey);margin:0 0 16px}
input[type=text]{width:100%;padding:14px;font-size:16px;border:1.5px solid var(--line);border-radius:10px;background:#fff}
input[type=text]:focus{outline:none;border-color:var(--gold)}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--gold);color:var(--navy);border:none;border-radius:8px;padding:16px 30px;font-size:17px;font-weight:700;font-family:'DM Sans',sans-serif;cursor:pointer;text-decoration:none;transition:.15s}
.btn:hover{background:var(--goldl)}
.btn.big{font-size:18px;padding:18px 26px;justify-content:center;width:100%}
.btn.ghost{background:transparent;border:1.5px solid var(--line);color:var(--navy);font-weight:700}
.row{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-end}
.grow{flex:1 1 320px}
.muted{color:var(--grey);font-size:15px}
.hero{text-align:center;max-width:880px;margin:18px auto 40px}
.hero h1{font-family:'Montserrat',sans-serif;color:var(--navy);font-size:44px;font-weight:700;line-height:1.15;letter-spacing:-1px;margin:0 0 18px}
.hero h1 em{color:var(--gold);font-style:italic}
.hero p{color:var(--ink);font-size:19px;line-height:1.6;margin:0}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:10px 0 0}
.metric{background:var(--cream);border:1px solid var(--line);border-radius:12px;padding:22px;text-align:center}
.metric .num{font-family:'Montserrat',sans-serif;font-size:32px;color:var(--navy);font-weight:700;line-height:1}
.metric .lbl{font-size:12px;color:var(--grey);margin-top:9px;text-transform:uppercase;letter-spacing:.5px}
.metric.bad{border-top:3px solid var(--concern)}.metric.warn{border-top:3px solid var(--elev)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin-top:12px}
table{width:100%;min-width:600px;border-collapse:collapse;font-size:13.5px}
th{background:var(--navy);color:#fff;text-align:left;padding:9px 11px;font-size:11.5px;text-transform:uppercase;letter-spacing:.3px;white-space:nowrap}
td{padding:9px 11px;border-bottom:1px solid var(--line);vertical-align:top}
td.lvl,td.safe{font-size:12.5px;color:var(--grey)}
.pill{font-size:11px;font-weight:800;padding:3px 9px;border-radius:20px;white-space:nowrap}
.pill.good{background:#E8F3EC;color:var(--good)}.pill.elevated{background:#FBF1DE;color:var(--elev)}
.pill.high{background:#FBE7D6;color:#C2611C}.pill.concern{background:#F8E6E6;color:var(--concern)}
.exp h3{font-family:'Montserrat',sans-serif;color:var(--gold);margin:20px 0 6px;font-size:18px}
.exp p{margin:0 0 14px;line-height:1.75}
.exp ul{margin:10px 0 16px;padding-left:22px;line-height:1.8}
.exp li{margin:6px 0}
.help{background:var(--cream);border-left:4px solid var(--gold);padding:16px 20px;border-radius:0 8px 8px 0;margin:18px 0 0!important;line-height:1.7}
.reco{background:var(--navy);color:#fff;border-radius:14px;padding:34px 38px;margin-bottom:24px}
.reco .k{font-size:13px;font-weight:700;letter-spacing:1.5px;color:var(--gold);text-transform:uppercase}
.reco h2{color:var(--goldl);font-family:'Montserrat',sans-serif;margin:10px 0 12px;font-size:28px;letter-spacing:-.5px}
.reco p{color:var(--cream);margin:0;line-height:1.65;font-size:17px}
.syscards{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:8px}
.syscard{border:1.4px solid var(--gold);background:var(--cream);border-radius:12px;border-top:4px solid var(--navy);padding:22px}
.syscard .tag{font-size:11px;font-weight:700;letter-spacing:1px;color:var(--gold);text-transform:uppercase}
.syscard h3{font-family:'Montserrat',sans-serif;color:var(--navy);margin:6px 0 4px;font-size:19px}
.syscard .short{font-style:italic;color:var(--grey);font-size:14px;margin:0 0 8px}
.syscard p{font-size:15px;line-height:1.6;margin:0;color:var(--ink)}
.alt{margin:10px 0;font-size:16px;line-height:1.6}
.cta{background:var(--navy);color:#fff;border:none;text-align:center;padding:44px 40px}
.cta h2{color:#fff;font-size:30px;letter-spacing:-.5px}
.cta p{color:var(--cream);max-width:680px;margin:14px auto;font-size:17px;line-height:1.6}
.cta .phone{font-size:26px;font-weight:700;color:#fff;text-decoration:none;display:inline-block;margin:10px 0}
.cta .small{color:var(--goldl);font-size:15px}
.trust{display:flex;gap:22px;justify-content:center;flex-wrap:wrap;color:var(--gold);font-weight:700;font-size:13px;letter-spacing:.5px;margin-top:20px}
.site-footer{background:var(--navy);color:#fff;padding:64px 24px 32px;margin-top:56px}
.site-footer .fwrap{max-width:var(--maxw);margin:0 auto;display:flex;justify-content:space-between;gap:40px;flex-wrap:wrap}
.site-footer h4{font-family:'DM Sans',sans-serif;color:#fff;font-size:19px;margin:0 0 9px;font-weight:700}
.site-footer p{color:#aeb8cc;font-size:16px;margin:0 0 26px;line-height:1.75}
.site-footer a{color:#aeb8cc;text-decoration:none}
.site-footer a:hover{color:var(--gold)}
.site-footer .fnav{display:flex;flex-direction:column;gap:13px;margin-right:110px}
.site-footer .fnav a{font-family:'DM Sans',sans-serif;color:#fff;font-size:17px}
.site-footer .fdiv{max-width:var(--maxw);margin:34px auto;border-top:1px solid rgba(255,255,255,.16)}
.site-footer .fbottom{max-width:var(--maxw);margin:0 auto;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;color:#8a97ad;font-size:14px}
.site-footer .fbottom a{color:#8a97ad}
.site-footer .flinks a{margin-left:34px}
.disc{color:var(--grey);font-size:13px;line-height:1.6;margin-top:20px}
@media(max-width:760px){.cards{grid-template-columns:repeat(2,1fr)}.syscards{grid-template-columns:1fr}.hero h1{font-size:26px}
.topbar .wrap{flex-wrap:wrap;gap:12px}.topbar .nav{gap:18px;margin-left:0;order:3;width:100%;justify-content:center}.topbar .callbox{margin-left:auto}
.site-footer .fnav{margin-right:0}.card{padding:24px 22px}.hero h1{font-size:28px}main{padding:0 18px}}
@media print{
  @page{margin:0.45in}
  .noprint{display:none!important}
  body{background:#fff;font-size:10.5px;color:#000}
  main{margin:0;padding:0;max-width:100%}
  .topbar{padding:6px 0;border-bottom:2px solid var(--gold)}
  .topbar .logo{height:42px}.topbar .nav,.topbar .callbox{display:none}
  .card{box-shadow:none;border:none;padding:4px 0 2px;margin:0 0 7px;break-inside:avoid}
  .card h2{font-size:14px;margin:0 0 2px}.kick{font-size:8.5px;margin:0 0 2px}
  .hero{margin:4px auto 6px}.hero h1{font-size:17px;margin:0 0 4px}.hero p{font-size:10.5px}
  .cards{gap:7px}.metric{padding:7px}.metric .num{font-size:19px}.metric .lbl{font-size:8.5px}
  .exp p{margin:0 0 3px;line-height:1.3}.exp ul{margin:2px 0 4px;line-height:1.3}.exp li{margin:1px 0}
  .help{padding:6px 9px;margin:5px 0 0!important;line-height:1.3}
  .reco{padding:11px;margin-bottom:8px}.reco h2{font-size:14px}.reco p{line-height:1.3}
  .syscards{gap:8px}.syscard{padding:8px}.syscard h3{font-size:13px}.syscard p{font-size:10px;line-height:1.25}
  .alt{font-size:10px;margin:3px 0;line-height:1.3}
  .cta{padding:12px}.cta h2{font-size:15px}.cta p{font-size:10px;margin:4px auto}.cta .phone{font-size:15px;margin:2px 0}.cta .small{font-size:9px}
  .trust{font-size:9px;gap:10px;margin-top:8px}
  .site-footer{padding:10px 0 6px;margin-top:10px;break-inside:avoid}
  .site-footer .fwrap{gap:20px}.site-footer h4{font-size:10px;margin:0 0 2px}
  .site-footer p{font-size:9px;margin:0 0 6px;line-height:1.3}
  .site-footer .fnav{gap:3px}.site-footer .fnav a{font-size:9px}
  .site-footer .fdiv{margin:8px auto}.site-footer .fbottom{font-size:8px}
  .disc{font-size:8px;margin-top:8px}
}
"""

TIER_CLASS = {"good": "good", "elevated": "elevated", "high": "high", "concern": "concern"}


def esc(s):
    return html.escape(str(s), quote=True)


def slug(key):
    return re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")


def page(title, body, description="", asset_prefix=""):
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Montserrat:wght@600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<header class="topbar"><div class="wrap">
<a class="brand" href="{SITE}/home"><img class="logo" src="{asset_prefix}assets/logo.png" alt="{esc(CO['name'])}"></a>
<nav class="nav">
<a href="{SITE}/home">Home</a><a href="{SITE}/about">About</a><a href="{SITE}/services">Services</a><a href="{SITE}/contact">Contact</a></nav>
<a class="callbox" href="tel:{PHONE_DIGITS}"><span class="ct">{PHONE_ICON}Call or Text Today</span><span class="cn">{esc(PHONE_FMT)}</span></a>
</div></header>
<main>{body}</main>
<footer class="site-footer">
<div class="fwrap">
<div class="fcol"><h4>Service Area</h4><p>The Twin Cities And Greater Minnesota</p>
<h4>Contact</h4><p><a href="mailto:{esc(CO['email'])}">{esc(CO['email'])}</a><br><a href="tel:{PHONE_DIGITS}">{esc(PHONE_FMT)}</a></p></div>
<nav class="fnav"><a href="{SITE}/home">Home</a><a href="{SITE}/about">About</a><a href="{SITE}/services">Services</a><a href="{SITE}/contact">Contact</a></nav>
</div>
<div class="fdiv"></div>
<div class="fbottom"><span>&copy; Copyright 2026. {esc(CO['name'])} All rights reserved.</span>
<span class="flinks"><a href="{SITE}/privacy-policy">Privacy Policy</a><a href="{SITE}/tos">Terms of Use</a></span></div>
</footer>
</body></html>"""


EDU = {
    "chlorine": {
        "title": "Chlorine — Why Your Water Can Smell Like a Pool",
        "what": "Your city adds a little chlorine to your water on purpose. It's a disinfectant that kills germs and keeps the water safe on its long trip through the pipes to your home. That part is genuinely a good thing.",
        "notice": ["A “pool water” smell or taste, especially from the cold tap",
                   "Dry skin and hair after showers",
                   "Coffee, tea, or ice that taste a little “off”"],
        "honest": "Chlorine in city water is safe to drink — it's doing its job. Most people just don't love the taste, or what it does to their skin and hair.",
        "help": "Our Whole Home Water Filtration System runs your water through high-quality coconut-shell carbon that grabs the chlorine right at your house. Your water tastes and smells clean, and every shower is gentler on your skin and hair.",
    },
    "tthm": {
        "title": "Disinfection Byproducts — Tiny Leftovers From Cleaning the Water",
        "what": "When chlorine mixes with natural bits of leaves and soil in river water, it can make tiny amounts of byproducts (scientists call them TTHMs and HAA5s).",
        "honest": "Your city keeps these below the EPA's legal safety limits, so your water is safe to drink. Even so, a lot of families like to lower them further in the water they actually drink and cook with.",
        "help": "Our reverse-osmosis drinking system reduces these at your kitchen sink, so the water your family drinks is about as clean as water gets.",
    },
    "lead": {
        "title": "Lead — It's About Your Home's Pipes, Not the City",
        "what": "Here's the honest truth: there is no lead in the water your city sends out. But if your house was built before the mid-1980s, the older pipes, solder, or fixtures inside the home can add small amounts of lead while the water sits in them overnight.",
        "honest": "So this one is really about your home, not your city. If your house is newer, this probably isn't an issue for you at all.",
        "help": "If you do have older plumbing, the simplest peace-of-mind fix is a reverse-osmosis system at your kitchen sink — it removes lead from the water you drink and cook with.",
    },
    "chloride": {
        "title": "Saltiness Is Slowly Rising (From Road Salt)",
        "what": "Every winter, road salt washes off the streets into our lakes and groundwater. Year by year, that's slowly making Twin Cities water a little saltier (it's called chloride). Right now it's still at safe levels.",
        "honest": "This isn't an emergency — it's a slow trend worth knowing about, and it can't be removed at the city plant.",
        "help": "If you'd like it out of your drinking water, our reverse-osmosis system takes care of it.",
    },
    "sodium": {
        "title": "Sodium — A Side Effect of the City Softening Your Water",
        "what": "Your city softens your water for you, which is a nice perk. But the usual way to soften water adds a little sodium (salt) to it along the way.",
        "honest": "For most people that's perfectly fine. But if anyone in your home watches their salt for health reasons, it's good to know.",
        "help": "Our reverse-osmosis drinking system takes that sodium back out of your drinking water — so you get the best of both worlds.",
    },
    "pfas": {
        "title": "PFAS — “Forever Chemicals” in the East Metro",
        "what": "PFAS are man-made chemicals that don't break down in nature — that's why people call them “forever chemicals.” In parts of the East Metro, they got into the groundwater years ago from old 3M manufacturing.",
        "honest": "This is a real, documented issue in your area — not something we made up. Cities are working on it, but the surest way to keep PFAS out of your family's drinking water is to filter it right at your tap.",
        "help": "Reverse osmosis is one of the most effective ways to remove PFAS. Our drinking system gives you water you can feel good about.",
    },
}


def render_report(profile):
    p = profile
    h = p["hardness"]
    city = esc(p["display"])
    co_name = esc(CO["name"])
    hard_cls = "bad" if h["gpg"] > 10.5 else "warn"
    is_hard = h["gpg"] >= 7

    # It's all treated municipal water — "City Water" for everyone. Only a genuine
    # private well would say otherwise. (The detailed line below still notes whether
    # the city draws it from wells or the river.)
    src_short = "Private Well" if p["source_type"] == "well" else "City Water"
    metrics = f"""<div class="cards">
      <div class="metric {hard_cls}"><div class="num">{h['gpg']}<span style="font-size:14px"> gpg</span></div><div class="lbl">Water Hardness</div></div>
      <div class="metric {hard_cls}"><div class="num" style="font-size:21px">{esc(h['label'])}</div><div class="lbl">How hard that is</div></div>
      <div class="metric warn"><div class="num">{p['tds']}</div><div class="lbl">Dissolved minerals (ppm)</div></div>
      <div class="metric" style="border-top:3px solid var(--gold)"><div class="num" style="font-size:18px">{src_short}</div><div class="lbl">Your water source</div></div>
    </div>"""

    safe_card = f"""<div class="card"><p class="kick">The honest truth</p>
      <h2>“Safe” Isn't the Same as “Soft &amp; Clean”</h2>
      <p>{city}'s water meets the basic federal and state safety standards — your city does that part.
      But meeting the legal minimum is a long way from <b>soft, clean, healthy, and great-tasting</b>
      water. Hard minerals, the chlorine they add, and whatever your own pipes pick up are all still in
      there — and that's exactly what we help families fix. Here's what's really in your water:</p></div>"""

    if is_hard:
        hard_card = f"""<div class="card exp"><p class="kick">Your water's #1 issue</p>
          <h2>Hard Water &mdash; and {city} Has a Lot of It</h2>
          <p>“Hard” water just means your water carries a lot of dissolved minerals &mdash; mostly
          calcium and magnesium &mdash; that it soaks up from rock deep underground. Minnesota has some of
          the hardest water in the entire country, and {city} is right up there at about
          <b>{h['gpg']} grains per gallon ({esc(h['label'])})</b>.</p>
          <p><b>Here's what hard water does around your home:</b></p>
          <ul>
            <li>White, crusty buildup on faucets, showerheads, and glass</li>
            <li>Spots and film on dishes and glasses, even after the dishwasher</li>
            <li>Soap and shampoo that won't lather, so you use more of everything</li>
            <li>Dry, itchy skin and dull, tangly hair</li>
            <li>Stiff, scratchy laundry that wears out faster</li>
            <li>Scale building up inside your water heater and pipes</li>
          </ul>
          <p>That last one quietly costs you the most: the mineral scale makes your water heater and
          appliances work harder, so they wear out years sooner.</p>
          <p class="help"><b>How we help:</b> This is exactly what our Whole Home Water Filtration System
          is built for. It removes the hardness minerals before the water reaches any tap &mdash; so you get
          softer skin and hair, spot-free dishes, far less soap use, and appliances that last much longer.</p></div>"""
    else:
        hard_card = f"""<div class="card exp"><p class="kick">The good news</p>
          <h2>Your Water Is on the Softer Side</h2>
          <p>At about <b>{h['gpg']} grains per gallon ({esc(h['label'])})</b>, {city}'s water is softer than
          most of the metro &mdash; so you'll see less of the crusty buildup and spotting that hard-water
          towns deal with. For you, the biggest improvements are at the kitchen tap (taste) and in the shower.</p>
          <p class="help"><b>How we help:</b> Our Whole Home Water Filtration System polishes out the
          chlorine taste and protects your home, and our reverse-osmosis drinking system makes your
          drinking and cooking water crisp and clean.</p></div>"""

    topic_cards = ""
    for c in p["concerns"]:
        e = EDU.get(c["key"])
        if not e:
            continue
        notice = ("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in e["notice"]) + "</ul>") if e.get("notice") else ""
        honest = f'<p class="muted">{esc(e["honest"])}</p>' if e.get("honest") else ""
        topic_cards += (f'<div class="card exp"><h2 style="font-size:19px">{esc(e["title"])}</h2>'
                        f'<p>{esc(e["what"])}</p>{notice}{honest}'
                        f'<p class="help"><b>How we help:</b> {esc(e["help"])}</p></div>')

    rec = p["recommendation"]
    sysd = CONFIG["systems"][rec["primary_key"]]
    ro = CONFIG["drinking"][rec["ro_default"]]
    alts = ""
    for k, note in rec["alternatives"]:
        if k in CONFIG["systems"]:
            alts += f'<p class="alt"><b style="color:var(--navy)">{esc(CONFIG["systems"][k]["name"])}</b> &mdash; {note}</p>'
    reco = f"""<div class="card">
      <div class="reco"><div class="k">How {co_name} helps your home</div>
        <h2>{esc(sysd['name'])} + {esc(ro['name'])}</h2><p>{esc(rec['reason'])}</p></div>
      <div class="syscards">
        <div class="syscard"><div class="tag">For every tap in the house</div><h3>{esc(sysd['name'])}</h3>
          <p>{esc(sysd['blurb'])}</p></div>
        <div class="syscard"><div class="tag">For drinking &amp; cooking</div><h3>{esc(ro['name'])}</h3>
          <p>{esc(ro['blurb'])}</p></div>
      </div>
      <p class="kick" style="margin-top:18px">Other options, depending on your home</p>{alts}</div>"""

    offer = CONFIG["offer"]
    phone_digits = re.sub(r"[^0-9]", "", CO["phone"])
    badges = " &nbsp;&nbsp; ".join("&#10022; " + esc(b) for b in CONFIG.get("trust_badges", []))
    cta = f"""<div class="card cta">
      <h2>{esc(offer['headline'])}</h2><p>{esc(offer['subhead'])}</p>
      <a class="phone" href="tel:{phone_digits}">&#128222; Call or text {esc(CO['phone'])}</a>
      <p class="small">{esc(CO['email'])} &nbsp;|&nbsp; {esc(CO['website'])} &middot; <i>{esc(offer['guarantee'])}</i></p>
      <div class="trust">{badges}</div></div>"""

    pfas_note = (f'<p style="color:var(--concern);font-weight:700;margin-top:8px">Heads up: your area is '
                 f'inside the documented East Metro PFAS zone &mdash; see the section below.</p>') if p["pfas_zone"] else ""

    disclaimer = (f'<p class="disc">Prepared by {co_name} as a free educational service. Hardness and '
                  f'source come from your city’s published water reports, the Minnesota Department of '
                  f'Health, USGS, and the U.S. EPA. Exact numbers vary by home and season — we’re '
                  f'happy to go over your specifics on a free, no-pressure call.</p>')

    body = f"""
    <div class="hero"><h1>What's <em>Really</em> In {city}'s Water?</h1>
      <p>A plain-English look at your tap water &mdash; what's in it, where it comes from, and what's actually worth doing about it.</p></div>
    <div class="noprint" style="text-align:center;margin:-6px 0 18px">
      <a class="btn ghost" href="../index.html">&larr; Check another city</a> &nbsp;
      <a class="btn" href="#" onclick="window.print();return false">&#128424; Print / Save as PDF</a></div>
    {safe_card}
    <div class="card"><p class="kick">Your water at a glance</p><h2>The Quick Numbers</h2>
      {metrics}
      <p style="margin-top:16px"><b>Where your water comes from:</b> {esc(p['source_detail'])}</p>{pfas_note}</div>
    {hard_card}
    {topic_cards}
    {reco}
    {cta}
    {disclaimer}
    """
    desc = f"Free plain-English water report for {p['display']}, MN: hardness {h['gpg']} gpg, {p['source_detail']}"
    return page(f"{p['display']} Water Report — {co_name}", body, desc, asset_prefix="../")


def build_profile_for(key):
    disp = kb.MSP["cities"][key]["display"]
    loc = {"zip": kb.CITY_TO_ZIP.get(key), "city": disp, "state_abbr": "MN", "epa_systems": []}
    return kb.build_profile(loc)


def main():
    city_to_slug = {}   # normalized name -> slug
    zip_to_slug = {}
    built = 0
    for key in kb.MSP["cities"]:
        prof = build_profile_for(key)
        s = slug(key)
        with open(os.path.join(REPORTS, s + ".html"), "w", encoding="utf-8") as f:
            f.write(render_report(prof))
        built += 1
        # name lookups: key, display, and any alias that maps to this key
        city_to_slug[kb._norm(key)] = s
        city_to_slug[kb._norm(prof["display"])] = s
    for alias, key in kb._CITY_ALIASES.items():
        if key in kb.MSP["cities"]:
            city_to_slug[kb._norm(alias)] = slug(key)
    for z, key in kb.MSP.get("zip_to_city", {}).items():
        if key in kb.MSP["cities"]:
            zip_to_slug[z] = slug(key)
    for core, zips in kb.MSP.get("core_zips", {}).items():
        for z in zips:
            zip_to_slug[z] = slug(core)

    cities_sorted = sorted({kb.MSP["cities"][k]["display"] for k in kb.MSP["cities"]})
    datalist = "".join(f'<option value="{esc(c)}">' for c in cities_sorted)

    landing_body = f"""
    <div class="hero"><h1>What's <em>Really</em> In Your Water?</h1>
      <p>Get a free, instant water-quality report for your Twin Cities home — your hardness, what's in it,
      where it comes from, and what it means. No sign-up, no waiting.</p></div>
    <div class="card" style="max-width:680px;margin:0 auto">
      <label for="q">Enter your city or ZIP code</label>
      <div class="row">
        <input class="grow" type="text" id="q" list="cl" placeholder="e.g. Brooklyn Park  ·  55125  ·  Eden Prairie" autofocus>
        <datalist id="cl">{datalist}</datalist>
        <button class="btn" onclick="go()">See My Water Report &rarr;</button>
      </div>
      <p id="msg" class="muted" style="margin-top:10px">{len(cities_sorted)} Twin Cities metro cities covered. Type your city name or ZIP and press the button.</p>
    </div>
    <div class="card cta">
      <h2>Questions about your water?</h2>
      <p>Talk it through with us — free, no pressure. We'll walk through your results and what (if anything) is worth doing.</p>
      <a class="phone" href="tel:{re.sub(r'[^0-9]','',CO['phone'])}">&#128222; Call or text {esc(CO['phone'])}</a>
      <p class="small">{esc(CO['email'])} &nbsp;|&nbsp; {esc(CO['website'])}</p>
    </div>
    <script>
      var ZIP={json.dumps(zip_to_slug)};
      var CITY={json.dumps(city_to_slug)};
      function norm(s){{return s.toLowerCase().replace(/\\./g,'').replace(/\\bst\\b/g,'saint').replace(/\\s+/g,' ').trim();}}
      function resolve(raw){{
        raw=(raw||'').trim(); if(!raw) return null;
        var m=raw.match(/\\b(\\d{{5}})\\b/); if(m){{return ZIP[m[1]]||null;}}
        var n=norm(raw); if(CITY[n]) return CITY[n];
        var keys=Object.keys(CITY).sort(function(a,b){{return b.length-a.length;}});
        for(var i=0;i<keys.length;i++){{var k=keys[i]; if(k && new RegExp('\\\\b'+k.replace(/[.*+?^${{}}()|[\\]\\\\]/g,'\\\\$&')+'\\\\b').test(n)) return CITY[k];}}
        return null;
      }}
      function go(){{
        var s=resolve(document.getElementById('q').value);
        if(s){{window.location.href='reports/'+s+'.html';}}
        else{{document.getElementById('msg').innerHTML='We don\\'t have detailed data for that one yet — call or text us at <b>{esc(CO['phone'])}</b> and we\\'ll pull it for you.';}}
      }}
      document.getElementById('q').addEventListener('keydown',function(e){{if(e.key==='Enter')go();}});
    </script>
    """
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(f"Free Home Water Report — {CO['name']}", landing_body,
                     "Free instant Twin Cities water-quality report: hardness, contaminants, source, and what it means."))
    # prevent GitHub Pages Jekyll processing
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    # custom domain for GitHub Pages
    if CUSTOM_DOMAIN:
        with open(os.path.join(DOCS, "CNAME"), "w", encoding="utf-8") as f:
            f.write(CUSTOM_DOMAIN + "\n")
    print(f"Built {built} city pages + landing into docs/  ({len(zip_to_slug)} ZIPs, {len(city_to_slug)} name keys mapped)")


if __name__ == "__main__":
    main()
