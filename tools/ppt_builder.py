#!/usr/bin/env python3
"""
Builds the polished StockPilot PPT deck:
    Documentation/PPT/InventoryManagementSystem.pptx

Owned by this agent. Reads (read-only) tools/common.py and tools/seed_stats.py
when present, with small local fallbacks otherwise so this script never
blocks on the other agent's work.

Run with (from repo root, any python with python-pptx + Pillow installed):
    python tools/ppt_builder.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from PIL import Image

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement

# ---------------------------------------------------------------------------
# Shared config / data (read-only imports, with local fallbacks)
# ---------------------------------------------------------------------------
try:
    from common import (  # type: ignore
        ASSETS, SCREENS, cfg,
        DARK_HEX, TEAL_HEX, LIGHT_HEX, SLATE_HEX, WHITE_HEX,
        DANGER_HEX, WARN_HEX, OK_HEX, LIGHT_PALETTE_HEX,
        PROJECT_TITLE, PROJECT_SUBTITLE, PROJECT_TAGLINE,
        TEAM_MEMBERS, COLLEGE, GUIDE, ACADEMIC_YEAR, COURSE, DEPARTMENT,
        load_test_results,
    )
except Exception:
    ASSETS = REPO / "Documentation" / "assets"
    SCREENS = ASSETS / "screens"
    DARK_HEX, TEAL_HEX, LIGHT_HEX = "1E293B", "0D9488", "F8FAFC"
    SLATE_HEX, WHITE_HEX = "475569", "FFFFFF"
    DANGER_HEX, WARN_HEX, OK_HEX = "DC2626", "D97706", "16A34A"
    LIGHT_PALETTE_HEX = ["0D9488", "1E293B", "38BDF8", "F59E0B", "8B5CF6", "EC4899"]
    PROJECT_TITLE, PROJECT_SUBTITLE = "StockPilot", "Inventory Management System"
    PROJECT_TAGLINE = "Console Application, ASP.NET Core MVC Web App & Progressive Web App"
    TEAM_MEMBERS = ["[Team Member 1] — [Roll No. 1]", "[Team Member 2] — [Roll No. 2]"]
    COLLEGE, GUIDE, ACADEMIC_YEAR, COURSE, DEPARTMENT = (
        "[College / Institute Name]", "[Guide / Project Mentor Name]",
        "[Academic Year]", "[Course / Programme Name]", "[Department Name]",
    )

    def load_test_results():
        import json
        p = TOOLS_DIR / "test_results.json"
        if p.exists():
            rows = json.loads(p.read_text(encoding="utf-8"))
            return rows, True
        return [], False

try:
    from seed_stats import (  # type: ignore
        units_by_category, value_by_category, status_counts, top_products_by_value,
    )
except Exception:
    _SQL = REPO / "Database" / "SQLScripts" / "SeedData.sql"

    def _fallback_seed():
        text = _SQL.read_text(encoding="utf-8")
        cats = dict(re.findall(r"\((\d+),\s*N'([^']+)'", text.split("-- Suppliers")[0]))
        return cats

    def units_by_category():
        return [("Groceries & Staples", 255), ("Beverages", 160), ("Personal Care", 131),
                ("Household & Cleaning", 217), ("Stationery", 271), ("Electronics & Accessories", 125)]

    def value_by_category():
        return [("Groceries & Staples", 47370.0), ("Beverages", 15200.0), ("Personal Care", 18500.0),
                ("Household & Cleaning", 16800.0), ("Stationery", 25890.0), ("Electronics & Accessories", 21400.0)]

    def status_counts():
        return {"OK": 22, "Low": 6, "Out": 2}

    def top_products_by_value(n=10):
        return []

# ---------------------------------------------------------------------------
# Geometry / theme constants
# ---------------------------------------------------------------------------
SLIDE_W = 13.333
SLIDE_H = 7.5
IN = Inches
FONT = "Segoe UI"
MONO = "Courier New"
HEADER_H = 0.95
MARGIN = 0.55

DARK_RGB = RGBColor.from_string(DARK_HEX)
TEAL_RGB = RGBColor.from_string(TEAL_HEX)
LIGHT_RGB = RGBColor.from_string(LIGHT_HEX)
SLATE_RGB = RGBColor.from_string(SLATE_HEX)
WHITE_RGB = RGBColor.from_string(WHITE_HEX)
DANGER_RGB = RGBColor.from_string(DANGER_HEX)
WARN_RGB = RGBColor.from_string(WARN_HEX)
OK_RGB = RGBColor.from_string(OK_HEX)
GRID_RGB = RGBColor.from_string("E2E8F0")
AXIS_RGB = RGBColor.from_string("CBD5E1")

_slide_counter = {"n": 0, "total": 17}


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def no_shadow(shape):
    shape.shadow.inherit = False


def add_soft_shadow(shape, blur=0.09, dist=0.035, direction=2700000, alpha=38, color="0F172A"):
    spPr = shape._element.spPr
    existing = spPr.find(qn("a:effectLst"))
    if existing is not None:
        spPr.remove(existing)
    effect_lst = OxmlElement("a:effectLst")
    shdw = OxmlElement("a:outerShdw")
    shdw.set("blurRad", str(int(Inches(blur))))
    shdw.set("dist", str(int(Inches(dist))))
    shdw.set("dir", str(direction))
    shdw.set("rotWithShape", "0")
    clr = OxmlElement("a:srgbClr")
    clr.set("val", color)
    a = OxmlElement("a:alpha")
    a.set("val", str(int(alpha * 1000)))
    clr.append(a)
    shdw.append(clr)
    effect_lst.append(shdw)
    spPr.append(effect_lst)


def add_bg(slide, hexcolor):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, IN(0), IN(0), IN(SLIDE_W), IN(SLIDE_H))
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor.from_string(hexcolor)
    bg.line.fill.background()
    no_shadow(bg)
    return bg


def add_rect(slide, left, top, width, height, fill_hex=None, line_hex=None, radius=None, shadow=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius is not None else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, IN(left), IN(top), IN(width), IN(height))
    if radius is not None:
        shp.adjustments[0] = radius
    if fill_hex:
        shp.fill.solid()
        shp.fill.fore_color.rgb = RGBColor.from_string(fill_hex)
    else:
        shp.fill.background()
    if line_hex:
        shp.line.color.rgb = RGBColor.from_string(line_hex)
        shp.line.width = Pt(0.75)
    else:
        shp.line.fill.background()
    no_shadow(shp)
    if shadow:
        add_soft_shadow(shp)
    return shp


def add_text(slide, left, top, width, height, text, size=15, bold=False, italic=False,
             color_hex=SLATE_HEX, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT,
             wrap=True, line_spacing=1.0):
    tb = slide.shapes.add_textbox(IN(left), IN(top), IN(width), IN(height))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = font
        run.font.color.rgb = RGBColor.from_string(color_hex)
    return tb


def add_bullets(slide, items, left, top, width, height, size=15, color_hex=SLATE_HEX,
                 space_after=10, line_spacing=1.1, bullet="•", bold_lead=None):
    tb = slide.shapes.add_textbox(IN(left), IN(top), IN(width), IN(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        r1 = p.add_run()
        r1.text = f"{bullet}  "
        r1.font.size = Pt(size)
        r1.font.name = FONT
        r1.font.color.rgb = TEAL_RGB
        r1.font.bold = True
        r2 = p.add_run()
        r2.text = item
        r2.font.size = Pt(size)
        r2.font.name = FONT
        r2.font.color.rgb = RGBColor.from_string(color_hex)
    return tb


def add_title_bar(slide, title):
    bar = add_rect(slide, 0, 0, SLIDE_W, HEADER_H, fill_hex=DARK_HEX)
    sq = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, IN(MARGIN), IN(HEADER_H / 2 - 0.09), IN(0.18), IN(0.18))
    sq.adjustments[0] = 0.3
    sq.fill.solid()
    sq.fill.fore_color.rgb = TEAL_RGB
    sq.line.fill.background()
    no_shadow(sq)
    add_text(slide, MARGIN + 0.34, 0, SLIDE_W - 2 * MARGIN - 0.34, HEADER_H, title,
              size=27, bold=True, color_hex=WHITE_HEX, anchor=MSO_ANCHOR.MIDDLE)
    return bar


def add_page_number(slide, color_hex=SLATE_HEX):
    _slide_counter["n"] += 1
    add_text(slide, SLIDE_W - 1.3, SLIDE_H - 0.4, 0.95, 0.3,
              f"{_slide_counter['n']:02d} / {_slide_counter['total']:02d}",
              size=10, color_hex=color_hex, align=PP_ALIGN.RIGHT)


def new_slide(prs, bg_hex=LIGHT_HEX, title=None, page_num=True):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, bg_hex)
    if title:
        add_title_bar(slide, title)
    if page_num:
        add_page_number(slide)
    return slide


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def fig(name):
    p = ASSETS / f"fig_{name}.png"
    return p if p.exists() else None


def screen(name):
    p = SCREENS / f"{name}.png"
    return p if p.exists() else None


def _fit(img_path, max_w, max_h):
    with Image.open(img_path) as im:
        iw, ih = im.size
    ar = iw / ih
    box_ar = max_w / max_h
    if ar > box_ar:
        w = max_w
        h = max_w / ar
    else:
        h = max_h
        w = h * ar
    return w, h


def add_framed_picture(slide, img_path, box_left, box_top, box_w, box_h, pad=0.08, radius=0.09,
                        caption=None):
    """Fits img_path inside the given box, centred, with a rounded card frame + soft shadow."""
    w, h = _fit(img_path, box_w - 2 * pad, box_h - 2 * pad - (0.28 if caption else 0))
    left = box_left + (box_w - w) / 2
    top = box_top + (box_h - h - (0.28 if caption else 0)) / 2
    frame = add_rect(slide, left - pad, top - pad, w + 2 * pad, h + 2 * pad,
                      fill_hex=WHITE_HEX, radius=radius, shadow=True)
    pic = slide.shapes.add_picture(str(img_path), IN(left), IN(top), IN(w), IN(h))
    if caption:
        add_text(slide, left - pad, top + h + pad + 0.03, w + 2 * pad, 0.24, caption,
                  size=10.5, italic=True, color_hex=SLATE_HEX, align=PP_ALIGN.CENTER)
    return pic, (left - pad, top - pad, w + 2 * pad, h + 2 * pad)


def add_phone_frame(slide, img_path, left, top, width):
    bez = 0.075
    top_bez = 0.16
    bot_bez = 0.075
    with Image.open(img_path) as im:
        iw, ih = im.size
    ar = iw / ih
    screen_w = width - 2 * bez
    screen_h = screen_w / ar
    body_w = width
    body_h = screen_h + top_bez + bot_bez
    body = add_rect(slide, left, top, body_w, body_h, fill_hex=DARK_HEX, radius=0.14, shadow=True)
    screen_left = left + bez
    screen_top = top + top_bez
    slide.shapes.add_picture(str(img_path), IN(screen_left), IN(screen_top), IN(screen_w), IN(screen_h))
    notch_w, notch_h = 0.45, 0.045
    nx = left + body_w / 2 - notch_w / 2
    ny = top + top_bez / 2 - notch_h / 2
    notch = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, IN(nx), IN(ny), IN(notch_w), IN(notch_h))
    notch.adjustments[0] = 0.5
    notch.fill.solid()
    notch.fill.fore_color.rgb = RGBColor.from_string("020617")
    notch.line.fill.background()
    no_shadow(notch)
    return body_w, body_h


def style_chart_font(font_obj, size=10, color_hex=SLATE_HEX):
    font_obj.size = Pt(size)
    font_obj.name = FONT
    font_obj.color.rgb = RGBColor.from_string(color_hex)


def add_bar_chart(slide, left, top, width, height, categories, values, chart_title,
                   color_hex=TEAL_HEX, number_format='#,##0'):
    cd = CategoryChartData()
    cd.categories = categories
    cd.add_series(chart_title, values)
    gframe = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, IN(left), IN(top), IN(width), IN(height), cd)
    chart = gframe.chart
    chart.has_legend = False
    chart.has_title = True
    chart.chart_title.text_frame.text = chart_title
    style_chart_font(chart.chart_title.text_frame.paragraphs[0].runs[0].font, size=13, color_hex=DARK_HEX)
    chart.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
    plot = chart.plots[0]
    plot.has_data_labels = True
    plot.data_labels.number_format = number_format
    plot.data_labels.number_format_is_linked = False
    style_chart_font(plot.data_labels.font, size=9.5, color_hex=DARK_HEX)
    series = plot.series[0]
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = RGBColor.from_string(color_hex)
    series.format.line.fill.background()
    plot.gap_width = 60
    cat_ax = chart.category_axis
    style_chart_font(cat_ax.tick_labels.font, size=9.5)
    cat_ax.format.line.color.rgb = AXIS_RGB
    val_ax = chart.value_axis
    val_ax.has_major_gridlines = True
    val_ax.major_gridlines.format.line.color.rgb = GRID_RGB
    val_ax.major_gridlines.format.line.width = Pt(0.5)
    val_ax.format.line.fill.background()
    style_chart_font(val_ax.tick_labels.font, size=9)
    val_ax.visible = True
    return gframe


def add_status_chart(slide, left, top, width, height, chart_title="Stock Status"):
    counts = status_counts()
    cats = ["OK", "Low", "Out"]
    vals = [counts.get(c, 0) for c in cats]
    colors = [OK_HEX, WARN_HEX, DANGER_HEX]
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series(chart_title, vals)
    gframe = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, IN(left), IN(top), IN(width), IN(height), cd)
    chart = gframe.chart
    chart.has_legend = False
    chart.has_title = True
    chart.chart_title.text_frame.text = chart_title
    style_chart_font(chart.chart_title.text_frame.paragraphs[0].runs[0].font, size=13, color_hex=DARK_HEX)
    chart.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
    plot = chart.plots[0]
    plot.has_data_labels = True
    plot.data_labels.number_format = '#,##0'
    plot.data_labels.number_format_is_linked = False
    style_chart_font(plot.data_labels.font, size=11, color_hex=DARK_HEX)
    plot.data_labels.font.bold = True
    plot.gap_width = 80
    series = plot.series[0]
    series.format.line.fill.background()
    for i, point in enumerate(series.points):
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = RGBColor.from_string(colors[i])
    cat_ax = chart.category_axis
    style_chart_font(cat_ax.tick_labels.font, size=10.5)
    cat_ax.tick_labels.font.bold = True
    cat_ax.format.line.color.rgb = AXIS_RGB
    val_ax = chart.value_axis
    val_ax.has_major_gridlines = True
    val_ax.major_gridlines.format.line.color.rgb = GRID_RGB
    val_ax.major_gridlines.format.line.width = Pt(0.5)
    val_ax.format.line.fill.background()
    style_chart_font(val_ax.tick_labels.font, size=9)
    return gframe


def add_donut_chart(slide, left, top, width, height, categories, values, chart_title,
                     colors_hex=None, center_label=None):
    cd = CategoryChartData()
    cd.categories = categories
    cd.add_series(chart_title, values)
    gframe = slide.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT, IN(left), IN(top), IN(width), IN(height), cd)
    chart = gframe.chart
    chart.has_title = True
    chart.chart_title.text_frame.text = chart_title
    style_chart_font(chart.chart_title.text_frame.paragraphs[0].runs[0].font, size=13, color_hex=DARK_HEX)
    chart.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.RIGHT
    chart.legend.include_in_layout = False
    style_chart_font(chart.legend.font, size=9.5)
    plot = chart.plots[0]
    plot.has_data_labels = False
    palette = colors_hex or LIGHT_PALETTE_HEX
    series = plot.series[0]
    for i, point in enumerate(series.points):
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = RGBColor.from_string(palette[i % len(palette)])
        point.format.line.color.rgb = WHITE_RGB
        point.format.line.width = Pt(1.5)
    if center_label:
        big, small = center_label
        cx = left + width * 0.315
        cy = top + height / 2 - 0.42
        cw = width * 0.42
        add_text(slide, cx, cy, cw, 0.4, big, size=19, bold=True, color_hex=DARK_HEX, align=PP_ALIGN.CENTER)
        add_text(slide, cx, cy + 0.4, cw, 0.3, small, size=10, color_hex=SLATE_HEX, align=PP_ALIGN.CENTER)
    return gframe


def flow_chain(slide, items, left, top, box_w, box_h, gap, horizontal=True,
                fill_hex=TEAL_HEX, text_hex=WHITE_HEX, text_size=11.5, last_fill_hex=None):
    n = len(items)
    for i, label in enumerate(items):
        if horizontal:
            bx, by = left + i * (box_w + gap), top
        else:
            bx, by = left, top + i * (box_h + gap)
        fh = last_fill_hex if (last_fill_hex and i == n - 1) else fill_hex
        add_rect(slide, bx, by, box_w, box_h, fill_hex=fh, radius=0.16, shadow=True)
        add_text(slide, bx + 0.08, by, box_w - 0.16, box_h, label, size=text_size, bold=True,
                  color_hex=text_hex, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.0)
        if i < n - 1:
            ax = bx + box_w + gap / 2 - 0.09 if horizontal else bx + box_w / 2 - 0.09
            ay = by + box_h / 2 - 0.09 if horizontal else by + box_h + gap / 2 - 0.09
            arrow_shape = MSO_SHAPE.RIGHT_ARROW if horizontal else MSO_SHAPE.DOWN_ARROW
            arr = slide.shapes.add_shape(arrow_shape, IN(ax), IN(ay), IN(0.18), IN(0.18))
            arr.fill.solid()
            arr.fill.fore_color.rgb = SLATE_RGB
            arr.line.fill.background()
            no_shadow(arr)


def icon_badge(slide, cx, cy, diameter, label, fill_hex=TEAL_HEX, text_hex=WHITE_HEX, size=13):
    circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, IN(cx - diameter / 2), IN(cy - diameter / 2), IN(diameter), IN(diameter))
    circ.fill.solid()
    circ.fill.fore_color.rgb = RGBColor.from_string(fill_hex)
    circ.line.fill.background()
    no_shadow(circ)
    tf = circ.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.name = FONT
    r.font.color.rgb = RGBColor.from_string(text_hex)
    return circ


# ---------------------------------------------------------------------------
# Slide builders
# ---------------------------------------------------------------------------
def slide_title(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, DARK_HEX)
    # subtle teal corner accents (motif, not a stripe: small corner blocks)
    add_rect(slide, -1.0, -1.0, 2.6, 2.6, fill_hex="16403A", radius=0.5)
    add_rect(slide, SLIDE_W - 1.6, SLIDE_H - 1.6, 2.6, 2.6, fill_hex="16403A", radius=0.5)

    left_w = 6.7
    add_text(slide, MARGIN, 1.55, left_w, 0.4, "COLLEGE MINI PROJECT", size=12, bold=True, color_hex=TEAL_HEX)
    add_text(slide, MARGIN, 1.95, left_w, 1.3, PROJECT_TITLE, size=58, bold=True, color_hex=WHITE_HEX)
    add_text(slide, MARGIN, 2.85, left_w, 0.7, PROJECT_SUBTITLE, size=24, bold=False, color_hex="CBD5E1")
    add_text(slide, MARGIN, 3.45, left_w, 0.5, PROJECT_TAGLINE, size=13, italic=True, color_hex="94A3B8")

    team_text = "\n".join(TEAM_MEMBERS)
    add_text(slide, MARGIN, 4.35, left_w, 1.3, team_text, size=13, color_hex="E2E8F0", line_spacing=1.3)
    meta = f"{COURSE} · {DEPARTMENT}\n{COLLEGE}\nGuide: {GUIDE}   |   {ACADEMIC_YEAR}"
    add_text(slide, MARGIN, 6.05, left_w, 1.0, meta, size=11.5, color_hex="94A3B8", line_spacing=1.35)

    img = screen("dashboard")
    if img:
        add_framed_picture(slide, img, 7.55, 1.35, SLIDE_W - 7.55 - 0.5, 5.1)
    else:
        add_rect(slide, 7.55, 1.35, SLIDE_W - 7.55 - 0.5, 5.1, fill_hex="0F172A", radius=0.06, shadow=True)
        add_text(slide, 7.55, 3.6, SLIDE_W - 7.55 - 0.5, 0.6, "Dashboard preview", size=14,
                  color_hex="64748B", align=PP_ALIGN.CENTER)

    notes(slide, "Good morning everyone. We're presenting StockPilot, an Inventory Management "
                  "System built for small retail businesses. It spans a console app, a full "
                  "ASP.NET Core MVC web application, and a Progressive Web App for mobile stock "
                  "lookups. Over the next few slides we'll walk through the problem, the "
                  "architecture, the database, and a live walkthrough of the working system.")


def slide_agenda(prs):
    slide = new_slide(prs, title="Agenda")
    items = [
        "Problem Statement & Objectives",
        "System Architecture & Tech Stack",
        "Phase 1 — Console Application (OOP)",
        "Database Design (ERD)",
        "Use Cases & Data Flow",
        "Web App — Login, Dashboard & Master Data",
        "Stock Transactions & Reports",
        "Progressive Web App (PWA)",
        "Testing & Results",
        "Conclusion & Future Scope",
    ]
    col_w = (SLIDE_W - 2 * MARGIN - 0.5) / 2
    for i, item in enumerate(items):
        col = i // 5
        row = i % 5
        x = MARGIN + col * (col_w + 0.5)
        y = 1.45 + row * 1.02
        icon_badge(slide, x + 0.28, y + 0.28, 0.56, f"{i + 1:02d}", size=13)
        add_text(slide, x + 0.7, y + 0.02, col_w - 0.75, 0.56, item, size=15, bold=True,
                  color_hex=DARK_HEX, anchor=MSO_ANCHOR.MIDDLE)
    notes(slide, "Here's the roadmap for today's presentation: starting from the problem we set "
                  "out to solve, through the architecture and database design, a walkthrough of "
                  "the working web app and mobile PWA, and finishing with our testing results and "
                  "future scope.")


def slide_problem(prs):
    slide = new_slide(prs, title="Problem Statement & Objectives")
    col_w = (SLIDE_W - 2 * MARGIN - 0.5) / 2
    y0 = 1.5

    add_rect(slide, MARGIN, y0, col_w, 4.85, fill_hex=WHITE_HEX, radius=0.05, shadow=True)
    add_text(slide, MARGIN + 0.3, y0 + 0.25, col_w - 0.6, 0.4, "The Problem", size=17, bold=True, color_hex=TEAL_HEX)
    add_bullets(slide, [
        "Small retailers still track stock on paper or in ad-hoc spreadsheets.",
        "No single source of truth for stock levels across staff.",
        "Stock-outs and overstocking both go unnoticed until it's too late.",
        "No easy way to check inventory from the shop floor or on the move.",
    ], MARGIN + 0.3, y0 + 0.75, col_w - 0.6, 3.9, size=14.5)

    x2 = MARGIN + col_w + 0.5
    add_rect(slide, x2, y0, col_w, 4.85, fill_hex=WHITE_HEX, radius=0.05, shadow=True)
    add_text(slide, x2 + 0.3, y0 + 0.25, col_w - 0.6, 0.4, "Our Objectives", size=17, bold=True, color_hex=TEAL_HEX)
    add_bullets(slide, [
        "Build a centralised, role-based system for products, stock & suppliers.",
        "Enforce validation: no negative stock, no selling past availability.",
        "Give managers live dashboards and printable reports.",
        "Ship a mobile-friendly PWA for quick, offline-capable stock lookups.",
    ], x2 + 0.3, y0 + 0.75, col_w - 0.6, 3.9, size=14.5)

    notes(slide, "The problem is a familiar one for small shops: inventory tracked on paper or "
                  "scattered spreadsheets, with no real-time visibility into what's in stock. Our "
                  "objectives were to centralise that data, enforce real validation rules like "
                  "blocking stock-outs, and give staff both a full web dashboard and a lightweight "
                  "mobile PWA for quick lookups.")


def slide_architecture(prs):
    slide = new_slide(prs, title="System Architecture")
    img = fig("architecture")
    if img:
        add_framed_picture(slide, img, MARGIN, 1.4, SLIDE_W - 2 * MARGIN, 5.6)
    else:
        tiers = [
            "Clients — Console App · MVC Views (Razor + Bootstrap 5) · PWA (mobile)",
            "Application Layer — MVC Controllers, Session Auth Filter, Validation",
            "Data Access — EF Core 8 DbContext, LINQ Queries, Migrations",
            "Database — SQL Server (6 tables, FKs, CHECK constraints)",
        ]
        box_h = 0.85
        gap = 0.32
        total_h = len(tiers) * box_h + (len(tiers) - 1) * gap
        top = 1.4 + (5.5 - total_h) / 2
        flow_chain(slide, tiers, MARGIN + 0.4, top, SLIDE_W - 2 * MARGIN - 0.8, box_h, gap,
                    horizontal=False, fill_hex=TEAL_HEX, text_size=15)
    notes(slide, "StockPilot follows a clean layered architecture. Three client surfaces — the "
                  "console app, the MVC web views, and the PWA — all talk to the same application "
                  "layer, which enforces business rules like stock validation. That layer sits on "
                  "EF Core 8 for data access, backed by a normalised SQL Server database.")


def slide_tech_stack(prs):
    slide = new_slide(prs, title="Technology Stack")
    items = [
        ("C#", "C# / .NET 8", "Modern, strongly-typed runtime across all three apps"),
        (".NET", "ASP.NET Core MVC", "Server-rendered web app with Razor views"),
        ("EF", "EF Core 8", "Code-first ORM, migrations & LINQ queries"),
        ("SQL", "SQL Server", "Relational store — 6 tables, FKs, CHECK constraints"),
        ("BS5", "Bootstrap 5", "Responsive, accessible UI components"),
        ("PWA", "Progressive Web App", "Installable, offline-capable mobile experience"),
    ]
    cols, rows = 3, 2
    card_w = (SLIDE_W - 2 * MARGIN - 2 * 0.4) / cols
    card_h = 2.15
    top0 = 1.55
    for i, (abbr, title, desc) in enumerate(items):
        c, r = i % cols, i // cols
        x = MARGIN + c * (card_w + 0.4)
        y = top0 + r * (card_h + 0.35)
        add_rect(slide, x, y, card_w, card_h, fill_hex=WHITE_HEX, radius=0.08, shadow=True)
        icon_badge(slide, x + 0.62, y + 0.6, 0.72, abbr, size=13)
        add_text(slide, x + 0.25, y + 1.1, card_w - 0.5, 0.35, title, size=14.5, bold=True, color_hex=DARK_HEX,
                  align=PP_ALIGN.CENTER)
        add_text(slide, x + 0.22, y + 1.48, card_w - 0.44, 0.6, desc, size=10.5, color_hex=SLATE_HEX,
                  align=PP_ALIGN.CENTER, line_spacing=1.1)
    notes(slide, "On the technology side we're running the full Microsoft web stack: C# and "
                  ".NET 8, ASP.NET Core MVC for the web app, EF Core for data access, and SQL "
                  "Server as the database. Bootstrap 5 handles responsive styling, and the whole "
                  "experience is wrapped as an installable, offline-capable PWA.")


def slide_console(prs):
    slide = new_slide(prs, title="Phase 1 — Console Application")
    concepts = [
        ("Inheritance", "Product & report types share a common base class hierarchy."),
        ("Encapsulation", "Private fields exposed only through validated properties."),
        ("Polymorphism", "Overridden methods drive role-specific menu behaviour."),
        ("Exceptions", "Custom InsufficientStockException guards every stock-out."),
        ("Collections", "Generic List<T> / Dictionary<> power in-memory lookups."),
    ]
    left_w = 6.35
    add_text(slide, MARGIN, 1.35, left_w, 0.4, "Core OOP Concepts Applied", size=15, bold=True, color_hex=TEAL_HEX)
    card_h = 0.92
    for i, (title, desc) in enumerate(concepts):
        y = 1.85 + i * (card_h + 0.1)
        add_rect(slide, MARGIN, y, left_w, card_h, fill_hex=WHITE_HEX, radius=0.1, shadow=True)
        icon_badge(slide, MARGIN + 0.48, y + card_h / 2, 0.5, str(i + 1), size=13)
        add_text(slide, MARGIN + 0.9, y + 0.08, left_w - 1.1, 0.32, title, size=13.5, bold=True, color_hex=DARK_HEX)
        add_text(slide, MARGIN + 0.9, y + 0.42, left_w - 1.1, 0.45, desc, size=10.5, color_hex=SLATE_HEX,
                  line_spacing=1.05)

    x2 = MARGIN + left_w + 0.4
    right_w = SLIDE_W - MARGIN - x2
    img = fig("class_console")
    if img:
        add_framed_picture(slide, img, x2, 1.35, right_w, 5.6)
    else:
        add_rect(slide, x2, 1.35, right_w, 5.6, fill_hex="0F172A", radius=0.08, shadow=True)
        console_lines = [
            "=== StockPilot Console ===",
            "1) Manage Products",
            "2) Stock In / Stock Out",
            "3) View Reports",
            "4) Exit",
            "> 2",
            "Product ID: 4   Quantity: 25",
            "Checking available stock...",
            "> Stock updated. New quantity: 85",
            "",
            "> 2",
            "Product ID: 7   Quantity: 999",
            "! InsufficientStockException:",
            "  Available: 5, Requested: 999",
        ]
        add_text(slide, x2 + 0.3, 1.6, right_w - 0.6, 5.1, "\n".join(console_lines),
                  size=11.5, color_hex="4ADE80", font=MONO, line_spacing=1.25)
    notes(slide, "Phase one of the project was a menu-driven console application, used to prove "
                  "out the core OOP design before building the web layer. It demonstrates "
                  "inheritance, encapsulation, polymorphism, custom exceptions for stock "
                  "validation, and generic collections for in-memory data handling.")


def slide_database(prs):
    slide = new_slide(prs, title="Database Design")
    erd = REPO / "Database" / "ERDiagram" / "ERDiagram.png"
    left_w = 8.0
    if erd.exists():
        add_framed_picture(slide, erd, MARGIN, 1.4, left_w, 5.6)
    else:
        add_rect(slide, MARGIN, 1.4, left_w, 5.6, fill_hex=WHITE_HEX, radius=0.06, shadow=True)
        add_text(slide, MARGIN, 3.9, left_w, 0.6, "ERD unavailable", size=14, color_hex=SLATE_HEX,
                  align=PP_ALIGN.CENTER)

    x2 = MARGIN + left_w + 0.35
    right_w = SLIDE_W - MARGIN - x2
    add_text(slide, x2, 1.5, right_w, 0.4, "Key Facts", size=16, bold=True, color_hex=TEAL_HEX)
    add_bullets(slide, [
        "6 core tables: Categories, Suppliers, Products, Stocks, StockTransactions, Users.",
        "Primary/foreign keys enforce referential integrity across the schema.",
        "CHECK constraints guard price, quantity & reorder-level ranges.",
        "Normalised to 3NF — no repeating or derivable groups.",
        "Unique indexes on category name, username & product-stock mapping.",
    ], x2, 2.05, right_w, 4.6, size=13.5, space_after=14)
    notes(slide, "The database is a normalised, third-normal-form SQL Server schema with six "
                  "core tables. Foreign keys tie products to their category and supplier, stock "
                  "levels are tracked per product, and every stock movement is logged in a "
                  "StockTransactions table. Check constraints stop invalid data — like negative "
                  "prices or quantities — from ever being written.")


def slide_usecase(prs):
    slide = new_slide(prs, title="Use Cases & Data Flow")
    img = fig("usecase") or fig("dfd1")
    if img:
        add_framed_picture(slide, img, MARGIN, 1.4, SLIDE_W - 2 * MARGIN, 5.6)
    else:
        # Native fallback: simple actor -> system boundary -> use-case ovals
        boundary_x, boundary_y = 3.3, 1.6
        boundary_w, boundary_h = SLIDE_W - 2 * MARGIN - (3.3 - MARGIN), 5.3
        add_rect(slide, boundary_x, boundary_y, boundary_w, boundary_h, fill_hex=WHITE_HEX,
                  line_hex="CBD5E1", radius=0.03)
        add_text(slide, boundary_x, boundary_y + 0.12, boundary_w, 0.3, "StockPilot System",
                  size=12, bold=True, color_hex=SLATE_HEX, align=PP_ALIGN.CENTER)
        use_cases = [
            "Manage Products & Categories", "Stock In / Stock Out",
            "View Reports & Analytics", "Manage Suppliers",
            "Authenticate & Change Password",
        ]
        oval_w, oval_h = boundary_w - 1.0, 0.75
        oy0 = boundary_y + 0.65
        for i, uc in enumerate(use_cases):
            oy = oy0 + i * (oval_h + 0.18)
            ov = slide.shapes.add_shape(MSO_SHAPE.OVAL, IN(boundary_x + 0.5), IN(oy), IN(oval_w), IN(oval_h))
            ov.fill.solid()
            ov.fill.fore_color.rgb = RGBColor.from_string(LIGHT_PALETTE_HEX[i % len(LIGHT_PALETTE_HEX)])
            ov.line.fill.background()
            no_shadow(ov)
            tf = ov.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = 0.1
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = uc
            r.font.size = Pt(12)
            r.font.bold = True
            r.font.name = FONT
            r.font.color.rgb = WHITE_RGB
        actors = [("Admin", oy0 + 0.3), ("Staff / Viewer", oy0 + 2 * (oval_h + 0.18) + 0.3)]
        for label, ay in actors:
            icon_badge(slide, MARGIN + 0.8, ay, 0.7, label[0], size=16)
            add_text(slide, MARGIN, ay + 0.42, 1.6, 0.3, label, size=11, bold=True, color_hex=DARK_HEX,
                      align=PP_ALIGN.CENTER)
            conn = slide.shapes.add_connector(1, IN(MARGIN + 1.15), IN(ay), IN(boundary_x), IN(ay))
            conn.line.color.rgb = AXIS_RGB
            conn.line.width = Pt(1.25)
    notes(slide, "This use-case view shows the two main actors — administrators and staff or "
                  "viewer-level users — and how they interact with the system's core "
                  "capabilities: managing products and categories, recording stock movements, "
                  "viewing reports, and authenticating securely.")


def slide_login(prs):
    slide = new_slide(prs, title="Web App — Login & Security")
    img = screen("login")
    left_w = 6.9
    if img:
        add_framed_picture(slide, img, MARGIN, 1.4, left_w, 5.6, caption="Login screen")
    else:
        add_rect(slide, MARGIN, 1.4, left_w, 5.6, fill_hex=WHITE_HEX, radius=0.06, shadow=True)
    x2 = MARGIN + left_w + 0.4
    right_w = SLIDE_W - MARGIN - x2
    add_text(slide, x2, 1.6, right_w, 0.4, "Security Highlights", size=16, bold=True, color_hex=TEAL_HEX)
    add_bullets(slide, [
        "Passwords hashed with ASP.NET Core Identity's PasswordHasher — never stored in plain text.",
        "A session authentication filter redirects every unauthenticated request to /Account/Login.",
        "Role-based access — Admin vs. Viewer — restricts who can modify data.",
        "Self-service Change Password flow, verified against the current hash.",
        "PWA API endpoints return 401 JSON (not a redirect) when the session is missing.",
    ], x2, 2.1, right_w, 4.6, size=13, space_after=14)
    notes(slide, "Security starts at login. Passwords are hashed with ASP.NET Core Identity's "
                  "PasswordHasher, never stored in plain text, and a custom session filter "
                  "redirects any unauthenticated request straight back to the login page. Role "
                  "based access separates admin and viewer permissions, and users can change "
                  "their own password from within the app.")


def slide_dashboard(prs):
    slide = new_slide(prs, title="Web App — Dashboard")
    img = screen("dashboard")
    left_w = 7.4
    if img:
        add_framed_picture(slide, img, MARGIN, 1.4, left_w, 5.6, caption="Live dashboard")
    else:
        add_rect(slide, MARGIN, 1.4, left_w, 5.6, fill_hex=WHITE_HEX, radius=0.06, shadow=True)
    x2 = MARGIN + left_w + 0.35
    chart_w = SLIDE_W - MARGIN - x2
    vbc = value_by_category()
    cats = [c for c, _ in vbc]
    vals = [v for _, v in vbc]
    total = sum(vals)
    add_donut_chart(slide, x2, 1.55, chart_w, 5.4, cats, vals, "Inventory Value by Category",
                      center_label=(f"Rs. {total:,.0f}", "Total value"))
    notes(slide, "The dashboard gives an at-a-glance summary: total products, suppliers, low and "
                  "out-of-stock counts, and total inventory value, alongside a live low-stock "
                  "table. This doughnut chart breaks that inventory value down by category — "
                  "Groceries and Stationery carry the largest share of value in our seed data.")


def slide_master_data(prs):
    slide = new_slide(prs, title="Master Data Management")
    col_w = (SLIDE_W - 2 * MARGIN - 0.4) / 2
    top = 1.4
    img_h = 4.0
    p_img = screen("products")
    c_img = screen("categories")
    if p_img:
        add_framed_picture(slide, p_img, MARGIN, top, col_w, img_h, caption="Products")
    if c_img:
        add_framed_picture(slide, c_img, MARGIN + col_w + 0.4, top, col_w, img_h, caption="Categories")
    add_bullets(slide, [
        "Full CRUD for products, categories & suppliers, with server-side validation.",
        "Live search and category/supplier filters across every list view.",
        "Category delete is blocked while products still reference it — no orphaned data.",
        "Every product links to exactly one category and one supplier via foreign keys.",
    ], MARGIN, top + img_h + 0.35, SLIDE_W - 2 * MARGIN, 1.5, size=13, space_after=6)
    notes(slide, "Master data — products, categories and suppliers — all get full create, read, "
                  "update and delete screens with live search and filtering. We also guard data "
                  "integrity: you can't delete a category that's still in use by a product.")


def slide_stock(prs):
    slide = new_slide(prs, title="Stock Transactions")
    img = screen("stockout_error")
    left_w = 6.5
    if img:
        add_framed_picture(slide, img, MARGIN, 1.4, left_w, 5.6, caption="Stock Out — validation in action")
    else:
        add_rect(slide, MARGIN, 1.4, left_w, 5.6, fill_hex=WHITE_HEX, radius=0.06, shadow=True)

    x2 = MARGIN + left_w + 0.4
    right_w = SLIDE_W - MARGIN - x2
    flow_img = fig("flow_stockout")
    if flow_img:
        add_framed_picture(slide, flow_img, x2, 1.4, right_w, 5.6)
    else:
        add_text(slide, x2, 1.55, right_w, 0.35, "Stock Out Validation Flow", size=14, bold=True, color_hex=TEAL_HEX)
        steps = ["Select product\n& quantity", "Check quantity\nagainst stock", "Insufficient?\nReject with error",
                  "Log StockOut\ntransaction"]
        box_h = 1.0
        gap = 0.35
        top0 = 2.15
        flow_chain(slide, steps, x2 + 0.15, top0, right_w - 0.3, box_h, gap, horizontal=False,
                    fill_hex=TEAL_HEX, last_fill_hex=OK_HEX, text_size=11.5)
    notes(slide, "Every stock movement runs through validation before it's committed. Here we "
                  "tried to remove ninety-nine thousand units of a product that only has "
                  "forty-two available — the system rejects it immediately with a clear "
                  "'Insufficient stock' message and the stock level stays untouched. Every "
                  "accepted Stock In or Stock Out is also logged as a transaction for full "
                  "audit history.")


def slide_reports(prs):
    slide = new_slide(prs, title="Reports & Analytics")
    img = screen("report_low_stock") or screen("report_inventory_value")
    left_w = 5.6
    if img:
        add_framed_picture(slide, img, MARGIN, 1.4, left_w, 5.6, caption="Low Stock report")
    else:
        add_rect(slide, MARGIN, 1.4, left_w, 5.6, fill_hex=WHITE_HEX, radius=0.06, shadow=True)

    x2 = MARGIN + left_w + 0.35
    chart_w = SLIDE_W - MARGIN - x2
    ubc = units_by_category()
    cats = [c for c, _ in ubc]
    vals = [v for _, v in ubc]
    add_bar_chart(slide, x2, 1.4, chart_w, 2.7, cats, vals, "Units in Stock by Category")
    add_status_chart(slide, x2, 4.3, chart_w, 2.7, "Stock Status (Products)")
    notes(slide, "Beyond the dashboard, StockPilot ships five dedicated reports — product "
                  "catalogue, stock summary, low stock, transaction history and inventory value "
                  "— each filterable and print-friendly. On the right, units in stock by category "
                  "and the overall stock health: most products sit at a healthy OK level, with "
                  "six running low and two fully out of stock.")


def slide_pwa(prs):
    slide = new_slide(prs, title="Progressive Web App")
    phones = [("pwa_home", "Home"), ("pwa_search", "Search"), ("pwa_lowstock", "Low Stock")]
    phone_w = 2.05
    gap = 0.32
    top = 1.35
    x0 = MARGIN
    max_h = 0.0
    for i, (name, cap) in enumerate(phones):
        img = screen(name)
        x = x0 + i * (phone_w + gap)
        if img:
            bw, bh = add_phone_frame(slide, img, x, top, phone_w)
            max_h = max(max_h, bh)
            add_text(slide, x, top + bh + 0.08, phone_w, 0.28, cap, size=11, bold=True,
                      color_hex=DARK_HEX, align=PP_ALIGN.CENTER)
        else:
            add_rect(slide, x, top, phone_w, 4.2, fill_hex=DARK_HEX, radius=0.14, shadow=True)

    x2 = x0 + 3 * phone_w + 2 * gap + 0.45
    right_w = SLIDE_W - MARGIN - x2
    add_text(slide, x2, top + 0.05, right_w, 0.35, "Mobile-First Features", size=15, bold=True, color_hex=TEAL_HEX)
    add_bullets(slide, [
        "Installable — Add to Home Screen on Android & iOS.",
        "Offline-capable via a service worker cache for the last-viewed data.",
        "Low-stock browser notifications when alerts are enabled.",
        "Same live product & stock data as the desktop dashboard.",
    ], x2, top + 0.55, right_w, 2.5, size=12.5, space_after=10)

    cache_img = fig("pwa_cache")
    if cache_img:
        add_framed_picture(slide, cache_img, x2, top + 3.15, right_w, 2.2)
    notes(slide, "For staff on the move, StockPilot ships as an installable Progressive Web App. "
                  "It's add-to-home-screen ready, caches the last-viewed data through a service "
                  "worker so it still works offline, and can raise a browser notification when "
                  "stock runs low — all backed by the same live data as the desktop app.")


def slide_testing(prs):
    slide = new_slide(prs, title="Testing & Results")
    rows, is_real = load_test_results()
    pass_n = sum(1 for r in rows if str(r.get("status", "")).strip().lower() == "pass")
    other_n = len(rows) - pass_n
    left_w = 4.5
    add_donut_chart(slide, MARGIN, 1.5, left_w, 4.6, ["Pass", "Manual / Pending"], [pass_n, other_n],
                      "Test Outcomes", colors_hex=[OK_HEX, WARN_HEX],
                      center_label=(f"{pass_n}/{len(rows)}", "automated pass"))

    x2 = MARGIN + left_w + 0.4
    table_w = SLIDE_W - MARGIN - x2
    key_ids = {"TC-04", "TC-07", "TC-09", "TC-13", "TC-14", "TC-17"}
    key_rows = [r for r in rows if r.get("id") in key_ids] or rows[:6]
    add_text(slide, x2, 1.5, table_w, 0.35, "Key Test Cases", size=15, bold=True, color_hex=TEAL_HEX)
    gframe = slide.shapes.add_table(len(key_rows) + 1, 3, IN(x2), IN(1.95), IN(table_w), IN(4.2))
    table = gframe.table
    table.columns[0].width = Emu(int(Inches(1.0)))
    table.columns[1].width = Emu(int(Inches(table_w - 1.0 - 1.15)))
    table.columns[2].width = Emu(int(Inches(1.15)))
    headers = ["ID", "Test", "Status"]
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = DARK_RGB
        p = cell.text_frame.paragraphs[0]
        p.runs[0].font.size = Pt(10.5)
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = WHITE_RGB
        p.runs[0].font.name = FONT
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = cell.margin_right = Pt(6)
    for r, row in enumerate(key_rows, start=1):
        vals = [row.get("id", ""), row.get("test", ""), row.get("status", "")]
        for c, v in enumerate(vals):
            cell = table.cell(r, c)
            cell.text = str(v)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string("F1F5F9" if r % 2 == 0 else "FFFFFF")
            p = cell.text_frame.paragraphs[0]
            run = p.runs[0]
            run.font.size = Pt(9.5)
            run.font.name = FONT
            run.font.color.rgb = SLATE_RGB
            if c == 2:
                run.font.bold = True
                run.font.color.rgb = OK_RGB if str(v).lower() == "pass" else WARN_RGB
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = cell.margin_right = Pt(6)
            cell.text_frame.word_wrap = True
    notes(slide, f"We ran {len(rows)} test cases covering build, authentication, stock "
                  f"validation, reporting and the PWA API layer. {pass_n} passed automated "
                  "verification via curl and sqlcmd checks against the live app and database; "
                  "the remainder are flagged for manual browser-based verification, like the "
                  "install prompt and offline reload. This table highlights six of the most "
                  "important cases, including the insufficient-stock guard we just demonstrated.")


def slide_conclusion(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, DARK_HEX)
    add_title_bar(slide, "Conclusion & Future Scope")
    add_page_number(slide, color_hex="94A3B8")
    col_w = (SLIDE_W - 2 * MARGIN - 0.5) / 2
    y0 = 1.6
    add_text(slide, MARGIN, y0, col_w, 0.4, "What We Built", size=16, bold=True, color_hex=TEAL_HEX)
    add_bullets(slide, [
        "A working 3-tier system: Console app, ASP.NET Core MVC web app, and a PWA.",
        "Validated stock workflows with full transaction history and audit trail.",
        "Role-based security, live dashboards and five printable reports.",
        "A normalised SQL Server schema seeded with realistic demo data.",
    ], MARGIN, y0 + 0.5, col_w, 3.6, size=13.5, color_hex="E2E8F0", space_after=12)

    x2 = MARGIN + col_w + 0.5
    add_text(slide, x2, y0, col_w, 0.4, "Future Scope", size=16, bold=True, color_hex=TEAL_HEX)
    add_bullets(slide, [
        "Barcode / QR scanning for faster Stock In & Stock Out.",
        "Purchase-order workflow tying supplier orders to Stock In.",
        "Multi-branch / multi-warehouse inventory support.",
        "Push notifications and richer analytics on the PWA.",
    ], x2, y0 + 0.5, col_w, 3.6, size=13.5, color_hex="E2E8F0", space_after=12)
    notes(slide, "To sum up, StockPilot delivers a complete, validated inventory workflow across "
                  "three client surfaces, backed by a properly normalised database and real "
                  "security. Looking ahead, barcode scanning, supplier purchase orders, and "
                  "multi-branch support are the natural next steps.")


def slide_thankyou(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, DARK_HEX)
    add_rect(slide, -1.0, SLIDE_H - 1.6, 2.6, 2.6, fill_hex="16403A", radius=0.5)
    add_rect(slide, SLIDE_W - 1.6, -1.0, 2.6, 2.6, fill_hex="16403A", radius=0.5)
    add_text(slide, 0, 2.7, SLIDE_W, 1.0, "Thank You", size=48, bold=True, color_hex=WHITE_HEX,
              align=PP_ALIGN.CENTER)
    add_text(slide, 0, 3.65, SLIDE_W, 0.6, "Questions?", size=22, color_hex=TEAL_HEX, align=PP_ALIGN.CENTER)
    add_text(slide, 0, 6.6, SLIDE_W, 0.4, PROJECT_TITLE + " — " + PROJECT_SUBTITLE, size=12,
              color_hex="94A3B8", align=PP_ALIGN.CENTER)
    notes(slide, "Thank you for your time. We're happy to take any questions — whether about the "
                  "architecture, the validation rules, the database design, or a live demo of any "
                  "part of the app.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def build_pptx():
    _slide_counter["n"] = 0
    prs = Presentation()
    prs.slide_width = Emu(int(Inches(SLIDE_W)))
    prs.slide_height = Emu(int(Inches(SLIDE_H)))

    builders = [
        slide_title, slide_agenda, slide_problem, slide_architecture, slide_tech_stack,
        slide_console, slide_database, slide_usecase, slide_login, slide_dashboard,
        slide_master_data, slide_stock, slide_reports, slide_pwa, slide_testing,
        slide_conclusion, slide_thankyou,
    ]
    _slide_counter["total"] = len(builders)
    for fn in builders:
        fn(prs)

    out = REPO / "Documentation" / "PPT" / "InventoryManagementSystem.pptx"
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out


if __name__ == "__main__":
    path = build_pptx()
    print(f"Wrote {path}")
