"""
Generates every diagram and chart PNG used by the Final Report (and reused by
the PPT) into Documentation/assets/. Pure matplotlib (patches + arrows), no
graphviz. ASCII-safe text only (no em dashes / arrows / rupee glyphs) because
the default sans-serif font used at render time does not reliably ship them.

Run standalone with:
    tools/.venv/bin/python tools/diagrams.py
or via generate_all() from tools/build_docs.py.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Wedge

import common
import seed_stats

ASSETS = common.ASSETS
ASSETS.mkdir(parents=True, exist_ok=True)

DPI = 200

DARK = "#" + common.DARK_HEX
TEAL = "#" + common.TEAL_HEX
LIGHT = "#" + common.LIGHT_HEX
SLATE = "#" + common.SLATE_HEX
WHITE = "#FFFFFF"
DANGER = "#" + common.DANGER_HEX
WARN = "#" + common.WARN_HEX
OK = "#" + common.OK_HEX
PALETTE = ["#" + c for c in common.LIGHT_PALETTE_HEX]

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["savefig.facecolor"] = WHITE
plt.rcParams["figure.facecolor"] = WHITE


# ---------------------------------------------------------------------------
# shared drawing helpers for box-and-arrow diagrams
# ---------------------------------------------------------------------------

def new_canvas(w, h, xlim=100, ylim=100):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xlim)
    ax.set_ylim(0, ylim)
    ax.axis("off")
    ax.set_aspect("auto")
    return fig, ax


def box(ax, cx, cy, w, h, text, fc=DARK, tc=WHITE, fontsize=10.5, weight="bold",
        ec=DARK, lw=1.4, rounding=0.08, italic=False, linestyle="solid"):
    patch = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle=f"round,pad=0,rounding_size={rounding * min(w, h):.2f}",
        linewidth=lw, edgecolor=ec, facecolor=fc, linestyle=linestyle,
        mutation_aspect=1,
    )
    ax.add_patch(patch)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize,
             fontweight=weight, color=tc, style=("italic" if italic else "normal"),
             linespacing=1.35)
    return (cx, cy, w, h)


def datastore(ax, cx, cy, w, h, text, fc=WHITE, tc=DARK, fontsize=10):
    """Gane-Sarson open-ended rectangle for a data store."""
    ax.plot([cx - w / 2, cx + w / 2], [cy + h / 2, cy + h / 2], color=DARK, lw=1.6)
    ax.plot([cx - w / 2, cx + w / 2], [cy - h / 2, cy - h / 2], color=DARK, lw=1.6)
    ax.plot([cx - w / 2, cx - w / 2], [cy - h / 2, cy + h / 2], color=DARK, lw=1.6)
    ax.add_patch(plt.Rectangle((cx - w / 2, cy - h / 2), w, h, fill=True, facecolor=fc, edgecolor="none", zorder=1))
    ax.plot([cx - w / 2, cx + w / 2], [cy + h / 2, cy + h / 2], color=DARK, lw=1.6, zorder=2)
    ax.plot([cx - w / 2, cx + w / 2], [cy - h / 2, cy - h / 2], color=DARK, lw=1.6, zorder=2)
    ax.plot([cx - w / 2, cx - w / 2], [cy - h / 2, cy + h / 2], color=DARK, lw=1.6, zorder=2)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize, fontweight="bold", color=tc, zorder=3)
    return (cx, cy, w, h)


def process_circle(ax, cx, cy, r, text, fc=TEAL, tc=WHITE, fontsize=10):
    c = Circle((cx, cy), r, facecolor=fc, edgecolor=DARK, linewidth=1.4, zorder=2)
    ax.add_patch(c)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize, fontweight="bold",
             color=tc, linespacing=1.3, zorder=3)
    return (cx, cy, r * 2, r * 2)


def diamond(ax, cx, cy, w, h, text, fc=WARN, tc=WHITE, fontsize=9.5):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(plt.Polygon(pts, closed=True, facecolor=fc, edgecolor=DARK, linewidth=1.4, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize, fontweight="bold", color=tc, zorder=3)
    return (cx, cy, w, h)


def actor(ax, cx, cy, label, scale=1.0, color=DARK):
    """A simple UML stick figure, head centred at (cx, cy)."""
    s = scale
    head = Circle((cx, cy), 2.1 * s, facecolor=WHITE, edgecolor=color, linewidth=1.8, zorder=3)
    ax.add_patch(head)
    ax.plot([cx, cx], [cy - 2.1 * s, cy - 8 * s], color=color, lw=1.8, zorder=2)  # body
    ax.plot([cx - 3.6 * s, cx + 3.6 * s], [cy - 4.5 * s, cy - 4.5 * s], color=color, lw=1.8, zorder=2)  # arms
    ax.plot([cx, cx - 3 * s], [cy - 8 * s, cy - 12.5 * s], color=color, lw=1.8, zorder=2)  # left leg
    ax.plot([cx, cx + 3 * s], [cy - 8 * s, cy - 12.5 * s], color=color, lw=1.8, zorder=2)  # right leg
    ax.text(cx, cy - 14.5 * s, label, ha="center", va="top", fontsize=10.5, fontweight="bold", color=DARK)


def arrow(ax, p1, p2, color=TEAL, lw=1.8, style="-|>", connectionstyle="arc3,rad=0.0",
          linestyle="solid", mutation_scale=14):
    fa = FancyArrowPatch(p1, p2, arrowstyle=style, color=color, lw=lw,
                          connectionstyle=connectionstyle, linestyle=linestyle,
                          mutation_scale=mutation_scale, shrinkA=2, shrinkB=2, zorder=1)
    ax.add_patch(fa)
    return fa


def edge_label(ax, x, y, text, fontsize=8.5, color=SLATE, rotation=0, bg=True):
    kw = dict(ha="center", va="center", fontsize=fontsize, color=color, rotation=rotation, zorder=4)
    if bg:
        kw["bbox"] = dict(boxstyle="round,pad=0.15", fc=WHITE, ec="none", alpha=0.92)
    ax.text(x, y, text, **kw)


def save(fig, name, pad=0.25):
    out = ASSETS / name
    fig.savefig(out, dpi=DPI, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    print(f"wrote {out}")
    return out


# ---------------------------------------------------------------------------
# 1. fig_architecture.png
# ---------------------------------------------------------------------------

def fig_architecture():
    fig, ax = new_canvas(12, 8.2, 120, 90)

    top_y = 82
    box(ax, 20, top_y, 32, 12, "Console Application\n(.NET 8 - OOP demo,\nno database)", fc=SLATE, fontsize=10)
    box(ax, 60, top_y, 32, 12, "ASP.NET Core MVC\nWeb App (Browser)", fc=DARK, fontsize=10.5)
    box(ax, 100, top_y, 32, 12, "Progressive Web App\n(installed on phone)", fc=DARK, fontsize=10.5)

    sw_box = box(ax, 100, 62, 30, 9, "Service Worker\ncache layer", fc=TEAL, fontsize=9.5)
    arrow(ax, (100, top_y - 6), (100, 62 + 4.5))
    edge_label(ax, 108, 72, "install /\nregister", fontsize=7.8)

    ctrl_y = 47
    ctrl = box(ax, 60, ctrl_y, 62, 10, "Controllers  (MVC views + Api/InventoryApiController)", fc=DARK, fontsize=10.5)
    arrow(ax, (60, top_y - 6), (60, ctrl_y + 5))
    arrow(ax, (95, 62 - 4.5), (75, ctrl_y + 5))
    edge_label(ax, 84, 55, "fetch (online)", fontsize=7.8)
    arrow(ax, (20, top_y - 6), (30, 30), color=SLATE, linestyle="dashed", style="-")
    edge_label(ax, 16, 55, "shares domain\nconcepts only\n(no runtime link)", fontsize=7.6, rotation=0)

    ef_y = 30
    ef = box(ax, 60, ef_y, 44, 10, "EF Core 8\n(ApplicationDbContext)", fc=TEAL, fontsize=10.5)
    arrow(ax, (60, ctrl_y - 5), (60, ef_y + 5))

    db_y = 13
    db = box(ax, 60, db_y, 46, 11, "SQL Server\nInventoryManagementDB\n(6 normalised tables)", fc=DARK, fontsize=10.5)
    arrow(ax, (60, ef_y - 5), (60, db_y + 5.5))

    ax.text(60, 91.5, "StockPilot - Layered Architecture", ha="center", fontsize=13.5, fontweight="bold", color=DARK)
    fig.tight_layout()
    save(fig, "fig_architecture.png")


# ---------------------------------------------------------------------------
# 2. fig_usecase.png
# ---------------------------------------------------------------------------

def fig_usecase():
    fig, ax = new_canvas(11, 8.5, 100, 90)

    boundary = plt.Rectangle((22, 6), 74, 78, fill=True, facecolor=LIGHT, edgecolor=DARK, linewidth=1.6, zorder=0)
    ax.add_patch(boundary)
    ax.text(59, 87, "StockPilot System", ha="center", fontsize=12, fontweight="bold", color=DARK, zorder=5)

    actor(ax, 8, 68, "Admin", scale=1.05)
    actor(ax, 8, 22, "Staff", scale=1.05)

    use_cases = [
        "Login",
        "Manage Categories,\nProducts & Suppliers",
        "Stock In / Stock Out",
        "View Dashboard",
        "Generate & Print\nReports",
        "Change Password",
        "Search Products\n(PWA)",
        "Receive Low-Stock\nAlerts",
    ]
    positions = [(42, 78), (78, 78), (42, 60), (78, 60), (42, 42), (78, 42), (42, 22), (78, 22)]
    ellipse_wh = (28, 13)
    for (cx, cy), label in zip(positions, use_cases):
        e = plt.matplotlib.patches.Ellipse((cx, cy), ellipse_wh[0], ellipse_wh[1],
                                            facecolor=WHITE, edgecolor=TEAL, linewidth=1.8, zorder=2)
        ax.add_patch(e)
        ax.text(cx, cy, label, ha="center", va="center", fontsize=8.6, color=DARK, fontweight="bold", zorder=3)

    admin_uc = list(range(8))  # all
    staff_uc = [0, 2, 3, 4, 5, 6, 7]  # everything except master-data management

    for i in admin_uc:
        cx, cy = positions[i]
        ax.plot([8 + 3, cx - ellipse_wh[0] / 2], [68, cy], color=DARK, lw=0.9, alpha=0.65, zorder=1)
    for i in staff_uc:
        cx, cy = positions[i]
        ax.plot([8 + 3, cx - ellipse_wh[0] / 2], [22, cy], color=TEAL, lw=0.9, alpha=0.65, zorder=1)

    ax.text(59, 2.5,
            "Admin has access to every use case; Staff covers day-to-day operation "
            "(no master-data management).",
            ha="center", fontsize=9, color=SLATE)
    fig.tight_layout()
    save(fig, "fig_usecase.png")


# ---------------------------------------------------------------------------
# 3. fig_dfd0.png (context diagram)
# ---------------------------------------------------------------------------

def fig_dfd0():
    fig, ax = new_canvas(9, 6.5, 100, 80)

    process_circle(ax, 50, 40, 20, "0\nStockPilot\nInventory\nManagement\nSystem", fc=TEAL, fontsize=10.5)

    box(ax, 12, 62, 20, 12, "Admin", fc=DARK, fontsize=11)
    box(ax, 12, 18, 20, 12, "Staff", fc=DARK, fontsize=11)
    box(ax, 88, 62, 22, 12, "Web Browser /\nPWA client", fc=SLATE, fontsize=9.5)
    box(ax, 88, 18, 22, 12, "SQL Server\n(data store)", fc=SLATE, fontsize=9.5)

    arrow(ax, (22, 62), (36, 47))
    edge_label(ax, 25, 52, "login, master data,\nstock transactions", fontsize=7.8)
    arrow(ax, (22, 18), (36, 33))
    edge_label(ax, 25, 28, "login, stock\ntransactions", fontsize=7.8)

    arrow(ax, (64, 47), (78, 60), color=SLATE)
    edge_label(ax, 74, 58, "dashboards,\nreports, alerts", fontsize=7.8)
    arrow(ax, (67, 35), (78, 20), color=SLATE)
    edge_label(ax, 75, 24, "persisted /\nqueried data", fontsize=7.8)

    ax.text(50, 76, "Level 0 DFD - Context Diagram", ha="center", fontsize=13, fontweight="bold", color=DARK)
    fig.tight_layout()
    save(fig, "fig_dfd0.png")


# ---------------------------------------------------------------------------
# 4. fig_dfd1.png (level 1)
# ---------------------------------------------------------------------------

def fig_dfd1():
    fig, ax = new_canvas(14, 11.5, 130, 112)

    # rows, evenly spaced top to bottom, with room below title and above x-axis
    rows = [90, 70.5, 51, 31.5, 12]
    proc_x, store_x, ent_x = 48, 100, 8

    procs = {
        "1.0": ("1.0\nAuthentication", rows[0]),
        "2.0": ("2.0\nMaster Data", rows[1]),
        "3.0": ("3.0\nStock\nTransactions", rows[2]),
        "4.0": ("4.0\nReports /\nDashboard", rows[3]),
        "5.0": ("5.0\nPWA Sync", rows[4]),
    }
    r = 9.2
    ppos = {}
    for key, (label, cy) in procs.items():
        process_circle(ax, proc_x, cy, r, label, fc=TEAL, fontsize=8.8)
        ppos[key] = (proc_x, cy)

    stores = {
        "D1": ("D1  Users", rows[0]),
        "D2": ("D2  Products /\nCategories / Suppliers", rows[1]),
        "D3": ("D3  Stocks", rows[2]),
        "D4": ("D4  StockTransactions", rows[3]),
    }
    spos = {}
    for key, (label, cy) in stores.items():
        datastore(ax, store_x, cy, 26, 9.5, label, fontsize=8.2)
        spos[key] = (store_x, cy)

    admin_y, staff_y = 80, 41
    box(ax, ent_x, admin_y, 16, 10, "Admin", fc=DARK, fontsize=10)
    box(ax, ent_x, staff_y, 16, 10, "Staff", fc=DARK, fontsize=10)

    def flow(p1, p2, label, mx=None, my=None, dashed=False, color=SLATE, fontsize=7.6, lw=1.3):
        arrow(ax, p1, p2, color=color, linestyle=("dashed" if dashed else "solid"), lw=lw, mutation_scale=11)
        lx = mx if mx is not None else (p1[0] + p2[0]) / 2
        ly = my if my is not None else (p1[1] + p2[1]) / 2
        edge_label(ax, lx, ly, label, fontsize=fontsize, color=color if color != SLATE else DARK)

    # entities -> processes
    flow((ent_x + 8, admin_y + 3), (proc_x - r, rows[0] + 2), "login", mx=25, my=88)
    flow((ent_x + 8, admin_y - 3), (proc_x - r, rows[1] + 1), "master data\nCRUD", my=71, mx=26)
    flow((ent_x + 8, staff_y + 5), (proc_x - r, rows[0] - 9), "login", mx=23, my=57)
    flow((ent_x + 8, staff_y), (proc_x - r, rows[2]), "stock in / out", my=44)

    # processes -> data stores
    flow((proc_x + r, rows[0]), (store_x - 13, rows[0]), "verify\ncredentials")
    flow((proc_x + r, rows[1]), (store_x - 13, rows[1]), "create / update /\ndelete")
    flow((proc_x + r, rows[2]), (store_x - 13, rows[2]), "update qty")
    flow((proc_x + 4, rows[2] - r + 1), (store_x - 13, rows[3] + 3), "insert\ntransaction", mx=76, my=39)

    # data stores -> 4.0 Reports/Dashboard (reads)
    flow((store_x - 13, rows[1] - 3), (proc_x + r - 2, rows[3] + 6), "read", dashed=True, mx=76, my=55)
    flow((store_x - 13, rows[2] - 3), (proc_x + r - 1, rows[3] + 2), "read", dashed=True, mx=80, my=42)
    flow((store_x - 13, rows[3]), (proc_x + r, rows[3]), "read", dashed=True)

    # 5.0 PWA Sync <-> D2 / D3 (cached reads)
    flow((proc_x + 3, rows[4] + r - 1), (store_x - 13, rows[1] - 4), "cached read",
         dashed=True, color=TEAL, mx=78, my=63)
    flow((proc_x + 6, rows[4] + r - 3), (store_x - 13, rows[2] - 4), "cached read",
         dashed=True, color=TEAL, mx=84, my=26)

    # outputs back to entities
    flow((proc_x - r, rows[3] + 3), (ent_x + 8, admin_y - 8), "dashboard / reports", mx=26, my=24)
    flow((proc_x - r, rows[3] - 2), (ent_x + 8, staff_y - 2), "dashboard / reports", mx=25, my=27)
    flow((proc_x - r + 1, rows[4] + 4), (ent_x + 8, staff_y - 7), "search results /\nlow-stock alerts",
         color=WARN, mx=25, my=17)

    ax.text(65, 108.5, "Level 1 DFD - Major Processes", ha="center", fontsize=13.5, fontweight="bold", color=DARK)
    fig.tight_layout()
    save(fig, "fig_dfd1.png")


# ---------------------------------------------------------------------------
# 5. fig_class_console.png
# ---------------------------------------------------------------------------

def uml_class(ax, cx, cy, w, h, name, fields, methods, fc=WHITE, header_fc=DARK, fontsize=8.0, italic_name=False):
    """Three-compartment UML class box. `h` is a MINIMUM height -- the box
    grows (centred on cy) to fit its field/method line count, so text never
    overlaps the compartment divider."""
    line_h, pad_top, pad_bottom, header_h = 1.95, 1.6, 1.0, 4.6
    fields_h = (pad_top + len(fields) * line_h + pad_bottom) if fields else 0
    methods_h = (pad_top + len(methods) * line_h + pad_bottom) if methods else 0
    body_min = fields_h + methods_h if (fields or methods) else 3.0
    H = max(h, header_h + body_min)
    x0, y0 = cx - w / 2, cy - H / 2

    ax.add_patch(plt.Rectangle((x0, y0), w, H, facecolor=fc, edgecolor=DARK, linewidth=1.3, zorder=2))
    ax.add_patch(plt.Rectangle((x0, y0 + H - header_h), w, header_h, facecolor=header_fc, edgecolor=DARK, linewidth=1.3, zorder=3))
    ax.text(cx, y0 + H - header_h / 2, name, ha="center", va="center", fontsize=fontsize + 1.2,
            fontweight="bold", color=WHITE, style=("italic" if italic_name else "normal"), zorder=4)

    y = y0 + H - header_h
    if fields:
        y -= pad_top
        ax.text(x0 + 2, y, "\n".join(fields), ha="left", va="top", fontsize=fontsize, color=DARK,
                 zorder=4, linespacing=1.5)
        y -= len(fields) * line_h + pad_bottom
    if fields and methods:
        ax.plot([x0, x0 + w], [y, y], color=DARK, lw=0.8, zorder=4)
    if methods:
        y -= pad_top
        ax.text(x0 + 2, y, "\n".join(methods), ha="left", va="top", fontsize=fontsize, color=TEAL,
                 zorder=4, linespacing=1.5)
    return (cx, cy, w, H)


def fig_class_console():
    fig, ax = new_canvas(16, 12.2, 169, 122)

    person = uml_class(ax, 80, 104, 40, 16, "Person  <<abstract>>",
                        ["- id : int", "- name : string", "- email : string"],
                        ["+ DisplayInfo() : void  {virtual}"], fc="#EEF2F7", fontsize=8.6)

    admin = uml_class(ax, 24, 80, 32, 15, "Admin",
                       ["+ AccessLevel : string"], ["+ DisplayInfo() : void  {override}"], fontsize=8.2)
    staff = uml_class(ax, 80, 80, 32, 15, "Staff",
                       ["+ Department : string"], ["+ DisplayInfo() : void  {override}"], fontsize=8.2)
    user = uml_class(ax, 136, 80, 32, 15, "User",
                      ["+ Role : string"], ["+ DisplayInfo() : void  {override}"], fontsize=8.2)

    for child_cx in (24, 80, 136):
        arrow(ax, (child_cx, 80 + 7.5), (80, 104 - 8), color=DARK, style="-|>", lw=1.4)

    cat = uml_class(ax, 12, 55, 26, 14, "Category",
                     ["- categoryId : int", "- categoryName : string"], [], fontsize=7.8)
    prod = uml_class(ax, 46, 55, 30, 16, "Product",
                      ["- productId : int", "- productName : string", "- price : decimal", "- quantity : int"],
                      ["+ ToString() : string"], fontsize=7.8)
    sup = uml_class(ax, 82, 55, 26, 14, "Supplier",
                     ["- supplierId : int", "- supplierName : string"], [], fontsize=7.8)
    stock = uml_class(ax, 112, 55, 28, 15, "Stock",
                       ["- quantityAvailable : int", "- reorderLevel : int"],
                       ["+ IsLowStock() : bool"], fontsize=7.8)
    stxn = uml_class(ax, 146, 55, 30, 16, "StockTransaction",
                      ["- quantity : int", "+ Type : TransactionType", "+ PerformedBy : string"], [], fontsize=7.6)

    arrow(ax, (25, 55 + 7), (37, 55 + 3), color=SLATE, style="-", lw=1.2)
    arrow(ax, (61, 55), (69, 55), color=SLATE, style="-", lw=1.2)
    arrow(ax, (97, 55 + 3), (105, 55 + 3), color=SLATE, style="-", lw=1.2)
    arrow(ax, (46, 55 - 8), (112, 55 - 7.5), color=SLATE, style="-", lw=1.2, connectionstyle="arc3,rad=-0.08")
    arrow(ax, (61, 47.5), (146, 47.5), color=SLATE, style="-", lw=1.2, connectionstyle="arc3,rad=-0.12")

    prodsvc = uml_class(ax, 12, 26, 30, 15, "ProductService",
                         [], ["+ AddProduct()", "+ SearchProduct()", "+ GetAllProducts()"], fontsize=7.6)
    stocksvc = uml_class(ax, 48, 26, 32, 17, "StockService",
                          [], ["+ StockIn()", "+ StockOut()", "+ GetLowStockItems()"], fontsize=7.6)
    mastersvc = uml_class(ax, 86, 26, 32, 16, "MasterDataService",
                           ["- categories : Dict<string,Category>", "- suppliers : Dict<string,Supplier>"], [], fontsize=7.2)
    usersvc = uml_class(ax, 118, 26, 30, 16, "UserService",
                         ["- users : Dict<string,Person>"], ["+ Login()", "+ CanModify : bool"], fontsize=7.4)
    reportsvc = uml_class(ax, 152, 26, 26, 14, "ReportService",
                           [], ["+ Generate...Report()"], fontsize=7.4)

    exc = uml_class(ax, 48, 9, 40, 11, "InsufficientStockException",
                     ["+ ProductName, Requested, Available"], [], fc="#FEF2F2", header_fc=DANGER, fontsize=7.4)

    arrow(ax, (12, 55 - 7), (12, 26 + 7.5), color=TEAL, style="-|>", lw=1.1, linestyle="dashed")
    arrow(ax, (46, 55 - 8), (48, 26 + 8.5), color=TEAL, style="-|>", lw=1.1, linestyle="dashed")
    arrow(ax, (112, 55 - 7.5), (48 + 14, 26 + 5), color=TEAL, style="-|>", lw=1.1, linestyle="dashed",
          connectionstyle="arc3,rad=0.15")
    arrow(ax, (146, 55 - 8), (48 + 15, 26 + 3), color=TEAL, style="-|>", lw=1.1, linestyle="dashed",
          connectionstyle="arc3,rad=0.25")
    arrow(ax, (82, 55 - 7), (86, 26 + 8), color=TEAL, style="-|>", lw=1.1, linestyle="dashed")
    arrow(ax, (12, 55 - 7), (86, 26 + 8), color=TEAL, style="-|>", lw=1.1, linestyle="dashed",
          connectionstyle="arc3,rad=-0.2")
    arrow(ax, (80, 80 - 7.5), (118, 26 + 8), color=TEAL, style="-|>", lw=1.1, linestyle="dashed",
          connectionstyle="arc3,rad=0.2")
    arrow(ax, (12, 26 - 7.5), (48, 26 + 8.5), color=SLATE, style="-|>", lw=1.0, linestyle="dashed",
          connectionstyle="arc3,rad=-0.3")
    arrow(ax, (152, 26 - 7), (48, 26 - 8.5), color=SLATE, style="-|>", lw=1.0, linestyle="dashed",
          connectionstyle="arc3,rad=0.15")
    arrow(ax, (48, 26 - 8.5), (48, 14.5), color=DANGER, style="-|>", lw=1.3)
    edge_label(ax, 55, 16, "throws", fontsize=7.5, color=DANGER)

    ax.text(80, 118, "Console Application - UML Class Diagram", ha="center", fontsize=13.5, fontweight="bold", color=DARK)
    ax.text(80, 1.2, "Solid = inheritance / association     Dashed teal = uses (dependency)     Dashed red = throws",
            ha="center", fontsize=8, color=SLATE)
    fig.tight_layout()
    save(fig, "fig_class_console.png")


# ---------------------------------------------------------------------------
# 6. fig_flow_stockout.png
# ---------------------------------------------------------------------------

def fig_flow_stockout():
    fig, ax = new_canvas(13.5, 7, 142, 60)

    y = 46
    start = plt.matplotlib.patches.Ellipse((10, y), 16, 10, facecolor=DARK, edgecolor=DARK, zorder=2)
    ax.add_patch(start)
    ax.text(10, y, "Start", ha="center", va="center", color=WHITE, fontsize=9.5, fontweight="bold", zorder=3)

    b1 = box(ax, 34, y, 24, 12, "Select product,\nenter quantity", fc=SLATE, fontsize=9)
    d1 = diamond(ax, 60, y, 20, 16, "Qty > 0?", fc=WARN, fontsize=9)
    d2 = diamond(ax, 86, y, 22, 16, "Qty <=\navailable?", fc=WARN, fontsize=8.6)
    b2 = box(ax, 112, y, 24, 14, "Update stock,\ninsert\nStockTransaction", fc=TEAL, fontsize=8.6)

    end = plt.matplotlib.patches.Ellipse((128, y), 14, 10, facecolor=OK, edgecolor=DARK, zorder=2)
    ax.add_patch(end)
    ax.text(128, y, "Success", ha="center", va="center", color=WHITE, fontsize=8.6, fontweight="bold", zorder=3)

    arrow(ax, (18, y), (22, y))
    arrow(ax, (46, y), (50, y))
    arrow(ax, (70, y), (75, y))
    arrow(ax, (97, y), (100, y))
    arrow(ax, (124, y), (121, y))

    err_y = 14
    e1 = box(ax, 60, err_y, 30, 12, "Reject:\n\"Quantity must be\ngreater than zero.\"", fc="#FEF2F2", tc=DANGER,
              ec=DANGER, fontsize=8.2)
    e2 = box(ax, 90, err_y, 34, 12, "Reject:\n\"Insufficient stock.\nAvailable: {n}\"", fc="#FEF2F2", tc=DANGER,
              ec=DANGER, fontsize=8.2)

    arrow(ax, (60, y - 8), (60, err_y + 6), color=DANGER)
    edge_label(ax, 54, 30, "No", fontsize=9, color=DANGER)
    arrow(ax, (86, y - 8), (88, err_y + 6), color=DANGER)
    edge_label(ax, 80, 30, "No", fontsize=9, color=DANGER)

    edge_label(ax, 60, y + 10, "Yes", fontsize=8.5, color=OK)
    edge_label(ax, 86, y + 10, "Yes", fontsize=8.5, color=OK)

    ax.text(65, 57, "Stock Out - Flowchart", ha="center", fontsize=13.5, fontweight="bold", color=DARK)
    ax.text(70, 3, "Enforced both by StockController.StockOut and by CK_Stocks_QuantityAvailable >= 0 in the database.",
            ha="center", fontsize=8.4, color=SLATE)
    fig.tight_layout()
    save(fig, "fig_flow_stockout.png")


# ---------------------------------------------------------------------------
# 7. fig_seq_login.png
# ---------------------------------------------------------------------------

def fig_seq_login():
    lifelines = ["Browser", "AccountController", "PasswordHasher", "DB", "Session", "Dashboard"]
    xs = [9, 27, 45, 63, 81, 99]
    top_y = 126
    bottom_y = 8

    fig, ax = new_canvas(14, 15, 112, 135)

    for x, name in zip(xs, lifelines):
        box(ax, x, top_y, 18, 6, name, fc=DARK, fontsize=8.6)
        ax.plot([x, x], [top_y - 3, bottom_y], color=SLATE, lw=1.1, linestyle=(0, (4, 3)), zorder=0)

    def msg(i1, i2, y, label, dashed=False, color=DARK, fontsize=7.6):
        x1, x2 = xs[i1], xs[i2]
        style = "dashed" if dashed else "solid"
        arrow(ax, (x1, y), (x2, y), color=color, lw=1.3, linestyle=style, mutation_scale=11)
        mid = (x1 + x2) / 2
        va = "bottom"
        ax.text(mid, y + 1.1, label, ha="center", va=va, fontsize=fontsize, color=DARK, zorder=4)

    y = 118
    step = 6.2
    ax.text(2, y, "1", fontsize=8, color=SLATE)
    msg(0, 1, y, "POST /Account/Login(username, password)")
    y -= step
    msg(1, 3, y, "Users.FirstOrDefault(username)")
    y -= step
    msg(3, 1, y, "user record", dashed=True)
    y -= step
    msg(1, 2, y, "VerifyHashedPassword(user, hash, password)")
    y -= step
    msg(2, 1, y, "Success / Failed", dashed=True)
    y -= step
    msg(1, 4, y, "SetInt32(UserId), SetString(Username, Role...)")
    y -= step
    msg(1, 0, y, "302 redirect -> /Dashboard", dashed=True)
    y -= step
    msg(0, 5, y, "GET /Dashboard")
    y -= step
    msg(5, 4, y, "GetInt32(UserId)  [SessionAuthFilter]")
    y -= step
    msg(4, 5, y, "userId (present)", dashed=True)
    y -= step
    msg(5, 0, y, "200 OK - dashboard view", dashed=True)

    div_y = y - 5
    ax.plot([2, 110], [div_y, div_y], color=SLATE, lw=1, linestyle="dotted")
    ax.text(54, div_y - 2.6, "Scenario B - request without a session (SessionAuthFilter)", ha="center",
            fontsize=9, fontweight="bold", color=DANGER)
    y = div_y - 8.5

    msg(0, 5, y, "GET /Dashboard  (no session cookie)")
    y -= step
    msg(5, 4, y, "GetInt32(UserId)  [SessionAuthFilter]", color=DANGER)
    y -= step
    msg(4, 5, y, "null", dashed=True, color=DANGER)
    y -= step
    msg(5, 0, y, "302 redirect -> /Account/Login?returnUrl=...", dashed=True, color=DANGER)

    ax.text(54, 131.5, "Login Sequence Diagram", ha="center", fontsize=13.5, fontweight="bold", color=DARK)
    fig.tight_layout()
    save(fig, "fig_seq_login.png")


# ---------------------------------------------------------------------------
# 8. fig_pwa_cache.png
# ---------------------------------------------------------------------------

def fig_pwa_cache():
    fig, ax = new_canvas(15, 11, 150, 108)

    box(ax, 75, 101, 50, 9, "Service Worker (sw.js) - fetch handler", fc=DARK, fontsize=11)

    cols = [
        dict(x=30, req="GET /api/*\n(JSON)", strat="Network-first", cache="Data Cache\n(ims-data)",
             fallback="offline -> serve cached\nJSON (X-IMS-Cache: hit)"),
        dict(x=75, req="Page navigation\n(mode: navigate)", strat="Network-first", cache="Pages Cache\n(ims-pages)",
             fallback="offline -> cached page,\nelse offline.html"),
        dict(x=120, req="Static asset\n(css / js / icons)", strat="Stale-while-\nrevalidate", cache="Static Cache\n(ims-static)",
             fallback="serve cache at once,\nrefresh in background"),
    ]
    for c in cols:
        x = c["x"]
        arrow(ax, (x, 96.5), (x, 90.5))
        box(ax, x, 84, 32, 10, c["req"], fc=SLATE, fontsize=8.8)
        arrow(ax, (x, 79), (x, 72.5))
        box(ax, x, 66, 30, 9, c["strat"], fc=TEAL, fontsize=9)
        arrow(ax, (x, 61.5), (x, 55))
        box(ax, x, 48, 30, 9, c["cache"], fc=WHITE, ec=DARK, tc=DARK, fontsize=8.6)
        arrow(ax, (x, 43.5), (x, 37.5), color=WARN, linestyle="dashed")
        box(ax, x, 28, 34, 15, c["fallback"], fc="#FFFBEB", ec=WARN, tc=DARK, fontsize=7.8)

    div_y = 16
    ax.plot([2, 148], [div_y, div_y], color=SLATE, lw=1, linestyle="dotted")
    ax.text(75, div_y - 3.2, "Low-stock notification path", ha="center", fontsize=10.5, fontweight="bold", color=DARK)

    steps = ["periodicsync\n'ims-low-stock'", "fetch\n/api/stock/low", "count > 0 ?", "showNotification\n(icon, body)",
             "notificationclick ->\nfocus / open\n/Pwa/LowStock"]
    n = len(steps)
    xs = [14 + i * (118 / (n - 1)) for i in range(n)]
    y0 = 6
    for i, (x, label) in enumerate(zip(xs, steps)):
        fc = WARN if i == 2 else TEAL
        w = 22 if i != 2 else 20
        if i == 2:
            diamond(ax, x, y0, 22, 11, label, fc=WARN, fontsize=7.6)
        else:
            box(ax, x, y0, w, 9, label, fc=fc, fontsize=7.2)
        if i > 0:
            arrow(ax, (xs[i - 1] + (9 if i - 1 != 2 else 11), y0), (x - (11 if i != 2 else 11), y0))

    ax.text(75, 106.5, "PWA Caching Strategies (sw.js)", ha="center", fontsize=13.5, fontweight="bold", color=DARK)
    fig.tight_layout()
    save(fig, "fig_pwa_cache.png")


# ---------------------------------------------------------------------------
# 9. fig_gantt.png
# ---------------------------------------------------------------------------

def fig_gantt():
    phases = [
        ("Requirements", 1, 2),
        ("Console app", 2, 4),
        ("DB design", 3, 4),
        ("Web app", 4, 8),
        ("PWA", 7, 9),
        ("Testing", 8, 10),
        ("Documentation", 9, 10),
    ]
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    colors = PALETTE[:len(phases)]
    for i, (name, start, end) in enumerate(phases):
        y = len(phases) - i
        ax.barh(y, end - start, left=start, height=0.55, color=colors[i % len(colors)],
                edgecolor=DARK, linewidth=0.8, zorder=3)
        ax.text(start - 0.15, y, name, ha="right", va="center", fontsize=9.5, color=DARK)
        ax.text((start + end) / 2, y, f"W{start}-W{end}", ha="center", va="center", fontsize=8, color=WHITE,
                fontweight="bold", zorder=4)

    ax.set_xlim(0.5, 10.5)
    ax.set_ylim(0.3, len(phases) + 0.9)
    ax.set_xticks(range(1, 11))
    ax.set_xticklabels([f"W{w}" for w in range(1, 11)], fontsize=9)
    ax.set_yticks([])
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(SLATE)
    ax.grid(axis="x", color="#E2E8F0", linewidth=0.8, zorder=0)
    ax.set_title("Planned Timeline", fontsize=13.5, fontweight="bold", color=DARK, pad=14)
    fig.tight_layout()
    save(fig, "fig_gantt.png", pad=0.35)


# ---------------------------------------------------------------------------
# charts from seed_stats
# ---------------------------------------------------------------------------

def _wrap_labels(labels, width=14):
    return ["\n".join(textwrap.wrap(l, width)) for l in labels]


def chart_units_by_category():
    data = seed_stats.units_by_category()
    names = [d[0] for d in data]
    values = [d[1] for d in data]

    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.bar(_wrap_labels(names, 12), values, color=PALETTE[:len(names)], edgecolor=DARK, linewidth=0.8, zorder=3)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + max(values) * 0.015, str(v), ha="center", fontsize=9,
                color=DARK, fontweight="bold")
    ax.set_ylabel("Units in stock", fontsize=10, color=DARK)
    ax.set_title("Stock Units by Category", fontsize=13, fontweight="bold", color=DARK, pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SLATE)
    ax.spines["bottom"].set_color(SLATE)
    ax.tick_params(axis="x", labelsize=8.6, colors=DARK)
    ax.tick_params(axis="y", labelsize=9, colors=SLATE)
    ax.set_ylim(0, max(values) * 1.18)
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.8, zorder=0)
    fig.tight_layout()
    save(fig, "chart_units_by_category.png", pad=0.25)


def chart_value_by_category():
    data = seed_stats.value_by_category()
    names = [d[0] for d in data]
    values = [d[1] for d in data]
    total = sum(values)

    fig, ax = plt.subplots(figsize=(8.5, 6.4))
    wedges, _ = ax.pie(values, colors=PALETTE[:len(names)], startangle=90,
                        wedgeprops=dict(width=0.42, edgecolor=WHITE, linewidth=2))
    for w, name, v in zip(wedges, names, values):
        ang = (w.theta2 + w.theta1) / 2
        import math
        rx, ry = 1.22 * math.cos(math.radians(ang)), 1.22 * math.sin(math.radians(ang))
        ha = "left" if rx >= 0 else "right"
        ax.annotate(f"{name}\nRs. {v:,.0f}  ({v / total:.0%})", xy=(0.78 * math.cos(math.radians(ang)),
                    0.78 * math.sin(math.radians(ang))), xytext=(rx, ry),
                    ha=ha, va="center", fontsize=8.4, color=DARK,
                    arrowprops=dict(arrowstyle="-", color=SLATE, lw=0.8))
    ax.text(0, 0, f"Rs. {total:,.0f}\ntotal", ha="center", va="center", fontsize=11.5, fontweight="bold", color=DARK)
    ax.set_title("Inventory Value by Category", fontsize=13, fontweight="bold", color=DARK, pad=16)
    ax.set_aspect("equal")
    fig.tight_layout()
    save(fig, "chart_value_by_category.png", pad=0.35)


def chart_stock_status():
    counts = seed_stats.status_counts()
    order = ["OK", "Low", "Out"]
    values = [counts[k] for k in order]
    colors = [OK, WARN, DANGER]

    fig, ax = plt.subplots(figsize=(6.8, 5))
    bars = ax.bar(order, values, color=colors, edgecolor=DARK, linewidth=0.8, width=0.55, zorder=3)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.4, str(v), ha="center", fontsize=13, fontweight="bold", color=DARK)
    ax.set_ylabel("Number of products", fontsize=10, color=DARK)
    ax.set_title("Stock Status of 30 Products", fontsize=13, fontweight="bold", color=DARK, pad=12)
    ax.set_ylim(0, max(values) * 1.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SLATE)
    ax.spines["bottom"].set_color(SLATE)
    ax.tick_params(labelsize=11, colors=DARK)
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.8, zorder=0)
    fig.tight_layout()
    save(fig, "chart_stock_status.png", pad=0.25)


def chart_in_out_30d():
    rows = seed_stats.daily_in_out(days=30)  # oldest -> newest
    days_ago = [r[0] for r in rows]
    stock_in = [r[1] for r in rows]
    stock_out = [r[2] for r in rows]
    x = list(range(len(rows)))

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(x, stock_in, color=TEAL, marker="o", markersize=3.5, linewidth=1.8, label="Stock In")
    ax.plot(x, stock_out, color=DANGER, marker="o", markersize=3.5, linewidth=1.8, label="Stock Out")
    ax.fill_between(x, stock_in, color=TEAL, alpha=0.08)
    ax.fill_between(x, stock_out, color=DANGER, alpha=0.08)

    tick_idx = list(range(0, len(rows), 3))
    ax.set_xticks(tick_idx)
    ax.set_xticklabels([f"-{days_ago[i]}d" if days_ago[i] else "today" for i in tick_idx], fontsize=8, rotation=0)
    ax.set_ylabel("Units moved", fontsize=10, color=DARK)
    ax.set_title("Daily Stock In vs Stock Out (last 30 days)", fontsize=13, fontweight="bold", color=DARK, pad=12)
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SLATE)
    ax.spines["bottom"].set_color(SLATE)
    ax.tick_params(colors=SLATE)
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.8, zorder=0)
    fig.tight_layout()
    save(fig, "chart_in_out_30d.png", pad=0.25)


def chart_top10_value():
    rows = seed_stats.top_products_by_value(10)
    rows = list(reversed(rows))  # largest at top when using barh
    names = [r["name"] for r in rows]
    values = [r["value"] for r in rows]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(_wrap_labels(names, 26), values, color=TEAL, edgecolor=DARK, linewidth=0.7, zorder=3)
    for b, v in zip(bars, values):
        ax.text(v + max(values) * 0.01, b.get_y() + b.get_height() / 2, f"Rs. {v:,.0f}", va="center",
                fontsize=8.6, color=DARK)
    ax.set_xlabel("Stock value (Rs.)", fontsize=10, color=DARK)
    ax.set_title("Top 10 Products by Stock Value", fontsize=13, fontweight="bold", color=DARK, pad=12)
    ax.set_xlim(0, max(values) * 1.22)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SLATE)
    ax.spines["bottom"].set_color(SLATE)
    ax.tick_params(axis="y", labelsize=8.6, colors=DARK)
    ax.tick_params(axis="x", labelsize=9, colors=SLATE)
    ax.grid(axis="x", color="#E2E8F0", linewidth=0.8, zorder=0)
    fig.tight_layout()
    save(fig, "chart_top10_value.png", pad=0.25)


def chart_test_summary():
    rows, _ = common.load_test_results()
    counts = {"Pass": 0, "Manual": 0, "Fail": 0}
    for r in rows:
        s = r["status"]
        if s in counts:
            counts[s] += 1
        elif s.lower() == "pending":
            counts["Manual"] += 1
    order = ["Pass", "Manual", "Fail"]
    values = [counts[k] for k in order]
    colors = [OK, WARN, DANGER]

    fig, ax = plt.subplots(figsize=(6.8, 5))
    bars = ax.bar(order, values, color=colors, edgecolor=DARK, linewidth=0.8, width=0.55, zorder=3)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.35, str(v), ha="center", fontsize=13, fontweight="bold", color=DARK)
    ax.set_ylabel("Number of test cases", fontsize=10, color=DARK)
    ax.set_title(f"Test Results ({sum(values)} cases)", fontsize=13, fontweight="bold", color=DARK, pad=12)
    ax.set_ylim(0, max(values) * 1.25 if max(values) else 1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SLATE)
    ax.spines["bottom"].set_color(SLATE)
    ax.tick_params(labelsize=11, colors=DARK)
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.8, zorder=0)
    fig.tight_layout()
    save(fig, "chart_test_summary.png", pad=0.25)


# ---------------------------------------------------------------------------
# generate_all
# ---------------------------------------------------------------------------

def generate_all():
    fig_architecture()
    fig_usecase()
    fig_dfd0()
    fig_dfd1()
    fig_class_console()
    fig_flow_stockout()
    fig_seq_login()
    fig_pwa_cache()
    chart_units_by_category()
    chart_value_by_category()
    chart_stock_status()
    chart_in_out_30d()
    chart_top10_value()
    chart_test_summary()
    fig_gantt()


if __name__ == "__main__":
    generate_all()
