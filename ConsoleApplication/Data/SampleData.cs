using System.Collections.Generic;
using InventoryManagementSystem.Models;
using InventoryManagementSystem.Services;

namespace InventoryManagementSystem.Data
{
    // Seeds demo data mirroring Database/SQLScripts/SeedData.sql: same 6 category names,
    // same 6 supplier names, same order, and the first 10 products (so IDs line up with the web app).
    public static class SampleData
    {
        public static void Seed(ProductService productService, StockService stockService, MasterDataService masterData)
        {
            // Same 6 categories, same order as SeedData.sql
            var categories = new List<Category>
            {
                masterData.GetOrCreateCategory("Groceries & Staples"),
                masterData.GetOrCreateCategory("Beverages"),
                masterData.GetOrCreateCategory("Personal Care"),
                masterData.GetOrCreateCategory("Household & Cleaning"),
                masterData.GetOrCreateCategory("Stationery"),
                masterData.GetOrCreateCategory("Electronics & Accessories")
            };

            // Same 6 suppliers, same order as SeedData.sql
            var suppliers = new List<Supplier>
            {
                masterData.GetOrCreateSupplier("Shree Ganesh Traders", "+91 90000 00001"),
                masterData.GetOrCreateSupplier("Annapurna Agro Foods", "+91 90000 00002"),
                masterData.GetOrCreateSupplier("Balaji Wholesale Distributors", "+91 90000 00003"),
                masterData.GetOrCreateSupplier("Sai Home Care Supplies", "+91 90000 00004"),
                masterData.GetOrCreateSupplier("Krishna Stationery Mart", "+91 90000 00005"),
                masterData.GetOrCreateSupplier("Om Electronics Hub", "+91 90000 00006")
            };

            // First 10 products from SeedData.sql: name, categoryIndex, supplierIndex, price, qty, reorder
            AddSeedProduct(productService, stockService, "Basmati Rice 5 kg", categories[0], suppliers[1], 545m, 42, 15);
            AddSeedProduct(productService, stockService, "Toor Dal 1 kg", categories[0], suppliers[1], 165m, 8, 20);
            AddSeedProduct(productService, stockService, "Wheat Atta 10 kg", categories[0], suppliers[0], 420m, 25, 10);
            AddSeedProduct(productService, stockService, "Sunflower Oil 1 L", categories[0], suppliers[0], 155m, 60, 24);
            AddSeedProduct(productService, stockService, "Iodised Salt 1 kg", categories[0], suppliers[0], 28m, 120, 40);
            AddSeedProduct(productService, stockService, "Assam Tea 500 g", categories[1], suppliers[2], 260m, 35, 12);
            AddSeedProduct(productService, stockService, "Filter Coffee Powder 500 g", categories[1], suppliers[2], 310m, 5, 10);
            AddSeedProduct(productService, stockService, "Mango Drink 1.2 L", categories[1], suppliers[2], 75m, 48, 24);
            AddSeedProduct(productService, stockService, "Packaged Drinking Water 1 L (case of 12)", categories[1], suppliers[2], 180m, 0, 10);
            AddSeedProduct(productService, stockService, "Lemon Soda 750 ml", categories[1], suppliers[2], 40m, 72, 24);
        }

        private static void AddSeedProduct(ProductService productService, StockService stockService, string name, Category category, Supplier supplier, decimal price, int quantity, int reorderLevel)
        {
            productService.AddProduct(name, price, quantity, category, supplier);
            var product = productService.GetAllProducts()[^1];
            stockService.InitializeStock(product, quantity, reorderLevel);
        }
    }
}
