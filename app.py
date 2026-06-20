#!/usr/bin/env python3
"""MSP Pure Water — web app.

Search a prospect by address, city, or ZIP, generate a branded water-quality
report, preview it, and download the PDF to send. Also keeps a searchable history
of past reports, and lets you upload your logo, system photos, and company info —
no code or terminal needed after launch.

Run:  python3 app.py     then open  http://127.0.0.1:5050
"""
import datetime
import json
import os
import re

from flask import (Flask, request, render_template, send_from_directory,
                   redirect, url_for, flash, abort)

from water_report.data_sources import resolve_location
from water_report.knowledge_base import (build_profile, apply_zip_override,
                                         resolve_query, all_cities)
from water_report import report as report_mod
from water_report import brand as B

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(HERE, "output")
ASSETS_SYS = os.path.join(HERE, "assets", "systems")
CONFIG_PATH = os.path.join(HERE, "config.json")
INDEX_PATH = os.path.join(OUTPUT_DIR, "reports_index.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_SYS, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "msp-pure-water-local")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload cap

# When deployed publicly, set ADMIN_PIN in the host's environment to lock the
# Settings page (branding/uploads). Left unset locally, settings stay open.
ADMIN_PIN = os.environ.get("ADMIN_PIN", "")


def _admin_ok():
    return (not ADMIN_PIN) or (request.form.get("admin_pin", "") == ADMIN_PIN)


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def slugify(loc):
    base = (loc.get("city") or "report").lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    tail = loc.get("zip") or ""
    return f"MSP-Water-Report-{base}{('-' + tail) if tail else ''}.pdf"


# ---- report history index (enables searching past reports) -----------------
def _load_index():
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _record_report(meta):
    idx = [r for r in _load_index() if r.get("filename") != meta["filename"]]
    idx.insert(0, meta)
    idx = idx[:300]
    try:
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(idx, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def recent_reports():
    """Return history entries whose PDF still exists on disk."""
    return [r for r in _load_index()
            if os.path.exists(os.path.join(OUTPUT_DIR, r.get("filename", "")))]


# ---- core generation -------------------------------------------------------
def build_from_query(raw, offline=False):
    """Resolve a free-form query and build the report.

    Returns (result_dict, error_dict). Exactly one is non-None.
    """
    parsed = resolve_query(raw)
    if parsed["error"]:
        return None, parsed

    zip_code, city, address = parsed["zip"], parsed["city"], parsed["address"]

    if zip_code and not offline:
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

    config = load_config()
    filename = slugify(location)
    out_path = os.path.join(OUTPUT_DIR, filename)
    today = datetime.date.today().strftime("%B %d, %Y")
    report_mod.build_report(profile, location, config, out_path, today)

    _record_report({
        "filename": filename,
        "city": profile["display"],
        "zip": location.get("zip") or "",
        "address": location.get("address") or "",
        "query": raw,
        "date": today,
        "score": profile["score"], "grade": profile["grade"],
        "hardness": profile["hardness"]["gpg"],
    })
    return {"profile": profile, "location": location, "filename": filename,
            "parsed": parsed}, None


# ---- routes ----------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", config=load_config(),
                           has_logo=bool(B.logo_path()), cities=all_cities(),
                           reports=recent_reports(), systems_with_images=_systems_with_images())


@app.route("/generate", methods=["POST"])
def generate_route():
    raw = (request.form.get("query") or "").strip()
    offline = bool(request.form.get("offline"))
    try:
        result, err = build_from_query(raw, offline=offline)
    except Exception as exc:  # never crash the page
        flash(f"Sorry — could not generate that report ({exc}). Try again or use offline mode.")
        return redirect(url_for("index"))

    if err:
        if err["error"] == "empty":
            flash("Type a prospect's address, city, or ZIP code to begin.")
        else:
            extra = ""
            if err.get("suggestions"):
                extra = " Did you mean: " + ", ".join(err["suggestions"]) + "?"
            flash("Couldn't find that location. Enter a 5-digit ZIP, a Twin Cities "
                  "city name, or a full address." + extra)
        return redirect(url_for("index"))

    return render_template("result.html", config=load_config(),
                           profile=result["profile"], location=result["location"],
                           filename=result["filename"],
                           n_concerns=len(result["profile"]["flagged"]))


@app.route("/reports/<path:filename>")
def reports(filename):
    if not os.path.exists(os.path.join(OUTPUT_DIR, filename)):
        abort(404)
    as_attach = request.args.get("download") == "1"
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=as_attach,
                               mimetype="application/pdf")


@app.route("/settings", methods=["POST"])
def settings():
    if not _admin_ok():
        flash("Incorrect admin PIN — settings were not changed.")
        return redirect(url_for("index"))
    config = load_config()
    for key in ("name", "phone", "email", "website", "rep_name", "service_area"):
        val = request.form.get(key)
        if val is not None:
            config["company"][key] = val.strip()
    save_config(config)

    msgs = []
    logo = request.files.get("logo")
    if logo and logo.filename:
        ext = os.path.splitext(logo.filename)[1].lower()
        if ext in (".png", ".jpg", ".jpeg"):
            for name in ("logo.png", "logo.jpg", "logo.jpeg", "logo.PNG"):
                p = os.path.join(HERE, name)
                if os.path.exists(p):
                    os.remove(p)
            logo.save(os.path.join(HERE, "logo.png" if ext == ".png" else "logo" + ext))
            msgs.append("Logo uploaded.")
        else:
            msgs.append("Logo must be a PNG or JPG.")

    sysimg = request.files.get("system_image")
    syskey = (request.form.get("system_key") or "").strip()
    if sysimg and sysimg.filename and syskey:
        ext = os.path.splitext(sysimg.filename)[1].lower()
        if ext in (".png", ".jpg", ".jpeg"):
            for old in os.listdir(ASSETS_SYS):
                if old.startswith(syskey + "."):
                    os.remove(os.path.join(ASSETS_SYS, old))
            sysimg.save(os.path.join(ASSETS_SYS, syskey + ext))
            msgs.append(f"System photo saved for “{config['systems'].get(syskey, {}).get('name', syskey)}”.")
        else:
            msgs.append("System photo must be a PNG or JPG.")

    flash(" ".join(msgs) if msgs else "Settings saved.")
    return redirect(url_for("index"))


@app.route("/logo/remove", methods=["POST"])
def remove_logo():
    if not _admin_ok():
        flash("Incorrect admin PIN — nothing was changed.")
        return redirect(url_for("index"))
    for name in ("logo.png", "logo.jpg", "logo.jpeg", "logo.PNG"):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            os.remove(p)
    flash("Logo removed — reports will use the built-in shield logo.")
    return redirect(url_for("index"))


def _systems_with_images():
    have = set()
    for f in os.listdir(ASSETS_SYS):
        have.add(os.path.splitext(f)[0])
    cfg = load_config()
    return [(k, v["name"], k in have) for k, v in cfg.get("systems", {}).items()]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    print("\n  MSP Pure Water — report generator")
    print(f"  Open your browser to:  http://127.0.0.1:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False)
