#!/usr/bin/env python3
"""
Partner One Pager — PDF Generator (v2)
Produces a 2-page A4 PDF matching the Optimove x Trade Desk template style.

Usage:
    python generate_pdf.py <partner_data.json> <output_dir>
"""

import sys
import json
import os
import re
import math
import pathlib
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white, black, Color
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable, Image,
                                    PageBreak, KeepTogether)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus.flowables import Flowable
    from reportlab.graphics.shapes import (Drawing, Circle, Rect, Line,
                                           Ellipse, Path as RLPath,
                                           String, Group, PolyLine, Polygon)
    from reportlab.graphics import renderPDF
except ImportError:
    os.system("pip install reportlab --break-system-packages -q")
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white, black, Color
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable, Image,
                                    PageBreak, KeepTogether)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus.flowables import Flowable
    from reportlab.graphics.shapes import (Drawing, Circle, Rect, Line,
                                           Ellipse, Path as RLPath,
                                           String, Group, PolyLine, Polygon)
    from reportlab.graphics import renderPDF

# ── Brand Colors ───────────────────────────────────────────────────────────────
MIDNIGHT_VIOLET  = HexColor("#302c69")
LIME_GLOW        = HexColor("#dff670")
CHARTREUSE_GLOW  = HexColor("#c2d456")
SHADOW_BLACK     = HexColor("#111111")
CLOUD_TINT       = HexColor("#efefef")
STORM_TINT       = HexColor("#d3d3d3")
SIGNAL_MIST      = HexColor("#9e97cb")
ECHO_OF_IRIS     = HexColor("#7a73a8")
SOFT_PERIWINKLE  = HexColor("#cecce5")
PURE_WHITE       = HexColor("#ffffff")

# ── Font Setup ─────────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent.parent
_font_candidates = [
    SKILL_DIR.parent / "optimove-brand-bible" / "assets" / "fonts" / "Poppins",
    SKILL_DIR.parent.parent / "optimove-brand-bible" / "assets" / "fonts" / "Poppins",
]
# Also search the sessions mount
for session_path in pathlib.Path("/sessions").glob("*/mnt/.claude/skills/optimove-brand-bible/assets/fonts/Poppins"):
    _font_candidates.append(session_path)
FONT_DIR = next((p for p in _font_candidates if isinstance(p, pathlib.Path) and p.exists()), None)

FONTS_REGISTERED = False

def register_fonts():
    global FONTS_REGISTERED
    if FONTS_REGISTERED:
        return True
    if not FONT_DIR or not FONT_DIR.exists():
        return False
    try:
        pdfmetrics.registerFont(TTFont("Poppins",            FONT_DIR / "Poppins-Regular.ttf"))
        pdfmetrics.registerFont(TTFont("Poppins-Bold",       FONT_DIR / "Poppins-Bold.ttf"))
        pdfmetrics.registerFont(TTFont("Poppins-SemiBold",   FONT_DIR / "Poppins-SemiBold.ttf"))
        pdfmetrics.registerFont(TTFont("Poppins-Light",      FONT_DIR / "Poppins-Light.ttf"))
        pdfmetrics.registerFont(TTFont("Poppins-BoldItalic", FONT_DIR / "Poppins-BoldItalic.ttf"))
        pdfmetrics.registerFont(TTFont("Poppins-Medium",     FONT_DIR / "Poppins-Medium.ttf"))
        FONTS_REGISTERED = True
        return True
    except Exception as e:
        print(f"⚠️  Font registration failed: {e}")
        return False

def F(weight="regular"):
    has = FONTS_REGISTERED
    return {
        "regular":    "Poppins"            if has else "Helvetica",
        "medium":     "Poppins-Medium"     if has else "Helvetica",
        "semibold":   "Poppins-SemiBold"   if has else "Helvetica-Bold",
        "bold":       "Poppins-Bold"       if has else "Helvetica-Bold",
        "light":      "Poppins-Light"      if has else "Helvetica",
        "bolditalic": "Poppins-BoldItalic" if has else "Helvetica-BoldOblique",
    }.get(weight, "Poppins" if has else "Helvetica")


# ── Styles ─────────────────────────────────────────────────────────────────────
def make_styles():
    register_fonts()
    return {
        # Headline: SemiBold, sized to fit ~2 lines
        "h1": ParagraphStyle("H1",
            fontName=F("semibold"), fontSize=28, leading=34,
            textColor=SHADOW_BLACK, spaceAfter=5*mm),

        "h2": ParagraphStyle("H2",
            fontName=F("semibold"), fontSize=20, leading=26,
            textColor=SHADOW_BLACK, spaceAfter=4*mm),

        "cap_title": ParagraphStyle("CapTitle",
            fontName=F("semibold"), fontSize=13, leading=17,
            textColor=MIDNIGHT_VIOLET, spaceAfter=2*mm),

        "use_title": ParagraphStyle("UseTitle",
            fontName=F("semibold"), fontSize=11, leading=15,
            textColor=MIDNIGHT_VIOLET, spaceAfter=1*mm),

        "body": ParagraphStyle("Body",
            fontName=F("regular"), fontSize=11, leading=16,
            textColor=SHADOW_BLACK, spaceAfter=3*mm),

        "body_sm": ParagraphStyle("BodySm",
            fontName=F("regular"), fontSize=10, leading=15,
            textColor=SHADOW_BLACK),

        "kpi_value": ParagraphStyle("KpiValue",
            fontName=F("semibold"), fontSize=18, leading=24,
            textColor=MIDNIGHT_VIOLET, alignment=TA_CENTER),

        "kpi_label": ParagraphStyle("KpiLabel",
            fontName=F("regular"), fontSize=9, leading=13,
            textColor=SHADOW_BLACK, alignment=TA_CENTER),

        "trusted": ParagraphStyle("Trusted",
            fontName=F("semibold"), fontSize=18, leading=24,
            textColor=SHADOW_BLACK, alignment=TA_CENTER, spaceAfter=4*mm),

        "cta": ParagraphStyle("CTA",
            fontName=F("semibold"), fontSize=18, leading=24,
            textColor=SHADOW_BLACK, alignment=TA_CENTER, spaceAfter=4*mm),

        "client_name": ParagraphStyle("ClientName",
            fontName=F("semibold"), fontSize=10, leading=13,
            textColor=SHADOW_BLACK, alignment=TA_CENTER),

        "partner_logo_placeholder": ParagraphStyle("PartnerLogoPlaceholder",
            fontName=F("semibold"), fontSize=12, leading=15,
            textColor=MIDNIGHT_VIOLET, alignment=TA_RIGHT),
    }


# ── Brand Icons (drawn in reportlab) ──────────────────────────────────────────
class BrandIcon(Flowable):
    """
    Draws a 32×32mm brand-aligned icon for a capability block.
    Icons use Optimove brand language: Midnight Violet + Lime Glow + Signal Mist.

    icon_type options:
      "audience"   — overlapping circles (segmentation / data power)
      "campaign"   — connected nodes with arrow (campaign flow)
      "sync"       — circular arrows (integration / sync)
      "predict"    — upward trend with spark (AI / prediction)
      "personalize"— person silhouette with sparkle (personalization)
      "target"     — concentric rings with center dot (targeting)
    """
    ICON_TYPES = ["audience", "campaign", "sync", "predict", "personalize", "target"]

    def __init__(self, size=30*mm, icon_type="audience", index=0):
        super().__init__()
        types = self.ICON_TYPES
        self.icon_type = types[index % len(types)] if icon_type == "auto" else icon_type
        self.size = size
        self.width  = size
        self.height = size

    def draw(self):
        c = self.canv
        s = self.size
        cx, cy = s / 2, s / 2

        if self.icon_type == "audience":
            self._draw_audience(c, cx, cy, s)
        elif self.icon_type == "campaign":
            self._draw_campaign(c, cx, cy, s)
        elif self.icon_type == "sync":
            self._draw_sync(c, cx, cy, s)
        elif self.icon_type == "predict":
            self._draw_predict(c, cx, cy, s)
        elif self.icon_type == "personalize":
            self._draw_personalize(c, cx, cy, s)
        elif self.icon_type == "target":
            self._draw_target(c, cx, cy, s)

    # ── Individual icon drawings ───────────────────────────────────────────────

    def _draw_audience(self, c, cx, cy, s):
        """Three overlapping circles — audience/segmentation."""
        from reportlab.lib.colors import Color as RLColor
        r = s * 0.28
        offset = s * 0.15

        def filled_circle(x, y, hex_color, alpha=1.0):
            base = HexColor(hex_color)
            col = RLColor(base.red, base.green, base.blue, alpha)
            c.setFillColor(col)
            c.circle(x, y, r, fill=1, stroke=0)

        filled_circle(cx - offset * 0.8, cy + offset * 0.5, "#302c69", 0.9)
        filled_circle(cx + offset * 0.8, cy + offset * 0.5, "#9e97cb", 0.9)
        filled_circle(cx, cy - offset * 0.3, "#dff670", 0.85)
        c.setFillColor(PURE_WHITE)
        c.circle(cx, cy + offset * 0.18, r * 0.22, fill=1, stroke=0)

    def _draw_campaign(self, c, cx, cy, s):
        """Connected nodes with directional arrows — campaign flow."""
        node_r = s * 0.09
        # Three nodes: left, center-top, right
        nodes = [
            (cx - s*0.28, cy - s*0.1),
            (cx,           cy + s*0.18),
            (cx + s*0.28,  cy - s*0.1),
        ]
        colors = [MIDNIGHT_VIOLET, LIME_GLOW, SIGNAL_MIST]

        # Draw connecting lines
        c.setStrokeColor(STORM_TINT)
        c.setLineWidth(1.5)
        for i in range(len(nodes)):
            j = (i + 1) % len(nodes)
            c.line(nodes[i][0], nodes[i][1], nodes[j][0], nodes[j][1])

        # Draw arrow on last connection
        c.setStrokeColor(MIDNIGHT_VIOLET)
        c.setLineWidth(1.8)
        # Arrow from node[1] to node[2]
        x1, y1 = nodes[1]
        x2, y2 = nodes[2]
        c.line(x1, y1, x2, y2)
        # Arrowhead
        ang = math.atan2(y2 - y1, x2 - x1)
        ah = s * 0.06
        c.setFillColor(MIDNIGHT_VIOLET)
        ax1 = x2 - ah * math.cos(ang - 0.4)
        ay1 = y2 - ah * math.sin(ang - 0.4)
        ax2 = x2 - ah * math.cos(ang + 0.4)
        ay2 = y2 - ah * math.sin(ang + 0.4)
        p = c.beginPath()
        p.moveTo(x2, y2)
        p.lineTo(ax1, ay1)
        p.lineTo(ax2, ay2)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # Draw nodes (circles) on top
        for (nx, ny), col in zip(nodes, colors):
            c.setFillColor(col)
            c.circle(nx, ny, node_r, fill=1, stroke=0)

    def _draw_sync(self, c, cx, cy, s):
        """Circular sync arrows — integration."""
        r = s * 0.3
        lw = s * 0.06
        c.setLineWidth(lw)
        c.setLineCap(1)

        # Top arc (Midnight Violet)
        c.setStrokeColor(MIDNIGHT_VIOLET)
        c.arc(cx - r, cy - r, cx + r, cy + r, startAng=30, extent=150)

        # Bottom arc (Lime Glow)
        c.setStrokeColor(LIME_GLOW)
        c.arc(cx - r, cy - r, cx + r, cy + r, startAng=210, extent=150)

        # Arrowheads
        def arrowhead(angle_deg, color):
            ang = math.radians(angle_deg)
            tip_x = cx + r * math.cos(ang)
            tip_y = cy + r * math.sin(ang)
            ah = s * 0.08
            perp = math.radians(angle_deg + 90)
            ax1 = tip_x + ah * math.cos(ang - 2.5)
            ay1 = tip_y + ah * math.sin(ang - 2.5)
            ax2 = tip_x + ah * math.cos(ang + 2.5)
            ay2 = tip_y + ah * math.sin(ang + 2.5)
            c.setFillColor(color)
            p = c.beginPath()
            p.moveTo(tip_x, tip_y)
            p.lineTo(ax1, ay1)
            p.lineTo(ax2, ay2)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

        arrowhead(180, MIDNIGHT_VIOLET)
        arrowhead(0,   LIME_GLOW)

    def _draw_predict(self, c, cx, cy, s):
        """Ascending bars with Lime Glow spark — AI / prediction."""
        bar_w   = s * 0.1
        bar_gap = s * 0.05
        n_bars  = 4
        total_w = n_bars * bar_w + (n_bars - 1) * bar_gap
        x_start = cx - total_w / 2
        bar_heights = [s*0.12, s*0.20, s*0.28, s*0.36]
        base_y = cy - s * 0.2
        bar_colors = [SOFT_PERIWINKLE, SIGNAL_MIST, ECHO_OF_IRIS, MIDNIGHT_VIOLET]

        for i, bh in enumerate(bar_heights):
            bx = x_start + i * (bar_w + bar_gap)
            c.setFillColor(bar_colors[i])
            c.rect(bx, base_y, bar_w, bh, fill=1, stroke=0)

        # Lime Glow dot above tallest bar
        spark_x = x_start + 3 * (bar_w + bar_gap) + bar_w / 2
        spark_y = base_y + bar_heights[-1] + s * 0.07
        spark_r = s * 0.06
        c.setFillColor(LIME_GLOW)
        c.circle(spark_x, spark_y, spark_r, fill=1, stroke=0)
        c.setFillColor(MIDNIGHT_VIOLET)
        c.circle(spark_x, spark_y, spark_r * 0.4, fill=1, stroke=0)

    def _draw_personalize(self, c, cx, cy, s):
        """Person silhouette with sparkle ring — personalization."""
        # Head
        c.setFillColor(MIDNIGHT_VIOLET)
        head_r = s * 0.11
        head_cx = cx - s * 0.05
        head_cy = cy + s * 0.12
        c.circle(head_cx, head_cy, head_r, fill=1, stroke=0)

        # Body (rounded trapezoid)
        bw_top = s * 0.14
        bw_bot = s * 0.22
        bh = s * 0.22
        body_cy = head_cy - head_r - bh * 0.5
        c.setFillColor(SIGNAL_MIST)
        p = c.beginPath()
        p.moveTo(head_cx - bw_top, body_cy + bh/2)
        p.lineTo(head_cx + bw_top, body_cy + bh/2)
        p.lineTo(head_cx + bw_bot, body_cy - bh/2)
        p.lineTo(head_cx - bw_bot, body_cy - bh/2)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # Lime sparkles around the right side
        spark_cx = cx + s * 0.16
        spark_cy = cy + s * 0.1
        c.setFillColor(LIME_GLOW)
        for angle, size_factor in [(0, 1.0), (100, 0.65), (200, 0.75), (300, 0.55)]:
            a = math.radians(angle)
            r_from_center = s * 0.17 * size_factor
            sx = spark_cx + r_from_center * math.cos(a) * 0.6
            sy = spark_cy + r_from_center * math.sin(a) * 0.6
            c.circle(sx, sy, s * 0.04 * size_factor, fill=1, stroke=0)

    def _draw_target(self, c, cx, cy, s):
        """Concentric rings with center dot — targeting / focus."""
        radii = [s*0.32, s*0.22, s*0.12]
        colors = [SOFT_PERIWINKLE, SIGNAL_MIST, MIDNIGHT_VIOLET]
        stroke_colors = [MIDNIGHT_VIOLET, MIDNIGHT_VIOLET, None]

        for r, fill_col, stroke_col in zip(radii, colors, stroke_colors):
            c.setFillColor(fill_col)
            if stroke_col:
                c.setStrokeColor(stroke_col)
                c.setLineWidth(0.5)
                c.circle(cx, cy, r, fill=1, stroke=1)
            else:
                c.circle(cx, cy, r, fill=1, stroke=0)

        # Center Lime Glow dot
        c.setFillColor(LIME_GLOW)
        c.circle(cx, cy, s * 0.045, fill=1, stroke=0)


# ── Logo helpers ───────────────────────────────────────────────────────────────
def _load_logo_image(path_or_url, max_height_mm, max_width_mm=None):
    """Load a logo image as a reportlab Image flowable."""
    if not path_or_url:
        return None
    p = Path(path_or_url)
    if not p.exists():
        return None
    try:
        from PIL import Image as PILImage
        pil = PILImage.open(str(p))
        w_px, h_px = pil.size
        aspect = w_px / h_px
        img_h = max_height_mm * mm
        img_w = img_h * aspect
        if max_width_mm and img_w > max_width_mm * mm:
            img_w = max_width_mm * mm
            img_h = img_w / aspect
        return Image(str(p), width=img_w, height=img_h)
    except Exception:
        try:
            img = Image(str(p), height=max_height_mm * mm)
            return img
        except Exception:
            return None


class LogoHeader(Flowable):
    """
    Renders the header bar:
      [Optimove Logo]         [Partner Logo or Name]
    """
    def __init__(self, width, partner_name,
                 optimove_logo_path=None, partner_logo_path=None):
        super().__init__()
        self.bar_width          = width
        self.partner_name       = partner_name
        self.optimove_logo_path = optimove_logo_path
        self.partner_logo_path  = partner_logo_path
        self.width  = width
        self.height = 16 * mm

    def draw(self):
        c    = self.canv
        w, h = self.bar_width, self.height
        logo_h_mm = 9
        logo_h    = logo_h_mm * mm

        # ── Optimove logo (left) ──────────────────────────────────────────────
        drawn = False
        if self.optimove_logo_path and Path(self.optimove_logo_path).exists():
            try:
                from PIL import Image as PILImage
                pil = PILImage.open(self.optimove_logo_path)
                pw, ph = pil.size
                aspect = pw / ph
                draw_h = logo_h
                draw_w = draw_h * aspect
                img = Image(self.optimove_logo_path, width=draw_w, height=draw_h)
                img.drawOn(c, 0, (h - draw_h) / 2)
                drawn = True
            except Exception:
                pass

        if not drawn:
            c.setFont(F("bold"), 13)
            c.setFillColor(MIDNIGHT_VIOLET)
            c.drawString(0, h / 2 - 4*mm, "IA OPTIMOVE")

        # ── Partner logo (right) ──────────────────────────────────────────────
        partner_drawn = False
        if self.partner_logo_path and Path(self.partner_logo_path).exists():
            try:
                from PIL import Image as PILImage
                pil = PILImage.open(self.partner_logo_path)
                pw, ph = pil.size
                aspect = pw / ph
                draw_h = logo_h
                draw_w = min(draw_h * aspect, 50*mm)
                img = Image(self.partner_logo_path, width=draw_w, height=draw_h)
                img.drawOn(c, w - draw_w, (h - draw_h) / 2)
                partner_drawn = True
            except Exception:
                pass

        if not partner_drawn:
            c.setFont(F("semibold"), 11)
            c.setFillColor(SHADOW_BLACK)
            c.drawRightString(w, h / 2 - 3.5*mm, self.partner_name)

        c.setStrokeColor(STORM_TINT)
        c.setLineWidth(0.5)
        c.line(0, 0, w, 0)



# ── Footer ─────────────────────────────────────────────────────────────────────
def _draw_footer(canvas, page_w, margin):
    """Draws the footer line on every page — website left, email right."""
    register_fonts()
    canvas.saveState()
    y = 7 * mm
    canvas.setStrokeColor(STORM_TINT)
    canvas.setLineWidth(0.5)
    canvas.line(margin, y + 4*mm, page_w - margin, y + 4*mm)
    canvas.setFont(F("light"), 8)
    canvas.setFillColor(SIGNAL_MIST)
    canvas.drawString(margin, y, "Partners.optimove.com")
    canvas.drawRightString(page_w - margin, y, "Partnerships@optimove.com")
    canvas.restoreState()


# ── Default capabilities (3 minimum) ───────────────────────────────────────────
_DEFAULT_CAPABILITIES = [
    {
        "title": "AI-powered audience segmentation for precise ad targeting",
        "description": "Sync Optimove's AI-built customer segments—from cart abandoners to VIPs—directly into your channels, keeping every campaign fresh and hyper-targeted.",
    },
    {
        "title": "Customer profile enrichment for smarter ad targeting",
        "description": "Enrich every customer profile with behavioral, transactional, and predictive data so your campaigns reach the right person with the right message at the right time.",
    },
    {
        "title": "Personalized campaign orchestration at scale",
        "description": "Automate multi-step campaign logic across channels with real-time signals, reducing manual effort while boosting engagement and conversion rates.",
    },
    {
        "title": "Predictive modeling to maximize return on ad spend",
        "description": "Identify high-value customers, predict churn risk, and allocate budget to the segments most likely to convert—driving higher ROAS with less waste.",
    },
]

def ensure_capabilities(data: dict) -> list:
    """Return at least 3 capabilities, filling gaps with sensible defaults."""
    caps = list(data.get("capabilities", []))
    while len(caps) < 3:
        caps.append(_DEFAULT_CAPABILITIES[len(caps) % len(_DEFAULT_CAPABILITIES)])
    return caps[:3]


# ── Grayscale logo helper ───────────────────────────────────────────────────────
def fetch_and_grayscale_logo(name: str, domain: str = None,
                              direct_url: str = None,
                              max_height_mm: float = 10,
                              max_width_mm: float = 40) -> "Image | None":
    """Fetch a company logo and return it as a grayscale reportlab Image."""
    sys.path.insert(0, str(Path(__file__).parent))
    from fetch_logo import fetch_logo as _fetch
    logo_path = _fetch(name, domain, direct_url=direct_url)
    if not logo_path:
        return None
    try:
        from PIL import Image as PILImage
        img = PILImage.open(logo_path).convert("L")   # grayscale
        img = img.convert("RGBA")                      # back to RGBA for transparency support
        # Save greyscale version
        grey_path = logo_path.replace(".png", "_grey.png")
        img.save(grey_path)

        pil_w, pil_h = img.size
        aspect = pil_w / pil_h
        draw_h = max_height_mm * mm
        draw_w = min(draw_h * aspect, max_width_mm * mm)
        if draw_w == max_width_mm * mm:
            draw_h = draw_w / aspect
        return Image(grey_path, width=draw_w, height=draw_h)
    except Exception as e:
        print(f"  ⚠️  Grayscale conversion failed for {name}: {e}")
        return None


# ── Page 1 ─────────────────────────────────────────────────────────────────────
def build_page1(data, styles, content_width, logos):
    elements = []
    elements.append(LogoHeader(
        content_width, data["partner_name"],
        optimove_logo_path=logos.get("optimove"),
        partner_logo_path=logos.get("partner"),
    ))
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(data["headline"], styles["h1"]))

    intro = data.get("intro", "")
    for p_text in [p.strip() for p in intro.split("\n\n") if p.strip()]:
        elements.append(Paragraph(p_text, styles["body"]))

    elements.append(Spacer(1, 2*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=STORM_TINT, spaceAfter=4*mm))

    icon_types = ["audience", "campaign", "sync", "predict", "personalize", "target"]
    for i, cap in enumerate(ensure_capabilities(data)):
        icon = BrandIcon(size=30*mm, icon_type=icon_types[i % len(icon_types)])
        title_para = Paragraph(cap["title"], styles["cap_title"])
        desc_para  = Paragraph(cap["description"], styles["body_sm"])
        text_block = [title_para, desc_para]
        row = Table([[icon, text_block]], colWidths=[36*mm, content_width - 36*mm])
        row.setStyle(TableStyle([
            ("VALIGN",       (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (-1,-1), 4*mm),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4*mm),
        ]))
        elements.append(row)
    return elements



def balance_kpi_label(text: str) -> str:
    """
    Insert a line break near the midpoint of a multi-word label so that
    both lines are roughly equal width.
    e.g. "Increase Customer Lifetime Value" → "Increase Customer<br/>Lifetime Value"
    """
    words = text.split()
    if len(words) <= 2:
        return text
    # Find split point closest to mid-character-count
    mid = len(text) // 2
    best_i, best_dist = 1, float("inf")
    pos = 0
    for i, w in enumerate(words[:-1]):
        pos += len(w) + 1
        dist = abs(pos - mid)
        if dist < best_dist:
            best_dist = dist
            best_i = i + 1
    return " ".join(words[:best_i]) + "<br/>" + " ".join(words[best_i:])

# ── Page 2 ─────────────────────────────────────────────────────────────────────
def build_page2(data, styles, content_width, logos):
    elements = []
    elements.append(LogoHeader(
        content_width, data["partner_name"],
        optimove_logo_path=logos.get("optimove"),
        partner_logo_path=logos.get("partner"),
    ))
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("Seamlessly power any use case", styles["h2"]))

    for uc in data.get("use_cases", []):
        elements.append(Paragraph(uc["title"], styles["use_title"]))
        elements.append(Paragraph(uc["description"], styles["body_sm"]))
        elements.append(Spacer(1, 3*mm))

    elements.append(Spacer(1, 3*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=STORM_TINT, spaceAfter=4*mm))

    trusted_by = data.get("trusted_by", "1,200+")
    elements.append(Paragraph(f"Trusted by {trusted_by} Brands", styles["trusted"]))

    client_logos = data.get("client_logos", [])
    if client_logos:
        logos_to_show = (client_logos + [""] * 6)[:6]
        rows_data = [logos_to_show[:3], logos_to_show[3:]]
        cell_w = content_width / 3
        grid_data = []
        for row in rows_data:
            grid_row = []
            for name in row:
                label = name if isinstance(name, str) else (name.get("name","") if isinstance(name, dict) else "")
                if label:
                    # Check for pre-downloaded local path first
                    logo_local = name.get("logo_path") if isinstance(name, dict) else None
                    if logo_local and Path(logo_local).exists():
                        logo_img = _load_logo_image(logo_local, max_height_mm=9, max_width_mm=38)
                    else:
                        logo_direct_url = name.get("logo_url") if isinstance(name, dict) else None
                        logo_img = fetch_and_grayscale_logo(label, direct_url=logo_direct_url,
                                                            max_height_mm=9, max_width_mm=38)
                    if logo_img:
                        grid_row.append(logo_img)
                    else:
                        grid_row.append(Paragraph(label, styles["client_name"]))
                else:
                    grid_row.append(Spacer(1, 1))
            grid_data.append(grid_row)
        grid = Table(grid_data, colWidths=[cell_w]*3, rowHeights=[14*mm, 14*mm])
        grid.setStyle(TableStyle([
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("LEFTPADDING", (0,0), (-1,-1), 4*mm),
            ("RIGHTPADDING",(0,0), (-1,-1), 4*mm),
        ]))
        elements.append(grid)

    quote = data.get("client_quote")
    if quote and quote.get("text"):
        elements.append(Spacer(1, 3*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=SOFT_PERIWINKLE, spaceAfter=3*mm))
        q_style = ParagraphStyle("Quote",
            fontName=F("light"), fontSize=10, leading=16,
            textColor=MIDNIGHT_VIOLET, alignment=TA_CENTER,
            leftIndent=12*mm, rightIndent=12*mm)
        a_style = ParagraphStyle("Attrib",
            fontName=F("semibold"), fontSize=9, leading=13,
            textColor=SHADOW_BLACK, alignment=TA_CENTER, spaceAfter=2*mm)
        q_text = "“" + quote["text"] + "”"
        elements.append(Paragraph(q_text, q_style))
        if quote.get("attribution"):
            elements.append(Paragraph(quote["attribution"], a_style))

    elements.append(Spacer(1, 3*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=STORM_TINT, spaceAfter=4*mm))

    cta = data.get("cta", "Do more when you go Positionless")
    elements.append(Paragraph(cta, styles["cta"]))

    kpis = data.get("kpis", [])[:3]
    if kpis:
        n = len(kpis)
        col_w = content_width / n
        kpi_data = [[[Paragraph(k["value"], styles["kpi_value"]),
                      Paragraph(balance_kpi_label(k["label"]), styles["kpi_label"])] for k in kpis]]
        kpi_table = Table(kpi_data, colWidths=[col_w]*n, rowHeights=[22*mm])
        ts = [
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("LEFTPADDING", (0,0), (-1,-1), 2*mm),
            ("RIGHTPADDING",(0,0), (-1,-1), 2*mm),
        ]
        for i in range(n-1):
            ts.append(("LINEAFTER", (i,0), (i,0), 0.5, STORM_TINT))
        kpi_table.setStyle(TableStyle(ts))
        elements.append(kpi_table)

    return elements


# ── Main ───────────────────────────────────────────────────────────────────────
def generate(data_path: str, output_dir: str) -> str:
    with open(data_path) as f:
        data = json.load(f)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    partner   = data["partner_name"]
    safe_name = re.sub(r'[^\w\s-]', '', partner).strip()
    out_file  = output_dir / f"Optimove x {safe_name} - One Pager.pdf"

    PAGE_W, PAGE_H = A4
    MARGIN         = 20 * mm
    content_width  = PAGE_W - 2 * MARGIN

    print("Fetching logos...")
    sys.path.insert(0, str(Path(__file__).parent))
    from fetch_logo import fetch_logo, get_optimove_logo_png

    logos = {"optimove": get_optimove_logo_png(height_px=54), "partner": None}

    partner_logo_url = data.get("partner_logo_url") or data.get("logo_url")
    if partner_logo_url and Path(partner_logo_url).exists():
        logos["partner"] = partner_logo_url
    else:
        partner_domain = data.get("partner_domain")
        direct_url = data.get("partner_logo_direct_url")
        logos["partner"] = fetch_logo(partner, partner_domain, direct_url=direct_url)

    FOOTER_H = 10*mm
    doc = SimpleDocTemplate(
        str(out_file), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN + FOOTER_H,
        title=f"Optimove x {partner} - Partner One Pager",
        author="Optimove",
    )

    styles = make_styles()
    story  = []
    story += build_page1(data, styles, content_width, logos)
    story.append(PageBreak())
    story += build_page2(data, styles, content_width, logos)
    def draw_footer(canvas, doc):
        _draw_footer(canvas, PAGE_W, MARGIN)
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    print(f"✅ PDF generated: {out_file}")
    return str(out_file)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: generate_pdf.py <partner_data.json> <output_dir>")
        sys.exit(1)
    generate(sys.argv[1], sys.argv[2])
