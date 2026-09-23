-- CreateTables.sql
-- Generated from the EF Core model (`dotnet ef dbcontext script --project ASPNETApplication`)
-- and wrapped with existence guards so it can be re-run safely. Table and
-- index/constraint names match the EF model exactly (see ApplicationDbContext.OnModelCreating).

IF DB_ID(N'InventoryManagementDB') IS NULL CREATE DATABASE InventoryManagementDB;
GO

USE InventoryManagementDB;
GO

IF OBJECT_ID(N'dbo.Categories', N'U') IS NULL
BEGIN
    CREATE TABLE [Categories] (
        [CategoryId] int NOT NULL IDENTITY,
        [CategoryName] nvarchar(100) NOT NULL,
        [Description] nvarchar(250) NULL,
        CONSTRAINT [PK_Categories] PRIMARY KEY ([CategoryId])
    );
END
GO

IF OBJECT_ID(N'dbo.Suppliers', N'U') IS NULL
BEGIN
    CREATE TABLE [Suppliers] (
        [SupplierId] int NOT NULL IDENTITY,
        [SupplierName] nvarchar(150) NOT NULL,
        [ContactNumber] nvarchar(20) NULL,
        [Email] nvarchar(150) NULL,
        [Address] nvarchar(250) NULL,
        CONSTRAINT [PK_Suppliers] PRIMARY KEY ([SupplierId])
    );
END
GO

IF OBJECT_ID(N'dbo.Users', N'U') IS NULL
BEGIN
    CREATE TABLE [Users] (
        [UserId] int NOT NULL IDENTITY,
        [Username] nvarchar(50) NOT NULL,
        [PasswordHash] nvarchar(256) NOT NULL,
        [FullName] nvarchar(100) NOT NULL,
        [Email] nvarchar(150) NULL,
        [Role] nvarchar(20) NOT NULL,
        CONSTRAINT [PK_Users] PRIMARY KEY ([UserId])
    );
END
GO

IF OBJECT_ID(N'dbo.Products', N'U') IS NULL
BEGIN
    CREATE TABLE [Products] (
        [ProductId] int NOT NULL IDENTITY,
        [ProductName] nvarchar(150) NOT NULL,
        [Price] decimal(10,2) NOT NULL,
        [Unit] nvarchar(20) NOT NULL,
        [CategoryId] int NOT NULL,
        [SupplierId] int NOT NULL,
        CONSTRAINT [PK_Products] PRIMARY KEY ([ProductId]),
        CONSTRAINT [CK_Products_Price] CHECK ([Price] >= 0),
        CONSTRAINT [FK_Products_Categories_CategoryId] FOREIGN KEY ([CategoryId]) REFERENCES [Categories] ([CategoryId]) ON DELETE NO ACTION,
        CONSTRAINT [FK_Products_Suppliers_SupplierId] FOREIGN KEY ([SupplierId]) REFERENCES [Suppliers] ([SupplierId]) ON DELETE NO ACTION
    );
END
GO

IF OBJECT_ID(N'dbo.Stocks', N'U') IS NULL
BEGIN
    CREATE TABLE [Stocks] (
        [StockId] int NOT NULL IDENTITY,
        [ProductId] int NOT NULL,
        [QuantityAvailable] int NOT NULL,
        [ReorderLevel] int NOT NULL,
        [LastUpdated] datetime2 NOT NULL,
        CONSTRAINT [PK_Stocks] PRIMARY KEY ([StockId]),
        CONSTRAINT [CK_Stocks_QuantityAvailable] CHECK ([QuantityAvailable] >= 0),
        CONSTRAINT [CK_Stocks_ReorderLevel] CHECK ([ReorderLevel] >= 0),
        CONSTRAINT [FK_Stocks_Products_ProductId] FOREIGN KEY ([ProductId]) REFERENCES [Products] ([ProductId]) ON DELETE CASCADE
    );
END
GO

IF OBJECT_ID(N'dbo.StockTransactions', N'U') IS NULL
BEGIN
    CREATE TABLE [StockTransactions] (
        [TransactionId] int NOT NULL IDENTITY,
        [ProductId] int NOT NULL,
        [Type] nvarchar(10) NOT NULL,
        [Quantity] int NOT NULL,
        [TransactionDate] datetime2 NOT NULL,
        [PerformedBy] nvarchar(100) NOT NULL,
        [Remarks] nvarchar(250) NULL,
        CONSTRAINT [PK_StockTransactions] PRIMARY KEY ([TransactionId]),
        CONSTRAINT [CK_StockTransactions_Quantity] CHECK ([Quantity] > 0),
        CONSTRAINT [CK_StockTransactions_Type] CHECK ([Type] IN ('StockIn','StockOut')),
        CONSTRAINT [FK_StockTransactions_Products_ProductId] FOREIGN KEY ([ProductId]) REFERENCES [Products] ([ProductId]) ON DELETE CASCADE
    );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Categories_CategoryName')
BEGIN
    CREATE UNIQUE INDEX [IX_Categories_CategoryName] ON [Categories] ([CategoryName]);
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Products_CategoryId')
BEGIN
    CREATE INDEX [IX_Products_CategoryId] ON [Products] ([CategoryId]);
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Products_ProductName')
BEGIN
    CREATE INDEX [IX_Products_ProductName] ON [Products] ([ProductName]);
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Products_SupplierId')
BEGIN
    CREATE INDEX [IX_Products_SupplierId] ON [Products] ([SupplierId]);
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Stocks_ProductId')
BEGIN
    CREATE UNIQUE INDEX [IX_Stocks_ProductId] ON [Stocks] ([ProductId]);
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_StockTransactions_ProductId')
BEGIN
    CREATE INDEX [IX_StockTransactions_ProductId] ON [StockTransactions] ([ProductId]);
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_StockTransactions_TransactionDate')
BEGIN
    CREATE INDEX [IX_StockTransactions_TransactionDate] ON [StockTransactions] ([TransactionDate]);
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Users_Username')
BEGIN
    CREATE UNIQUE INDEX [IX_Users_Username] ON [Users] ([Username]);
END
GO
