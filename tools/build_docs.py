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
import sys
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
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

# ---------------------------------------------------------------------------
# Shared config/colours/test-results now live in tools/common.py (imported by
# both this module and tools/ppt_builder.py, so they stay in sync).
# ---------------------------------------------------------------------------
from common import (  # noqa: E402
    cfg,
    PROJECT_TITLE,
    PROJECT_SUBTITLE,
    PROJECT_TAGLINE,
    FULL_TITLE,
    TEAM_MEMBERS,
    COLLEGE,
    DEPARTMENT,
    GUIDE,
    ACADEMIC_YEAR,
    COURSE,
    BASE_REPO_URL,
    BASE_REPO_CREDIT,
    DARK_HEX,
    TEAL_HEX,
    LIGHT_HEX,
    SLATE_HEX,
    WHITE_HEX,
    DANGER_HEX,
    WARN_HEX,
    OK_HEX,
    hx,
    DARK_RGB,
    TEAL_RGB,
    LIGHT_RGB,
    SLATE_RGB,
    WHITE_RGB,
    DARK_DOCX,
    TEAL_DOCX,
    SLATE_DOCX,
    load_test_results,
    FALLBACK_TEST_CASES,
    status_color,
)

# ---------------------------------------------------------------------------
# tools/doc_config.py is owned by another agent; read-only. common.py already
# reads it for the values above -- this stays only so any code below that
# still calls cfg(...) directly keeps working unchanged.
# ---------------------------------------------------------------------------
try:
    import doc_config  # type: ignore  # noqa: F401  (already read by common.py; kept importable)
except Exception:
    doc_config = None

# PPTX-specific colour objects (not in common.py, which only builds docx
# RGBColor objects) -- used by the fallback build_pptx() below.
DARK_PPTX = PptxColor(*DARK_RGB)
TEAL_PPTX = PptxColor(*TEAL_RGB)
LIGHT_PPTX = PptxColor(*LIGHT_RGB)
SLATE_PPTX = PptxColor(*SLATE_RGB)
WHITE_PPTX = PptxColor(*WHITE_RGB)


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
# 3. UserManual.md -> UserManual.docx (small markdown converter)
# ---------------------------------------------------------------------------
# The Final Report build (style_document, add_toc, add_docx_table, the title
# page and chapters, build_final_report) now lives in tools/report_builder.py
# -- it is owned and improved there. The two small helpers below are kept
# here only because the UserManual converter needs them too.
# ===========================================================================

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


def set_cell_shading(cell, hex_color):
    shd = OxmlElement("w:shd")
    shd.set(docx_qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shd)


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
    print("1/5 Generating diagrams and charts...")
    import diagrams
    diagrams.generate_all()

    print("2/5 Drawing ER diagram...")
    draw_erd_diagram()

    print("3/5 Building presentation...")
    try:
        import ppt_builder
    except ImportError:
        ppt_builder = None
    if ppt_builder is not None:
        ppt_builder.build_pptx()
    else:
        print("  tools/ppt_builder.py not found; falling back to build_docs.build_pptx()")
        build_pptx()

    print("4/5 Building final report...")
    import report_builder
    report_builder.build_final_report()

    print("5/5 Converting user manual...")
    build_user_manual_docx()
    print("Done.")


if __name__ == "__main__":
    main()
