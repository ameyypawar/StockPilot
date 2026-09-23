using Microsoft.AspNetCore.Mvc;
using InventoryManagement.Web.Data;
using InventoryManagement.Web.Models;
using Microsoft.EntityFrameworkCore;
using System;
using System.Linq;

namespace InventoryManagement.Web.Controllers
{
    public class StockController : Controller
    {
        private readonly ApplicationDbContext _context;

        public StockController(ApplicationDbContext context)
        {
            _context = context;
        }

        // GET: Stock - shows current stock levels for all products
        public IActionResult Index(string searchTerm, string status)
        {
            var stocks = _context.Stocks
                .Include(s => s.Product)
                    .ThenInclude(p => p.Category)
                .AsQueryable();

            if (!string.IsNullOrEmpty(searchTerm))
            {
                stocks = stocks.Where(s => s.Product.ProductName.Contains(searchTerm));
            }

            var list = stocks.OrderBy(s => s.Product.ProductName).ToList();

            if (!string.IsNullOrEmpty(status))
            {
                list = list.Where(s => StockStatus.For(s.QuantityAvailable, s.ReorderLevel) == status).ToList();
            }

            ViewBag.SearchTerm = searchTerm;
            ViewBag.Status = status;
            return View(list);
        }

        // GET: Stock/Initialize - set up stock tracking for a product that doesn't have it yet
        public IActionResult Initialize()
        {
            var productsWithoutStock = _context.Products
                .Where(p => !_context.Stocks.Any(s => s.ProductId == p.ProductId))
                .OrderBy(p => p.ProductName)
                .ToList();

            ViewBag.Products = productsWithoutStock;
            return View();
        }

        [HttpPost]
        public IActionResult Initialize(int productId, int quantityAvailable, int reorderLevel)
        {
            if (_context.Stocks.Any(s => s.ProductId == productId))
            {
                ViewBag.Error = "This product already has a stock record.";
                ViewBag.Products = _context.Products
                    .Where(p => !_context.Stocks.Any(s => s.ProductId == p.ProductId))
                    .OrderBy(p => p.ProductName)
                    .ToList();
                return View();
            }

            if (quantityAvailable < 0 || reorderLevel < 0)
            {
                ViewBag.Error = "Quantity and reorder level cannot be negative.";
                ViewBag.Products = _context.Products
                    .Where(p => !_context.Stocks.Any(s => s.ProductId == p.ProductId))
                    .OrderBy(p => p.ProductName)
                    .ToList();
                return View();
            }

            var stock = new Stock
            {
                ProductId = productId,
                QuantityAvailable = quantityAvailable,
                ReorderLevel = reorderLevel,
                LastUpdated = DateTime.Now,
            };
            _context.Stocks.Add(stock);
            _context.SaveChanges();
            TempData["Success"] = "Stock initialized successfully.";
            return RedirectToAction("Index");
        }

        // GET: Stock/StockIn
        public IActionResult StockIn(int? productId)
        {
            ViewBag.Stocks = _context.Stocks.Include(s => s.Product).OrderBy(s => s.Product.ProductName).ToList();
            ViewBag.SelectedProductId = productId;
            return View();
        }

        [HttpPost]
        public IActionResult StockIn(int productId, int quantity, string performedBy, string? remarks)
        {
            if (quantity <= 0)
            {
                ViewBag.Error = "Quantity must be greater than zero.";
                ViewBag.Stocks = _context.Stocks.Include(s => s.Product).OrderBy(s => s.Product.ProductName).ToList();
                ViewBag.SelectedProductId = productId;
                return View();
            }

            var stock = _context.Stocks.FirstOrDefault(s => s.ProductId == productId);
            if (stock == null)
            {
                ViewBag.Error = "Stock record not found for this product.";
                ViewBag.Stocks = _context.Stocks.Include(s => s.Product).OrderBy(s => s.Product.ProductName).ToList();
                ViewBag.SelectedProductId = productId;
                return View();
            }

            stock.QuantityAvailable += quantity;
            stock.LastUpdated = DateTime.Now;

            var transaction = new StockTransaction
            {
                ProductId = productId,
                Type = TransactionType.StockIn,
                Quantity = quantity,
                PerformedBy = string.IsNullOrWhiteSpace(performedBy) ? (HttpContext.Session.GetString("Username") ?? "admin") : performedBy,
                Remarks = remarks,
            };
            _context.StockTransactions.Add(transaction);

            try
            {
                _context.SaveChanges();
            }
            catch (DbUpdateException)
            {
                ViewBag.Error = "Could not save this stock movement.";
                ViewBag.Stocks = _context.Stocks.Include(s => s.Product).OrderBy(s => s.Product.ProductName).ToList();
                ViewBag.SelectedProductId = productId;
                return View();
            }

            TempData["Success"] = "Stock in recorded successfully.";
            return RedirectToAction("Index");
        }

        // GET: Stock/StockOut
        public IActionResult StockOut(int? productId)
        {
            ViewBag.Stocks = _context.Stocks.Include(s => s.Product).OrderBy(s => s.Product.ProductName).ToList();
            ViewBag.SelectedProductId = productId;
            return View();
        }

        [HttpPost]
        public IActionResult StockOut(int productId, int quantity, string performedBy, string? remarks)
        {
            if (quantity <= 0)
            {
                ViewBag.Error = "Quantity must be greater than zero.";
                ViewBag.Stocks = _context.Stocks.Include(s => s.Product).OrderBy(s => s.Product.ProductName).ToList();
                ViewBag.SelectedProductId = productId;
                return View();
            }

            var stock = _context.Stocks.FirstOrDefault(s => s.ProductId == productId);
            if (stock == null)
            {
                ViewBag.Error = "Stock record not found for this product.";
                ViewBag.Stocks = _context.Stocks.Include(s => s.Product).OrderBy(s => s.Product.ProductName).ToList();
                ViewBag.SelectedProductId = productId;
                return View();
            }

            if (quantity > stock.QuantityAvailable)
            {
                ViewBag.Error = $"Insufficient stock. Available: {stock.QuantityAvailable}";
                ViewBag.Stocks = _context.Stocks.Include(s => s.Product).OrderBy(s => s.Product.ProductName).ToList();
                ViewBag.SelectedProductId = productId;
                return View();
            }

            stock.QuantityAvailable -= quantity;
            stock.LastUpdated = DateTime.Now;

            var transaction = new StockTransaction
            {
                ProductId = productId,
                Type = TransactionType.StockOut,
                Quantity = quantity,
                PerformedBy = string.IsNullOrWhiteSpace(performedBy) ? (HttpContext.Session.GetString("Username") ?? "admin") : performedBy,
                Remarks = remarks,
            };
            _context.StockTransactions.Add(transaction);

            try
            {
                _context.SaveChanges();
            }
            catch (DbUpdateException)
            {
                ViewBag.Error = "Could not save this stock movement.";
                ViewBag.Stocks = _context.Stocks.Include(s => s.Product).OrderBy(s => s.Product.ProductName).ToList();
                ViewBag.SelectedProductId = productId;
                return View();
            }

            TempData["Success"] = "Stock out recorded successfully.";
            return RedirectToAction("Index");
        }

        // GET: Stock/Transactions - view transaction history
        public IActionResult Transactions(string type)
        {
            var transactions = _context.StockTransactions
                .Include(t => t.Product)
                .OrderByDescending(t => t.TransactionDate)
                .AsQueryable();

            if (!string.IsNullOrEmpty(type) && Enum.TryParse<TransactionType>(type, out var parsedType))
            {
                transactions = transactions.Where(t => t.Type == parsedType);
            }

            ViewBag.SelectedType = type;
            return View(transactions.ToList());
        }
    }
}
