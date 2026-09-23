"""
Shared configuration and helpers for the generated documentation deliverables
(PPT, Final Report, User Manual): paths, brand colours, doc_config wiring and
the real (or fallback) test results.

Owned by the Final-Report agent, but imported by tools/ppt_builder.py too --
keep this importable with no side effects, and keep the public names stable.
"""
from __future__ import annotations

import json
from pathlib import Path

from docx.shared import RGBColor as DocxColor

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO  # backward-compatible alias used by tools/build_docs.py
ASSETS = REPO / "Documentation" / "assets"
SCREENS = ASSETS / "screens"

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

# Aliases matching the naming used in the task brief.
SLATE = DARK_HEX   # slate #1E293B (kept distinct from body-text SLATE_HEX below)
TEAL = TEAL_HEX


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i: i + 2], 16) for i in (0, 2, 4))


DARK_RGB = hx(DARK_HEX)
TEAL_RGB = hx(TEAL_HEX)
LIGHT_RGB = hx(LIGHT_HEX)
SLATE_RGB = hx(SLATE_HEX)
WHITE_RGB = hx(WHITE_HEX)
DANGER_RGB = hx(DANGER_HEX)
WARN_RGB = hx(WARN_HEX)
OK_RGB = hx(OK_HEX)

# Light palette (for chart fills / category series) -- teal/slate family.
LIGHT_PALETTE_HEX = ["0D9488", "1E293B", "38BDF8", "F59E0B", "8B5CF6", "EC4899", "84CC16", "F43F5E"]
LIGHT_PALETTE_RGB = [hx(c) for c in LIGHT_PALETTE_HEX]

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
    path = REPO / "tools" / "test_results.json"
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


def status_color(status):
    s = (status or "").strip().lower()
    if s == "pass":
        return hx(OK_HEX)
    if s == "fail":
        return hx(DANGER_HEX)
    return hx(WARN_HEX)
