using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Storage;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using InventoryManagement.Web.Models;

namespace InventoryManagement.Web.Data
{
    public static class DbInitializer
    {
        public static void Initialize(IServiceProvider sp)
        {
            var db = sp.GetRequiredService<ApplicationDbContext>();
            var hasher = sp.GetRequiredService<IPasswordHasher<ApplicationUser>>();
            var logger = sp.GetRequiredService<ILoggerFactory>().CreateLogger("DbInitializer");

            try
            {
                // 1. Make sure the database exists (no-op if it already has tables).
                db.Database.EnsureCreated();

                // 2. EnsureCreated() is a no-op on a database that already has ANY
                //    tables (e.g. one left over with only __EFMigrationsHistory).
                //    Fall back to creating the EF-model tables directly in that case.
                var productsTableCount = db.Database
                    .SqlQueryRaw<int>("SELECT COUNT(*) AS Value FROM sys.tables WHERE name = 'Products'")
                    .AsEnumerable()
                    .FirstOrDefault();

                if (productsTableCount == 0)
                {
                    logger.LogInformation("Products table missing; creating EF model tables directly.");
                    db.GetService<IRelationalDatabaseCreator>().CreateTables();
                }

                // 3. Seed the admin user first (independent of SeedData.sql), so the
                //    app can always log in even if the SQL seed fails.
                if (!db.Users.Any(u => u.Username == "admin"))
                {
                    var admin = new ApplicationUser
                    {
                        Username = "admin",
                        FullName = "System Administrator",
                        Email = "admin@example.com",
                        Role = "Admin",
                    };
                    admin.PasswordHash = hasher.HashPassword(admin, "Admin@123");
                    db.Users.Add(admin);
                    db.SaveChanges();
                    logger.LogInformation("Seeded default admin user.");
                }

                // 4. Seed demo data (categories/suppliers/products/stocks/transactions)
                //    from the embedded SeedData.sql, batch-split on GO.
                if (!db.Categories.Any())
                {
                    RunSeedDataScript(db, logger);
                }

                // 5. Log row counts so a broken seed is loud in the console, not silent.
                logger.LogInformation(
                    "Row counts - Categories: {Categories}, Suppliers: {Suppliers}, Products: {Products}, Stocks: {Stocks}, StockTransactions: {StockTransactions}, Users: {Users}",
                    db.Categories.Count(), db.Suppliers.Count(), db.Products.Count(),
                    db.Stocks.Count(), db.StockTransactions.Count(), db.Users.Count());
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Database initialization failed.");
                throw;
            }
        }

        private static void RunSeedDataScript(ApplicationDbContext db, ILogger logger)
        {
            var assembly = Assembly.GetExecutingAssembly();
            const string resourceName = "InventoryManagement.Web.SeedData.sql";

            using var stream = assembly.GetManifestResourceStream(resourceName);
            if (stream == null)
            {
                logger.LogWarning("Embedded resource {ResourceName} not found; skipping seed data.", resourceName);
                return;
            }

            using var reader = new StreamReader(stream);
            string sql = reader.ReadToEnd();

            // Batches are separated by a line containing only "GO" (optionally
            // followed by a semicolon), matching sqlcmd/SSMS batch semantics.
            var batches = Regex.Split(sql, @"^\s*GO\s*;?\s*$", RegexOptions.Multiline | RegexOptions.IgnoreCase);

            foreach (var rawBatch in batches)
            {
                var batch = rawBatch.Trim();
                if (string.IsNullOrWhiteSpace(batch))
                    continue;

                // Skip batches that are only comments (nothing left after
                // stripping -- line comments).
                var withoutComments = Regex.Replace(batch, @"^\s*--.*$", "", RegexOptions.Multiline).Trim();
                if (string.IsNullOrWhiteSpace(withoutComments))
                    continue;

                // Skip USE <database> batches - the app is already connected to
                // the target database via the connection string.
                if (Regex.IsMatch(withoutComments, @"^\s*USE\s+", RegexOptions.IgnoreCase))
                    continue;

                db.Database.ExecuteSqlRaw(batch);
            }

            logger.LogInformation("Seed data script executed.");
        }
    }
}
