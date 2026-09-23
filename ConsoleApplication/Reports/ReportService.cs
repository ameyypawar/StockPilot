using System;
using System.Collections.Generic;
using System.Linq;
using InventoryManagementSystem.Services;

namespace InventoryManagementSystem.Reports
{
    // Reports module: aggregates data from ProductService/StockService; uses a Dictionary
    // (Collections) to build the category-wise summary.
    public class ReportService
    {
        private ProductService _productService;
        private StockService _stockService;

        public ReportService(ProductService productService, StockService stockService)
        {
            _productService = productService;
            _stockService = stockService;
        }

        public void GenerateStockSummaryReport()
        {
            Console.WriteLine("\n===== STOCK SUMMARY REPORT =====");
            _stockService.DisplayAllStock();
            Console.WriteLine("=================================\n");
        }

        public void GenerateLowStockReport()
        {
            Console.WriteLine("\n===== LOW STOCK REPORT =====");
            var lowStockItems = _stockService.GetLowStockItems();

            if (lowStockItems.Count == 0)
            {
                Console.WriteLine("No low stock items.");
            }
            else
            {
                foreach (var item in lowStockItems)
                {
                    Console.WriteLine(item.ToString());
                }
            }
            Console.WriteLine("=============================\n");
        }

        public void GenerateTransactionReport()
        {
            Console.WriteLine("\n===== TRANSACTION HISTORY REPORT =====");
            _stockService.DisplayTransactionHistory();
            Console.WriteLine("========================================\n");
        }

        public void GenerateProductCatalogReport()
        {
            Console.WriteLine("\n===== PRODUCT CATALOG REPORT =====");
            _productService.DisplayAllProducts();
            Console.WriteLine("===================================\n");
        }

        public void GenerateInventoryValueReport()
        {
            Console.WriteLine("\n===== INVENTORY VALUE REPORT =====");
            var products = _productService.GetAllProducts();

            if (products.Count == 0)
            {
                Console.WriteLine("No products available.");
            }
            else
            {
                decimal totalValue = 0;
                foreach (var product in products)
                {
                    int qty = _stockService.GetStock(product.ProductId)?.QuantityAvailable ?? product.Quantity;
                    decimal value = product.Price * qty;
                    totalValue += value;
                    Console.WriteLine($"{product.ProductName} : Value=Rs.{value:F2}");
                }
                Console.WriteLine($"\nTotal Inventory Value: Rs.{totalValue:F2}");
            }
            Console.WriteLine("===================================\n");
        }

        public void GenerateCategoryWiseReport()
        {
            Console.WriteLine("\n===== CATEGORY-WISE SUMMARY =====");
            var products = _productService.GetAllProducts();

            if (products.Count == 0)
            {
                Console.WriteLine("No products available.");
                Console.WriteLine("==================================\n");
                return;
            }

            var summary = new Dictionary<string, (int Products, int Units, decimal Value)>();

            foreach (var product in products)
            {
                string categoryName = product.Category?.CategoryName ?? "Uncategorized";
                int qty = _stockService.GetStock(product.ProductId)?.QuantityAvailable ?? product.Quantity;
                decimal value = product.Price * qty;

                if (summary.TryGetValue(categoryName, out var existing))
                {
                    summary[categoryName] = (existing.Products + 1, existing.Units + qty, existing.Value + value);
                }
                else
                {
                    summary[categoryName] = (1, qty, value);
                }
            }

            Console.WriteLine($"{"Category",-28} {"Products",8} {"Units",8} {"Value",14}");
            foreach (var entry in summary)
            {
                Console.WriteLine($"{entry.Key,-28} {entry.Value.Products,8} {entry.Value.Units,8} {"Rs." + entry.Value.Value.ToString("F2"),14}");
            }
            Console.WriteLine("==================================\n");
        }
    }
}
