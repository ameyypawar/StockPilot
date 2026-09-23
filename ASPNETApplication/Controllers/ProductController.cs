using Microsoft.AspNetCore.Mvc;
using InventoryManagement.Web.Data;
using InventoryManagement.Web.Models;
using Microsoft.EntityFrameworkCore;
using System;
using System.Linq;

namespace InventoryManagement.Web.Controllers
{
    public class ProductController : Controller
    {
        private readonly ApplicationDbContext _context;

        public ProductController(ApplicationDbContext context)
        {
            _context = context;
        }

        // GET: Product
        public IActionResult Index(string searchTerm, int? categoryId)
        {
            var products = _context.Products
                .Include(p => p.Category)
                .Include(p => p.Supplier)
                .Include(p => p.Stock)
                .AsQueryable();

            if (!string.IsNullOrEmpty(searchTerm))
            {
                products = products.Where(p =>
                    p.ProductName.Contains(searchTerm) ||
                    (p.Category != null && p.Category.CategoryName.Contains(searchTerm)) ||
                    (p.Supplier != null && p.Supplier.SupplierName.Contains(searchTerm)));
            }

            if (categoryId.HasValue)
            {
                products = products.Where(p => p.CategoryId == categoryId.Value);
            }

            ViewBag.SearchTerm = searchTerm;
            ViewBag.CategoryId = categoryId;
            ViewBag.Categories = _context.Categories.OrderBy(c => c.CategoryName).ToList();

            return View(products.OrderBy(p => p.ProductName).ToList());
        }

        // GET: Product/Create
        public IActionResult Create()
        {
            LoadDropdowns();
            return View();
        }

        // POST: Product/Create
        [HttpPost]
        public IActionResult Create(Product product, int openingQuantity = 0, int reorderLevel = 10)
        {
            if (openingQuantity < 0)
            {
                ModelState.AddModelError(string.Empty, "Opening quantity cannot be negative.");
            }
            if (reorderLevel < 0)
            {
                ModelState.AddModelError(string.Empty, "Reorder level cannot be negative.");
            }

            if (!ModelState.IsValid)
            {
                LoadDropdowns();
                return View(product);
            }

            _context.Products.Add(product);

            var stock = new Stock
            {
                Product = product,
                QuantityAvailable = openingQuantity,
                ReorderLevel = reorderLevel,
                LastUpdated = DateTime.Now,
            };
            _context.Stocks.Add(stock);

            if (openingQuantity > 0)
            {
                var performedBy = HttpContext.Session.GetString("Username") ?? "admin";
                var transaction = new StockTransaction
                {
                    Product = product,
                    Type = TransactionType.StockIn,
                    Quantity = openingQuantity,
                    PerformedBy = performedBy,
                    Remarks = "Opening stock",
                };
                _context.StockTransactions.Add(transaction);
            }

            _context.SaveChanges();
            TempData["Success"] = $"Product '{product.ProductName}' added successfully.";
            return RedirectToAction("Index");
        }

        // GET: Product/Edit/5
        public IActionResult Edit(int id)
        {
            var product = _context.Products.Find(id);
            if (product == null) return NotFound();
            LoadDropdowns();
            return View(product);
        }

        // POST: Product/Edit/5
        [HttpPost]
        public IActionResult Edit(int id, Product product)
        {
            if (id != product.ProductId || !ModelState.IsValid)
            {
                LoadDropdowns();
                return View(product);
            }

            _context.Products.Update(product);
            _context.SaveChanges();
            TempData["Success"] = $"Product '{product.ProductName}' updated successfully.";
            return RedirectToAction("Index");
        }

        // GET: Product/Delete/5
        public IActionResult Delete(int id)
        {
            var product = _context.Products
                .Include(p => p.Stock)
                .FirstOrDefault(p => p.ProductId == id);
            if (product == null) return NotFound();

            ViewBag.TransactionCount = _context.StockTransactions.Count(t => t.ProductId == id);
            ViewBag.StockQuantity = product.Stock?.QuantityAvailable ?? 0;
            return View(product);
        }

        // POST: Product/Delete/5
        [HttpPost, ActionName("Delete")]
        public IActionResult DeleteConfirmed(int id)
        {
            var product = _context.Products.Find(id);
            if (product != null)
            {
                _context.Products.Remove(product);
                _context.SaveChanges();
                TempData["Success"] = $"Product '{product.ProductName}' deleted successfully.";
            }
            return RedirectToAction("Index");
        }

        private void LoadDropdowns()
        {
            ViewBag.Categories = _context.Categories.OrderBy(c => c.CategoryName).ToList();
            ViewBag.Suppliers = _context.Suppliers.OrderBy(s => s.SupplierName).ToList();
        }
    }
}
