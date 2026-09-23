-- SeedData.sql
-- Demo data for InventoryManagementDB. Executed by DbInitializer on first run
-- (batch-split on GO), and can also be run manually via sqlcmd/SSMS after
-- CreateTables.sql.

USE InventoryManagementDB;
GO

-- Categories
IF NOT EXISTS (SELECT 1 FROM dbo.Categories)
BEGIN
    SET IDENTITY_INSERT dbo.Categories ON;
    INSERT INTO dbo.Categories (CategoryId, CategoryName, Description) VALUES
        (1, N'Groceries & Staples', N'Everyday staple foods and cooking essentials'),
        (2, N'Beverages', N'Tea, coffee, juices and soft drinks'),
        (3, N'Personal Care', N'Soaps, shampoos and personal hygiene products'),
        (4, N'Household & Cleaning', N'Cleaning supplies and household consumables'),
        (5, N'Stationery', N'Office and school stationery items'),
        (6, N'Electronics & Accessories', N'Small electronics and accessories');
    SET IDENTITY_INSERT dbo.Categories OFF;
END
GO

-- Suppliers
IF NOT EXISTS (SELECT 1 FROM dbo.Suppliers)
BEGIN
    SET IDENTITY_INSERT dbo.Suppliers ON;
    INSERT INTO dbo.Suppliers (SupplierId, SupplierName, ContactNumber, Email, Address) VALUES
        (1, N'Shree Ganesh Traders', N'+91 98765 43210', N'shreeganesh.traders@example.com', N'Market Yard, Pune'),
        (2, N'Annapurna Agro Foods', N'+91 97654 32109', N'annapurna.agro@example.com', N'Satpur MIDC, Nashik'),
        (3, N'Balaji Wholesale Distributors', N'+91 96543 21098', N'balaji.wholesale@example.com', N'Masjid Bunder, Mumbai'),
        (4, N'Sai Home Care Supplies', N'+91 95432 10987', N'sai.homecare@example.com', N'Itwari, Nagpur'),
        (5, N'Krishna Stationery Mart', N'+91 94321 09876', N'krishna.stationery@example.com', N'Rajarampuri, Kolhapur'),
        (6, N'Om Electronics Hub', N'+91 93210 98765', N'om.electronics@example.com', N'SP Road, Bengaluru');
    SET IDENTITY_INSERT dbo.Suppliers OFF;
END
GO

-- Users (admin only; PasswordHasher<ApplicationUser> V3 hash for 'Admin@123',
-- generated with .NET 8's Microsoft.AspNetCore.Identity)
IF NOT EXISTS (SELECT 1 FROM dbo.Users WHERE Username = N'admin')
BEGIN
    SET IDENTITY_INSERT dbo.Users ON;
    INSERT INTO dbo.Users (UserId, Username, PasswordHash, FullName, Email, Role) VALUES
        (1, N'admin', N'AQAAAAIAAYagAAAAEL7kDGynrsuXtpT7gi20Cf9/m/f9OLMHe++0u7eJVnuGYmUSaSbliDuetV6UoMuFKw==', N'System Administrator', N'admin@example.com', N'Admin');
    SET IDENTITY_INSERT dbo.Users OFF;
END
GO

-- Products
IF NOT EXISTS (SELECT 1 FROM dbo.Products)
BEGIN
    SET IDENTITY_INSERT dbo.Products ON;
    INSERT INTO dbo.Products (ProductId, ProductName, Price, CategoryId, SupplierId, Unit) VALUES
        (1, N'Basmati Rice 5 kg', 545.00, 1, 2, N'bag'),
        (2, N'Toor Dal 1 kg', 165.00, 1, 2, N'pack'),
        (3, N'Wheat Atta 10 kg', 420.00, 1, 1, N'bag'),
        (4, N'Sunflower Oil 1 L', 155.00, 1, 1, N'bottle'),
        (5, N'Iodised Salt 1 kg', 28.00, 1, 1, N'pack'),
        (6, N'Assam Tea 500 g', 260.00, 2, 3, N'pack'),
        (7, N'Filter Coffee Powder 500 g', 310.00, 2, 3, N'pack'),
        (8, N'Mango Drink 1.2 L', 75.00, 2, 3, N'bottle'),
        (9, N'Packaged Drinking Water 1 L (case of 12)', 180.00, 2, 3, N'case'),
        (10, N'Lemon Soda 750 ml', 40.00, 2, 3, N'bottle'),
        (11, N'Neem Soap 125 g (pack of 4)', 140.00, 3, 4, N'pack'),
        (12, N'Herbal Shampoo 340 ml', 210.00, 3, 4, N'bottle'),
        (13, N'Coconut Hair Oil 500 ml', 185.00, 3, 4, N'bottle'),
        (14, N'Toothpaste 150 g', 95.00, 3, 4, N'tube'),
        (15, N'Talcum Powder 300 g', 150.00, 3, 4, N'bottle'),
        (16, N'Dishwash Bar 500 g', 45.00, 4, 4, N'pcs'),
        (17, N'Detergent Powder 1 kg', 120.00, 4, 4, N'pack'),
        (18, N'Floor Cleaner 1 L', 199.00, 4, 4, N'bottle'),
        (19, N'Agarbatti (100 sticks)', 60.00, 4, 1, N'box'),
        (20, N'Mosquito Coil (pack of 10)', 55.00, 4, 1, N'pack'),
        (21, N'A4 Copier Paper (500 sheets)', 310.00, 5, 5, N'ream'),
        (22, N'Ball Pen Blue (box of 10)', 70.00, 5, 5, N'box'),
        (23, N'Long Notebook 200 pages', 65.00, 5, 5, N'pcs'),
        (24, N'Geometry Box', 120.00, 5, 5, N'pcs'),
        (25, N'Stapler No. 10', 95.00, 5, 5, N'pcs'),
        (26, N'LED Bulb 9 W', 99.00, 6, 6, N'pcs'),
        (27, N'USB-C Charging Cable 1 m', 249.00, 6, 6, N'pcs'),
        (28, N'Extension Board 4-Socket', 449.00, 6, 6, N'pcs'),
        (29, N'AA Batteries (pack of 4)', 120.00, 6, 6, N'pack'),
        (30, N'Wired Earphones with Mic', 399.00, 6, 6, N'pcs');
    SET IDENTITY_INSERT dbo.Products OFF;
END
GO

-- Stocks
IF NOT EXISTS (SELECT 1 FROM dbo.Stocks)
BEGIN
    SET IDENTITY_INSERT dbo.Stocks ON;
    INSERT INTO dbo.Stocks (StockId, ProductId, QuantityAvailable, ReorderLevel, LastUpdated) VALUES
        (1, 1, 42, 15, DATEADD(DAY, -2, SYSDATETIME())),
        (2, 2, 8, 20, DATEADD(DAY, -3, SYSDATETIME())),
        (3, 3, 25, 10, DATEADD(DAY, -4, SYSDATETIME())),
        (4, 4, 60, 24, DATEADD(DAY, -5, SYSDATETIME())),
        (5, 5, 120, 40, DATEADD(DAY, -6, SYSDATETIME())),
        (6, 6, 35, 12, DATEADD(DAY, -7, SYSDATETIME())),
        (7, 7, 5, 10, DATEADD(DAY, -8, SYSDATETIME())),
        (8, 8, 48, 24, DATEADD(DAY, -9, SYSDATETIME())),
        (9, 9, 0, 10, DATEADD(DAY, -10, SYSDATETIME())),
        (10, 10, 72, 24, DATEADD(DAY, -1, SYSDATETIME())),
        (11, 11, 30, 10, DATEADD(DAY, -2, SYSDATETIME())),
        (12, 12, 18, 8, DATEADD(DAY, -3, SYSDATETIME())),
        (13, 13, 6, 10, DATEADD(DAY, -4, SYSDATETIME())),
        (14, 14, 55, 20, DATEADD(DAY, -5, SYSDATETIME())),
        (15, 15, 22, 8, DATEADD(DAY, -6, SYSDATETIME())),
        (16, 16, 90, 30, DATEADD(DAY, -7, SYSDATETIME())),
        (17, 17, 40, 15, DATEADD(DAY, -8, SYSDATETIME())),
        (18, 18, 12, 12, DATEADD(DAY, -9, SYSDATETIME())),
        (19, 19, 75, 20, DATEADD(DAY, -10, SYSDATETIME())),
        (20, 20, 0, 15, DATEADD(DAY, -1, SYSDATETIME())),
        (21, 21, 28, 10, DATEADD(DAY, -2, SYSDATETIME())),
        (22, 22, 64, 20, DATEADD(DAY, -3, SYSDATETIME())),
        (23, 23, 150, 50, DATEADD(DAY, -4, SYSDATETIME())),
        (24, 24, 9, 10, DATEADD(DAY, -5, SYSDATETIME())),
        (25, 25, 20, 6, DATEADD(DAY, -6, SYSDATETIME())),
        (26, 26, 85, 25, DATEADD(DAY, -7, SYSDATETIME())),
        (27, 27, 16, 10, DATEADD(DAY, -8, SYSDATETIME())),
        (28, 28, 7, 5, DATEADD(DAY, -9, SYSDATETIME())),
        (29, 29, 3, 12, DATEADD(DAY, -10, SYSDATETIME())),
        (30, 30, 14, 6, DATEADD(DAY, -1, SYSDATETIME()));
    SET IDENTITY_INSERT dbo.Stocks OFF;
END
GO

-- Stock Transactions (22 StockIn, 18 StockOut)
IF NOT EXISTS (SELECT 1 FROM dbo.StockTransactions)
BEGIN
    SET IDENTITY_INSERT dbo.StockTransactions ON;
    INSERT INTO dbo.StockTransactions (TransactionId, ProductId, Type, Quantity, TransactionDate, PerformedBy, Remarks) VALUES
        (1, 2, N'StockOut', 5, DATEADD(DAY, -1, SYSDATETIME()), N'admin', N'Counter sale'),
        (2, 7, N'StockOut', 5, DATEADD(DAY, -2, SYSDATETIME()), N'Rahul Patil', N'Issued to branch'),
        (3, 9, N'StockOut', 2, DATEADD(DAY, -2, SYSDATETIME()), N'admin', N'Counter sale'),
        (4, 13, N'StockOut', 5, DATEADD(DAY, -3, SYSDATETIME()), N'Rahul Patil', N'Issued to branch'),
        (5, 18, N'StockOut', 5, DATEADD(DAY, -3, SYSDATETIME()), N'admin', N'Counter sale'),
        (6, 20, N'StockOut', 2, DATEADD(DAY, -4, SYSDATETIME()), N'Rahul Patil', N'Issued to branch'),
        (7, 24, N'StockOut', 5, DATEADD(DAY, -4, SYSDATETIME()), N'admin', N'Counter sale'),
        (8, 29, N'StockOut', 5, DATEADD(DAY, -5, SYSDATETIME()), N'Rahul Patil', N'Issued to branch'),
        (9, 25, N'StockOut', 3, DATEADD(DAY, -13, SYSDATETIME()), N'admin', N'Issued to branch'),
        (10, 11, N'StockOut', 10, DATEADD(DAY, -10, SYSDATETIME()), N'Rahul Patil', N'Issued to branch'),
        (11, 27, N'StockOut', 7, DATEADD(DAY, -23, SYSDATETIME()), N'admin', N'Counter sale'),
        (12, 16, N'StockOut', 3, DATEADD(DAY, -4, SYSDATETIME()), N'Rahul Patil', N'Counter sale'),
        (13, 6, N'StockOut', 5, DATEADD(DAY, -28, SYSDATETIME()), N'admin', N'Issued to branch'),
        (14, 22, N'StockOut', 5, DATEADD(DAY, -10, SYSDATETIME()), N'Rahul Patil', N'Counter sale'),
        (15, 21, N'StockOut', 6, DATEADD(DAY, -29, SYSDATETIME()), N'admin', N'Issued to branch'),
        (16, 14, N'StockOut', 7, DATEADD(DAY, -17, SYSDATETIME()), N'Rahul Patil', N'Counter sale'),
        (17, 10, N'StockOut', 7, DATEADD(DAY, -25, SYSDATETIME()), N'admin', N'Counter sale'),
        (18, 23, N'StockOut', 6, DATEADD(DAY, -28, SYSDATETIME()), N'Rahul Patil', N'Counter sale'),
        (19, 23, N'StockIn', 51, DATEADD(DAY, -13, SYSDATETIME()), N'admin', N'Purchase - Krishna Stationery Mart'),
        (20, 16, N'StockIn', 19, DATEADD(DAY, -15, SYSDATETIME()), N'Rahul Patil', N'Purchase - Sai Home Care Supplies'),
        (21, 30, N'StockIn', 18, DATEADD(DAY, -9, SYSDATETIME()), N'admin', N'Purchase - Om Electronics Hub'),
        (22, 29, N'StockIn', 57, DATEADD(DAY, -8, SYSDATETIME()), N'Rahul Patil', N'Purchase - Om Electronics Hub'),
        (23, 3, N'StockIn', 44, DATEADD(DAY, -18, SYSDATETIME()), N'admin', N'Purchase - Shree Ganesh Traders'),
        (24, 12, N'StockIn', 57, DATEADD(DAY, -9, SYSDATETIME()), N'Rahul Patil', N'Purchase - Sai Home Care Supplies'),
        (25, 10, N'StockIn', 37, DATEADD(DAY, -19, SYSDATETIME()), N'admin', N'Purchase - Balaji Wholesale Distributors'),
        (26, 4, N'StockIn', 47, DATEADD(DAY, -29, SYSDATETIME()), N'Rahul Patil', N'Purchase - Shree Ganesh Traders'),
        (27, 17, N'StockIn', 33, DATEADD(DAY, -13, SYSDATETIME()), N'admin', N'Purchase - Sai Home Care Supplies'),
        (28, 5, N'StockIn', 18, DATEADD(DAY, -8, SYSDATETIME()), N'Rahul Patil', N'Purchase - Shree Ganesh Traders'),
        (29, 7, N'StockIn', 41, DATEADD(DAY, -17, SYSDATETIME()), N'admin', N'Purchase - Balaji Wholesale Distributors'),
        (30, 26, N'StockIn', 58, DATEADD(DAY, -3, SYSDATETIME()), N'Rahul Patil', N'Purchase - Om Electronics Hub'),
        (31, 22, N'StockIn', 17, DATEADD(DAY, -2, SYSDATETIME()), N'admin', N'Purchase - Krishna Stationery Mart'),
        (32, 1, N'StockIn', 50, DATEADD(DAY, -5, SYSDATETIME()), N'Rahul Patil', N'Purchase - Annapurna Agro Foods'),
        (33, 14, N'StockIn', 60, DATEADD(DAY, -6, SYSDATETIME()), N'admin', N'Purchase - Sai Home Care Supplies'),
        (34, 19, N'StockIn', 37, DATEADD(DAY, -22, SYSDATETIME()), N'Rahul Patil', N'Purchase - Shree Ganesh Traders'),
        (35, 2, N'StockIn', 14, DATEADD(DAY, -20, SYSDATETIME()), N'admin', N'Purchase - Annapurna Agro Foods'),
        (36, 11, N'StockIn', 34, DATEADD(DAY, -13, SYSDATETIME()), N'Rahul Patil', N'Purchase - Sai Home Care Supplies'),
        (37, 25, N'StockIn', 39, DATEADD(DAY, -20, SYSDATETIME()), N'admin', N'Purchase - Krishna Stationery Mart'),
        (38, 27, N'StockIn', 26, DATEADD(DAY, -17, SYSDATETIME()), N'Rahul Patil', N'Purchase - Om Electronics Hub'),
        (39, 9, N'StockIn', 10, DATEADD(DAY, -18, SYSDATETIME()), N'admin', N'Purchase - Balaji Wholesale Distributors'),
        (40, 13, N'StockIn', 56, DATEADD(DAY, -22, SYSDATETIME()), N'Rahul Patil', N'Purchase - Sai Home Care Supplies');
    SET IDENTITY_INSERT dbo.StockTransactions OFF;
END
GO
