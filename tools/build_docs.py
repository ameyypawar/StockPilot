#!/usr/bin/env python3
"""
Regenerates the generated documentation deliverables for
StockPilot -- Inventory Management System:

  - Database/ERDiagram/ERDiagram.png
  - Documentation/PPT/InventoryManagementSystem.pptx
  - Documentation/FinalReport/InventoryManagementSystem_FinalReport.docx
  - Documentation/UserManual/UserManual.docx   (converted from UserManual.md)

Run with any Python that has python-pptx, python-docx and Pillow installed:

    python tools/build_docs.py

from the repository root (or, using this project's own doc-building venv:
tools/.venv/bin/python tools/build_docs.py).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor as PptxColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn as pptx_qn

from docx import Document
from docx.shared import Pt as DocxPt, Inches as DocxInches, RGBColor as DocxColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn as docx_qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Configuration (tools/doc_config.py is owned by another agent; read-only)
# ---------------------------------------------------------------------------
try:
    import doc_config  # type: ignore
except Exception:
    doc_config = None


def cfg(name, default):
    if doc_config is None:
        return default
    return getattr(doc_config, name, default)


PROJECT_TITLE = cfg("PROJECT_TITLE", "StockPilot")
PROJECT_SUBTITLE = cfg("PROJECT_SUBTITLE", "Inventory Management System")
PROJECT_TAGLINE = cfg(
    "PROJECT_TAGLINE",
    "Console Application, ASP.NET Core MVC Web App & Progressive Web App",
)
FULL_TITLE = f"{PROJECT_TITLE} — {PROJECT_SUBTITLE}" if PROJECT_SUBTITLE else PROJECT_TITLE

_DEFAULT_TEAM = [
    "[Team Member 1 — Roll No.]",
    "[Team Member 2 — Roll No.]",
    "[Team Member 3 — Roll No.]",
]


def _team_members():
    raw = cfg("TEAM_MEMBERS", _DEFAULT_TEAM)
    out = []
    for m in raw:
        if isinstance(m, (list, tuple)):
            parts = [str(p) for p in m if str(p).strip()]
            out.append(" — ".join(parts))
        else:
            out.append(str(m))
    return out or list(_DEFAULT_TEAM)


TEAM_MEMBERS = _team_members()
COLLEGE = cfg("COLLEGE", "[College Name]")
DEPARTMENT = cfg("DEPARTMENT", "[Department Name]")
GUIDE = cfg("GUIDE", "[Guide Name]")
ACADEMIC_YEAR = cfg("ACADEMIC_YEAR", "[2026–27]")
COURSE = cfg("COURSE", "[Course / Programme Name]")
BASE_REPO_URL = cfg("BASE_REPO_URL", "https://github.com/MilanGite06/InventoryManagementSystem")
BASE_REPO_CREDIT = cfg(
    "BASE_REPO_CREDIT",
    "Base project by Milan Gite (MilanGite06/InventoryManagementSystem)",
)

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
DARK_HEX = "1E293B"     # dark slate
TEAL_HEX = "0D9488"     # teal accent
LIGHT_HEX = "F8FAFC"    # off-white background
SLATE_HEX = "475569"    # body text grey
WHITE_HEX = "FFFFFF"
DANGER_HEX = "DC2626"
WARN_HEX = "D97706"
OK_HEX = "16A34A"


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


DARK_RGB = hx(DARK_HEX)
TEAL_RGB = hx(TEAL_HEX)
LIGHT_RGB = hx(LIGHT_HEX)
SLATE_RGB = hx(SLATE_HEX)
WHITE_RGB = hx(WHITE_HEX)

DARK_PPTX = PptxColor(*DARK_RGB)
TEAL_PPTX = PptxColor(*TEAL_RGB)
LIGHT_PPTX = PptxColor(*LIGHT_RGB)
SLATE_PPTX = PptxColor(*SLATE_RGB)
WHITE_PPTX = PptxColor(*WHITE_RGB)

DARK_DOCX = DocxColor(*DARK_RGB)
TEAL_DOCX = DocxColor(*TEAL_RGB)
SLATE_DOCX = DocxColor(*SLATE_RGB)


# ---------------------------------------------------------------------------
# Test results (owned by the main coder; never invent "Pass")
# ---------------------------------------------------------------------------
FALLBACK_TEST_CASES = [
    dict(id="TC-01", area="Auth", test="Log in with valid admin credentials (admin / Admin@123)",
         expected="Redirect to Dashboard; session established"),
    dict(id="TC-02", area="Auth", test="Log in with a wrong password",
         expected="Error message shown; stays on Login"),
    dict(id="TC-03", area="Auth", test="Request /Product while logged out",
         expected="Redirect to /Account/Login"),
    dict(id="TC-04", area="Auth", test="Request /api/products while logged out",
         expected="401 JSON response"),
    dict(id="TC-05", area="Auth", test="Change password with the wrong current password",
         expected="Error shown; password unchanged"),
    dict(id="TC-06", area="Auth", test="Change password correctly, then log in with the new password",
         expected="Success message; new password works"),
    dict(id="TC-07", area="Category", test="Delete a category that is still used by a product",
         expected="Delete blocked with an explanatory message"),
    dict(id="TC-08", area="Product", test="Search products by name/category/supplier",
         expected="Only matching products are listed"),
    dict(id="TC-09", area="Stock", test="Stock In a valid quantity",
         expected="Quantity increases; transaction logged"),
    dict(id="TC-10", area="Stock", test="Stock Out a quantity greater than available",
         expected="\"Insufficient stock\" error; quantity unchanged"),
    dict(id="TC-11", area="Stock", test="Stock In / Stock Out with a zero or negative quantity",
         expected="Request rejected"),
    dict(id="TC-12", area="Dashboard", test="Total Inventory Value KPI",
         expected="Matches sum(QuantityAvailable * Price) across all products"),
    dict(id="TC-13", area="Reports", test="Transaction History filtered by type=StockOut and a date range",
         expected="Only matching rows are shown"),
    dict(id="TC-14", area="Reports", test="Print a report",
         expected="Print layout hides navigation/buttons; shows a clean report"),
    dict(id="TC-15", area="Console", test="Log in as viewer and attempt to add a product",
         expected="\"Access denied: viewers cannot modify data.\""),
    dict(id="TC-16", area="Console", test="Send EOF on stdin mid-session",
         expected="\"No more input. Exiting.\" and a clean exit"),
    dict(id="TC-17", area="PWA", test="Request /manifest.json, /sw.js, /offline.html, /icons/icon-192.png",
         expected="200 OK with the correct content types"),
]


def load_test_results():
    """Returns (rows, is_real). rows always have id/area/test/expected/actual/status."""
    path = ROOT / "tools" / "test_results.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                rows = []
                for r in data:
                    rows.append(
                        dict(
                            id=str(r.get("id", "")),
                            area=str(r.get("area", "")),
                            test=str(r.get("test", "")),
                            expected=str(r.get("expected", "")),
                            actual=str(r.get("actual", "")),
                            status=str(r.get("status", "")),
                        )
                    )
                return rows, True
        except Exception:
            pass
    rows = []
    for tc in FALLBACK_TEST_CASES:
        rows.append(
            dict(
                id=tc["id"], area=tc["area"], test=tc["test"], expected=tc["expected"],
                actual="Pending", status="Pending",
            )
        )
    return rows, False


# ===========================================================================
# 1. ER Diagram (Pillow)
# ===========================================================================

def get_font(size, bold=False):
    """Font-independent: falls back to Pillow's built-in bitmap font on any
    Pillow version, so this runs identically on any machine."""
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


TABLES = {
    "CATEGORIES": [
        ("CategoryId", "PK"), ("CategoryName", "UK"), ("Description", ""),
    ],
    "SUPPLIERS": [
        ("SupplierId", "PK"), ("SupplierName", ""), ("ContactNumber", ""),
        ("Email", ""), ("Address", ""),
    ],
    "PRODUCTS": [
        ("ProductId", "PK"), ("ProductName", ""), ("Price", ""), ("Unit", ""),
        ("CategoryId", "FK"), ("SupplierId", "FK"),
    ],
    "STOCKS": [
        ("StockId", "PK"), ("ProductId", "FK/UK"), ("QuantityAvailable", ""),
        ("ReorderLevel", ""), ("LastUpdated", ""),
    ],
    "STOCK_TRANSACTIONS": [
        ("TransactionId", "PK"), ("ProductId", "FK"), ("Type", ""),
        ("Quantity", ""), ("TransactionDate", ""), ("PerformedBy", ""),
        ("Remarks", ""),
    ],
    "USERS": [
        ("UserId", "PK"), ("Username", "UK"), ("PasswordHash", ""),
        ("FullName", ""), ("Email", ""), ("Role", ""),
    ],
}


def draw_table_box(draw, x, y, w, title, columns, font_title, font_col):
    header_h = 34
    row_h = 26
    h = header_h + row_h * len(columns)

    draw.rectangle([x, y, x + w, y + h], fill=WHITE_RGB, outline=DARK_RGB, width=2)
    draw.rectangle([x, y, x + w, y + header_h], fill=DARK_RGB)

    tw = draw.textlength(title, font=font_title)
    draw.text((x + (w - tw) / 2, y + (header_h - 14) / 2), title, font=font_title, fill=WHITE_RGB)

    ry = y + header_h
    for i, (colname, marker) in enumerate(columns):
        if i % 2 == 1:
            draw.rectangle([x + 1, ry, x + w - 1, ry + row_h], fill=(241, 245, 249))
        label = colname if not marker else f"{colname}  ({marker})"
        color = TEAL_RGB if marker == "PK" else (DARK_RGB if not marker else SLATE_RGB)
        draw.text((x + 12, ry + (row_h - 12) / 2), label, font=font_col, fill=color)
        ry += row_h

    draw.line([x, y + header_h, x + w, y + header_h], fill=DARK_RGB, width=1)
    return (x, y, w, h)


def box_anchor(box, side):
    x, y, w, h = box
    if side == "top":
        return (x + w / 2, y)
    if side == "bottom":
        return (x + w / 2, y + h)
    if side == "left":
        return (x, y + h / 2)
    if side == "right":
        return (x + w, y + h / 2)
    return (x + w / 2, y + h / 2)


def draw_relationship(draw, p1, p2, label1, label2, font_lbl):
    draw.line([p1, p2], fill=TEAL_RGB, width=3)

    def along(p, q, t):
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

    a = along(p1, p2, 0.14)
    b = along(p1, p2, 0.86)
    for pt, lbl in ((a, label1), (b, label2)):
        tw = draw.textlength(lbl, font=font_lbl)
        pad = 3
        draw.rectangle(
            [pt[0] - tw / 2 - pad, pt[1] - 9, pt[0] + tw / 2 + pad, pt[1] + 9],
            fill=WHITE_RGB, outline=TEAL_RGB, width=1,
        )
        draw.text((pt[0] - tw / 2, pt[1] - 7), lbl, font=font_lbl, fill=DARK_RGB)


def draw_erd_diagram():
    # A4 landscape at ~150 dpi, readable when printed at A4.
    W, H = 1754, 1240
    img = Image.new("RGB", (W, H), WHITE_RGB)
    draw = ImageDraw.Draw(img)

    font_h1 = get_font(26)
    font_title = get_font(15)
    font_col = get_font(13)
    font_lbl = get_font(13)
    font_note = get_font(13)

    heading = f"{PROJECT_TITLE} - Entity-Relationship Diagram"
    draw.text((40, 28), heading, font=font_h1, fill=DARK_RGB)
    draw.line([40, 70, W - 40, 70], fill=TEAL_RGB, width=3)

    box_w = 300
    boxes = {}

    boxes["CATEGORIES"] = draw_table_box(draw, 60, 130, box_w, "CATEGORIES", TABLES["CATEGORIES"], font_title, font_col)
    boxes["SUPPLIERS"] = draw_table_box(draw, 1394, 130, box_w, "SUPPLIERS", TABLES["SUPPLIERS"], font_title, font_col)
    boxes["PRODUCTS"] = draw_table_box(draw, 727, 160, box_w, "PRODUCTS", TABLES["PRODUCTS"], font_title, font_col)
    boxes["STOCKS"] = draw_table_box(draw, 460, 620, box_w, "STOCKS", TABLES["STOCKS"], font_title, font_col)
    boxes["STOCK_TRANSACTIONS"] = draw_table_box(draw, 940, 620, box_w + 30, "STOCK_TRANSACTIONS", TABLES["STOCK_TRANSACTIONS"], font_title, font_col)
    boxes["USERS"] = draw_table_box(draw, 1394, 620, box_w, "USERS", TABLES["USERS"], font_title, font_col)

    draw_relationship(
        draw,
        box_anchor(boxes["CATEGORIES"], "right"),
        box_anchor(boxes["PRODUCTS"], "left"),
        "1", "N", font_lbl,
    )
    draw_relationship(
        draw,
        box_anchor(boxes["SUPPLIERS"], "left"),
        box_anchor(boxes["PRODUCTS"], "right"),
        "1", "N", font_lbl,
    )
    draw_relationship(
        draw,
        box_anchor(boxes["PRODUCTS"], "bottom"),
        box_anchor(boxes["STOCKS"], "top"),
        "1", "1", font_lbl,
    )
    draw_relationship(
        draw,
        box_anchor(boxes["PRODUCTS"], "bottom"),
        box_anchor(boxes["STOCK_TRANSACTIONS"], "top"),
        "1", "N", font_lbl,
    )

    ux, uy, uw, uh = boxes["USERS"]
    draw.text(
        (ux, uy - 24), "(standalone - no FK to inventory tables)",
        font=font_note, fill=SLATE_RGB,
    )

    legend_y = H - 70
    draw.text((60, legend_y), "PK = Primary Key    FK = Foreign Key    UK = Unique Key", font=font_note, fill=SLATE_RGB)
    draw.text((60, legend_y + 22), f"{PROJECT_TITLE} - {PROJECT_SUBTITLE} - SQL Server (InventoryManagementDB), 6 tables, 3NF", font=font_note, fill=SLATE_RGB)

    out_path = ROOT / "Database" / "ERDiagram" / "ERDiagram.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"wrote {out_path} ({W}x{H})")
    return out_path


# ===========================================================================
# 2. PPT (python-pptx)
# ===========================================================================

def new_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = WHITE_PPTX
    return slide


def add_title_bar(slide, prs, title, kicker=None):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.15))
    bar.fill.solid()
    bar.fill.fore_color.rgb = DARK_PPTX
    bar.line.fill.background()
    bar.shadow.inherit = False

    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(1.15), prs.slide_width, Inches(0.08))
    accent.fill.solid()
    accent.fill.fore_color.rgb = TEAL_PPTX
    accent.line.fill.background()
    accent.shadow.inherit = False

    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.18), prs.slide_width - Inches(1.0), Inches(0.85))
    tf = tb.text_frame
    tf.word_wrap = True
    if kicker:
        p0 = tf.paragraphs[0]
        r0 = p0.add_run()
        r0.text = kicker.upper()
        r0.font.size = Pt(12)
        r0.font.bold = True
        r0.font.color.rgb = TEAL_PPTX
        p = tf.add_paragraph()
    else:
        p = tf.paragraphs[0]
    r = p.add_run()
    r.text = title
    r.font.size = Pt(28)
    r.font.bold = True
    r.font.color.rgb = WHITE_PPTX
    return tb


def add_bullets(slide, items, left, top, width, height, font_size=18, color=SLATE_PPTX, bold_first=False):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"•  {item}"
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.space_after = Pt(10)
    return tb


def add_note(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def add_footer(slide, prs, page_no):
    tb = slide.shapes.add_textbox(Inches(0.5), prs.slide_height - Inches(0.4), Inches(6), Inches(0.3))
    p = tb.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = FULL_TITLE
    r.font.size = Pt(10)
    r.font.color.rgb = SLATE_PPTX

    tb2 = slide.shapes.add_textbox(prs.slide_width - Inches(1.0), prs.slide_height - Inches(0.4), Inches(0.6), Inches(0.3))
    p2 = tb2.text_frame.paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    r2 = p2.add_run()
    r2.text = str(page_no)
    r2.font.size = Pt(10)
    r2.font.color.rgb = SLATE_PPTX


def styled_box(slide, x, y, w, h, text, fill_rgb, text_rgb=WHITE_PPTX, size=14, bold=True, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    box = slide.shapes.add_shape(shape, x, y, w, h)
    box.fill.solid()
    box.fill.fore_color.rgb = fill_rgb
    box.line.color.rgb = DARK_PPTX
    box.line.width = Pt(1)
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = text_rgb
    return box


def add_arrow(slide, x1, y1, x2, y2):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    conn.line.color.rgb = TEAL_PPTX
    conn.line.width = Pt(2.25)
    line = conn.line._get_or_add_ln()
    tail = OxmlElement("a:tailEnd")
    tail.set("type", "triangle")
    line.append(tail)
    return conn


def add_table(slide, left, top, width, height, headers, rows, font_size=11):
    n_rows = len(rows) + 1
    n_cols = len(headers)
    gtable = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = gtable.table
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = str(h)
        cell.fill.solid()
        cell.fill.fore_color.rgb = DARK_PPTX
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(font_size)
            p.font.bold = True
            p.font.color.rgb = WHITE_PPTX
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(val)
            cell.fill.solid()
            cell.fill.fore_color.rgb = LIGHT_PPTX if r % 2 == 0 else WHITE_PPTX
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(font_size)
                p.font.color.rgb = SLATE_PPTX
    return gtable


def status_color(status):
    s = (status or "").strip().lower()
    if s == "pass":
        return hx(OK_HEX)
    if s == "fail":
        return hx(DANGER_HEX)
    return hx(WARN_HEX)


def build_pptx():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    page = [0]

    def finish(slide, notes):
        page[0] += 1
        add_footer(slide, prs, page[0])
        add_note(slide, notes)

    # Slide 1 -- Title & team
    s = new_slide(prs)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = DARK_PPTX
    bg.line.fill.background()
    bg.shadow.inherit = False
    accent = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(3.55), prs.slide_width, Inches(0.06))
    accent.fill.solid()
    accent.fill.fore_color.rgb = TEAL_PPTX
    accent.line.fill.background()
    accent.shadow.inherit = False

    tb = s.shapes.add_textbox(Inches(0.8), Inches(1.1), Inches(11.7), Inches(1.4))
    p = tb.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = PROJECT_TITLE
    r.font.size = Pt(60)
    r.font.bold = True
    r.font.color.rgb = WHITE_PPTX

    tb2 = s.shapes.add_textbox(Inches(0.8), Inches(2.25), Inches(11.7), Inches(0.8))
    p2 = tb2.text_frame.paragraphs[0]
    r2 = p2.add_run()
    r2.text = PROJECT_SUBTITLE
    r2.font.size = Pt(28)
    r2.font.color.rgb = TEAL_PPTX

    tb3 = s.shapes.add_textbox(Inches(0.8), Inches(2.9), Inches(11.7), Inches(0.6))
    p3 = tb3.text_frame.paragraphs[0]
    r3 = p3.add_run()
    r3.text = PROJECT_TAGLINE
    r3.font.size = Pt(15)
    r3.font.italic = True
    r3.font.color.rgb = PptxColor(0xCB, 0xD5, 0xE1)

    tb4 = s.shapes.add_textbox(Inches(0.8), Inches(3.9), Inches(11.7), Inches(2.6))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    p4 = tf4.paragraphs[0]
    r4 = p4.add_run()
    r4.text = "Project Team"
    r4.font.size = Pt(16)
    r4.font.bold = True
    r4.font.color.rgb = TEAL_PPTX
    for m in TEAM_MEMBERS:
        pm = tf4.add_paragraph()
        rm = pm.add_run()
        rm.text = m
        rm.font.size = Pt(16)
        rm.font.color.rgb = WHITE_PPTX
    pblank = tf4.add_paragraph()
    pcollege = tf4.add_paragraph()
    rcollege = pcollege.add_run()
    rcollege.text = f"{COLLEGE}"
    rcollege.font.size = Pt(14)
    rcollege.font.color.rgb = PptxColor(0xCB, 0xD5, 0xE1)
    pguide = tf4.add_paragraph()
    rguide = pguide.add_run()
    rguide.text = f"Guide: {GUIDE}   |   {ACADEMIC_YEAR}"
    rguide.font.size = Pt(14)
    rguide.font.color.rgb = PptxColor(0xCB, 0xD5, 0xE1)
    finish(s, "Welcome/title slide. Introduce the project name, the three-part scope (console app, web app, PWA), and the team, college and guide. Keep this brief -- about 30 seconds.")

    # Slide 2 -- Problem & objectives
    s = new_slide(prs)
    add_title_bar(s, prs, "Problem Statement & Objectives")
    add_bullets(s, [
        "Small shops/warehouses often track stock in notebooks or spreadsheets -- slow, error-prone, no audit trail.",
        "Goal: a single system covering product/category/supplier master data, stock movements and reporting.",
        "Objective 1: prevent selling more stock than is available (negative-stock guard).",
        "Objective 2: give management a live dashboard and printable reports for decisions.",
        "Objective 3: demonstrate core OOP (console app) alongside a real database-backed web app.",
        "Objective 4: make the app usable on a phone, including offline, via a PWA.",
    ], Inches(0.7), Inches(1.5), Inches(11.9), Inches(5.5), font_size=19)
    finish(s, "Explain the real-world problem (manual inventory tracking) and the four objectives. This sets up why the project has three parts (console/web/PWA), not just one.")

    # Slide 3 -- 3-phase architecture
    s = new_slide(prs)
    add_title_bar(s, prs, "System Architecture -- 3 Phases")
    y = Inches(2.0)
    w, h = Inches(3.6), Inches(2.3)
    xs = [Inches(0.7), Inches(4.9), Inches(9.1)]
    labels = [
        ("Phase 1\nConsole Application", "OOP core: classes, inheritance,\npolymorphism, exceptions,\nList/Dictionary collections"),
        ("Phase 2\nASP.NET Core MVC Web App", "Controllers + Razor views\nEF Core 8 + SQL Server\nSession auth, CRUD, reports"),
        ("Phase 3\nProgressive Web App", "Manifest + Service Worker\nOffline search/stock/alerts\nInstallable on phone/desktop"),
    ]
    for x, (title, body) in zip(xs, labels):
        styled_box(s, x, y, w, Inches(0.9), title, DARK_PPTX, size=16)
        b = styled_box(s, x, y + Inches(0.9), w, h - Inches(0.9), body, LIGHT_PPTX, text_rgb=DARK_PPTX, size=13, bold=False, shape=MSO_SHAPE.RECTANGLE)
    add_arrow(s, xs[0] + w, y + h / 2, xs[1], y + h / 2)
    add_arrow(s, xs[1] + w, y + h / 2, xs[2], y + h / 2)
    styled_box(s, Inches(3.6), Inches(4.7), Inches(6.1), Inches(1.6),
               "Shared domain concepts\n(Products, Categories, Suppliers, Stock, Users)\nSQL Server: InventoryManagementDB",
               TEAL_PPTX, size=14)
    finish(s, "Walk left to right: the console app proves OOP fundamentals standalone; the web app is the real database-backed system; the PWA layer sits on top of the web app, reusing its data via a JSON API. All three model the same domain.")

    # Slide 4 -- Tech stack
    s = new_slide(prs)
    add_title_bar(s, prs, "Technology Stack")
    stack = [
        ("Runtime", ".NET 8 LTS"),
        ("Web framework", "ASP.NET Core MVC"),
        ("ORM", "Entity Framework Core 8"),
        ("Database", "Microsoft SQL Server (LocalDB / container)"),
        ("Front end", "Razor views, Bootstrap 5.3, vanilla JS"),
        ("PWA", "Web App Manifest, Service Worker, Notifications API"),
    ]
    add_table(s, Inches(0.9), Inches(1.7), Inches(11.5), Inches(4.6),
              ["Layer", "Technology"], stack, font_size=16)
    finish(s, "Run through each row briefly. Emphasise .NET 8 is the current LTS release, and that the same SQL Server database backs both the web app and its PWA layer.")

    # Slide 5 -- Console app & OOP concept map
    s = new_slide(prs)
    add_title_bar(s, prs, "Console App & OOP Concept Map")
    styled_box(s, Inches(5.3), Inches(1.7), Inches(2.7), Inches(0.7), "Person (abstract)", DARK_PPTX, size=14)
    children = [("Admin", Inches(1.6)), ("Staff", Inches(5.6)), ("User (Viewer)", Inches(9.4))]
    for label, x in children:
        styled_box(s, x, Inches(3.1), Inches(2.7), Inches(0.7), label, TEAL_PPTX, size=14)
        add_arrow(s, Inches(6.65), Inches(2.4), x + Inches(1.35), Inches(3.1))
    add_bullets(s, [
        "Encapsulation -- private fields with validating properties (e.g. Product.Price rejects negatives)",
        "Inheritance -- Admin / Staff / User all derive from Person",
        "Polymorphism -- DisplayInfo() is virtual; each role overrides it",
        "Exception handling -- custom InsufficientStockException on an invalid Stock Out",
        "Collections -- List<T> for products/stock; Dictionary<TKey,TValue> for fast lookup (categories, suppliers, users)",
    ], Inches(0.6), Inches(4.2), Inches(12.1), Inches(2.9), font_size=15)
    finish(s, "Point at the inheritance diagram first, then the bullet list. This slide is the answer to almost every OOP viva question, so spend real time here.")

    # Slide 6 -- Database design (ERD image)
    s = new_slide(prs)
    add_title_bar(s, prs, "Database Design")
    erd_path = ROOT / "Database" / "ERDiagram" / "ERDiagram.png"
    if erd_path.exists():
        s.shapes.add_picture(str(erd_path), Inches(1.6), Inches(1.5), height=Inches(5.6))
    else:
        add_bullets(s, ["ERDiagram.png not found -- run build_docs.py to generate it."], Inches(1), Inches(2), Inches(10), Inches(2))
    finish(s, "6 tables, third normal form: Categories, Suppliers, Products, Stocks, StockTransactions, Users. Category/Supplier are reference masters (Restrict delete); Stock/StockTransactions depend on Product (Cascade delete). Full data dictionary in Database/ERDiagram/README.md.")

    # Slide 7 -- Web modules
    s = new_slide(prs)
    add_title_bar(s, prs, "Web Application Modules")
    add_bullets(s, [
        "Authentication -- session-based login, hashed passwords, change password",
        "Categories & Suppliers -- master data CRUD with in-use delete protection",
        "Products -- CRUD with search/filter, opening stock on create",
        "Stock -- Initialize, Stock In, Stock Out, transaction history",
        "Dashboard -- live KPIs, low-stock list, category summary, recent activity",
        "Reports -- 5 filterable, printable reports",
    ], Inches(0.7), Inches(1.5), Inches(11.9), Inches(5.5), font_size=19)
    finish(s, "One line per module is enough -- this is the map of what the examiner is about to see live in the demo.")

    # Slide 8 -- Stock In/Out flow with negative-stock guard
    s = new_slide(prs)
    add_title_bar(s, prs, "Stock Out Flow -- Negative-Stock Guard")
    steps = ["Enter Product\n& Quantity", "Quantity > 0?", "Quantity <=\nAvailable?", "Update Stock\n+ Log Transaction"]
    xw = Inches(2.6)
    xs2 = [Inches(0.6), Inches(3.6), Inches(6.6), Inches(9.6)]
    for i, (label, x) in enumerate(zip(steps, xs2)):
        shape = MSO_SHAPE.DIAMOND if i in (1, 2) else MSO_SHAPE.ROUNDED_RECTANGLE
        color = TEAL_PPTX if i == 3 else DARK_PPTX
        styled_box(s, x, Inches(2.0), xw, Inches(1.4), label, color, size=13, shape=shape)
        if i < 3:
            add_arrow(s, x + xw, Inches(2.7), xs2[i + 1], Inches(2.7))
    styled_box(s, Inches(6.9), Inches(4.3), Inches(5.3), Inches(1.1),
               "No  -->  reject: \"Insufficient stock. Available: {n}\"\n(also enforced by CK_Stocks_QuantityAvailable >= 0)",
               PptxColor(*hx(DANGER_HEX)), size=13)
    add_arrow(s, Inches(7.9), Inches(3.4), Inches(9.5), Inches(4.3))
    finish(s, "Show this alongside the live demo of a Stock Out that exceeds availability. Two layers of protection: an application check before saving, and a database CHECK constraint as a last-resort safety net.")

    # Slide 9 -- Reports & printing
    s = new_slide(prs)
    add_title_bar(s, prs, "Reports & Printing")
    add_bullets(s, [
        "Product Catalog -- filter by search term, category, supplier",
        "Stock Summary -- filter by category and status (OK/Low/Out)",
        "Low Stock -- items at/under reorder level, with suggested order quantity",
        "Transaction History -- filter by type and date range",
        "Inventory Value -- category subtotals and a grand total",
        "Every report has a print button; @media print hides navigation and shows a clean A4 layout",
    ], Inches(0.7), Inches(1.5), Inches(11.9), Inches(5.5), font_size=18)
    finish(s, "Mention that filters are server-side (query string driven) so a printed/URL-shared report reproduces the same filtered view.")

    # Slide 10 -- PWA features
    s = new_slide(prs)
    add_title_bar(s, prs, "Progressive Web App Features")
    add_bullets(s, [
        "Installable -- Web App Manifest, icons, \"Install app\" on desktop and mobile",
        "Offline -- Service Worker with 3 caching strategies (API: network-first; pages: network-first; static assets: stale-while-revalidate)",
        "Offline modules -- Product Search, Stock Overview, Low Stock Alerts keep working from cached data",
        "Notifications -- low-stock alerts via the Notifications API, refreshed periodically",
        "Responsive -- mobile-first layout down to phone width",
    ], Inches(0.7), Inches(1.5), Inches(11.9), Inches(5.5), font_size=18)
    finish(s, "Demo tip: DevTools -> Application -> Service Workers, tick Offline, reload /Pwa/Search to prove it works without a network. Full detail in PWA/README.md.")

    # Slide 11 -- Testing summary table
    s = new_slide(prs)
    add_title_bar(s, prs, "Testing Summary")
    rows, is_real = load_test_results()
    if not is_real:
        note = s.shapes.add_textbox(Inches(0.7), Inches(1.35), Inches(11.9), Inches(0.4))
        rn = note.text_frame.paragraphs[0].add_run()
        rn.text = "Test results pending — run build_docs.py after testing"
        rn.font.size = Pt(14)
        rn.font.bold = True
        rn.font.color.rgb = PptxColor(*hx(WARN_HEX))
        table_top = Inches(1.85)
        table_h = Inches(5.1)
    else:
        table_top = Inches(1.5)
        table_h = Inches(5.5)
    trows = [(r["id"], r["area"], r["test"][:70], r["status"]) for r in rows[:14]]
    add_table(s, Inches(0.5), table_top, Inches(12.3), table_h,
              ["ID", "Area", "Test", "Status"], trows, font_size=10)
    finish(s, "If this still says 'pending', it means testing hasn't been run yet -- rerun tools/build_docs.py once tools/test_results.json exists so this slide reflects real results, never invented ones.")

    # Slide 12 -- Conclusion & future scope
    s = new_slide(prs)
    add_title_bar(s, prs, "Conclusion & Future Scope")
    add_bullets(s, [
        "Delivered: console app (OOP), ASP.NET Core MVC web app (full CRUD + reports), and a PWA layer -- all on one shared, normalized SQL Server schema.",
        "Enforced negative-stock prevention at both the application and database layers.",
        "Future scope: role-based access control in the web app (Admin/Staff/Viewer, mirroring the console app)",
        "Future scope: barcode/QR scanning for faster Stock In/Out on mobile",
        "Future scope: multi-branch/multi-warehouse support",
        "Note: .NET 8 is an LTS release; its official support window ends November 2026 -- a future maintenance task is upgrading to the next LTS.",
    ], Inches(0.7), Inches(1.5), Inches(11.9), Inches(5.6), font_size=17)
    finish(s, "Close with what was delivered, then the future-scope items. Be upfront about the .NET 8 support-window note -- it shows awareness of maintaining the project beyond submission.")

    out_path = ROOT / "Documentation" / "PPT" / "InventoryManagementSystem.pptx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out_path)
    print(f"wrote {out_path} ({len(prs.slides._sldIdLst)} slides)")
    return out_path


# ===========================================================================
# 3. Final Report (.docx)
# ===========================================================================

DATA_DICTIONARY = {
    "Categories": [
        ("CategoryId", "int", "PK, identity"),
        ("CategoryName", "nvarchar(100)", "required, unique index"),
        ("Description", "nvarchar(250)", "optional"),
    ],
    "Suppliers": [
        ("SupplierId", "int", "PK, identity"),
        ("SupplierName", "nvarchar(150)", "required"),
        ("ContactNumber", "nvarchar(20)", "optional"),
        ("Email", "nvarchar(150)", "optional, email format"),
        ("Address", "nvarchar(250)", "optional"),
    ],
    "Products": [
        ("ProductId", "int", "PK, identity"),
        ("ProductName", "nvarchar(150)", "required, indexed"),
        ("Price", "decimal(10,2)", "CK_Products_Price >= 0"),
        ("Unit", "nvarchar(20)", "required, e.g. pcs/kg/L"),
        ("CategoryId", "int", "FK -> Categories, ON DELETE RESTRICT"),
        ("SupplierId", "int", "FK -> Suppliers, ON DELETE RESTRICT"),
    ],
    "Stocks": [
        ("StockId", "int", "PK, identity"),
        ("ProductId", "int", "FK -> Products, unique index, ON DELETE CASCADE"),
        ("QuantityAvailable", "int", "CK_Stocks_QuantityAvailable >= 0"),
        ("ReorderLevel", "int", "CK_Stocks_ReorderLevel >= 0"),
        ("LastUpdated", "datetime2", "defaults to current time"),
    ],
    "StockTransactions": [
        ("TransactionId", "int", "PK, identity"),
        ("ProductId", "int", "FK -> Products, ON DELETE CASCADE, indexed"),
        ("Type", "nvarchar(10)", "CK_StockTransactions_Type IN ('StockIn','StockOut')"),
        ("Quantity", "int", "CK_StockTransactions_Quantity > 0"),
        ("TransactionDate", "datetime2", "indexed"),
        ("PerformedBy", "nvarchar(100)", "required"),
        ("Remarks", "nvarchar(250)", "optional"),
    ],
    "Users": [
        ("UserId", "int", "PK, identity"),
        ("Username", "nvarchar(50)", "required, unique index"),
        ("PasswordHash", "nvarchar(256)", "required, hashed (PBKDF2-SHA512)"),
        ("FullName", "nvarchar(100)", "required"),
        ("Email", "nvarchar(150)", "optional, email format"),
        ("Role", "nvarchar(20)", "required, e.g. Admin"),
    ],
}

ROUTES = [
    ("Account", "GET /Account/Login", "Show the login form"),
    ("Account", "POST /Account/Login", "Validate credentials, start session"),
    ("Account", "POST /Account/Logout", "Clear session, redirect to Login"),
    ("Account", "GET/POST /Account/ChangePassword", "Change the current user's password"),
    ("Home", "GET /", "Redirects to /Dashboard"),
    ("Category", "GET /Category?searchTerm=", "List/search categories"),
    ("Category", "GET/POST /Category/Create", "Create a category"),
    ("Category", "GET/POST /Category/Edit/{id}", "Edit a category"),
    ("Category", "GET /Category/Delete/{id} + POST confirm", "Delete a category (blocked if in use)"),
    ("Product", "GET /Product?searchTerm=&categoryId=", "List/search/filter products"),
    ("Product", "GET/POST /Product/Create", "Create a product (+ opening stock, reorder level)"),
    ("Product", "GET/POST /Product/Edit/{id}", "Edit a product"),
    ("Product", "GET /Product/Delete/{id} + POST confirm", "Delete a product (cascades to stock/transactions)"),
    ("Supplier", "GET /Supplier?searchTerm=", "List/search suppliers"),
    ("Supplier", "GET/POST /Supplier/Create", "Create a supplier"),
    ("Supplier", "GET/POST /Supplier/Edit/{id}", "Edit a supplier"),
    ("Supplier", "GET /Supplier/Delete/{id} + POST confirm", "Delete a supplier (blocked if in use)"),
    ("Stock", "GET /Stock?searchTerm=&status=", "List/search/filter stock"),
    ("Stock", "GET/POST /Stock/Initialize", "Set opening stock for a product with none"),
    ("Stock", "GET/POST /Stock/StockIn?productId=", "Record a Stock In transaction"),
    ("Stock", "GET/POST /Stock/StockOut?productId=", "Record a Stock Out transaction (guards negative stock)"),
    ("Stock", "GET /Stock/Transactions?type=", "List stock transactions"),
    ("Dashboard", "GET /Dashboard", "KPIs, low-stock list, category summary, recent activity"),
    ("Report", "GET /Report", "Reports landing page"),
    ("Report", "GET /Report/ProductCatalog", "Product catalog report"),
    ("Report", "GET /Report/StockSummary", "Stock summary report"),
    ("Report", "GET /Report/LowStock", "Low stock report"),
    ("Report", "GET /Report/TransactionHistory", "Transaction history report"),
    ("Report", "GET /Report/InventoryValue", "Inventory value report"),
    ("Pwa", "GET /Pwa, /Pwa/Search, /Pwa/Stock, /Pwa/LowStock", "Mobile-first PWA pages"),
    ("Api", "GET /api/products?q=", "JSON product list (optionally filtered)"),
    ("Api", "GET /api/stock", "JSON stock list with status"),
    ("Api", "GET /api/stock/low", "JSON low/out-of-stock list"),
]

SYLLABUS_MAPPING = [
    ("Menu-driven console interface", "ConsoleApplication/Program.cs"),
    ("Classes & encapsulation", "ConsoleApplication/Models/*.cs (private fields + validating setters)"),
    ("Inheritance & polymorphism", "Person.cs -> Admin.cs / Staff.cs / User.cs, used by Services/UserService.cs"),
    ("Exception handling", "Program.cs catch blocks + Exceptions/InsufficientStockException.cs"),
    ("List / Dictionary collections", "ProductService / StockService (List); MasterDataService, UserService, ReportService.GenerateCategoryWiseReport (Dictionary)"),
    ("Search", "ProductService.SearchProduct"),
    ("Reports", "Reports/ReportService.cs"),
    ("Login / Logout / Change Password", "AccountController.cs + Views/Account/* + Filters/SessionAuthFilter.cs"),
    ("Master add/update/delete/search", "CategoryController, ProductController, SupplierController + views"),
    ("Stock transactions + negative-stock prevention", "StockController.StockIn/StockOut + CK_Stocks_QuantityAvailable"),
    ("Dashboard", "DashboardController + Views/Dashboard/Index.cshtml"),
    ("Reports search/filter/print", "ReportController, Views/Report/*, site.css @media print, _ReportHeader.cshtml"),
    ("SQL Server PK/FK/relationships, 6 normalized tables", "ApplicationDbContext.OnModelCreating, Database/SQLScripts/CreateTables.sql, Database/ERDiagram/README.md"),
    ("PWA responsive/installable/SW/offline/notifications", "_Layout.cshtml, site.css, manifest.json, sw.js, pwa.js, pwa-pages.js, PwaController, InventoryApiController"),
    ("PWA modules: Product Search / Low Stock Alerts / Stock Overview", "Views/Pwa/Search.cshtml, LowStock.cshtml, Stock.cshtml"),
]


def style_document(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = DocxPt(11)
    normal.font.color.rgb = SLATE_DOCX

    h1 = doc.styles["Heading 1"]
    h1.font.color.rgb = DARK_DOCX
    h1.font.size = DocxPt(20)
    h1.font.bold = True

    h2 = doc.styles["Heading 2"]
    h2.font.color.rgb = TEAL_DOCX
    h2.font.size = DocxPt(15)
    h2.font.bold = True

    h3 = doc.styles["Heading 3"]
    h3.font.color.rgb = DARK_DOCX
    h3.font.size = DocxPt(12.5)
    h3.font.bold = True


def add_toc(document):
    paragraph = document.add_paragraph()
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(docx_qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(docx_qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(docx_qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Right-click here and choose \"Update Field\" (or press F9) to build the table of contents."
    fld_sep.append(placeholder)
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(docx_qn("w:fldCharType"), "end")
    r = run._r
    r.append(fld_begin)
    r.append(instr)
    r.append(fld_sep)
    r.append(fld_end)


def set_cell_shading(cell, hex_color):
    shd = OxmlElement("w:shd")
    shd.set(docx_qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shd)


def add_docx_table(document, headers, rows, widths=None):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = str(h)
        set_cell_shading(hdr_cells[i], DARK_HEX)
        for p in hdr_cells[i].paragraphs:
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = DocxColor(0xFF, 0xFF, 0xFF)
                run.font.size = DocxPt(10)
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
            for p in cells[i].paragraphs:
                for run in p.runs:
                    run.font.size = DocxPt(10)
    if widths:
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = w
    document.add_paragraph()
    return table


def title_page(document):
    for _ in range(3):
        document.add_paragraph()
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(PROJECT_TITLE)
    r.font.size = DocxPt(40)
    r.font.bold = True
    r.font.color.rgb = DARK_DOCX

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(PROJECT_SUBTITLE)
    r.font.size = DocxPt(20)
    r.font.color.rgb = TEAL_DOCX

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Final Project Report")
    r.font.size = DocxPt(15)
    r.italic = True
    r.font.color.rgb = SLATE_DOCX

    for _ in range(2):
        document.add_paragraph()

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"Submitted in partial fulfilment of the requirements of\n{COURSE}")
    r.font.size = DocxPt(12)

    document.add_paragraph()
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Submitted by")
    r.font.bold = True
    for m in TEAM_MEMBERS:
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(m)

    document.add_paragraph()
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"{DEPARTMENT}\n{COLLEGE}\nGuide: {GUIDE}\n{ACADEMIC_YEAR}")
    r.font.size = DocxPt(12)
    document.add_page_break()


def certificate_page(document):
    document.add_heading("Certificate", level=1)
    document.add_paragraph(
        f"This is to certify that the project titled \"{FULL_TITLE}\" has been "
        f"successfully completed by the students named below, in partial "
        f"fulfilment of the requirements of {COURSE}, during the academic "
        f"year {ACADEMIC_YEAR}, under the guidance of {GUIDE}."
    )
    document.add_paragraph()
    for m in TEAM_MEMBERS:
        document.add_paragraph(m, style="List Bullet")
    document.add_paragraph()
    document.add_paragraph()
    document.add_paragraph("_______________________________")
    document.add_paragraph(f"{GUIDE}\nProject Guide")
    document.add_paragraph()
    document.add_paragraph("_______________________________")
    document.add_paragraph("Head of Department")
    document.add_page_break()


def acknowledgement_page(document):
    document.add_heading("Acknowledgement", level=1)
    document.add_paragraph(
        f"We would like to express our sincere gratitude to {GUIDE} for "
        f"continuous guidance and support throughout this project, and to "
        f"the {DEPARTMENT} of {COLLEGE} for providing the resources and "
        f"opportunity to undertake this work. We also thank our peers and "
        f"families for their encouragement during the development of "
        f"{FULL_TITLE}."
    )
    document.add_page_break()


def abstract_section(document):
    document.add_heading("Abstract", level=1)
    document.add_paragraph(
        f"{FULL_TITLE} is a college project that models a complete, "
        f"small-business inventory workflow across three coordinated "
        f"deliverables built on .NET 8: a menu-driven console application "
        f"demonstrating core object-oriented programming concepts; an "
        f"ASP.NET Core MVC web application backed by a normalized SQL "
        f"Server database, offering category, supplier, product and stock "
        f"management with session-based authentication and five printable "
        f"reports; and a Progressive Web App layer that makes the same web "
        f"application installable, responsive on mobile, and partly usable "
        f"offline, with low-stock notifications. A central design goal is "
        f"correctness under everyday operational pressure -- most visibly, "
        f"the system refuses to record a Stock Out that would push a "
        f"product's quantity below zero, enforced both in application code "
        f"and as a database check constraint. The system ships with "
        f"realistic demo data (6 categories, 6 suppliers, 30 products and "
        f"40 stock transactions) and a seeded administrator account so it "
        f"can be evaluated immediately after a first run."
    )
    document.add_page_break()


def toc_section(document):
    document.add_heading("Table of Contents", level=1)
    add_toc(document)
    document.add_page_break()


def chapter1_introduction(document):
    document.add_heading("Chapter 1: Introduction", level=1)
    document.add_heading("1.1 Overview", level=2)
    document.add_paragraph(
        f"{FULL_TITLE} addresses the everyday problem of tracking stock by "
        f"hand -- notebooks and spreadsheets that drift out of sync with "
        f"reality. The project delivers a working, demonstrable system "
        f"rather than a purely theoretical design: a console application, "
        f"a full web application, and a PWA layer on top of it, all "
        f"sharing the same domain concepts."
    )
    document.add_heading("1.2 Objectives", level=2)
    for item in [
        "Provide CRUD management of categories, suppliers and products.",
        "Track stock levels accurately through Stock In / Stock Out transactions.",
        "Prevent stock from ever going negative, at both the application and database layers.",
        "Give management a live dashboard and a set of filterable, printable reports.",
        "Demonstrate core OOP concepts (encapsulation, inheritance, polymorphism, exceptions, collections) in a standalone console application.",
        "Make the system usable on mobile, including partial offline access, via a Progressive Web App.",
    ]:
        document.add_paragraph(item, style="List Bullet")
    document.add_heading("1.3 Scope", level=2)
    document.add_paragraph(
        "The system is single-tenant and single-store: it does not model "
        "multiple warehouses, branches or currencies. Authentication is "
        "session-based and covers a single seeded administrator account "
        "for the web app; the console app separately demonstrates "
        "role-based behaviour (Admin / Staff / Viewer) as an OOP exercise. "
        "See the Future Scope section (Chapter 7) for planned extensions "
        "beyond this scope."
    )
    document.add_page_break()


def chapter2_requirements(document):
    document.add_heading("Chapter 2: Requirements", level=1)
    document.add_paragraph(
        "This chapter summarizes the Software Requirements Specification "
        "(full detail in Documentation/SRS/README.md)."
    )
    document.add_heading("2.1 Users", level=2)
    for item in [
        "Admin -- full access: manage categories, suppliers, products, stock, and view all reports. Seeded account: admin / Admin@123.",
        "Staff -- day-to-day operator: records Stock In/Out, views reports.",
        "Viewer (console app) -- read-only; any add/update/delete is blocked.",
    ]:
        document.add_paragraph(item, style="List Bullet")
    document.add_heading("2.2 Key functional requirements", level=2)
    fr_rows = [
        ("FR-01", "Log in / log out with session-based authentication"),
        ("FR-05/07/09", "Create, edit, delete, search Categories / Suppliers / Products"),
        ("FR-06/08", "Block deleting a Category/Supplier still referenced by a Product"),
        ("FR-12/13", "Record Stock In / Stock Out; reject a Stock Out that would go negative"),
        ("FR-16", "Dashboard with live KPIs, low-stock list, category summary"),
        ("FR-17", "Five filterable, print-friendly reports"),
        ("FR-19", "PWA install, offline browsing of cached data, low-stock notifications"),
        ("FR-20", "Demo data seeded automatically on first run"),
    ]
    add_docx_table(document, ["ID", "Requirement"], fr_rows)
    document.add_heading("2.3 Non-functional requirements", level=2)
    for item in [
        "Security -- passwords are hashed (PBKDF2-SHA512), never stored in plain text; anti-forgery tokens on state-changing requests.",
        "Usability -- responsive Bootstrap UI down to phone width; clear success/error messages.",
        "Availability -- PWA offline access to previously synced product/stock data.",
        "Data integrity -- database check constraints back up application-level validation.",
    ]:
        document.add_paragraph(item, style="List Bullet")
    document.add_page_break()


def chapter3_design(document):
    document.add_heading("Chapter 3: Design", level=1)

    document.add_heading("3.1 System Architecture", level=2)
    document.add_paragraph(
        "The system is built in three layered phases that share one domain "
        "model. Phase 1, the console application, is an in-memory, "
        "file-free implementation used to demonstrate OOP fundamentals: "
        "classes, inheritance (Person -> Admin/Staff/User), polymorphism "
        "(overridden DisplayInfo()), custom exceptions "
        "(InsufficientStockException) and collections (List<T>, "
        "Dictionary<TKey,TValue>). Phase 2, the ASP.NET Core MVC web "
        "application, is the primary deliverable: Controllers handle "
        "requests, Entity Framework Core 8 maps six normalized tables in "
        "SQL Server, and Razor views render the UI. A SessionAuthFilter "
        "enforces that every page but Login requires an active session. "
        "Phase 3, the Progressive Web App layer, sits on top of Phase 2 "
        "without a separate backend: a Web App Manifest and Service Worker "
        "make the same web app installable and partly usable offline, "
        "backed by a small JSON API (Controllers/Api/InventoryApiController.cs)."
    )

    document.add_heading("3.2 Data Dictionary", level=2)
    document.add_paragraph(
        "Six tables, normalized to Third Normal Form (3NF) -- see "
        "Database/ERDiagram/README.md for the full normalization "
        "rationale."
    )
    for table_name, cols in DATA_DICTIONARY.items():
        document.add_heading(table_name, level=3)
        add_docx_table(document, ["Column", "Type", "Constraint"], cols)

    document.add_heading("3.3 Entity-Relationship Diagram", level=2)
    erd_path = ROOT / "Database" / "ERDiagram" / "ERDiagram.png"
    if erd_path.exists():
        document.add_picture(str(erd_path), width=DocxInches(6.2))
    document.add_paragraph(
        "Category -> Product and Supplier -> Product are one-to-many with "
        "ON DELETE RESTRICT (a master record in use cannot be deleted). "
        "Product -> Stock is one-to-one (optional) and Product -> "
        "StockTransaction is one-to-many, both with ON DELETE CASCADE "
        "(dependent data is removed with its product). Users has no "
        "foreign key relationship to the inventory tables."
    )

    document.add_heading("3.4 Web Application Routes", level=2)
    add_docx_table(document, ["Controller", "Route", "Purpose"], ROUTES)

    document.add_page_break()


def chapter4_implementation(document):
    document.add_heading("Chapter 4: Implementation", level=1)

    document.add_heading("4.1 Console Application", level=2)
    document.add_paragraph(
        "A menu-driven .NET 8 console app (ConsoleApplication/Program.cs) "
        "covering Product Management, Stock Management, Reports and "
        "Viewing Users. Domain objects (Product, Category, Supplier, "
        "Stock, StockTransaction) use private fields with validating "
        "properties -- encapsulation. Person is an abstract base class "
        "with Admin, Staff and User derived classes overriding the virtual "
        "DisplayInfo() method -- inheritance and polymorphism. "
        "MasterDataService and UserService use Dictionary<TKey,TValue> for "
        "fast name/username lookup; ProductService and StockService use "
        "List<T>. StockService throws a custom InsufficientStockException "
        "on an invalid Stock Out, caught explicitly in Program.cs. Input "
        "reading goes through InputHelper.ReadLine(), which exits cleanly "
        "on EOF instead of looping forever."
    )

    document.add_heading("4.2 ASP.NET Core MVC Web Application", level=2)
    document.add_paragraph(
        "Controllers (Account, Home, Category, Product, Supplier, Stock, "
        "Dashboard, Report, Pwa, Api/InventoryApi) sit over an Entity "
        "Framework Core DbContext (ApplicationDbContext) mapping the six "
        "tables described in Chapter 3. DbInitializer creates the "
        "database on first run, seeds the admin account with a hashed "
        "password, and loads demo data from Database/SQLScripts/SeedData.sql. "
        "A SessionAuthFilter action filter enforces login on every "
        "controller action except those marked [AllowAnonymous], "
        "returning a redirect for page requests and a 401 JSON response "
        "for API requests under /api. State-changing POST actions require "
        "anti-forgery tokens. StockController.StockIn/StockOut validate "
        "the requested quantity in code before saving, and the database "
        "check constraints (CK_Stocks_QuantityAvailable, "
        "CK_StockTransactions_Quantity, CK_StockTransactions_Type, "
        "CK_Products_Price) enforce the same rules as a backstop."
    )

    document.add_heading("4.3 Progressive Web App", level=2)
    document.add_paragraph(
        "manifest.json declares the installable app identity (name, "
        "icons, theme colour #1E293B, start URL /Pwa). sw.js implements "
        "three caching strategies across three named caches: network-first "
        "for /api/* JSON calls and for page navigations (each falling "
        "back to a cached copy, and further to offline.html for pages), "
        "and stale-while-revalidate for static assets. pwa.js registers "
        "the service worker, manages the install prompt, the offline "
        "banner and low-stock notification scheduling; pwa-pages.js "
        "renders the Search / Stock / Low Stock pages from JSON returned "
        "by InventoryApiController, working from cached data when "
        "offline. Full detail is in PWA/README.md."
    )
    document.add_page_break()


def chapter5_testing(document, test_rows, is_real):
    document.add_heading("Chapter 5: Testing", level=1)
    if not is_real:
        p = document.add_paragraph()
        r = p.add_run("Test results pending — run build_docs.py after testing")
        r.font.bold = True
        r.font.color.rgb = DocxColor(*hx(WARN_HEX))
        document.add_paragraph(
            "tools/test_results.json has not been produced yet by the test "
            "run. The table below lists the planned test cases with every "
            "status shown as \"Pending\" -- no result is claimed until the "
            "real test run writes tools/test_results.json and this report "
            "is regenerated."
        )
    else:
        document.add_paragraph(
            "Results below are taken directly from tools/test_results.json, "
            "produced by the project's test run."
        )
    rows = [(r["id"], r["area"], r["test"], r["expected"], r["actual"], r["status"]) for r in test_rows]
    add_docx_table(document, ["ID", "Area", "Test", "Expected", "Actual", "Status"], rows)
    document.add_page_break()


def chapter6_setup(document):
    document.add_heading("Chapter 6: Setup", level=1)
    document.add_paragraph(
        "Full click-by-click instructions are in "
        "Documentation/UserManual/UserManual.md (also available as "
        "UserManual.docx). Summary for a Windows/Visual Studio 2022 "
        "examiner machine:"
    )
    for item in [
        "Install Visual Studio 2022 Community with the \"ASP.NET and web development\" workload and the .NET 8.0 Runtime.",
        "Open InventoryManagementSystem.sln.",
        "Press F5 -- the database and demo data are created automatically on first run (LocalDB).",
        "Log in with admin / Admin@123.",
        "Optionally run the console app (right-click ConsoleApplication -> Set as Startup Project -> Ctrl+F5).",
    ]:
        document.add_paragraph(item, style="List Number")
    document.add_page_break()


def chapter7_conclusion(document):
    document.add_heading("Chapter 7: Conclusion & Future Scope", level=1)
    document.add_heading("7.1 Conclusion", level=2)
    document.add_paragraph(
        f"{FULL_TITLE} meets its stated objectives: a normalized, "
        f"constraint-backed database; a full-featured web application "
        f"with authentication, CRUD, stock control and reporting; a "
        f"console application demonstrating core OOP concepts; and a PWA "
        f"layer that makes the system installable and partly usable "
        f"offline. The negative-stock guard -- checked in application "
        f"code and enforced again by a database CHECK constraint -- "
        f"exemplifies the project's approach of defending correctness at "
        f"more than one layer."
    )
    document.add_heading("7.2 Future Scope", level=2)
    for item in [
        "Role-based access control in the web app (Admin/Staff/Viewer), mirroring the console app's role model.",
        "Barcode/QR scanning for faster Stock In/Out from a mobile device.",
        "Multi-branch/multi-warehouse support.",
        "Purchase-order workflow tied directly to Low Stock alerts.",
        "Automated test suite and CI pipeline.",
    ]:
        document.add_paragraph(item, style="List Bullet")
    p = document.add_paragraph()
    r = p.add_run(
        "Note: .NET 8 is a Long-Term Support (LTS) release; its official "
        "Microsoft support window ends November 2026. This is fine for "
        "the current submission, but any future maintenance of this "
        "project should plan a migration to the next LTS release before "
        "that date."
    )
    r.italic = True
    document.add_page_break()


def references_section(document):
    document.add_heading("References", level=1)
    for item in [
        BASE_REPO_CREDIT + f" -- {BASE_REPO_URL}",
        "Microsoft Learn -- ASP.NET Core documentation (learn.microsoft.com/aspnet/core)",
        "Microsoft Learn -- Entity Framework Core documentation (learn.microsoft.com/ef/core)",
        "Microsoft Learn -- ASP.NET Core Identity password hashing (PasswordHasher)",
        "MDN Web Docs -- Progressive Web Apps, Service Worker API, Web App Manifest",
        "Bootstrap 5.3 documentation (getbootstrap.com)",
        "Microsoft -- .NET support policy (dotnet.microsoft.com/platform/support-policy)",
    ]:
        document.add_paragraph(item, style="List Bullet")
    document.add_page_break()


def appendix_mapping(document):
    document.add_heading("Appendix A: Syllabus Requirement Mapping", level=1)
    document.add_paragraph(
        "Maps each graded syllabus requirement to the file(s) that "
        "implement it."
    )
    add_docx_table(document, ["Requirement", "File(s)"], SYLLABUS_MAPPING)


def build_final_report():
    test_rows, is_real = load_test_results()

    document = Document()
    style_document(document)

    title_page(document)
    certificate_page(document)
    acknowledgement_page(document)
    abstract_section(document)
    toc_section(document)
    chapter1_introduction(document)
    chapter2_requirements(document)
    chapter3_design(document)
    chapter4_implementation(document)
    chapter5_testing(document, test_rows, is_real)
    chapter6_setup(document)
    chapter7_conclusion(document)
    references_section(document)
    appendix_mapping(document)

    out_path = ROOT / "Documentation" / "FinalReport" / "InventoryManagementSystem_FinalReport.docx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(out_path)
    print(f"wrote {out_path}")
    return out_path


# ===========================================================================
# 4. UserManual.md -> UserManual.docx (small markdown converter)
# ===========================================================================

INLINE_RE = re.compile(r"(\*\*.+?\*\*|`[^`]+?`)")


def add_inline_runs(paragraph, text):
    if not text:
        paragraph.add_run("")
        return
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.font.bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = DocxPt(10)
            run.font.color.rgb = DocxColor(*hx(DARK_HEX))
        else:
            paragraph.add_run(part)


def parse_pipe_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def is_separator_row(cells):
    return all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells if c.strip())


def convert_markdown_to_docx(md_path: Path, out_path: Path):
    lines = md_path.read_text(encoding="utf-8").splitlines()

    document = Document()
    style_document(document)

    i = 0
    n = len(lines)
    in_code = False
    code_lines = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            p = document.add_paragraph()
            p.paragraph_format.left_indent = DocxInches(0.3)
            joined = "\n".join(code_lines)
            run = p.add_run(joined)
            run.font.name = "Consolas"
            run.font.size = DocxPt(10)
            run.font.color.rgb = DocxColor(*hx(DARK_HEX))
            code_lines = []

    while i < n:
        raw = lines[i]
        line = raw.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            document.add_page_break()
            i += 1
            continue

        if stripped.startswith("| ") or (stripped.startswith("|") and stripped.endswith("|")):
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2 and is_separator_row(parse_pipe_row(table_lines[1])):
                header = parse_pipe_row(table_lines[0])
                body = [parse_pipe_row(r) for r in table_lines[2:]]
                table = document.add_table(rows=1, cols=len(header))
                table.style = "Table Grid"
                for c, h in enumerate(header):
                    cell = table.rows[0].cells[c]
                    set_cell_shading(cell, DARK_HEX)
                    p = cell.paragraphs[0]
                    add_inline_runs(p, h)
                    for run in p.runs:
                        run.font.bold = True
                        run.font.size = DocxPt(10)
                        run.font.color.rgb = DocxColor(0xFF, 0xFF, 0xFF)
                for row in body:
                    cells = table.add_row().cells
                    for c, val in enumerate(row):
                        if c < len(cells):
                            p = cells[c].paragraphs[0]
                            add_inline_runs(p, val)
                            for run in p.runs:
                                run.font.size = DocxPt(10)
                document.add_paragraph()
            continue

        m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            document.add_heading(m.group(2), level=level)
            i += 1
            continue

        if stripped.startswith("> "):
            p = document.add_paragraph()
            p.paragraph_format.left_indent = DocxInches(0.3)
            run_text = stripped[2:]
            add_inline_runs(p, run_text)
            for run in p.runs:
                run.italic = True
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if m:
            p = document.add_paragraph()
            p.paragraph_format.left_indent = DocxInches(0.25)
            add_inline_runs(p, stripped)
            i += 1
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            p = document.add_paragraph()
            p.paragraph_format.left_indent = DocxInches(0.25)
            add_inline_runs(p, "• " + stripped[2:])
            i += 1
            continue

        p = document.add_paragraph()
        add_inline_runs(p, stripped)
        i += 1

    flush_code()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(out_path)
    print(f"wrote {out_path}")
    return out_path


def build_user_manual_docx():
    md_path = ROOT / "Documentation" / "UserManual" / "UserManual.md"
    out_path = ROOT / "Documentation" / "UserManual" / "UserManual.docx"
    return convert_markdown_to_docx(md_path, out_path)


# ===========================================================================
# main
# ===========================================================================

def main():
    print("1/4 Drawing ER diagram...")
    draw_erd_diagram()
    print("2/4 Building presentation...")
    build_pptx()
    print("3/4 Building final report...")
    build_final_report()
    print("4/4 Converting user manual...")
    build_user_manual_docx()
    print("Done.")


if __name__ == "__main__":
    main()
