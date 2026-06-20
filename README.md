# MSP Pure Water — Home Water Quality Report Generator

A complete, branded lead-generation tool. Search a prospect by **address, city, or
ZIP code** and instantly produce a polished PDF water-quality report you can preview,
download, and send — positioning the right **MSP Pure Water** system as the solution.

Built for the **Minneapolis–Saint Paul metro**: it knows the region's hard groundwater
suburbs, the East Metro 3M PFAS plume, road-salt chloride, manganese, iron, lead service
lines, and the surface-water systems of Minneapolis & Saint Paul — and recommends the
correct system (Standard Softener + Carbon, Dual-Tank, Hydrogen Peroxide, or Salt-Free)
paired with reverse osmosis.

---

## Quick start — just double-click

**Double-click `Start MSP Water Report.command`** in this folder. A small black window
opens and your browser opens to the app automatically. Then:

1. Type a prospect's **address, city, or ZIP** (city autocomplete included) → **Generate Report**.
2. Review the on-page summary + full PDF preview.
3. Click **Download PDF** to send it.

Notes:
- **Keep the little black window open** while you use the app. Close it (or press
  `Control-C`) to stop.
- First launch may take a few extra seconds while it installs components.
- If macOS says it's from an unidentified developer: right-click the file → **Open** →
  **Open**. One time only.

### Or start it from a terminal
```bash
python3 -m pip install --user -r requirements.txt   # one-time
python3 app.py                                       # then open http://127.0.0.1:5050
```

### First-run setup (one minute)
Open **⚙️ Branding, systems & company settings** and:
- **Upload your logo** (PNG/JPG) — used on every report, framed cleanly on the cover.
- Set your **phone, email, website, and rep name** (these print on every report).
- Optionally **upload a system photo** per product — it appears on the recommended-system
  page when that system is recommended.

---

## Search — three ways

The search box accepts any of these:

| You type | What happens |
|----------|--------------|
| `55125` | ZIP lookup (most precise — geocodes + EPA enrichment when online) |
| `Brooklyn Park` | City lookup against the built-in 98-city metro database |
| `123 Maple St, Woodbury, MN 55125` | Pulls the ZIP from the address; prints the address on the cover |
| `4521 Main St, Eden Prairie, MN` | No ZIP? Finds the city name inside the address |
| `St Paul`, `mpls` | Common aliases are understood |
| `Brookln Park` (typo) | Suggests the closest matches |

The **Recent Reports** panel keeps a searchable history of everything you've generated —
filter by city, ZIP, or address and re-download any past PDF.

> **Why ZIP, not just city?** In this metro the USPS *postal* city is unreliable — Brooklyn
> Park ZIPs are labeled "Minneapolis," Woodbury ZIPs "Saint Paul." The engine resolves by
> ZIP first (with a guard so a postal "Minneapolis"/"Saint Paul" never hijacks a suburb),
> then by city name, so the water profile is always correct.

### Command line

```bash
python3 generate_report.py 55125
python3 generate_report.py "Brooklyn Park"
python3 generate_report.py "123 Maple St, Woodbury, MN 55125"
python3 generate_report.py "Eden Prairie" --offline --out ~/Desktop/report.pdf
python3 generate_report.py --list-cities          # all supported cities
```

---

## What's in the report (5–6 pages)

1. **Branded cover** — your logo, the prospect's address/city, water provider, date.
2. **At a glance** — Water-Quality Score & grade, **Hardness (gpg + ppm)**, **estimated TDS**,
   and an items-above-ideal count.
3. **What's In Your Water** — a clean table: *Contaminant · Your Est. Level · Normal/Safe
   Level · Rating* (Normal / Elevated / High / Concerning), with Hardness and TDS as rows.
4. **The concerns, explained** — plain-language health/aesthetic effects and sources.
5. **What hard water is costing you** + **the good news** (honest credibility).
6. **Your recommended system** — the right MSP system for this water, paired with RO, with
   *also-available* options and the trust badges + call-to-action.

### The rating model
The table shows **only the issues your systems can remove** — every row is something MSP
treats. Each level is in **real units** (gpg / ppm / ppb / pCi/L / ppt) next to its **normal/safe
level**, rated **Elevated / High / Concerning** against EPA limits and MN Department of Health
guidance. Items that are genuinely fine are simply not listed (no reassuring filler). Hardness
is always shown — it's the core of every report.

### Grading
The score is from the **homeowner's point of use**: municipal water is never perfect at the tap
— it isn't softened to ideal, carries a disinfectant, and isn't filtered for drinking — so it
starts below 100 and **hardness dominates**. No city that runs through a treatment plant grades
A or B+; the effective ceiling is ~C+, and very/extremely hard suburbs land in D/F. That's the
point: every home is a candidate for treatment.

### The recommendation logic
- **City / municipal water → Standard Softener + Carbon** (always — regardless of hardness).
- **Dual-Tank City** is offered only as an upsell *"for 6+ full-time residents and 4+ bathrooms."*
- **Dual-Tank Well** and **Hydrogen Peroxide** are presented for **private wells**.
- **Already-softened cities** (Eden Prairie, Maple Grove, Roseville…) → **Salt-Free + Carbon**.
- Every recommendation pairs with **7-Stage RO (AlkaPro)** or **Tankless RO**.

---

## Customizing

| To change… | Edit / do this |
|------------|----------------|
| Logo | Upload on the website, or drop `logo.png` in the project root |
| Phone / email / rep / offer | The website settings, or `config.json` |
| Product names & descriptions | `systems` and `drinking` in `config.json` |
| Trust badges | `trust_badges` in `config.json` |
| A city's water values | `data/msp_water.json` (see below) |
| Contaminant science / safe levels | `data/contaminants.json` |
| System photos | Upload on the website, or drop `assets/systems/<system_key>.png` |

### Adding or tuning a city
Edit `data/msp_water.json`:
- Add the city under `cities` with `display`, `source_type`
  (`surface` / `groundwater` / `groundwater_soft` / `blended`), and `hardness_gpg`.
- Most suburbs resolve by their geocoded name automatically. If a suburb's **postal city**
  differs (it gets labeled "Minneapolis"/"Saint Paul"), add its ZIPs to `zip_to_city`.
- Add a ZIP to `east_metro_pfas_zips` to flag the PFAS zone.

Each concern's `key` must exist in `data/contaminants.json` (which carries the `safe_level`).

---

## Testing

A full `unittest` suite (zero extra dependencies) covers query parsing, ZIP/city resolution,
the rating model, recommendation rules, data integrity, and end-to-end PDF generation:

```bash
python3 -m unittest discover -s tests -v      # 38 tests
# or, if you have pytest:  python3 -m pytest tests/
```

---

## Architecture

```
app.py                 # Flask website (search, history, settings) — python3 app.py
generate_report.py     # command-line generator
templates/             # web UI (base / index / result / _logo.svg)
config.json            # company info · offer · systems · drinking · trust badges
data/
  contaminants.json    # contaminant reference (effects, safe levels, units)
  msp_water.json       # metro city profiles · ZIP maps · concern templates · fallbacks
water_report/
  data_sources.py      # live geocoding + EPA Envirofacts (urllib, fails soft)
  knowledge_base.py    # query resolution, city resolution, ratings, recommendations
  report.py            # branded PDF builder (ReportLab)
  brand.py             # palette + vector logo + image/asset helpers
assets/systems/        # optional system photos (<system_key>.png)
output/                # generated PDFs + searchable report history index
tests/                 # unittest suite
logo.png               # your logo (optional; uploaded via the website)
```

### How the data flows
1. **Resolve** the query → ZIP and/or city (fuzzy-matched, alias-aware).
2. **Geocode** the ZIP and look up the EPA water system (live, short timeout; `--offline` skips).
3. **Build the profile** — city resolved by ZIP → core-ZIP guard → city name → MN/national
   fallback; hardness, TDS, contaminant levels & ratings, quality score, and the recommended
   system.
4. **Render** the branded PDF and record it in the searchable history.

Levels are *typical regional estimates*, not lab readings — which is the point: the report's
call-to-action is a **free in-home water test** for exact numbers (and to get you in the door).

---

## Requirements
- Python 3.9+
- `reportlab` (PDF), `flask` (website) — see `requirements.txt`
- `pymupdf` is optional, used only to assert page counts in tests
- No internet required for core use (`--offline`); live lookups enrich the report when online
