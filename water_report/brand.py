"""MSP Pure Water brand assets: color palette and the shield logo.

If a real logo file (logo.png / logo.jpg) is present in the project root it is used
directly. Otherwise a vector recreation of the MSP shield is drawn so reports are
always fully branded.
"""
import os
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Path, Rect, String, Line, Group, Polygon
from reportlab.platypus import Image

# ---- Palette (sampled from the MSP Pure Water logo) ----
NAVY        = colors.HexColor("#13243B")
NAVY_DARK   = colors.HexColor("#0C1A2C")
NAVY_LIGHT  = colors.HexColor("#1E3957")
GOLD        = colors.HexColor("#C9A24B")
GOLD_LIGHT  = colors.HexColor("#DEC07A")
CREAM       = colors.HexColor("#FAF8F3")
PAPER       = colors.HexColor("#FFFFFF")
INK         = colors.HexColor("#23303F")
GREY        = colors.HexColor("#6B7785")
LINE_GREY   = colors.HexColor("#D9DEE4")

# Status / rating colors for contaminant tables
STATUS_GOOD     = colors.HexColor("#2E8B57")
STATUS_ELEVATED = colors.HexColor("#C98A2B")
STATUS_HIGH     = colors.HexColor("#C2611C")
STATUS_CONCERN  = colors.HexColor("#B23B3B")
GOOD_BG     = colors.HexColor("#E8F3EC")
ELEVATED_BG = colors.HexColor("#FBF1DE")
HIGH_BG     = colors.HexColor("#FBE7D6")
CONCERN_BG  = colors.HexColor("#F8E6E6")

# rating tier -> (text color, cell background)
TIER_COLORS = {
    "good":     (STATUS_GOOD, GOOD_BG),
    "elevated": (STATUS_ELEVATED, ELEVATED_BG),
    "high":     (STATUS_HIGH, HIGH_BG),
    "concern":  (STATUS_CONCERN, CONCERN_BG),
}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _shield_points(scale, cx=50, cy=65):
    """Return the shield outline (heraldic, peaked top) scaled about (cx, cy)."""
    raw = [
        ("m", 50, 99),
        ("c", 45, 95, 29, 91, 17, 86),
        ("c", 15, 79, 15, 68, 15, 58),
        ("c", 15, 47, 25, 39, 50, 32),
        ("c", 75, 39, 85, 47, 85, 58),
        ("c", 85, 68, 85, 79, 83, 86),
        ("c", 71, 91, 55, 95, 50, 99),
        ("z",),
    ]
    def s(x, y):
        return (cx + (x - cx) * scale, cy + (y - cy) * scale)
    return raw, s


def _shield_path(scale, fill, stroke=None, sw=0, cx=50, cy=65):
    raw, s = _shield_points(scale, cx, cy)
    p = Path(fillColor=fill, strokeColor=stroke, strokeWidth=sw)
    for seg in raw:
        if seg[0] == "m":
            x, y = s(seg[1], seg[2]); p.moveTo(x, y)
        elif seg[0] == "l":
            x, y = s(seg[1], seg[2]); p.lineTo(x, y)
        elif seg[0] == "c":
            x1, y1 = s(seg[1], seg[2]); x2, y2 = s(seg[3], seg[4]); x3, y3 = s(seg[5], seg[6])
            p.curveTo(x1, y1, x2, y2, x3, y3)
        elif seg[0] == "z":
            p.closePath()
    return p


def _drop_path(fill, stroke, sw):
    p = Path(fillColor=fill, strokeColor=stroke, strokeWidth=sw)
    p.moveTo(50, 80)
    p.curveTo(56, 67, 64, 60, 64, 52)
    p.curveTo(64, 44, 58, 40, 50, 40)
    p.curveTo(42, 40, 36, 44, 36, 52)
    p.curveTo(36, 60, 44, 67, 50, 80)
    p.closePath()
    return p


def _drop_highlight():
    """The inner reflection swoosh in the lower-left of the drop."""
    hl = Path(fillColor=None, strokeColor=GOLD_LIGHT, strokeWidth=1.3)
    hl.moveTo(46, 45)
    hl.curveTo(41, 48, 40, 55, 44, 61)
    return hl


def _banner_pts(l, r, t, b, nx, ny):
    """Flat point list for a plaque with notched (stepped) corners."""
    return [l + nx, t, r - nx, t, r - nx, t - ny, r, t - ny,
            r, b + ny, r - nx, b + ny, r - nx, b, l + nx, b,
            l + nx, b + ny, l, b + ny, l, t - ny, l + nx, t - ny]


def _add_shield(g):
    # gold outer edge, navy body, thin gold pinstripe
    g.add(_shield_path(1.00, GOLD))
    g.add(_shield_path(0.955, NAVY))
    g.add(_shield_path(0.90, None, stroke=GOLD, sw=0.8))
    # water drop + reflection
    g.add(_drop_path(NAVY_DARK, GOLD, 2.2))
    g.add(_drop_highlight())


def logo_drawing(width=46 * mm):
    """Vector recreation of the MSP Pure Water shield logo (Drawing scaled to width)."""
    native_w, native_h = 100.0, 104.0
    scale = width / native_w
    d = Drawing(width, native_h * scale)
    g = Group()

    _add_shield(g)

    # Banner plaque (notched corners) overlapping the shield base
    g.add(Polygon(_banner_pts(14, 86, 34, 13, 4, 5), fillColor=GOLD, strokeColor=None))
    g.add(Polygon(_banner_pts(16, 84, 32, 15, 4, 5), fillColor=NAVY, strokeColor=None))
    g.add(Polygon(_banner_pts(18, 82, 30, 17, 3, 4), fillColor=None,
                  strokeColor=GOLD, strokeWidth=0.7))
    g.add(String(50, 18, "MSP", fontName="Times-Bold", fontSize=19,
                 fillColor=GOLD, textAnchor="middle"))

    # Tagline with flanking rules + end ticks (kept clear of the text)
    g.add(String(50, 5, "P U R E   W A T E R", fontName="Times-Roman", fontSize=5.4,
                 fillColor=GOLD, textAnchor="middle"))
    for x0, x1 in ((7, 25), (75, 93)):
        g.add(Line(x0, 6.5, x1, 6.5, strokeColor=GOLD, strokeWidth=0.6))
        g.add(Line(x0, 4.8, x0, 8.2, strokeColor=GOLD, strokeWidth=0.6))
        g.add(Line(x1, 4.8, x1, 8.2, strokeColor=GOLD, strokeWidth=0.6))

    g.transform = (scale, 0, 0, scale, 0, 0)
    d.add(g)
    return d


def shield_mark_drawing(width=14 * mm):
    """Compact shield-only mark (no banner/tagline) for page headers."""
    native_w, native_h = 100.0, 70.0
    scale = width / native_w
    d = Drawing(width, native_h * scale)
    g = Group()
    _add_shield(g)
    g.transform = (scale, 0, 0, scale, 0, -31 * scale)
    d.add(g)
    return d


def logo_path():
    for name in ("logo.png", "logo.jpg", "logo.jpeg", "logo.PNG"):
        path = os.path.join(PROJECT_ROOT, name)
        if os.path.exists(path):
            return path
    return None


def system_image_path(key):
    """Path to a system photo/diagram (assets/systems/<key>.<ext>) if present."""
    folder = os.path.join(PROJECT_ROOT, "assets", "systems")
    for ext in (".png", ".jpg", ".jpeg", ".PNG"):
        path = os.path.join(folder, key + ext)
        if os.path.exists(path):
            return path
    return None


def draw_logo_canvas(c, cx, top_y, width=46 * mm, mark=False):
    """Draw the logo centered horizontally on cx, with its top at top_y.

    mark=True uses the compact shield-only mark when no image logo is present
    (good for small page headers).
    """
    from reportlab.lib.utils import ImageReader
    from reportlab.graphics import renderPDF
    path = logo_path()
    if path:
        try:
            ir = ImageReader(path)
            iw, ih = ir.getSize()
            h = width * ih / iw
            c.drawImage(ir, cx - width / 2, top_y - h, width=width, height=h,
                        mask="auto", preserveAspectRatio=True)
            return h
        except Exception:
            pass
    d = shield_mark_drawing(width) if mark else logo_drawing(width)
    renderPDF.draw(d, c, cx - width / 2, top_y - d.height)
    return d.height


def logo_flowable(width=46 * mm):
    """Return a Flowable for the logo: the real image if present, else the vector."""
    for name in ("logo.png", "logo.jpg", "logo.jpeg", "logo.PNG"):
        path = os.path.join(PROJECT_ROOT, name)
        if os.path.exists(path):
            try:
                from reportlab.lib.utils import ImageReader
                ir = ImageReader(path)
                iw, ih = ir.getSize()
                return Image(path, width=width, height=width * ih / iw, mask="auto")
            except Exception:
                break
    return logo_drawing(width)
