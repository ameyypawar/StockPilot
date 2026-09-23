# StockPilot — Inventory Management System

A college group project built in three phases on one shared data model:

1. **Console application** (`ConsoleApplication/`) — menu-driven, in-memory, demonstrates core OOP (classes, inheritance, polymorphism, encapsulation), exception handling, `List<T>`/`Dictionary<K,V>`.
2. **ASP.NET Core MVC web application** (`ASPNETApplication/`) — full CRUD over SQL Server via EF Core, session-based login, reports, printing.
3. **Progressive Web App layer** (same web app) — installable, works offline for product search / stock overview / low-stock alerts, and can show low-stock notifications.

Base project by Milan Gite ([MilanGite06/InventoryManagementSystem](https://github.com/MilanGite06/InventoryManagementSystem)), retargeted to .NET 8 LTS and substantially extended (auth, schema, reports, responsive UI, PWA, console app, SQL scripts, documentation).

## Folder structure

```
ConsoleApplication/     Console app (net8.0)
ASPNETApplication/       MVC web app (net8.0, EF Core 8, SQL Server)
Database/SQLScripts/     CreateTables.sql, SeedData.sql, ResetDatabase.sql
Database/ERDiagram/      ER diagram (Mermaid + generated PNG)
PWA/                     PWA notes
Documentation/           SRS, presentation, final report, user manual
tools/                   Icon generator, doc generator (Python)
```

## Tech stack

.NET 8 LTS · ASP.NET Core MVC · Entity Framework Core 8 · SQL Server (LocalDB on Windows, a Docker container on Mac) · Bootstrap 5.3 · vanilla JS PWA (Service Worker + Web App Manifest).

## Windows / Visual Studio 2022 quick start

1. Install Visual Studio 2022 Community with the **ASP.NET and web development** workload (includes the .NET 8.0 runtime/SDK).
2. Open `InventoryManagementSystem.sln`.
3. Press **F5**. The database (`InventoryManagementDB` on `(localdb)\MSSQLLocalDB`) and demo data are created automatically on first run.
4. Log in with `admin` / `Admin@123`.

See `Documentation/UserManual` for a fully click-by-click walkthrough.

## Mac quick start

```bash
brew install dotnet@8
export DOTNET_ROOT=/opt/homebrew/opt/dotnet@8/libexec
export PATH=/opt/homebrew/opt/dotnet@8/bin:$PATH

docker run -d --name ims-sql --platform linux/amd64 \
  -e ACCEPT_EULA=1 -e MSSQL_SA_PASSWORD='Inventory@2026Dev' \
  -p 1433:1433 mcr.microsoft.com/mssql/server:2022-latest

dotnet run --project ASPNETApplication --launch-profile MacDocker
```

Then open `http://localhost:5080` and log in with `admin` / `Admin@123`.

> Note: `mcr.microsoft.com/azure-sql-edge` (the originally-planned lighter image) also works, but recent Go-based `sqlcmd` builds fail its TLS handshake with `x509: negative serial number`. Either run sqlcmd with `GODEBUG=x509negativeserial=1` in the environment, or use `mssql/server:2022-latest` under Rosetta as above.

### Running the SQL scripts manually

```bash
sqlcmd -S localhost,1433 -U sa -P 'Inventory@2026Dev' -C -i Database/SQLScripts/ResetDatabase.sql
sqlcmd -S localhost,1433 -U sa -P 'Inventory@2026Dev' -C -i Database/SQLScripts/CreateTables.sql
sqlcmd -S localhost,1433 -U sa -P 'Inventory@2026Dev' -C -i Database/SQLScripts/SeedData.sql
```

(On Windows/SSMS: connect to `(localdb)\MSSQLLocalDB` and run the three `.sql` files in the same order.)

### Console app

```bash
dotnet run --project ConsoleApplication
```

Or in Visual Studio: right-click `ConsoleApplication` → **Set as Startup Project** → Ctrl+F5.

### PWA

See `PWA/README.md` for how the manifest/service worker/offline pages work and how to test install + offline + notifications on desktop, Android and iPhone.

### Regenerating documentation

```bash
tools/.venv/bin/python tools/build_docs.py
```

Regenerates the ER diagram PNG, the PPTX presentation and the DOCX final report from `tools/doc_config.py` and the current test results. Fill in `tools/doc_config.py` (team names, college, guide, year — currently placeholders) before a final submission.

## Syllabus coverage

| Requirement | Where |
|---|---|
| Menu-driven console app | `ConsoleApplication/Program.cs` |
| Classes / encapsulation | `ConsoleApplication/Models/*.cs` (private fields, validating setters) |
| Inheritance / polymorphism | `Person` → `Admin`/`Staff`/`User`, used by `Services/UserService.cs` |
| Exception handling | `Program.cs` catch blocks + `Exceptions/InsufficientStockException.cs` |
| `List<T>` / `Dictionary<K,V>` | `ProductService`/`StockService` (List), `MasterDataService`, `UserService`, `ReportService` (Dictionary) |
| Search | `ProductService.SearchProduct` |
| Reports | `ConsoleApplication/Reports/ReportService.cs` |
| Login / Logout / Change Password | `AccountController`, `Views/Account/*`, `Filters/SessionAuthFilter.cs` |
| Master add/update/delete/search | `CategoryController`, `ProductController`, `SupplierController` + views |
| Stock transactions + negative-stock prevention | `StockController.StockIn/StockOut` + `CK_Stocks_QuantityAvailable` |
| Dashboard | `DashboardController` + `Views/Dashboard/Index.cshtml` |
| Reports with search/filter/print | `ReportController`, `Views/Report/*`, `site.css` `@media print` |
| SQL Server PK/FK/relationships, normalized schema | `ApplicationDbContext.OnModelCreating`, `Database/SQLScripts/CreateTables.sql`, `Database/ERDiagram/README.md` |
| PWA — responsive, installable, offline, notifications | `_Layout.cshtml`, `site.css`, `manifest.json`, `sw.js`, `pwa.js`, `pwa-pages.js`, `PwaController`, `InventoryApiController` |
| PWA modules (Search / Low Stock / Stock Overview) | `Views/Pwa/{Search,LowStock,Stock}.cshtml` |

## Demo data

6 categories, 6 suppliers, 30 products, 30 stock rows and 40 transactions, seeded automatically on first run (`DbInitializer` + `Database/SQLScripts/SeedData.sql`).
