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
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from water_report import knowledge_base as kb

DOCS = os.path.join(HERE, "docs")
REPORTS = os.path.join(DOCS, "reports")
os.makedirs(REPORTS, exist_ok=True)
CONFIG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
CO = CONFIG["company"]

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
:root{--navy:#13243B;--navy2:#0C1A2C;--navy3:#1E3957;--gold:#C9A24B;--goldl:#DEC07A;
--cream:#FAF8F3;--ink:#23303F;--grey:#6B7785;--line:#E2E6EC;--good:#2E8B57;--elev:#C98A2B;--concern:#B23B3B;}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--cream);}
a{color:var(--navy)}
.topbar{background:linear-gradient(180deg,var(--navy) 0%,var(--navy2) 100%);color:#fff;padding:20px;border-bottom:3px solid var(--gold);}
.topbar .wrap{max-width:980px;margin:0 auto;display:flex;align-items:center;gap:16px}
.topbar h1{font-family:Georgia,serif;font-size:20px;margin:0;font-weight:700}
.topbar .sub{color:var(--goldl);font-size:12px;letter-spacing:2px;text-transform:uppercase}
main{max-width:980px;margin:26px auto 50px;padding:0 20px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:0 6px 24px rgba(19,36,59,.06);padding:26px;margin-bottom:22px}
.card h2{font-family:Georgia,serif;color:var(--navy);margin:0 0 6px;font-size:22px}
.kick{font-size:11px;font-weight:800;letter-spacing:1.5px;color:var(--gold);text-transform:uppercase;margin:0 0 4px}
.lead{color:var(--grey);margin:0 0 16px}
input[type=text]{width:100%;padding:14px;font-size:16px;border:1.5px solid var(--line);border-radius:10px;background:#fff}
input[type=text]:focus{outline:none;border-color:var(--gold)}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--gold);color:var(--navy);border:none;border-radius:10px;padding:14px 22px;font-size:16px;font-weight:800;cursor:pointer;text-decoration:none;transition:.15s}
.btn:hover{background:var(--goldl)}
.btn.big{font-size:18px;padding:16px 24px;justify-content:center;width:100%}
.btn.ghost{background:transparent;border:1.5px solid var(--line);color:var(--navy);font-weight:700}
.row{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-end}
.grow{flex:1 1 320px}
.muted{color:var(--grey);font-size:13px}
.hero{text-align:center;max-width:760px;margin:8px auto 22px}
.hero h1{font-family:Georgia,serif;color:var(--navy);font-size:32px;line-height:1.15;margin:0 0 12px}
.hero h1 em{color:var(--gold);font-style:italic}
.hero p{color:var(--ink);font-size:16px;line-height:1.5;margin:0}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:6px 0 0}
.metric{background:var(--cream);border:1px solid var(--line);border-radius:12px;padding:16px;text-align:center}
.metric .num{font-family:Georgia,serif;font-size:30px;color:var(--navy);font-weight:700;line-height:1}
.metric .lbl{font-size:11px;color:var(--grey);margin-top:7px;text-transform:uppercase;letter-spacing:.5px}
.metric.bad{border-top:3px solid var(--concern)}.metric.warn{border-top:3px solid var(--elev)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin-top:12px}
table{width:100%;min-width:600px;border-collapse:collapse;font-size:13.5px}
th{background:var(--navy);color:#fff;text-align:left;padding:9px 11px;font-size:11.5px;text-transform:uppercase;letter-spacing:.3px;white-space:nowrap}
td{padding:9px 11px;border-bottom:1px solid var(--line);vertical-align:top}
td.lvl,td.safe{font-size:12.5px;color:var(--grey)}
.pill{font-size:11px;font-weight:800;padding:3px 9px;border-radius:20px;white-space:nowrap}
.pill.good{background:#E8F3EC;color:var(--good)}.pill.elevated{background:#FBF1DE;color:var(--elev)}
.pill.high{background:#FBE7D6;color:#C2611C}.pill.concern{background:#F8E6E6;color:var(--concern)}
.exp h3{font-family:Georgia,serif;color:var(--gold);margin:16px 0 4px;font-size:16px}
.exp p{margin:0 0 4px;line-height:1.5}
.reco{background:var(--navy);color:#fff;border-radius:14px;padding:22px;margin-bottom:16px}
.reco .k{font-size:11px;font-weight:800;letter-spacing:1.5px;color:var(--gold);text-transform:uppercase}
.reco h2{color:var(--goldl);font-family:Georgia,serif;margin:6px 0 8px;font-size:21px}
.reco p{color:var(--cream);margin:0;line-height:1.5}
.syscards{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.syscard{border:1.4px solid var(--gold);background:var(--cream);border-radius:12px;border-top:4px solid var(--navy);padding:16px}
.syscard .tag{font-size:10.5px;font-weight:800;letter-spacing:1px;color:var(--gold);text-transform:uppercase}
.syscard h3{font-family:Georgia,serif;color:var(--navy);margin:4px 0 2px;font-size:16px}
.syscard .short{font-style:italic;color:var(--grey);font-size:12.5px;margin:0 0 6px}
.syscard p{font-size:13px;line-height:1.45;margin:0;color:var(--ink)}
.alt{margin:6px 0;font-size:14px;line-height:1.5}
.cta{background:var(--navy);color:#fff;border:none;text-align:center}
.cta h2{color:#fff;font-size:24px}
.cta p{color:var(--cream);max-width:620px;margin:8px auto}
.cta .phone{font-size:22px;font-weight:800;color:#fff;text-decoration:none;display:inline-block;margin:6px 0}
.cta .small{color:var(--goldl);font-size:13px}
.trust{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;color:var(--gold);font-weight:700;font-size:12px;letter-spacing:.5px;margin-top:14px}
footer{text-align:center;color:var(--grey);font-size:12px;padding:24px}
.disc{color:var(--grey);font-size:11.5px;line-height:1.5;margin-top:14px}
@media(max-width:760px){.cards{grid-template-columns:repeat(2,1fr)}.syscards{grid-template-columns:1fr}.hero h1{font-size:26px}}
@media print{.noprint{display:none!important}.card{box-shadow:none;break-inside:avoid}body{background:#fff}}
"""

TIER_CLASS = {"good": "good", "elevated": "elevated", "high": "high", "concern": "concern"}


def esc(s):
    return html.escape(str(s), quote=True)


def slug(key):
    return re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")


def page(title, body, description=""):
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<style>{CSS}</style></head><body>
<div class="topbar"><div class="wrap"><span>{LOGO_SVG}</span>
<div><h1>{esc(CO['name'])}</h1><div class="sub">Free Home Water Report</div></div></div></div>
<main>{body}</main>
<footer>{esc(CO['name'])} &middot; {esc(CO['service_area'])} &middot; {esc(CO['phone'])}</footer>
</body></html>"""


def render_report(profile):
    p = profile
    h = p["hardness"]
    n = len(p["flagged"])
    city = esc(p["display"])
    score_cls = "bad" if p["score"] < 70 else "warn"
    hard_cls = "bad" if h["gpg"] > 10.5 else "warn"

    # metric cards
    metrics = f"""<div class="cards">
      <div class="metric {score_cls}"><div class="num">{p['score']}</div><div class="lbl">Water Score &middot; {esc(p['grade'])}</div></div>
      <div class="metric {hard_cls}"><div class="num">{h['gpg']}<span style="font-size:14px"> gpg</span></div><div class="lbl">{esc(h['label'])} &middot; {h['mgl']} ppm</div></div>
      <div class="metric warn"><div class="num">{p['tds']}</div><div class="lbl">Est. TDS (ppm)</div></div>
      <div class="metric {'bad' if n>=4 else 'warn'}"><div class="num">{n}</div><div class="lbl">Items Above Ideal</div></div>
    </div>"""

    pfas = ('<div style="margin-top:10px;color:var(--concern);font-weight:700">East Metro PFAS zone — '
            'within the documented 3M groundwater contamination area.</div>') if p["pfas_zone"] else ""

    # contaminant table
    rows = ""
    for c in p["table_rows"]:
        cls = TIER_CLASS.get(c["tier"], "elevated")
        rows += (f'<tr><td><strong>{esc(c["name"])}</strong></td>'
                 f'<td class="lvl">{esc(c.get("level") or "—")}</td>'
                 f'<td class="safe">{esc(c.get("safe") or "—")}</td>'
                 f'<td><span class="pill {cls}">{esc(c["rating_label"])}</span></td></tr>')
    table = f"""<div class="tablewrap"><table>
      <thead><tr><th>What's in your water</th><th>Your est. level</th><th>Normal / safe level</th><th>Rating</th></tr></thead>
      <tbody>{rows}</tbody></table></div>
      <p class="muted" style="margin-top:10px">Levels are typical estimates for your area (gpg = grains per gallon,
      ppm = parts per million). Ratings are benchmarked against EPA limits &amp; MN Department of Health guidance.</p>"""

    # concerns explained
    explain = p["health_concerns"] + [c for c in p["elevated"]
                                      if c["key"] in ("tthm", "haa5", "manganese", "chlorine", "iron", "sodium")]
    seen, blocks = set(), ""
    for c in explain:
        if c["key"] in seen:
            continue
        seen.add(c["key"])
        meta = []
        if c.get("sources"):
            meta.append(f"<b>Where it comes from:</b> {esc(c['sources'])}")
        if c.get("aesthetic"):
            meta.append(f"<b>What you notice:</b> {esc(c['aesthetic'])}")
        blocks += (f'<h3>{esc(c["name"])}</h3>'
                   + (f'<p>{esc(c["health_effects"])}</p>' if c.get("health_effects") else "")
                   + (f'<p class="muted">{" &middot; ".join(meta)}</p>' if meta else ""))
    explain_card = f'<div class="card exp"><p class="kick">Why it matters</p><h2>The Concerns, Explained</h2>{blocks}</div>' if blocks else ""

    # recommendation
    rec = p["recommendation"]
    sysd = CONFIG["systems"][rec["primary_key"]]
    ro = CONFIG["drinking"][rec["ro_default"]]
    package = f"{sysd['name']} + {ro['name']}"
    alts = ""
    for k, note in rec["alternatives"]:
        if k in CONFIG["systems"]:
            alts += f'<p class="alt"><b style="color:var(--navy)">{esc(CONFIG["systems"][k]["name"])}</b> — {note}</p>'
    reco = f"""<div class="card">
      <div class="reco"><div class="k">Recommended for your water</div><h2>{esc(package)}</h2><p>{esc(rec['reason'])}</p></div>
      <div class="syscards">
        <div class="syscard"><div class="tag">Recommended — Whole Home</div><h3>{esc(sysd['name'])}</h3>
          <p class="short">{esc(sysd.get('short',''))}</p><p>{esc(sysd['blurb'])}</p></div>
        <div class="syscard"><div class="tag">Recommended — Drinking Water</div><h3>{esc(ro['name'])}</h3>
          <p class="short">Final-stage drinking &amp; cooking water</p><p>{esc(ro['blurb'])}</p></div>
      </div>
      <p class="kick" style="margin-top:18px">Also available</p>{alts}</div>"""

    # CTA
    offer = CONFIG["offer"]
    phone_digits = re.sub(r"[^0-9]", "", CO["phone"])
    badges = " &nbsp;&nbsp; ".join("&#10022; " + esc(b) for b in CONFIG.get("trust_badges", []))
    cta = f"""<div class="card cta">
      <h2>{esc(offer['headline'])}</h2>
      <p>{esc(offer['subhead'])}</p>
      <a class="phone" href="tel:{phone_digits}">&#128222; Call or text {esc(CO['phone'])}</a>
      <p class="small">{esc(CO['email'])} &nbsp;|&nbsp; {esc(CO['website'])} &middot; <i>{esc(offer['guarantee'])}</i></p>
      <div class="trust">{badges}</div></div>"""

    prov_lbl = "Water provider (estimated)" if p["match"] in ("mn_region", "national") else "Water provider"
    disclaimer = (f'<p class="disc">Educational estimate by {esc(CO["name"])}. Levels are typical regional values '
                  f'from public utility reports, the U.S. EPA, USGS and the Minnesota Department of Health — not a '
                  f'measurement of your individual tap. We\'ll review the specifics on a free water consultation.</p>')

    body = f"""
    <div class="hero"><h1>What's <em>Really</em> In {city}'s Water?</h1>
      <p>{esc(p['verdict'])}</p></div>
    <div class="noprint" style="text-align:center;margin:-8px 0 18px"><a class="btn ghost" href="../index.html">&larr; Check another address</a>
      &nbsp; <a class="btn" href="#" onclick="window.print();return false">&#128424; Print / Save as PDF</a></div>
    <div class="card"><p class="kick">Your water at a glance</p><h2>The Bottom Line</h2>
      {metrics}
      <p style="margin-top:16px"><b>{prov_lbl}:</b> {esc(p['provider'])}<br>
      <b>Where your water comes from:</b> {esc(p['source_detail'])}</p>{pfas}</div>
    <div class="card"><p class="kick">The full breakdown</p><h2>What's In Your Water</h2>
      <p class="lead" style="margin-bottom:0">These are the issues in your water that affect your home — and every one is something
      an {esc(CO['name'])} system removes or reduces.</p>{table}</div>
    {explain_card}
    {reco}
    {cta}
    {disclaimer}
    """
    desc = f"Water quality report for {p['display']}, MN — hardness {h['gpg']} gpg, {p['source_detail']}"
    return page(f"{p['display']} Water Report — {CO['name']}", body, desc)


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
    print(f"Built {built} city pages + landing into docs/  ({len(zip_to_slug)} ZIPs, {len(city_to_slug)} name keys mapped)")


if __name__ == "__main__":
    main()
