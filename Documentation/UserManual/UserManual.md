# User Manual

## StockPilot — Inventory Management System

This guide is written for someone who has **never used Visual Studio
before**. Follow the steps in order. Every step tells you exactly what to
click. Lines starting with ✅ tell you what you should see if the step
worked.

---

## A. Install Visual Studio 2022

1. Go to `visualstudio.microsoft.com` and download **Visual Studio 2022
   Community** (it is free).
2. Run the installer.
3. On the "Workloads" screen, tick the box for **ASP.NET and web
   development**.
4. On the right side panel ("Installation details"), make sure
   **.NET 8.0 Runtime** is ticked. If you don't see it, click the
   **Individual components** tab, type "8.0" in the search box, and tick
   **.NET 8.0 Runtime (LTS)**.
5. Click **Install**. This can take 15–30 minutes.
6. When it finishes, click **Launch**.

✅ You should see: the Visual Studio "Start Window" with options like
"Clone a repository", "Open a project or solution".

---

## B. Get the project folder

Choose ONE of these:

**Option 1 — ZIP file**
1. Download the project as a ZIP file.
2. Right-click the ZIP → **Extract All…** → choose a folder (for example
   `Documents\StockPilot`) → **Extract**.

**Option 2 — Clone with Git**
1. On the Visual Studio Start Window, click **Clone a repository**.
2. Paste the repository URL, choose a location, click **Clone**.

✅ You should see: a folder containing `InventoryManagementSystem.sln`,
`ASPNETApplication`, `ConsoleApplication`, `Database`, `Documentation`,
`PWA` and `tools`.

---

## C. Open the solution

1. Open the extracted/cloned folder in **File Explorer**.
2. Double-click **`InventoryManagementSystem.sln`**.

✅ You should see: Visual Studio opens, and the **Solution Explorer** panel
(usually on the right) lists two projects: **ASPNETApplication** and
**ConsoleApplication**.

---

## D. Run the web app (F5)

1. At the top of Visual Studio, check the green **Run** button — it should
   say something like **ASPNETApplication** or **https**. If it says
   **ConsoleApplication** instead, click the small dropdown arrow next to
   the button and pick the **ASPNETApplication** / **https** profile.
2. Press **F5** (or click the green ▶ **Run** button).
3. The first run downloads NuGet packages and builds the project — wait for
   it to finish (watch the status bar at the bottom).
4. A browser window opens automatically.
5. If Visual Studio asks **"Trust the ASP.NET Core HTTPS development
   certificate?"**, click **Yes**, then **Yes** again on the Windows
   security prompt.

✅ You should see: a browser tab opens showing the **StockPilot** login
page. The very first run also silently creates the `InventoryManagementDB`
database (in **LocalDB**, which ships with Visual Studio) and fills it with
demo categories, suppliers, products and stock — you do not need to run any
SQL yourself.

---

## E. Log in and change your password

1. On the login page, type:
   - **Username:** `admin`
   - **Password:** `Admin@123`
2. Click **Log In**.
3. In the top navigation (or the sidebar footer), click your name, then
   click **Change Password**.
4. Enter the current password (`Admin@123`), a new password (at least 6
   characters), and confirm it.
5. Click **Change Password**.

✅ You should see: after login, the **Dashboard** page with KPI cards
(Total Products, Total Suppliers, etc.). After changing the password, a
green success message.

> For the actual exam demo, you can log back in with the original
> `admin` / `Admin@123` afterwards if you changed it just to show the
> feature — just repeat step E with the old password to change it back.

---

## F. Demo each feature (click by click)

Do this once yourself before the real demo, so it feels familiar.

1. **Categories** — sidebar → **Categories**. Click **Create New**, type a
   name (e.g. "Snacks"), click **Save**. It appears in the list.
2. **Products (with opening stock)** — sidebar → **Products** → **Create
   New**. Fill in Name, Price, Unit, Category, Supplier, **Opening
   Quantity** and **Reorder Level**, click **Save**. The product now shows
   up with stock already set.
3. **Suppliers** — sidebar → **Suppliers**, same Create/Edit/Delete pattern.
4. **Stock In** — sidebar → **Stock** → **Stock In**. Pick a product, enter
   a quantity, click **Save**. The quantity increases.
5. **Stock Out (negative-stock error)** — sidebar → **Stock** → **Stock
   Out**. Pick a low-stock product, type a quantity **larger** than what's
   available, click **Save** — you'll see a red **"Insufficient stock"**
   message and the stock does **not** change. Try again with a valid
   smaller quantity — it succeeds.
6. **Dashboard** — sidebar → **Dashboard**: point out the KPI cards, the
   Low Stock table, the Category Summary bars and Recent Transactions.
7. **Reports** — sidebar → **Reports**, open each one (Product Catalog,
   Stock Summary, Low Stock, Transaction History, Inventory Value), set a
   filter (e.g. a category or a date range), then click the **Print**
   button on the page — a print preview shows a clean report layout
   (no navigation/buttons on the printed page).
8. **Logout** — click **Logout**. You're returned to the login page.

✅ You should see: every action ends with either the updated list/table, or
a clear success/error message.

---

## G. Run the console app

1. In **Solution Explorer**, right-click **ConsoleApplication** →
   **Set as Startup Project**.
2. Press **Ctrl+F5** (Run without debugging — keeps the black console
   window open after it finishes).
3. When prompted, log in with one of: `admin`, `staff`, or `viewer`.
4. Try the menus: **1 Product Management**, **2 Stock Management**,
   **3 Reports**, **4 View Users**, **5 Exit**.
5. Try logging in as `viewer` and attempting to add a product — you should
   see **"Access denied: viewers cannot modify data."**

✅ You should see: a black console window with numbered menus, and demo
products/categories/suppliers already loaded.

6. When you're done, right-click **ASPNETApplication** → **Set as Startup
   Project** again, so **F5** goes back to the web app.

---

## H. (Optional) Run the SQL scripts manually

You don't need to do this for a normal demo — the app creates and seeds the
database itself. Only do this if a teacher specifically asks to see the raw
SQL, or if the database gets into a bad state.

1. In Visual Studio, open **View** → **SQL Server Object Explorer**.
2. Expand **(localdb)\MSSQLLocalDB** → find **InventoryManagementDB**.
3. Right-click the database → **New Query**.
4. Open `Database/SQLScripts/CreateTables.sql` in a text editor, copy its
   contents, paste into the query window, click **Execute** (▶ or Ctrl+E).
5. Repeat with `Database/SQLScripts/SeedData.sql`.

To start completely fresh, run `Database/SQLScripts/ResetDatabase.sql`
first (this deletes the database), then re-run **D** (press F5) and let the
app recreate everything.

---

## I. Install the app on an Android phone

1. On your laptop, find your local IP address (Windows: open **Command
   Prompt**, type `ipconfig`, look for **IPv4 Address**, e.g.
   `192.168.1.23`).
2. In Visual Studio, next to the Run button, pick the **LAN** launch
   profile (instead of `https`), then press **F5**.
3. Make sure your phone is on the **same Wi-Fi network** as your laptop.
4. On the phone, open Chrome and go to
   `chrome://flags/#unsafely-treat-insecure-origin-as-secure`.
5. In the text box, type `http://<your-laptop-ip>:5080` (use the IP from
   step 1), then tap **Relaunch**.
6. In Chrome, browse to `http://<your-laptop-ip>:5080`.
7. Log in.
8. Tap the Chrome menu (⋮) → **Install app** (or **Add to Home screen**).

✅ You should see: an app icon added to your phone's home screen. Opening it
launches StockPilot full-screen, without Chrome's address bar.

---

## J. Troubleshooting

| Problem | Fix |
|---|---|
| "Cannot connect to LocalDB" / LocalDB not running | Open a Command Prompt and run `sqllocaldb start MSSQLLocalDB`, then press F5 again |
| "Invalid object name 'dbo.Products'" or similar | The database is in a broken half-created state. Run `ResetDatabase.sql` (see section H), then press F5 to let the app recreate everything |
| ".NET 8.0 runtime not found" when running | Install the **ASP.NET Core 8.0 Runtime** (not just the SDK) from Microsoft's .NET download page, then restart Visual Studio |
| HTTPS certificate warning/prompt | Click **Yes** — this is a normal one-time local development certificate |
| Forgot the changed admin password | Open SQL Server Object Explorer (see section H), run `DELETE FROM Users WHERE Username='admin'`, then restart the app — it re-seeds the default `admin` / `Admin@123` account on next run |
| "Address already in use" / port 5080 busy | Close any other running copy of the app (check the taskbar / Visual Studio's other Debug sessions), or edit `Properties/launchSettings.json` to use a different port |
| No "Install app" option shows on the phone | The site must be treated as a secure origin — recheck the `chrome://flags` step, or use `http://localhost` only when testing on the same device |
| Notifications don't appear / are blocked | Check the site's notification permission: Chrome menu → Site settings → Notifications → set to Allow, then reload the page and try again |

---

## Demo script for the examiner (10 minutes)

A click-by-click walkthrough that shows every graded feature, in order.
Practice this once before the real demo.

| # | Time | Action | What it proves |
|---|---|---|---|
| 1 | 0:00 | Open the app, log in with **admin** / **Admin@123** | Authentication, hashed passwords |
| 2 | 0:45 | Show the **Dashboard** (KPI cards, low-stock list, category summary, recent transactions) | Aggregation queries, reporting overview |
| 3 | 1:45 | **Categories** — create one, show the list | Master data CRUD |
| 4 | 2:45 | **Products** — search for a product by name; create one with opening stock and reorder level | Search, CRUD, Product↔Category↔Supplier relationships |
| 5 | 4:00 | **Suppliers** — show the list, edit one | Master data CRUD |
| 6 | 4:30 | **Stock → Stock In** — add stock to a product | Stock transaction, audit trail |
| 7 | 5:15 | **Stock → Stock Out** — try a quantity larger than available → show the **"Insufficient stock"** error, then retry with a valid quantity | Business-rule validation, database check constraint |
| 8 | 6:15 | **Reports** — open each report (Product Catalog, Stock Summary, Low Stock, Transaction History, Inventory Value), apply a filter on one, click **Print** to show the print layout | Filtering, reporting, print stylesheet |
| 9 | 8:00 | **Change Password**, then **Logout** | Security workflow |
| 10 | 8:30 | Switch to the **console app** (Ctrl+F5), log in as `admin`, show a product search and the category-wise report, then show `viewer` blocked from adding a product | OOP, collections, exception handling, polymorphism |
| 11 | 9:30 | Open the app on a phone (or show DevTools → Application → Service Worker with **Offline** ticked, reload `/Pwa/Search`) | PWA: installable, offline-capable |

---

## Likely viva questions and simple answers

1. **Q: What is encapsulation, and where is it used here?**
   A: Hiding a class's internal data behind private fields and exposing it
   only through properties/methods that can validate it. In the console
   app's `Product` and `Person` classes, fields like `_name` and `_price`
   are private; their public properties reject bad values (e.g. a negative
   price throws an error) before storing them.

2. **Q: What is inheritance, and where is it used here?**
   A: A class reusing and extending another class's members. `Admin`,
   `Staff` and `User` all inherit from an abstract base class `Person`,
   which holds the shared `Id`, `Name`, `Email` and a `DisplayInfo()`
   method.

3. **Q: What is polymorphism, and where is it used here?**
   A: The same method call behaving differently depending on the actual
   object type. `Person.DisplayInfo()` is `virtual`; `Admin`, `Staff` and
   `User` each `override` it to print their own role-specific line. The
   console app's user list loops over `Person` references and calls
   `DisplayInfo()` — each object prints its own version automatically.

4. **Q: What's the difference between a primary key and a foreign key?**
   A: A **primary key (PK)** uniquely identifies each row in its own table
   (e.g. `ProductId` in `Products`). A **foreign key (FK)** is a column in
   one table that points to a primary key in another table, linking the
   rows together (e.g. `Products.CategoryId` points to
   `Categories.CategoryId`).

5. **Q: What is database normalization, and is this schema normalized?**
   A: Normalization is organizing tables so each fact is stored in exactly
   one place, to avoid repeating or inconsistent data. This schema is in
   3NF: category and supplier details live only in their own master
   tables (not repeated on every product row), and stock levels live in a
   separate `Stocks` table from product identity data because they change
   at a different rate. See `Database/ERDiagram/README.md` for the full
   explanation.

6. **Q: Why is Stock a separate table from Product instead of just columns
   on Product?**
   A: Stock quantity changes constantly (every Stock In/Out), while a
   product's name/price/unit change rarely. Splitting them keeps the
   catalog and the operational stock level independent, and it's also what
   3NF normalization calls for — quantity doesn't describe the product
   itself, it describes the product's current state.

7. **Q: What is a service worker, and what does it do in this project?**
   A: A background script the browser runs separately from the page, which
   can intercept network requests. Here it caches pages, static assets and
   API responses so the **Product Search**, **Stock Overview** and **Low
   Stock Alerts** pages keep working when the phone/laptop has no internet
   connection, and it also shows low-stock notifications.

8. **Q: How are passwords stored — as plain text?**
   A: No. The app uses ASP.NET Core Identity's `PasswordHasher`, which
   applies PBKDF2-SHA512 hashing with a random salt. Only the hash is
   stored in the `Users.PasswordHash` column; the original password is
   never saved anywhere.

9. **Q: What stops someone from selling more stock than exists?**
   A: Two layers: the application checks the requested quantity against
   `Stocks.QuantityAvailable` before saving and shows "Insufficient stock"
   if it's too high; and the database itself has a check constraint,
   `CK_Stocks_QuantityAvailable >= 0`, as a last-resort safety net even if
   application logic were bypassed.

10. **Q: What is exception handling, and where is a custom exception used?**
    A: Catching and responding to runtime errors instead of letting the
    program crash. The console app defines a custom
    `InsufficientStockException` (inherits from `Exception`) that carries
    the product name, requested quantity and available quantity; `Program.cs`
    catches it specifically and prints a friendly message instead of a raw
    stack trace.

11. **Q: What collections are used, and why?**
    A: `List<T>` for ordered collections like the product and stock lists
    (`ProductService`, `StockService`), and `Dictionary<TKey,TValue>` where
    fast lookup by name/username matters — for example
    `MasterDataService` looks up an existing category by name instead of
    scanning a list, and `UserService` looks up a user by username.

12. **Q: Why does the app use sessions instead of just a login form with no
    persistence?**
    A: HTTP is stateless — without a session, the server would forget who
    you are after every request. A `SessionAuthFilter` checks for a
    `UserId` in the session on every request (except Login) and redirects
    to the login page (or returns a 401 for API calls) if it's missing,
    which is what keeps you logged in as you move between pages and logs
    you out cleanly.
