"""Turns a resolved location into a complete, report-ready water profile.

Cities are resolved primarily by ZIP code: in the Twin Cities metro the USPS
"postal city" is unreliable (e.g. Brooklyn Park ZIPs report as "Minneapolis"),
so trusting the geocoded city name alone produces badly wrong water profiles.
Contaminant levels are reported in real units (gpg / ppm / ppb / pCi/L) with a
plain-language rating (Normal / Elevated / High / Concerning).
"""
import difflib
import json
import os
import re

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _load(name):
    with open(os.path.join(_DATA, name), "r", encoding="utf-8") as f:
        return json.load(f)


CONTAMINANTS = _load("contaminants.json")["contaminants"]
MSP = _load("msp_water.json")
GPG_TO_MGL = 17.1

_TEMPLATE_FOR = {"surface": "surface", "groundwater": "groundwater",
                 "groundwater_soft": "groundwater_soft", "blended": "groundwater"}

# rating -> (display label, color tier, score penalty)
RATING = {
    "normal":     {"label": "NORMAL",     "tier": "good",     "pen": 0},
    "low":        {"label": "LOW",        "tier": "good",     "pen": 0},
    "elevated":   {"label": "ELEVATED",   "tier": "elevated", "pen": 4},
    "high":       {"label": "HIGH",       "tier": "high",     "pen": 8},
    "concerning": {"label": "CONCERNING", "tier": "concern",  "pen": 13},
}


def _norm(name):
    if not name:
        return ""
    n = name.lower().strip().replace(".", "")
    # Expand the abbreviation "St" -> "Saint" only as a whole word, so "St Paul"
    # becomes "saint paul" but "West"/"East" are left intact.
    n = re.sub(r"\bst\b", "saint", n)
    return " ".join(n.split())


def hardness_label(gpg):
    for band in MSP["hardness_scale"]:
        if gpg <= band["max_gpg"]:
            return band["label"]
    return "Hard"


def _hardness_rating(gpg):
    if gpg <= 3:
        return "normal"
    if gpg <= 7:
        return "elevated"
    if gpg <= 10.5:
        return "high"
    return "concerning"


def _tds_rating(tds):
    if tds < 300:
        return "normal"
    if tds <= 500:
        return "elevated"
    return "high"


def resolve_city_key(location):
    """Return (city_key_or_None, match_type). ZIP wins; postal city only as a
    last resort and never for Minneapolis/Saint Paul (handled via core_zips)."""
    zip_code = str(location.get("zip") or "")[:5]
    if zip_code in MSP.get("zip_to_city", {}):
        return MSP["zip_to_city"][zip_code], "zip_map"
    for core, zips in MSP.get("core_zips", {}).items():
        if zip_code in zips:
            return core, "core_zip"
    # Match the (normalized) city name through the city index, which also covers
    # display names and aliases. Keys in `cities` may not be self-normalized
    # (e.g. "st louis park"), so always resolve via CITY_INDEX, never raw keys.
    key = CITY_INDEX.get(_norm(location.get("city")))
    if key:
        # Trust a geocoded "Minneapolis"/"Saint Paul" only with NO ZIP (a direct city
        # search). With a ZIP, a real core ZIP already matched above, so a leftover
        # "Minneapolis" here is a suburb mislabeled by its postal city — fall through.
        if key in ("minneapolis", "saint paul") and zip_code:
            return None, "fallback"
        return key, "geocode"
    return None, "fallback"


def apply_zip_override(location):
    location = dict(location)
    key, match = resolve_city_key(location)
    if key and key in MSP["cities"]:
        location["city"] = MSP["cities"][key]["display"]
        if not location.get("state_abbr"):
            location["state_abbr"] = "MN"
    return location


_CITY_ALIASES = {
    "st paul": "saint paul", "st. paul": "saint paul", "stpaul": "saint paul",
    "minneapolis mn": "minneapolis", "mpls": "minneapolis",
    "st louis park": "st louis park", "saint louis park": "st louis park",
    "st anthony": "saint anthony", "saint anthony village": "saint anthony",
    "st francis": "saint francis", "st paul park": "saint paul park",
    "south st paul": "south saint paul", "west st paul": "west saint paul",
    "north st paul": "north saint paul",
}


def _build_city_index():
    """Normalized city name / key -> city key, longest names first for matching."""
    idx = {}
    for key, c in MSP["cities"].items():
        idx[_norm(key)] = key
        idx[_norm(c["display"])] = key
    for alias, key in _CITY_ALIASES.items():
        if key in MSP["cities"]:
            idx[_norm(alias)] = key
    return idx


def _build_city_to_zip():
    """A representative ZIP per city (for display, filenames, and PFAS detection)."""
    m = {}
    for core, zips in MSP.get("core_zips", {}).items():
        if zips:
            m.setdefault(core, zips[0])  # core cities prefer their primary ZIP
    for z, c in MSP.get("zip_to_city", {}).items():
        m.setdefault(c, z)
    # East-metro PFAS cities: prefer a ZIP that is in the PFAS list so the flag triggers
    pfas = set(MSP.get("east_metro_pfas_zips", []))
    for z, c in MSP.get("zip_to_city", {}).items():
        if z in pfas:
            m[c] = z
    return m


CITY_INDEX = _build_city_index()
CITY_TO_ZIP = _build_city_to_zip()


def all_cities():
    """Sorted list of supported city display names (for autocomplete / browse)."""
    return sorted({c["display"] for c in MSP["cities"].values()})


def resolve_query(raw):
    """Parse free-form input (ZIP, city, or address) into a location dict.

    Returns a dict with keys: zip, city, address, state_abbr, matched_by, error,
    suggestions. `matched_by` is one of zip | city | city_in_text | None.
    """
    out = {"zip": None, "city": None, "address": None, "state_abbr": None,
           "matched_by": None, "error": None, "suggestions": []}
    raw = (raw or "").strip()
    if not raw:
        out["error"] = "empty"
        return out

    # 1) explicit 5-digit ZIP anywhere in the text wins
    m = re.search(r"\b(\d{5})\b", raw)
    if m:
        out["zip"] = m.group(1)
        out["matched_by"] = "zip"
        if re.sub(r"[\s,]+", "", raw) != m.group(1):
            out["address"] = raw  # full address typed — show it on the cover
        return out

    norm = _norm(raw)

    # 2) exact city / alias match
    if norm in CITY_INDEX:
        key = CITY_INDEX[norm]
        out.update(city=MSP["cities"][key]["display"], zip=CITY_TO_ZIP.get(key),
                   state_abbr="MN", matched_by="city")
        return out

    # 3) a known city name appears inside the text (e.g. a full address). Prefer the
    #    longest city name to avoid 'saint paul' matching inside 'south saint paul'.
    for name in sorted(CITY_INDEX, key=len, reverse=True):
        if name and re.search(r"\b" + re.escape(name) + r"\b", norm):
            key = CITY_INDEX[name]
            out.update(city=MSP["cities"][key]["display"], zip=CITY_TO_ZIP.get(key),
                       state_abbr="MN", matched_by="city_in_text",
                       address=raw if len(norm.split()) > len(name.split()) else None)
            return out

    # 4) no match -> fuzzy suggestions
    close = difflib.get_close_matches(norm, list(CITY_INDEX.keys()), n=5, cutoff=0.55)
    out["suggestions"] = sorted({MSP["cities"][CITY_INDEX[c]]["display"] for c in close})
    out["error"] = "no_match"
    return out


def _city_profile(location):
    key, match = resolve_city_key(location)
    if key:
        prof = dict(MSP["cities"][key]); prof["_match"] = match
        return prof
    state = (location.get("state_abbr") or "").upper()
    if state in ("MN", ""):
        prof = dict(MSP["fallbacks"]["mn_groundwater_suburb"]); prof["_match"] = "mn_region"
        if location.get("city"):
            prof["display"] = location["city"]
        return prof
    prof = dict(MSP["fallbacks"]["national_generic"]); prof["_match"] = "national"
    if location.get("city"):
        prof["display"] = location["city"]
    return prof


def _concerns_for(source_type, zip_code):
    template = [dict(c) for c in MSP["concern_templates"][_TEMPLATE_FOR.get(source_type, "groundwater")]]
    if source_type == "blended":
        template = template + [dict(MSP["blended_extra"])]
    if zip_code in MSP.get("east_metro_pfas_zips", []):
        if "pfas" not in [c["key"] for c in template]:
            template = [dict(MSP["pfas_entry"])] + template
    return template


def _merge_concern(c):
    ref = CONTAMINANTS.get(c["key"], {})
    rating = c.get("rating", "elevated")
    return {
        "key": c["key"], "name": ref.get("name", c["key"].title()),
        "level": c.get("level", ""), "rating": rating,
        "rating_label": RATING[rating]["label"], "tier": RATING[rating]["tier"],
        "safe": ref.get("safe_level", ""),
        "category": ref.get("category", ""), "health_effects": ref.get("health_effects", ""),
        "aesthetic": ref.get("aesthetic", ""), "sources": ref.get("sources", ""),
        "removed_by": ref.get("removed_by", "ro"),
    }


def _estimate_tds(gpg, source_type):
    base = 160 if source_type == "surface" else 300
    return max(230, min(round(gpg * GPG_TO_MGL * 0.5 + base), 600))


def _quality_score(rows, gpg):
    """Score from the homeowner's point of use. Municipal water is never perfect at
    the tap — it isn't softened to ideal, carries a disinfectant, and isn't filtered
    for drinking — so it starts below 100 and hardness dominates."""
    score = 92
    if gpg <= 3:
        score -= 4
    elif gpg <= 7:
        score -= 14
    elif gpg <= 10.5:
        score -= 22
    elif gpg <= 15:
        score -= 28
    elif gpg <= 20:
        score -= 34
    elif gpg <= 25:
        score -= 40
    else:
        score -= 48
    for r in rows:
        if r.get("key") == "hardness":
            continue  # hardness already counted above
        pen = RATING[r["rating"]]["pen"]
        if "Health" not in r.get("category", ""):
            pen = max(0, pen - 3)  # aesthetic issues weigh a little less
        score -= pen
    return max(18, min(score, 82))


def _grade(score):
    # Municipal water tops out around C+; truly good water needs treatment at the home.
    if score >= 72:
        return "B-", "Solid municipal water — but there's clear room to improve at the tap."
    if score >= 62:
        return "C+", "Drinkable, but several issues are worth treating."
    if score >= 54:
        return "C", "Hardness and contaminants are affecting your home and water."
    if score >= 46:
        return "C-", "Hard water and contaminants are taking a real toll."
    if score >= 38:
        return "D", "Significant water-quality problems worth addressing now."
    return "F", "Severe hardness and contaminants — this water needs treatment."


def _good_points(source_type):
    goods = ["Professionally treated and disinfected by a regulated public utility.",
             "Meets federal Safe Drinking Water Act standards for acute safety."]
    if source_type == "surface":
        goods.append("Surface-water supply is continuously monitored and tested.")
    elif source_type == "groundwater_soft":
        goods.append("Your city already softens the water — a great head start.")
    else:
        goods.append("Deep groundwater source is naturally filtered and bacteria-free.")
    goods.append("Fluoridated per Minnesota law to support dental health.")
    return goods[:4]


def recommend_systems(source_type, gpg, concerns, pfas):
    """Pick the MSP system that best fits this water. Returns keys + reasons;
    the report pulls display names/blurbs from config.

    Rule (city/municipal water): over 20 gpg -> Dual-Tank City Water System;
    20 gpg and under -> Whole Home Water Filtration System. Dual-tank/peroxide are
    for private wells. Salt-free + RO are offered as alternatives.
    """
    ro_default = "ro_tank"
    if gpg > 20:
        primary = "dual_tank_city"
        reason = (f"At {gpg} gpg this is {hardness_label(gpg).lower()} city water — our Dual-Tank "
                  "City Water System pairs a high-capacity softening/conditioning tank with a "
                  "dedicated carbon tank to handle the hardness and chlorine, with reverse osmosis "
                  "for your drinking water.")
    else:
        primary = "standard_mixed_bed"  # Whole Home Water Filtration System
        reason = (f"City water at {gpg} gpg — our Whole Home Water Filtration System reduces the "
                  "hard-water scale and strips chlorine/chloramine taste throughout your home, with "
                  "reverse osmosis at the kitchen tap.")

    alternatives = [
        ("salt_free", "Prefer no salt or on a low-sodium diet? Our Salt-Free Conditioning + Carbon "
         "system keeps your minerals and adds zero sodium."),
        ("dual_tank_well", "On a private well? Our Dual-Tank Well system uses chemical-free "
         "air-injection to remove iron, sulfur and manganese — with a hydrogen-peroxide system for "
         "heavy iron & sulfur."),
    ]
    return {"primary_key": primary, "reason": reason, "ro_default": ro_default,
            "alternatives": alternatives}


def build_profile(location):
    location = apply_zip_override(location)
    zip_code = str(location.get("zip") or "")[:5]
    prof = _city_profile(location)

    source_type = prof.get("source_type", "groundwater")
    gpg = float(prof.get("hardness_gpg", 18))
    mgl = round(gpg * GPG_TO_MGL)
    tds = _estimate_tds(gpg, source_type)

    concerns = [_merge_concern(c) for c in _concerns_for(source_type, zip_code)]

    # Hardness & TDS as their own table rows
    hr = _hardness_rating(gpg)
    hardness_row = {"key": "hardness", "name": "Water Hardness",
                    "level": f"{round(gpg, 1)} gpg  ({mgl} ppm)", "rating": hr,
                    "rating_label": RATING[hr]["label"], "tier": RATING[hr]["tier"],
                    "safe": "0–3 gpg (soft)", "category": "Aesthetic"}
    tr = _tds_rating(tds)
    tds_row = {"key": "tds", "name": "Total Dissolved Solids (TDS)",
               "level": f"{tds} ppm", "rating": tr,
               "rating_label": RATING[tr]["label"], "tier": RATING[tr]["tier"],
               "safe": "Under 300 ppm", "category": "Aesthetic"}

    score = _quality_score([hardness_row, tds_row] + concerns, gpg)
    grade, verdict = _grade(score)
    pfas = zip_code in MSP.get("east_metro_pfas_zips", [])
    rec = recommend_systems(source_type, gpg, concerns, pfas)

    # Only show what's actually a problem (and every item we show, our systems remove).
    # Hardness is always shown — it's the core of every report.
    shown = [hardness_row] + [r for r in [tds_row] + concerns if r["rating"] != "normal"]
    flagged = [r for r in ([hardness_row, tds_row] + concerns) if r["rating"] != "normal"]
    health_concerns = [c for c in concerns if c["rating"] in ("high", "concerning")]
    provider = prof.get("provider") or f"City of {prof.get('display','Your Area')} Public Utilities"
    # "Where your water actually comes from" — specific source (city override or type default).
    source_detail = (prof.get("source_detail")
                     or MSP.get("source_detail", {}).get(source_type)
                     or MSP["source_text"].get(source_type, "Public water system"))

    return {
        "provider": provider,
        "source": MSP["source_text"].get(source_type, "Public water system"),
        "source_detail": source_detail,
        "source_type": source_type,
        "display": prof.get("display", location.get("city") or "Your Area"),
        "match": prof.get("_match"),
        "pfas_zone": pfas, "softened": source_type == "groundwater_soft",
        "hardness": {"gpg": round(gpg, 1), "mgl": mgl, "label": hardness_label(gpg), "rating": hr},
        "tds": tds, "tds_rating": tr,
        "hardness_row": hardness_row, "tds_row": tds_row,
        "concerns": concerns,
        "table_rows": shown,
        "flagged": flagged,
        "health_concerns": health_concerns,
        "elevated": [c for c in concerns if c["rating"] == "elevated"],
        "goods": _good_points(source_type),
        "score": score, "grade": grade, "verdict": verdict,
        "recommendation": rec,
    }
