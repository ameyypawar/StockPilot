#!/usr/bin/env python3
"""
Captures real screenshots of the running StockPilot web app for use in the
PPT deck (tools/ppt_builder.py). Uses Playwright's sync API against the
locally installed Google Chrome (channel="chrome") so no browser download
is needed.

Prereqs (see tools/capture_screens.py docstring in the task): the ims-sql
SQL Server container must already be running and seeded, and the ASP.NET
Core app must already be running at BASE_URL (started separately with the
MacDocker launch profile).

Run with:
    <docenv python> tools/capture_screens.py
from the repository root.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Documentation" / "assets" / "screens"
OUT.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://localhost:5080"
USERNAME = "admin"
PASSWORD = "Admin@123"

DESKTOP_VIEWPORT = {"width": 1440, "height": 900}
MOBILE_VIEWPORT = {"width": 390, "height": 844}


def shot(page, name: str):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    print(f"  saved {path.relative_to(ROOT)}")


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")

        # ---------------------------------------------------------------
        # Desktop screens
        # ---------------------------------------------------------------
        ctx = browser.new_context(viewport=DESKTOP_VIEWPORT, device_scale_factor=2)
        page = ctx.new_page()

        print("desktop: login page")
        page.goto(f"{BASE_URL}/Account/Login", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "login")

        print("desktop: logging in")
        page.fill("input[name=username]", USERNAME)
        page.fill("input[name=password]", PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(300)

        print("desktop: dashboard")
        page.goto(f"{BASE_URL}/Dashboard", wait_until="networkidle")
        page.wait_for_timeout(400)
        shot(page, "dashboard")

        print("desktop: categories")
        page.goto(f"{BASE_URL}/Category", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "categories")

        print("desktop: products")
        page.goto(f"{BASE_URL}/Product", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "products")

        print("desktop: product create")
        page.goto(f"{BASE_URL}/Product/Create", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "product_create")

        print("desktop: suppliers")
        page.goto(f"{BASE_URL}/Supplier", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "suppliers")

        print("desktop: stock")
        page.goto(f"{BASE_URL}/Stock", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "stock")

        print("desktop: stock in")
        page.goto(f"{BASE_URL}/Stock/StockIn?productId=1", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "stockin")

        print("desktop: stock out -> insufficient stock error (no data change)")
        page.goto(f"{BASE_URL}/Stock/StockOut?productId=1", wait_until="networkidle")
        page.wait_for_timeout(300)
        try:
            qty_input = page.locator("input[name=quantity]")
            qty_input.fill("99999")
            page.click("button[type=submit]")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(300)
        except PWTimeoutError:
            pass
        shot(page, "stockout_error")

        print("desktop: reports index")
        page.goto(f"{BASE_URL}/Report", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "reports_index")

        print("desktop: report inventory value")
        page.goto(f"{BASE_URL}/Report/InventoryValue", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "report_inventory_value")

        print("desktop: report low stock")
        page.goto(f"{BASE_URL}/Report/LowStock", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "report_low_stock")

        print("desktop: change password")
        page.goto(f"{BASE_URL}/Account/ChangePassword", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, "change_password")

        ctx.close()

        # ---------------------------------------------------------------
        # Mobile / PWA screens (fresh context, re-login as mobile session)
        # ---------------------------------------------------------------
        mctx = browser.new_context(
            viewport=MOBILE_VIEWPORT,
            is_mobile=True,
            has_touch=True,
            device_scale_factor=3,
        )
        mpage = mctx.new_page()

        print("mobile: logging in")
        mpage.goto(f"{BASE_URL}/Account/Login", wait_until="networkidle")
        mpage.wait_for_timeout(300)
        mpage.fill("input[name=username]", USERNAME)
        mpage.fill("input[name=password]", PASSWORD)
        mpage.click("button[type=submit]")
        mpage.wait_for_load_state("networkidle")
        mpage.wait_for_timeout(300)

        print("mobile: pwa home")
        mpage.goto(f"{BASE_URL}/Pwa", wait_until="networkidle")
        mpage.wait_for_timeout(400)
        shot(mpage, "pwa_home")

        print("mobile: pwa search")
        mpage.goto(f"{BASE_URL}/Pwa/Search", wait_until="networkidle")
        mpage.wait_for_timeout(300)
        try:
            search_box = mpage.locator("#q")
            search_box.fill("rice")
            mpage.wait_for_timeout(500)
        except PWTimeoutError:
            pass
        shot(mpage, "pwa_search")

        print("mobile: pwa stock")
        mpage.goto(f"{BASE_URL}/Pwa/Stock", wait_until="networkidle")
        mpage.wait_for_timeout(300)
        shot(mpage, "pwa_stock")

        print("mobile: pwa low stock")
        mpage.goto(f"{BASE_URL}/Pwa/LowStock", wait_until="networkidle")
        mpage.wait_for_timeout(300)
        shot(mpage, "pwa_lowstock")

        print("mobile: dashboard")
        mpage.goto(f"{BASE_URL}/Dashboard", wait_until="networkidle")
        mpage.wait_for_timeout(300)
        shot(mpage, "mobile_dashboard")

        mctx.close()
        browser.close()

    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
