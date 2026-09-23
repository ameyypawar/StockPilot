# Software Requirements Specification

## StockPilot — Inventory Management System

### 1. Introduction

#### 1.1 Purpose

This document specifies the functional and non-functional requirements for
**StockPilot**, an Inventory Management System built as a college project.
It covers three deliverables built on a shared data model: a **console
application** (core OOP concepts), an **ASP.NET Core MVC web application**
(full CRUD, reporting, authentication) and a **Progressive Web App (PWA)**
layer over the web app (offline browsing, installability, low-stock
notifications).

#### 1.2 Scope

The system lets a small shop or warehouse track product categories,
suppliers, products, stock levels and stock movements (Stock In / Stock
Out), and produce operational reports (catalog, stock summary, low stock,
transaction history, inventory value). It is a single-tenant, single-store
system — there is no multi-warehouse or multi-branch support.

#### 1.3 Intended users

| Role | Description |
|---|---|
| **Admin** | Full access: manage categories, suppliers, products, stock, and view all reports. Seeded demo account: `admin` / `Admin@123`. |
| **Staff** | Day-to-day operator: records Stock In/Out, views reports (console app distinguishes Admin/Staff/Viewer via OOP polymorphism; the web app currently ships a single Admin-role account, with `Role` on `Users` ready for future role-based restrictions). |
| **Viewer** (console app only) | Read-only: can view products, stock and reports, but any add/update/delete is blocked with "Access denied: viewers cannot modify data." |

### 2. Overall description

The web app is the primary deliverable: an ASP.NET Core MVC application
backed by SQL Server via EF Core, with session-cookie authentication, server
rendered Razor views, Bootstrap 5 styling, and a PWA layer (manifest,
service worker, offline pages, JSON API, push-style notifications). The
console application is a parallel, in-memory implementation of the same
domain concepts (products, categories, suppliers, stock, users) built to
demonstrate classes, inheritance, polymorphism, encapsulation, exception
handling and collections (`List<T>`, `Dictionary<TKey,TValue>`) without a
database.

### 3. Functional requirements

| ID | Requirement | Module |
|---|---|---|
| FR-01 | User can log in with username/password; a wrong password is rejected | AccountController, session auth |
| FR-02 | User can change their password (current password verified, new password confirmed) | AccountController |
| FR-03 | User can log out, clearing their session | AccountController |
| FR-04 | Every page except Login requires an active session; an anonymous request is redirected to Login (API requests get 401 JSON) | SessionAuthFilter |
| FR-05 | Admin can create, edit, delete and search Categories | CategoryController |
| FR-06 | Deleting a Category in use by a Product is blocked with an explanatory message | CategoryController |
| FR-07 | Admin can create, edit, delete and search Suppliers | SupplierController |
| FR-08 | Deleting a Supplier in use by a Product is blocked with an explanatory message | SupplierController |
| FR-09 | Admin can create, edit, delete and search/filter Products (by name, category, supplier) | ProductController |
| FR-10 | Creating a Product can set an opening stock quantity and reorder level in one step | ProductController |
| FR-11 | Admin can initialize stock for a product that has none yet | StockController |
| FR-12 | Admin can record a Stock In transaction (quantity, performed-by, remarks) | StockController |
| FR-13 | Admin can record a Stock Out transaction; a request exceeding the available quantity is rejected with an "Insufficient stock" message and the stock is left unchanged | StockController, `CK_Stocks_QuantityAvailable` |
| FR-14 | A non-positive Stock In/Out quantity is rejected | StockController |
| FR-15 | Transaction history can be filtered by type and date range | ReportController / StockController |
| FR-16 | Dashboard shows total products, suppliers, categories, units in stock, low/out-of-stock counts, total inventory value, today's In/Out counts, top low-stock items, category summary and recent transactions | DashboardController |
| FR-17 | Reports (Product Catalog, Stock Summary, Low Stock, Transaction History, Inventory Value) support filtering and a print-friendly layout | ReportController, `@media print` |
| FR-18 | The console app supports the same product/stock/report operations menu-driven, with a Viewer role blocked from modifying data | ConsoleApplication/Program.cs |
| FR-19 | The web app is installable as a PWA, browses product search / stock overview / low-stock alerts offline from previously cached data, and can show a low-stock notification | manifest.json, sw.js, PwaController, InventoryApiController |
| FR-20 | Demo data (6 categories, 6 suppliers, 30 products with stock and 40 transactions) is seeded automatically on first run | DbInitializer, SeedData.sql |

### 4. Non-functional requirements

- **Usability** — plain Bootstrap 5 UI, mobile-responsive down to phone
  width, clear success/error banners (`TempData`), print-optimized report
  layouts.
- **Security** — passwords are never stored in plain text (ASP.NET Core
  Identity's `PasswordHasher`, PBKDF2-SHA512); all state-changing requests
  require anti-forgery tokens; every page but Login requires an active
  session.
- **Availability (offline)** — the PWA's service worker lets Search, Stock
  Overview and Low Stock Alerts keep working with the last-synced data when
  the device has no connection.
- **Responsiveness** — the layout adapts from a desktop sidebar to a mobile
  hamburger/offcanvas navigation and a 2-column KPI grid under 768px width.
- **Data integrity** — check constraints (`CK_Products_Price >= 0`,
  `CK_Stocks_QuantityAvailable >= 0`, `CK_Stocks_ReorderLevel >= 0`,
  `CK_StockTransactions_Quantity > 0`, `CK_StockTransactions_Type IN
  (…)`) back up the application-level validation at the database layer.
- **Maintainability** — a 6-table, 3NF-normalized schema (see
  `Database/ERDiagram/README.md`) keeps category/supplier reference data,
  product identity, stock levels and transaction history each in a single
  place.

### 5. Constraints

- Single SQL Server database instance; no distributed/multi-node design.
- Sessions are in-memory (not distributed), so horizontal scaling and app
  restarts both invalidate active sessions — acceptable for a demo/college
  deployment, not for production scale.
- Background PWA notifications (`periodicsync`) are best-effort and
  Chromium-only; iOS requires the app to be installed via HTTPS.
- .NET 8 is a Long-Term Support release; see the Final Report's Future
  Scope chapter for the framework support-window note.

### 6. Environment

| Layer | Technology |
|---|---|
| Runtime | .NET 8 LTS |
| Web framework | ASP.NET Core MVC |
| ORM | Entity Framework Core 8 |
| Database | Microsoft SQL Server (LocalDB for Windows/Visual Studio; SQL Server container on Mac) |
| Front end | Razor views, Bootstrap 5.3, vanilla JS |
| PWA | Web App Manifest, Service Worker (Cache API), Notifications API |
| Console app | .NET 8 console project sharing the same domain concepts |
| Dev tooling | Visual Studio 2022 (Windows), `dotnet` CLI (Mac) |
