using Microsoft.AspNetCore.Mvc;
using InventoryManagement.Web.Data;
using InventoryManagement.Web.Models;
using InventoryManagement.Web.ViewModels;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;

namespace InventoryManagement.Web.Controllers
{
    public class ReportController : Controller
    {
        private readonly ApplicationDbContext _context;

        public ReportController(ApplicationDbContext context)
        {
            _context = context;
        }

        // GET: Report - main reports menu
        public IActionResult Index()
        {
            return View();
        }

        private void LoadFilterDropdowns()
        {
            ViewBag.Categories = _context.Categories.OrderBy(c => c.CategoryName).ToList();
            ViewBag.Suppliers = _context.Suppliers.OrderBy(s => s.SupplierName).ToList();
        }

        // GET: Report/ProductCatalog
        public IActionResult ProductCatalog(string searchTerm, int? categoryId, int? supplierId)
        {
            LoadFilterDropdowns();

            var products = _context.Products
                .Include(p => p.Category)
                .Include(p => p.Supplier)
                .AsQueryable();

            if (!string.IsNullOrEmpty(searchTerm))
            {
                products = products.Where(p => p.ProductName.Contains(searchTerm));
            }
            if (categoryId.HasValue)
            {
                products = products.Where(p => p.CategoryId == categoryId.Value);
            }
            if (supplierId.HasValue)
            {
                products = products.Where(p => p.SupplierId == supplierId.Value);
            }

            ViewBag.SearchTerm = searchTerm;
            ViewBag.CategoryId = categoryId;
            ViewBag.SupplierId = supplierId;
            ViewBag.FilterSummary = BuildFilterSummary(searchTerm, categoryId, supplierId, null, null, null, null);

            return View(products.OrderBy(p => p.ProductName).ToList());
        }

        // GET: Report/StockSummary
        public IActionResult StockSummary(int? categoryId, string status)
        {
            LoadFilterDropdowns();

            var stocks = _context.Stocks
                .Include(s => s.Product)
                    .ThenInclude(p => p.Category)
                .AsQueryable();

            if (categoryId.HasValue)
            {
                stocks = stocks.Where(s => s.Product.CategoryId == categoryId.Value);
            }

            var list = stocks.OrderBy(s => s.Product.ProductName).ToList();

            if (!string.IsNullOrEmpty(status))
            {
                list = list.Where(s => StockStatus.For(s.QuantityAvailable, s.ReorderLevel) == status).ToList();
            }

            ViewBag.CategoryId = categoryId;
            ViewBag.Status = status;
            ViewBag.FilterSummary = BuildFilterSummary(null, categoryId, null, status, null, null, null);

            return View(list);
        }

        // GET: Report/LowStock
        public IActionResult LowStock(int? supplierId)
        {
            LoadFilterDropdowns();

            var lowStock = _context.Stocks
                .Include(s => s.Product)
                    .ThenInclude(p => p.Supplier)
                .Where(s => s.QuantityAvailable <= s.ReorderLevel)
                .AsQueryable();

            if (supplierId.HasValue)
            {
                lowStock = lowStock.Where(s => s.Product.SupplierId == supplierId.Value);
            }

            ViewBag.SupplierId = supplierId;
            ViewBag.FilterSummary = BuildFilterSummary(null, null, supplierId, null, null, null, null);

            return View(lowStock.OrderBy(s => s.QuantityAvailable).ToList());
        }

        // GET: Report/TransactionHistory
        public IActionResult TransactionHistory(string type, DateTime? from, DateTime? to, string searchTerm)
        {
            LoadFilterDropdowns();

            var transactions = _context.StockTransactions
                .Include(t => t.Product)
                .OrderByDescending(t => t.TransactionDate)
                .AsQueryable();

            if (!string.IsNullOrEmpty(type) && Enum.TryParse<TransactionType>(type, out var parsedType))
            {
                transactions = transactions.Where(t => t.Type == parsedType);
            }

            if (from.HasValue)
            {
                transactions = transactions.Where(t => t.TransactionDate >= from.Value.Date);
            }
            if (to.HasValue)
            {
                var toInclusive = to.Value.Date.AddDays(1);
                transactions = transactions.Where(t => t.TransactionDate < toInclusive);
            }
            if (!string.IsNullOrEmpty(searchTerm))
            {
                transactions = transactions.Where(t => t.Product.ProductName.Contains(searchTerm));
            }

            ViewBag.SelectedType = type;
            ViewBag.From = from;
            ViewBag.To = to;
            ViewBag.SearchTerm = searchTerm;
            ViewBag.FilterSummary = BuildFilterSummary(searchTerm, null, null, null, type, from, to);

            return View(transactions.ToList());
        }

        // GET: Report/InventoryValue
        public IActionResult InventoryValue(int? categoryId)
        {
            LoadFilterDropdowns();

            var stocks = _context.Stocks
                .Include(s => s.Product)
                    .ThenInclude(p => p.Category)
                .AsQueryable();

            if (categoryId.HasValue)
            {
                stocks = stocks.Where(s => s.Product.CategoryId == categoryId.Value);
            }

            var rows = stocks
                .ToList()
                .Select(s => new InventoryValueRow
                {
                    ProductName = s.Product.ProductName,
                    CategoryName = s.Product.Category?.CategoryName,
                    Unit = s.Product.Unit,
                    Quantity = s.QuantityAvailable,
                    Price = s.Product.Price,
                    Value = s.QuantityAvailable * s.Product.Price,
                })
                .OrderBy(r => r.ProductName)
                .ToList();

            ViewBag.CategoryId = categoryId;
            ViewBag.TotalValue = rows.Sum(r => r.Value);
            ViewBag.FilterSummary = BuildFilterSummary(null, categoryId, null, null, null, null, null);

            return View(rows);
        }

        private string BuildFilterSummary(string? searchTerm, int? categoryId, int? supplierId, string? status, string? type, DateTime? from, DateTime? to)
        {
            var parts = new List<string>();

            if (!string.IsNullOrEmpty(searchTerm)) parts.Add($"Search: \"{searchTerm}\"");
            if (categoryId.HasValue)
            {
                var name = _context.Categories.FirstOrDefault(c => c.CategoryId == categoryId.Value)?.CategoryName;
                parts.Add($"Category: {name}");
            }
            if (supplierId.HasValue)
            {
                var name = _context.Suppliers.FirstOrDefault(s => s.SupplierId == supplierId.Value)?.SupplierName;
                parts.Add($"Supplier: {name}");
            }
            if (!string.IsNullOrEmpty(status)) parts.Add($"Status: {status}");
            if (!string.IsNullOrEmpty(type)) parts.Add($"Type: {type}");
            if (from.HasValue) parts.Add($"From: {from.Value:d}");
            if (to.HasValue) parts.Add($"To: {to.Value:d}");

            return parts.Count == 0 ? "All records" : string.Join(" | ", parts);
        }
    }
}
