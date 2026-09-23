-- ResetDatabase.sql
-- Drops the InventoryManagementDB database so it can be recreated from
-- scratch (CreateTables.sql + SeedData.sql, or by starting the web app,
-- which creates and seeds the database automatically).
--
-- Run with, e.g.:
--   sqlcmd -S localhost,1433 -U sa -P '<password>' -C -i Database/SQLScripts/ResetDatabase.sql
--   sqlcmd -S "(localdb)\MSSQLLocalDB" -i Database/SQLScripts/ResetDatabase.sql

USE master;
GO

IF DB_ID(N'InventoryManagementDB') IS NOT NULL
BEGIN
    ALTER DATABASE InventoryManagementDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE InventoryManagementDB;
END
GO
