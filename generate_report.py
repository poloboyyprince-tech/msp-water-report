#!/usr/bin/env python3
"""Generate a branded MSP Pure Water home water-quality report.

Search by ZIP, city, or full address:
    python3 generate_report.py 55125
    python3 generate_report.py "Brooklyn Park"
    python3 generate_report.py "123 Maple St, Woodbury, MN 55125"
    python3 generate_report.py 55401 --offline          # skip live lookups
    python3 generate_report.py "Eden Prairie" --out ~/Desktop/report.pdf

Tuned for the Twin Cities metro; falls back to Minnesota / national estimates
elsewhere. Run the web app instead with:  python3 app.py
"""
import argparse
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from water_report.data_sources import resolve_location
from water_report.knowledge_base import (build_profile, apply_zip_override,
                                         resolve_query, all_cities)
from water_report import report as report_mod


def _load_config():
    with open(os.path.join(HERE, "config.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def _slug(loc):
    base = re.sub(r"[^a-z0-9]+", "-", (loc.get("city") or "report").lower()).strip("-")
    tail = loc.get("zip") or ""
    return f"MSP-Water-Report-{base}{('-' + tail) if tail else ''}"


def main():
    ap = argparse.ArgumentParser(description="MSP Pure Water report generator")
    ap.add_argument("query", nargs="*", help="ZIP code, city name, or full address")
    ap.add_argument("--offline", action="store_true", help="Skip live geocoding/EPA lookups")
    ap.add_argument("--out", default=None, help="Output PDF path")
    ap.add_argument("--list-cities", action="store_true", help="List supported cities and exit")
    args = ap.parse_args()

    if args.list_cities:
        for c in all_cities():
            print(c)
        return

    if not args.query:
        ap.error("provide a ZIP code, city name, or address (or use --list-cities)")
    raw = " ".join(args.query).strip()
    parsed = resolve_query(raw)
    if parsed["error"]:
        if parsed["suggestions"]:
            ap.error("No match for %r. Did you mean: %s ?"
                     % (raw, ", ".join(parsed["suggestions"])))
        ap.error("Could not resolve %r — enter a 5-digit ZIP, a Twin Cities city, "
                 "or a full address." % raw)

    zip_code, city, address = parsed["zip"], parsed["city"], parsed["address"]
    print(f"→ Resolving {raw!r} ({parsed['matched_by']}) ...")

    if zip_code and not args.offline:
        location = resolve_location(zip_code, address=address, online=True)
    else:
        location = {"zip": zip_code, "address": address, "city": city,
                    "state_abbr": parsed["state_abbr"], "epa_systems": []}
    location["zip"] = zip_code
    if city and not location.get("city"):
        location["city"] = city
    if parsed["state_abbr"] and not location.get("state_abbr"):
        location["state_abbr"] = parsed["state_abbr"]
    if address:
        location["address"] = address
    location = apply_zip_override(location)

    profile = build_profile(location)
    epa = [s.get("name") for s in location.get("epa_systems", []) if s.get("name")]
    if epa and profile["match"] in ("mn_region", "national"):
        profile["provider"] = epa[0].title()

    n = len(profile["flagged"])
    print(f"  {profile['display']}, {location.get('state_abbr') or '?'} "
          f"{location.get('zip') or ''}".rstrip())
    print(f"  score {profile['score']}/100 (grade {profile['grade']}), "
          f"hardness {profile['hardness']['gpg']} gpg, {n} items above ideal")

    config = _load_config()
    out = args.out or os.path.join(HERE, "output", f"{_slug(location)}.pdf")
    out = os.path.expanduser(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    today = datetime.date.today().strftime("%B %d, %Y")

    print("→ Generating PDF ...")
    report_mod.build_report(profile, location, config, out, today)
    print(f"\n✓ Report saved: {out}")


if __name__ == "__main__":
    main()
