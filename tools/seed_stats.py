"""
Parses Database/SQLScripts/SeedData.sql (read-only) into plain Python data
structures, so the documentation generators (report_builder.py, and the PPT
agent's ppt_builder.py) can build real charts from the actual demo data
instead of inventing numbers.

Public API:
    load_seed() -> dict with "categories", "suppliers", "products", "transactions"
    units_by_category()
    value_by_category()
    status_counts()
    daily_in_out(days=30)
    top_products_by_value(n=10)

Status rule: qty == 0 -> "Out"; qty <= reorder -> "Low"; else "OK".
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SEED_SQL = REPO / "Database" / "SQLScripts" / "SeedData.sql"

_INSERT_RE = re.compile(
    r"INSERT INTO dbo\.(\w+)\s*\(([^)]*)\)\s*VALUES\s*(.*?);",
    re.IGNORECASE | re.DOTALL,
)


def _split_top_level(text, sep=","):
    """Split text on `sep` at paren-depth 0, respecting N'...'/'...' string
    literals (with '' as an escaped quote inside them)."""
    parts = []
    depth = 0
    in_str = False
    buf = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if in_str:
            if ch == "'":
                if i + 1 < n and text[i + 1] == "'":
                    buf.append("''")
                    i += 2
                    continue
                in_str = False
                buf.append(ch)
            else:
                buf.append(ch)
        else:
            if ch == "'":
                in_str = True
                buf.append(ch)
            elif ch == "(":
                depth += 1
                buf.append(ch)
            elif ch == ")":
                depth -= 1
                buf.append(ch)
            elif ch == sep and depth == 0:
                parts.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
        i += 1
    if buf:
        parts.append("".join(buf))
    return [p.strip() for p in parts]


def _split_rows(values_text):
    """Split a `(...), (...), (...)` VALUES clause into a list of raw row
    strings (without the outer parens), at paren-depth 0."""
    rows = []
    depth = 0
    in_str = False
    buf = []
    started = False
    for ch in values_text:
        if in_str:
            buf.append(ch)
            if ch == "'":
                in_str = False
            continue
        if ch == "'":
            in_str = True
            buf.append(ch)
            continue
        if ch == "(":
            depth += 1
            if depth == 1:
                started = True
                buf = []
                continue
        if ch == ")":
            depth -= 1
            if depth == 0 and started:
                rows.append("".join(buf))
                started = False
                continue
        if started:
            buf.append(ch)
    return rows


_DATEADD_RE = re.compile(r"DATEADD\s*\(\s*DAY\s*,\s*(-?\d+)\s*,\s*SYSDATETIME\s*\(\s*\)\s*\)", re.IGNORECASE)


def _parse_field(raw):
    """Parse a single SQL literal field into a Python value."""
    s = raw.strip()
    if not s:
        return None
    # N'...'/'...' string literal
    if s[0] in "Nn" and len(s) > 1 and s[1] == "'":
        s = s[1:]
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1].replace("''", "'")
    m = _DATEADD_RE.match(s)
    if m:
        return -int(m.group(1))  # DATEADD(DAY, -2, ...) -> 2 days ago
    try:
        if re.fullmatch(r"-?\d+", s):
            return int(s)
        return float(s)
    except ValueError:
        return s


def _parse_insert_blocks(sql_text):
    blocks = {}
    for m in _INSERT_RE.finditer(sql_text):
        table = m.group(1)
        cols = [c.strip() for c in m.group(2).split(",")]
        rows_raw = _split_rows(m.group(3))
        rows = []
        for row_raw in rows_raw:
            fields = _split_top_level(row_raw)
            values = [_parse_field(f) for f in fields]
            rows.append(dict(zip(cols, values)))
        blocks.setdefault(table, []).extend(rows)
    return blocks


def _status_for(qty, reorder):
    if qty == 0:
        return "Out"
    if qty <= reorder:
        return "Low"
    return "OK"


_cache = None


def load_seed(force=False):
    """Parses SeedData.sql and returns a dict:
        categories: [{id, name, description}]
        suppliers:  [{id, name, contact, email, address}]
        products:   [{id, name, category, supplier, unit, price, qty, reorder, status}]
        transactions: [{id, product_id, type, qty, days_ago, performed_by, remarks}]
    """
    global _cache
    if _cache is not None and not force:
        return _cache

    sql_text = SEED_SQL.read_text(encoding="utf-8")
    blocks = _parse_insert_blocks(sql_text)

    categories = [
        dict(id=r["CategoryId"], name=r["CategoryName"], description=r.get("Description"))
        for r in blocks.get("Categories", [])
    ]
    cat_by_id = {c["id"]: c["name"] for c in categories}

    suppliers = [
        dict(
            id=r["SupplierId"], name=r["SupplierName"], contact=r.get("ContactNumber"),
            email=r.get("Email"), address=r.get("Address"),
        )
        for r in blocks.get("Suppliers", [])
    ]
    sup_by_id = {s["id"]: s["name"] for s in suppliers}

    stock_by_product = {
        r["ProductId"]: dict(qty=r["QuantityAvailable"], reorder=r["ReorderLevel"])
        for r in blocks.get("Stocks", [])
    }

    products = []
    for r in blocks.get("Products", []):
        pid = r["ProductId"]
        stock = stock_by_product.get(pid, dict(qty=0, reorder=0))
        qty = stock["qty"]
        reorder = stock["reorder"]
        products.append(
            dict(
                id=pid,
                name=r["ProductName"],
                category=cat_by_id.get(r.get("CategoryId"), "Uncategorised"),
                supplier=sup_by_id.get(r.get("SupplierId"), "Unknown"),
                unit=r.get("Unit"),
                price=float(r["Price"]),
                qty=qty,
                reorder=reorder,
                status=_status_for(qty, reorder),
            )
        )
    products.sort(key=lambda p: p["id"])

    transactions = []
    for r in blocks.get("StockTransactions", []):
        transactions.append(
            dict(
                id=r["TransactionId"],
                product_id=r["ProductId"],
                type=r["Type"],
                qty=r["Quantity"],
                days_ago=r["TransactionDate"],
                performed_by=r.get("PerformedBy"),
                remarks=r.get("Remarks"),
            )
        )
    transactions.sort(key=lambda t: t["id"])

    data = dict(categories=categories, suppliers=suppliers, products=products, transactions=transactions)
    _sanity_check(data)
    _cache = data
    return data


def _sanity_check(data):
    n_products = len(data["products"])
    n_low = sum(1 for p in data["products"] if p["status"] == "Low")
    n_out = sum(1 for p in data["products"] if p["status"] == "Out")
    problems = []
    if n_products != 30:
        problems.append(f"expected 30 products, got {n_products}")
    if n_low + n_out != 8:
        problems.append(f"expected 8 Low+Out products, got {n_low + n_out}")
    if n_out != 2:
        problems.append(f"expected 2 Out products, got {n_out}")
    if problems:
        print("seed_stats: WARNING - " + "; ".join(problems), file=sys.stderr)


def units_by_category():
    """[(category_name, total_units_available)], in category-id order."""
    data = load_seed()
    totals = {c["name"]: 0 for c in data["categories"]}
    order = [c["name"] for c in data["categories"]]
    for p in data["products"]:
        totals[p["category"]] = totals.get(p["category"], 0) + p["qty"]
    return [(name, totals.get(name, 0)) for name in order]


def value_by_category():
    """[(category_name, total_stock_value)], in category-id order."""
    data = load_seed()
    totals = {c["name"]: 0.0 for c in data["categories"]}
    order = [c["name"] for c in data["categories"]]
    for p in data["products"]:
        totals[p["category"]] = totals.get(p["category"], 0.0) + p["qty"] * p["price"]
    return [(name, totals.get(name, 0.0)) for name in order]


def status_counts():
    """{"OK": n, "Low": n, "Out": n}"""
    data = load_seed()
    counts = {"OK": 0, "Low": 0, "Out": 0}
    for p in data["products"]:
        counts[p["status"]] += 1
    return counts


def daily_in_out(days=30):
    """[(days_ago, stock_in_qty, stock_out_qty)] for days_ago in
    range(days - 1, -1, -1) -- oldest to newest, today last."""
    data = load_seed()
    in_by_day = {d: 0 for d in range(days)}
    out_by_day = {d: 0 for d in range(days)}
    for t in data["transactions"]:
        d = t["days_ago"]
        if 0 <= d < days:
            if t["type"] == "StockIn":
                in_by_day[d] += t["qty"]
            elif t["type"] == "StockOut":
                out_by_day[d] += t["qty"]
    return [(d, in_by_day[d], out_by_day[d]) for d in range(days - 1, -1, -1)]


def top_products_by_value(n=10):
    """[{id, name, category, qty, price, value}], highest stock value first."""
    data = load_seed()
    rows = []
    for p in data["products"]:
        rows.append(dict(p, value=p["qty"] * p["price"]))
    rows.sort(key=lambda r: r["value"], reverse=True)
    return rows[:n]


if __name__ == "__main__":
    d = load_seed()
    print(f"categories={len(d['categories'])} suppliers={len(d['suppliers'])} "
          f"products={len(d['products'])} transactions={len(d['transactions'])}")
    print("status_counts:", status_counts())
    print("units_by_category:", units_by_category())
    print("top3 by value:", [(r["name"], round(r["value"], 2)) for r in top_products_by_value(3)])
