using InventoryManagement.Web.Data;
using InventoryManagement.Web.ViewModels;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;

namespace InventoryManagement.Web.Controllers
{
    public class DashboardController : Controller
    {
        private readonly ApplicationDbContext _context;

        public DashboardController(ApplicationDbContext context)
        {
            _context = context;
        }

        public IActionResult Index()
        {
            ViewBag.Username = HttpContext.Session.GetString("Username");
            ViewBag.Role = HttpContext.Session.GetString("Role");

            // Key metrics
            ViewBag.TotalProducts = _context.Products.Count();
            ViewBag.TotalSuppliers = _context.Suppliers.Count();
            ViewBag.TotalCategories = _context.Categories.Count();
            ViewBag.TotalUnits = _context.Stocks.Sum(s => (int?)s.QuantityAvailable) ?? 0;
            ViewBag.LowStockCount = _context.Stocks.Count(s => s.QuantityAvailable <= s.ReorderLevel);
            ViewBag.OutOfStockCount = _context.Stocks.Count(s => s.QuantityAvailable == 0);

            ViewBag.TotalInventoryValue = _context.Stocks
                .Sum(s => (decimal?)s.QuantityAvailable * s.Product.Price) ?? 0;

            var today = DateTime.Today;
            ViewBag.TodayIn = _context.StockTransactions
                .Count(t => t.TransactionDate >= today && t.Type == Models.TransactionType.StockIn);
            ViewBag.TodayOut = _context.StockTransactions
                .Count(t => t.TransactionDate >= today && t.Type == Models.TransactionType.StockOut);

            ViewBag.LowStockItems = _context.Stocks
                .Include(s => s.Product)
                .OrderBy(s => s.QuantityAvailable)
                .Take(5)
                .ToList();

            ViewBag.RecentTransactions = _context.StockTransactions
                .Include(t => t.Product)
                .OrderByDescending(t => t.TransactionDate)
                .Take(5)
                .ToList();

            var categorySummary = _context.Stocks
                .Include(s => s.Product)
                    .ThenInclude(p => p.Category)
                .ToList()
                .GroupBy(s => s.Product.Category?.CategoryName ?? "Uncategorized")
                .Select(g => new CategorySummaryRow
                {
                    CategoryName = g.Key,
                    ProductCount = g.Select(s => s.ProductId).Distinct().Count(),
                    Units = g.Sum(s => s.QuantityAvailable),
                    Value = g.Sum(s => s.QuantityAvailable * s.Product.Price),
                })
                .OrderByDescending(c => c.Value)
                .ToList();

            ViewBag.CategorySummary = categorySummary;

            return View();
        }
    }
}
