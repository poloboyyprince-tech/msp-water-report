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
import urllib.parse
import urllib.request

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
LEADS_PATH = os.path.join(OUTPUT_DIR, "leads.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_SYS, exist_ok=True)

BEST_TIMES = ["8 AM – 12 PM", "12 – 3 PM", "3 – 6 PM"]

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


# ---- lead capture ----------------------------------------------------------
def _save_lead(lead):
    try:
        leads = json.load(open(LEADS_PATH, encoding="utf-8"))
    except Exception:
        leads = []
    leads.insert(0, lead)
    try:
        with open(LEADS_PATH, "w", encoding="utf-8") as f:
            json.dump(leads[:1000], f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _email_lead(lead):
    """Email the lead to the business via Web3Forms (free) if a key is configured."""
    key = os.environ.get("WEB3FORMS_KEY", "").strip()
    if not key:
        return False
    payload = {
        "access_key": key,
        "subject": f"🚰 New Water Report Lead — {lead['name']} ({lead['city']})",
        "from_name": "MSP Pure Water — Website",
        "Name": lead["name"], "Phone": lead["phone"], "Email": lead["email"],
        "Address": lead["address"], "Best time to reach": lead["best_time"],
        "City (report)": lead["city"], "Water hardness": f"{lead['hardness']} gpg",
        "Water grade": lead["grade"], "Submitted": lead["date"],
    }
    try:
        req = urllib.request.Request(
            "https://api.web3forms.com/submit",
            data=urllib.parse.urlencode(payload).encode(),
            headers={"User-Agent": "MSP-Pure-Water/1.0",
                     "Content-Type": "application/x-www-form-urlencoded"})
        urllib.request.urlopen(req, timeout=8)
        return True
    except Exception:
        return False


def capture_lead(form, profile, location):
    lead = {
        "name": (form.get("name") or "").strip(),
        "phone": (form.get("phone") or "").strip(),
        "email": (form.get("email") or "").strip(),
        "address": (form.get("address") or "").strip(),
        "best_time": (form.get("best_time") or "").strip(),
        "city": profile["display"],
        "hardness": profile["hardness"]["gpg"], "grade": profile["grade"],
        "date": datetime.datetime.now().strftime("%b %d, %Y %I:%M %p"),
    }
    _save_lead(lead)
    lead["emailed"] = _email_lead(lead)
    return lead


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
@app.route("/health")
def health():
    """Lightweight endpoint for an uptime pinger to keep the instance warm."""
    return "ok", 200


@app.route("/")
def index():
    # Public, customer-facing landing: the lead-capture form only.
    return render_template("index.html", config=load_config(),
                           cities=all_cities(), best_times=BEST_TIMES)


@app.route("/generate", methods=["POST"])
def generate_route():
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    email = (request.form.get("email") or "").strip()
    address = (request.form.get("address") or "").strip()
    best_time = (request.form.get("best_time") or "").strip()

    missing = [lbl for val, lbl in [(name, "name"), (phone, "phone number"),
                                    (email, "email"), (address, "home address")] if not val]
    if missing:
        flash("Please fill in your " + ", ".join(missing) + " so we can prepare your report.")
        return redirect(url_for("index"))

    try:
        result, err = build_from_query(address, offline=True)
    except Exception as exc:  # never crash the page
        flash(f"Sorry — something went wrong building your report ({exc}). Please try again.")
        return redirect(url_for("index"))

    if err:
        extra = ""
        if err.get("suggestions"):
            extra = " Did you mean: " + ", ".join(err["suggestions"]) + "?"
        flash("We couldn't find that address. Please include your city and ZIP code "
              "(e.g. “123 Maple St, Woodbury, MN 55125”)." + extra)
        return redirect(url_for("index"))

    lead = capture_lead(request.form, result["profile"], result["location"])

    return render_template("result.html", config=load_config(),
                           profile=result["profile"], location=result["location"],
                           filename=result["filename"], lead=lead,
                           n_concerns=len(result["profile"]["flagged"]))


@app.route("/admin/leads")
def admin_leads():
    if not ADMIN_PIN or request.args.get("pin", "") != ADMIN_PIN:
        return "Not authorized. Add ?pin=YOURPIN to the URL.", 401
    try:
        leads = json.load(open(LEADS_PATH, encoding="utf-8"))
    except Exception:
        leads = []
    rows = "".join(
        f"<tr><td>{l.get('date','')}</td><td><b>{l.get('name','')}</b></td>"
        f"<td>{l.get('phone','')}</td><td>{l.get('email','')}</td>"
        f"<td>{l.get('address','')}</td><td>{l.get('best_time','')}</td>"
        f"<td>{l.get('city','')} · {l.get('hardness','')} gpg · {l.get('grade','')}</td></tr>"
        for l in leads)
    return (f"<h2>Leads ({len(leads)})</h2><table border=1 cellpadding=6 "
            f"style='border-collapse:collapse;font-family:sans-serif;font-size:14px'>"
            f"<tr><th>When</th><th>Name</th><th>Phone</th><th>Email</th><th>Address</th>"
            f"<th>Best time</th><th>Water</th></tr>{rows}</table>")


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
