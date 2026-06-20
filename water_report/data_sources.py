"""Live data lookups with graceful offline fallback.

Uses only the Python standard library (urllib) so no extra installs are needed.
Every function fails soft: if the network is unavailable the report still renders
from the curated regional knowledge base.
"""
import json
import ssl
import urllib.request
import urllib.parse

_CTX = ssl.create_default_context()
_UA = {"User-Agent": "MSP-Pure-Water-Report/1.0"}
_TIMEOUT = 7


def _get_json(url):
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_CTX) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def geocode_zip(zip_code):
    """ZIP -> {city, state, state_abbr, zip} using zippopotam.us. None on failure."""
    zip_code = str(zip_code).strip()[:5]
    data = _get_json(f"https://api.zippopotam.us/us/{zip_code}")
    if not data or not data.get("places"):
        return None
    place = data["places"][0]
    return {
        "zip": zip_code,
        "city": place.get("place name", "").strip(),
        "state": place.get("state", "").strip(),
        "state_abbr": place.get("state abbreviation", "").strip(),
    }


def epa_water_systems(zip_code):
    """Best-effort: official water systems serving a ZIP from EPA Envirofacts SDWIS.

    Returns a list of {pwsid, name, population} or [] on any failure.
    """
    zip_code = str(zip_code).strip()[:5]
    url = (
        "https://data.epa.gov/efservice/GEOGRAPHIC_AREA/ZIP_CODE_SERVED/"
        f"{zip_code}/JSON"
    )
    rows = _get_json(url)
    if not isinstance(rows, list) or not rows:
        return []
    pwsids = []
    for row in rows:
        pid = row.get("PWSID") or row.get("pwsid")
        if pid and pid not in [p["pwsid"] for p in pwsids]:
            pwsids.append({"pwsid": pid, "name": None, "population": None})
    # Enrich first few with system name
    for entry in pwsids[:4]:
        sys_url = (
            "https://data.epa.gov/efservice/WATER_SYSTEM/PWSID/"
            f"{entry['pwsid']}/JSON"
        )
        sysrows = _get_json(sys_url)
        if isinstance(sysrows, list) and sysrows:
            entry["name"] = (sysrows[0].get("PWS_NAME")
                             or sysrows[0].get("pws_name"))
            entry["population"] = (sysrows[0].get("POPULATION_SERVED_COUNT")
                                   or sysrows[0].get("population_served_count"))
    return pwsids


def resolve_location(zip_code, address=None, online=True):
    """Combine geocoding + EPA lookups into a single location dict.

    Always returns a dict; fields are None when a source is unavailable.
    """
    loc = {"zip": str(zip_code).strip()[:5], "address": address,
           "city": None, "state": None, "state_abbr": None,
           "epa_systems": []}
    if online:
        geo = geocode_zip(zip_code)
        if geo:
            loc.update({k: geo[k] for k in ("city", "state", "state_abbr")})
        try:
            loc["epa_systems"] = epa_water_systems(zip_code)
        except Exception:
            loc["epa_systems"] = []
    return loc
