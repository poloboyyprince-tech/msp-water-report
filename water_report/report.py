"""Builds the branded MSP Pure Water PDF water-quality report."""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether, Flowable, Image,
)
from reportlab.lib import colors

from . import brand as B

USABLE_W = letter[0] - 1.4 * inch  # 0.7" margins


def _hx(c):
    """reportlab Color -> '#rrggbb' for use inside <font color> markup."""
    return "#" + c.hexval()[2:]


# ---------------------------------------------------------------- styles
def _styles():
    s = {}
    s["h1"] = ParagraphStyle("h1", fontName="Times-Bold", fontSize=19, leading=22,
                             textColor=B.NAVY, spaceBefore=4, spaceAfter=8)
    s["h2"] = ParagraphStyle("h2", fontName="Times-Bold", fontSize=13.5, leading=17,
                             textColor=B.GOLD, spaceBefore=10, spaceAfter=4)
    s["kicker"] = ParagraphStyle("kicker", fontName="Helvetica-Bold", fontSize=8.5,
                                 leading=11, textColor=B.GOLD, spaceAfter=2,
                                 tracking=2)
    s["body"] = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=14.5,
                               textColor=B.INK, spaceAfter=6)
    s["small"] = ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=11,
                                textColor=B.GREY)
    s["bullet"] = ParagraphStyle("bullet", fontName="Helvetica", fontSize=10, leading=14,
                                 textColor=B.INK, leftIndent=14, spaceAfter=3,
                                 bulletIndent=2)
    s["card_num"] = ParagraphStyle("cn", fontName="Times-Bold", fontSize=23, leading=24,
                                   textColor=B.NAVY, alignment=TA_CENTER)
    s["card_lbl"] = ParagraphStyle("cl", fontName="Helvetica", fontSize=7.6, leading=9.5,
                                   textColor=B.GREY, alignment=TA_CENTER)
    s["th"] = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8.5, leading=11,
                             textColor=colors.white)
    s["td"] = ParagraphStyle("td", fontName="Helvetica", fontSize=8.8, leading=11.5,
                             textColor=B.INK)
    s["td_b"] = ParagraphStyle("tdb", fontName="Helvetica-Bold", fontSize=8.8,
                               leading=11.5, textColor=B.NAVY)
    s["prod_h"] = ParagraphStyle("ph", fontName="Times-Bold", fontSize=13, leading=16,
                                 textColor=B.NAVY)
    s["prod_b"] = ParagraphStyle("pb", fontName="Helvetica", fontSize=9, leading=12.5,
                                 textColor=B.INK)
    return s


# ---------------------------------------------------------------- helpers
class HRule(Flowable):
    def __init__(self, width=USABLE_W, color=B.GOLD, thickness=1.2, space=6):
        super().__init__()
        self.width = width; self.color = color; self.thickness = thickness
        self.space = space; self.height = thickness + space
    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.space, self.width, self.space)


def _metric_card(value, label, accent=B.GOLD):
    inner = Table([[Paragraph(value, _S["card_num"])],
                   [Paragraph(label, _S["card_lbl"])]],
                  colWidths=[USABLE_W / 4 - 10])
    inner.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (0, 0), 10),
        ("BOTTOMPADDING", (0, 0), (0, 0), 2),
        ("TOPPADDING", (0, 1), (0, 1), 0),
        ("BOTTOMPADDING", (0, 1), (0, 1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (-1, -1), B.CREAM),
        ("LINEABOVE", (0, 0), (-1, 0), 3, accent),
        ("BOX", (0, 0), (-1, -1), 0.6, B.LINE_GREY),
    ]))
    return inner


def metrics_row(profile):
    n = len(profile["flagged"])
    cards = [
        _metric_card(f"{profile['score']}", f"WATER QUALITY SCORE&nbsp;&nbsp;(Grade {profile['grade']})",
                     B.STATUS_CONCERN if profile["score"] < 70 else B.STATUS_ELEVATED),
        _metric_card(f"{profile['hardness']['gpg']} <font size=10>gpg</font>",
                     f"{profile['hardness']['label'].upper()}<br/>{profile['hardness']['mgl']} ppm", B.STATUS_CONCERN if profile['hardness']['gpg'] > 10.5 else B.STATUS_ELEVATED),
        _metric_card(f"{profile['tds']}", "EST. TOTAL DISSOLVED<br/>SOLIDS (ppm)", B.STATUS_ELEVATED),
        _metric_card(f"{n}", "ITEMS ABOVE<br/>IDEAL LEVELS", B.STATUS_CONCERN if n >= 4 else B.STATUS_ELEVATED),
    ]
    t = Table([cards], colWidths=[USABLE_W / 4] * 4)
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


_STATUS_STYLE = {
    "good": (B.STATUS_GOOD, B.GOOD_BG, "OK"),
    "elevated": (B.STATUS_ELEVATED, B.ELEVATED_BG, "ELEVATED"),
    "concern": (B.STATUS_CONCERN, B.CONCERN_BG, "CONCERN"),
}


def contaminant_table(profile):
    header = [Paragraph(t, _S["th"]) for t in
              ("WHAT'S IN YOUR WATER", "YOUR EST. LEVEL", "NORMAL / SAFE LEVEL", "RATING")]
    rows = [header]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), B.NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, B.LINE_GREY),
    ]
    for i, c in enumerate(profile["table_rows"], start=1):
        color, bg = B.TIER_COLORS.get(c["tier"], B.TIER_COLORS["elevated"])
        rows.append([
            Paragraph(c["name"], _S["td_b"]),
            Paragraph(c["level"] or "—", _S["td"]),
            Paragraph(c.get("safe") or "—", _S["td"]),
            Paragraph(f'<font color="{_hx(color)}"><b>{c["rating_label"]}</b></font>', _S["td"]),
        ])
        style.append(("BACKGROUND", (3, i), (3, i), bg))
        if c["key"] in ("hardness", "tds"):
            style.append(("BACKGROUND", (0, i), (0, i), B.CREAM))
    t = Table(rows, colWidths=[USABLE_W * w for w in (0.33, 0.23, 0.25, 0.19)], repeatRows=1)
    t.setStyle(TableStyle(style))
    return t


def _system_card(title, short, blurb, badge, recommended=False):
    badge_txt = (f'<font color="#13243B"><b>{badge}</b></font>' if recommended
                 else f'<font color="#6B7785">{badge}</font>')
    rows = [[Paragraph(badge_txt, _S["small"])],
            [Paragraph(title, _S["prod_h"])],
            [Paragraph(f'<i>{short}</i>', _S["small"])],
            [Spacer(1, 3)],
            [Paragraph(blurb, _S["prod_b"])]]
    inner = Table(rows, colWidths=[USABLE_W / 2 - 16])
    box_color = B.GOLD if recommended else B.LINE_GREY
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), B.CREAM if recommended else colors.white),
        ("BOX", (0, 0), (-1, -1), 1.4 if recommended else 0.8, box_color),
        ("LINEABOVE", (0, 0), (-1, 0), 4, B.NAVY if recommended else B.LINE_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (0, 0), 7), ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 2), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return inner


def _reco_banner(package, reason):
    title = ParagraphStyle("rb", fontName="Times-Bold", fontSize=15, leading=18,
                           textColor=B.GOLD_LIGHT)
    kick = ParagraphStyle("rbk", fontName="Helvetica-Bold", fontSize=8, leading=11,
                          textColor=B.GOLD)
    body = ParagraphStyle("rbb", fontName="Helvetica", fontSize=9.5, leading=13.5,
                          textColor=B.CREAM)
    inner = Table([[Paragraph("RECOMMENDED FOR YOUR WATER", kick)],
                   [Paragraph(package, title)],
                   [Spacer(1, 3)],
                   [Paragraph(reason, body)]], colWidths=[USABLE_W - 36])
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), B.NAVY),
        ("BOX", (0, 0), (-1, -1), 1.5, B.GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 18), ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (0, 0), 12), ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
        ("TOPPADDING", (0, 1), (-1, -1), 1),
    ]))
    return inner


# ---------------------------------------------------------------- page furniture
def _cover(canvas, doc):
    cfg = doc.cfg; prof = doc.profile; loc = doc.loc
    w, h = letter
    canvas.saveState()
    # background
    canvas.setFillColor(B.NAVY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(B.NAVY_DARK)
    canvas.rect(0, 0, w, 1.5 * inch, fill=1, stroke=0)
    # gold top + bottom rules
    canvas.setStrokeColor(B.GOLD); canvas.setLineWidth(2)
    canvas.line(0.9 * inch, h - 0.55 * inch, w - 0.9 * inch, h - 0.55 * inch)
    canvas.line(0.9 * inch, 1.5 * inch, w - 0.9 * inch, 1.5 * inch)

    logo_w = 2.15 * inch
    logo_top = h - 1.0 * inch
    path = B.logo_path()
    if path:
        # Frame an image logo (which may have a white background) on a clean badge
        try:
            from reportlab.lib.utils import ImageReader
            ir = ImageReader(path); iw, ih = ir.getSize()
            logo_h = logo_w * ih / iw
            pad = 0.22 * inch
            canvas.setFillColor(colors.white)
            canvas.roundRect(w / 2 - logo_w / 2 - pad, logo_top - logo_h - pad,
                             logo_w + 2 * pad, logo_h + 2 * pad, 10, fill=1, stroke=0)
        except Exception:
            pass
    B.draw_logo_canvas(canvas, w / 2, logo_top, width=logo_w)

    canvas.setFillColor(B.GOLD); canvas.setFont("Helvetica-Bold", 13)
    canvas.drawCentredString(w / 2, h - 4.45 * inch, "H O M E   W A T E R   Q U A L I T Y   R E P O R T")
    canvas.setFillColor(colors.white); canvas.setFont("Times-Bold", 30)
    canvas.drawCentredString(w / 2, h - 5.15 * inch, "What's Really In")
    canvas.drawCentredString(w / 2, h - 5.78 * inch, "Your Water?")

    # location box
    loc_line = loc.get("address") or (f"{loc.get('city','')}, {loc.get('state_abbr','')} {loc.get('zip','')}".strip(", "))
    canvas.setFont("Helvetica", 11.5); canvas.setFillColor(B.GOLD_LIGHT)
    canvas.drawCentredString(w / 2, h - 6.55 * inch, "PREPARED FOR")
    canvas.setFont("Helvetica-Bold", 14); canvas.setFillColor(colors.white)
    canvas.drawCentredString(w / 2, h - 6.9 * inch, loc_line)
    canvas.setFont("Helvetica", 10.5); canvas.setFillColor(B.GOLD_LIGHT)
    _prov_lbl = ("Water provider (estimated)"
                 if prof.get("match") in ("mn_region", "national") else "Water provider")
    canvas.drawCentredString(w / 2, h - 7.17 * inch,
                             f"{_prov_lbl}: {prof['provider']}")

    # footer block (on navy band)
    co = cfg["company"]
    canvas.setFont("Times-Bold", 13); canvas.setFillColor(B.GOLD)
    canvas.drawCentredString(w / 2, 1.12 * inch, co["name"])
    canvas.setFont("Helvetica", 9.5); canvas.setFillColor(colors.white)
    canvas.drawCentredString(w / 2, 0.9 * inch,
                             f"{co['phone']}   •   {co['email']}   •   {co['website']}")
    canvas.setFont("Helvetica-Oblique", 8); canvas.setFillColor(B.GOLD_LIGHT)
    canvas.drawCentredString(w / 2, 0.66 * inch, co["service_area"])
    canvas.setFont("Helvetica", 7); canvas.setFillColor(B.GREY)
    canvas.drawCentredString(w / 2, 0.4 * inch, f"Report date: {doc.report_date}")
    canvas.restoreState()


def _later(canvas, doc):
    w, h = letter
    canvas.saveState()
    # header
    B.draw_logo_canvas(canvas, 0.85 * inch, h - 0.32 * inch, width=0.5 * inch, mark=True)
    canvas.setFillColor(B.NAVY); canvas.setFont("Times-Bold", 10)
    canvas.drawRightString(w - 0.7 * inch, h - 0.6 * inch, "Home Water Quality Report")
    canvas.setStrokeColor(B.GOLD); canvas.setLineWidth(0.8)
    canvas.line(0.7 * inch, h - 0.98 * inch, w - 0.7 * inch, h - 0.98 * inch)
    # footer
    canvas.setStrokeColor(B.LINE_GREY); canvas.setLineWidth(0.6)
    canvas.line(0.7 * inch, 0.62 * inch, w - 0.7 * inch, 0.62 * inch)
    canvas.setFont("Helvetica", 7.5); canvas.setFillColor(B.GREY)
    canvas.drawString(0.7 * inch, 0.46 * inch, doc.cfg["company"]["name"]
                      + " — " + doc.cfg["company"]["phone"])
    canvas.drawCentredString(w / 2, 0.46 * inch,
                             "Regional estimates — let's review the details on a free water consultation.")
    canvas.drawRightString(w - 0.7 * inch, 0.46 * inch, f"Page {doc.page - 1}")
    canvas.restoreState()


# ---------------------------------------------------------------- main build
_S = None


def build_report(profile, location, config, out_path, report_date):
    global _S
    _S = _styles()

    doc = SimpleDocTemplate(out_path, pagesize=letter,
                            leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                            topMargin=1.2 * inch, bottomMargin=0.8 * inch,
                            title="MSP Pure Water — Home Water Quality Report",
                            author=config["company"]["name"])
    doc.cfg = config; doc.profile = profile; doc.loc = location
    doc.report_date = report_date

    st = _S
    story = [Spacer(1, 1), PageBreak()]  # page 1 reserved for cover art

    # ---- Section 1: At a glance
    story += [Paragraph("YOUR WATER AT A GLANCE", st["kicker"]),
              Paragraph("The Bottom Line", st["h1"]),
              Paragraph(profile["verdict"], st["body"]),
              Spacer(1, 6), metrics_row(profile), Spacer(1, 10)]
    _prov_lbl = ("Water provider (estimated)"
                 if profile.get("match") in ("mn_region", "national") else "Water provider")
    src_line = (f"<b>{_prov_lbl}:</b> {profile['provider']}<br/>"
                f"<b>Where your water comes from:</b> {profile['source_detail']}")
    if profile.get("pfas_zone"):
        src_line += ("<br/><b><font color='#B23B3B'>East Metro PFAS Zone:</font></b> "
                     "Your area is within the documented 3M PFAS groundwater contamination "
                     "footprint — see the PFAS note below.")
    story += [Paragraph(src_line, st["body"]), HRule()]

    # ---- Section 2: What's in your water
    story += [Paragraph("THE FULL BREAKDOWN", st["kicker"]),
              Paragraph("What's In Your Water", st["h1"]),
              Paragraph("These are the issues in your water that affect your home — and every "
                        "one is something an MSP Pure Water system removes or reduces. Each is rated "
                        "<b><font color='#C98A2B'>Elevated</font></b>, "
                        "<b><font color='#C2611C'>High</font></b>, or "
                        "<b><font color='#B23B3B'>Concerning</font></b> against EPA limits and MN "
                        "Department of Health guidance.", st["body"]),
              Spacer(1, 4), contaminant_table(profile), Spacer(1, 6),
              Paragraph("Levels are typical estimates for your area in real units (gpg = grains "
                        "per gallon, ppm = parts per million) — not a measurement of your specific "
                        "tap. We'll review your exact options on a free water consultation.", st["small"]),
              PageBreak()]

    # ---- Section 3: Concerns explained
    story += [Paragraph("WHY IT MATTERS", st["kicker"]),
              Paragraph("The Concerns, Explained", st["h1"])]
    explain = profile["health_concerns"] + [c for c in profile["elevated"]
                                            if c["key"] in ("tthm", "haa5", "manganese", "chlorine", "iron", "sodium")]
    seen = set()
    for c in explain:
        if c["key"] in seen:
            continue
        seen.add(c["key"])
        block = [Paragraph(c["name"], st["h2"])]
        if c["health_effects"]:
            block.append(Paragraph(c["health_effects"], st["body"]))
        meta = []
        if c["sources"]:
            meta.append(f"<b>Where it comes from:</b> {c['sources']}")
        if c["aesthetic"]:
            meta.append(f"<b>What you notice:</b> {c['aesthetic']}")
        if meta:
            block.append(Paragraph("<br/>".join(meta), st["small"]))
        story.append(KeepTogether(block))
        story.append(Spacer(1, 4))

    # ---- Section 4: Hard water cost
    gpg = profile["hardness"]["gpg"]
    story += [PageBreak(), Paragraph("THE HIDDEN COST", st["kicker"]),
              Paragraph(f"What {profile['hardness']['label']} Water Is Costing You", st["h1"]),
              Paragraph(f"Your water measures an estimated <b>{gpg} grains per gallon</b> "
                        f"({profile['hardness']['mgl']} mg/L) — classified as "
                        f"<b>{profile['hardness']['label']}</b>. Here's what that means day to day:",
                        st["body"])]
    for txt in [
        "<b>Scale buildup</b> coats your water heater, pipes and fixtures — the harder the water, "
        "the more scale, the higher your energy bills, and the sooner appliances wear out.",
        "<b>Wasted soap &amp; detergent</b> — hard water keeps soap from lathering, so you use "
        "more shampoo, dish and laundry soap to get the same result.",
        "<b>Spotty dishes &amp; cloudy glassware</b> and crusty buildup on faucets and shower heads.",
        "<b>Dry, itchy skin and dull hair</b> as minerals leave a film and clog pores.",
        "<b>Stiff, gray laundry</b> that wears out faster.",
    ]:
        story.append(Paragraph(f"•&nbsp; {txt}", st["bullet"]))

    # ---- Section 5: "Safe" isn't "clean" (pivot, not reassurance)
    story += [Spacer(1, 6), Paragraph("THE BIGGER PICTURE", st["kicker"]),
              Paragraph("“Safe” Isn't the Same as “Clean”", st["h1"]),
              Paragraph("Your city treats and disinfects your water to meet federal Safe Drinking "
                        "Water Act limits — that's why it's legal to drink. But the legal limit is a "
                        "floor, not a goal. Everything flagged in this report is still in your water "
                        "today, still hard on your home, your skin, and your appliances, and still "
                        "worth removing.", st["body"]),
              Paragraph("That's the difference between water that's merely <i>allowed</i> and water "
                        "that's genuinely <b>soft, clean, and great-tasting</b> — which is exactly "
                        "what the right system delivers.", st["body"]), PageBreak()]

    # ---- Section 6: Solutions (recommendation-driven)
    rec = profile["recommendation"]
    systems = config["systems"]; drinking = config["drinking"]
    prim = systems[rec["primary_key"]]
    ro = drinking[rec["ro_default"]]
    ro_other = drinking["ro_tank" if rec["ro_default"] == "ro_tankless" else "ro_tankless"]
    package = f"{prim['name']} + {ro['name']}"

    story += [Paragraph("YOUR SOLUTION", st["kicker"]),
              Paragraph("Your Recommended System", st["h1"]),
              _reco_banner(package, rec["reason"]), Spacer(1, 4)]
    sys_img = B.system_image_path(rec["primary_key"])
    if sys_img:
        try:
            from reportlab.lib.utils import ImageReader
            iw, ih = ImageReader(sys_img).getSize()
            img_w = USABLE_W
            img = Image(sys_img, width=img_w, height=img_w * ih / iw)
            img.hAlign = "CENTER"
            story += [img, Spacer(1, 6)]
        except Exception:
            pass
    cards = Table([[_system_card(prim["name"], prim["short"], prim["blurb"],
                                 "RECOMMENDED — WHOLE HOME", recommended=True),
                    _system_card(ro["name"], "Final-stage drinking & cooking water",
                                 ro["blurb"], "RECOMMENDED — DRINKING WATER", recommended=True)]],
                  colWidths=[USABLE_W / 2, USABLE_W / 2])
    cards.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 8),
        ("LEFTPADDING", (1, 0), (1, 0), 8), ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story += [cards, Spacer(1, 8)]

    # ---- Section 7: Also-available + CTA + sources as one balanced closing block
    cta = _cta_block(config, profile)
    disc_style = ParagraphStyle("disc", fontName="Helvetica", fontSize=7, leading=9.5,
                                textColor=B.GREY, alignment=TA_CENTER)
    disc = Paragraph(
        "Educational estimate by " + config["company"]["name"] +
        ". Levels are typical regional values from public utility reports, the U.S. EPA, USGS and "
        "the Minnesota Department of Health — not a measurement of your individual tap. We'll review "
        "the specifics on your free water consultation.", disc_style)
    others = [(systems[k]["name"], note) for k, note in rec["alternatives"] if k in systems][:3]
    closing = [Paragraph("ALSO AVAILABLE", st["kicker"])]
    for name, note in others:
        closing.append(Paragraph(f'<b><font color="#13243B">{name}</font></b> — {note}', st["bullet"]))
    closing += [Spacer(1, 10), cta, Spacer(1, 7), disc]
    story += [KeepTogether(closing)]

    doc.build(story, onFirstPage=_cover, onLaterPages=_later)
    return out_path


def _cta_block(config, profile):
    co = config["company"]; offer = config["offer"]
    st = _S
    head = ParagraphStyle("ctaH", fontName="Times-Bold", fontSize=18, leading=21,
                          textColor=colors.white, alignment=TA_CENTER)
    sub = ParagraphStyle("ctaS", fontName="Helvetica", fontSize=10, leading=14,
                         textColor=B.CREAM, alignment=TA_CENTER)
    big = ParagraphStyle("ctaB", fontName="Helvetica-Bold", fontSize=13, leading=17,
                         textColor=B.NAVY, alignment=TA_CENTER)
    contact = ParagraphStyle("ctaC", fontName="Helvetica-Bold", fontSize=12, leading=18,
                             textColor=colors.white, alignment=TA_CENTER)
    inner = Table([
        [Paragraph(offer["headline"], head)],
        [Paragraph(offer["subhead"], sub)],
        [Spacer(1, 5)],
        [Table([[Paragraph(offer["cta_primary"], big)]], colWidths=[USABLE_W - 60],
               style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), B.GOLD),
                                 ("TOPPADDING", (0, 0), (-1, -1), 9),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                                 ("ROUNDEDCORNERS", [6, 6, 6, 6])]))],
        [Spacer(1, 6)],
        [Paragraph(f"Call or text&nbsp;&nbsp;{co['phone']}", contact)],
        [Paragraph(f"{co['email']}　|　{co['website']}　·　<i>{offer['guarantee']}</i>", sub)],
        [Spacer(1, 5)],
        [Paragraph("&nbsp;&nbsp;".join(
            f'<font color="#C9A24B">✦</font> {b}' for b in config.get("trust_badges", [])),
            ParagraphStyle("badges", fontName="Helvetica-Bold", fontSize=8, leading=11,
                           textColor=B.GOLD_LIGHT, alignment=TA_CENTER))],
    ], colWidths=[USABLE_W])
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), B.NAVY),
        ("BOX", (0, 0), (-1, -1), 2, B.GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 30), ("RIGHTPADDING", (0, 0), (-1, -1), 30),
        ("TOPPADDING", (0, 0), (0, 0), 10), ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    return inner
