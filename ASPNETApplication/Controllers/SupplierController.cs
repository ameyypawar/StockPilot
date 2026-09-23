using Microsoft.AspNetCore.Mvc;
using InventoryManagement.Web.Data;
using InventoryManagement.Web.Models;
using Microsoft.EntityFrameworkCore;
using System.Linq;

namespace InventoryManagement.Web.Controllers
{
    public class SupplierController : Controller
    {
        private readonly ApplicationDbContext _context;

        public SupplierController(ApplicationDbContext context)
        {
            _context = context;
        }

        // GET: Supplier
        public IActionResult Index(string searchTerm)
        {
            var suppliers = _context.Suppliers
                .Include(s => s.Products)
                .AsQueryable();

            if (!string.IsNullOrEmpty(searchTerm))
            {
                suppliers = suppliers.Where(s =>
                    s.SupplierName.Contains(searchTerm) ||
                    (s.ContactNumber != null && s.ContactNumber.Contains(searchTerm)) ||
                    (s.Email != null && s.Email.Contains(searchTerm)) ||
                    (s.Address != null && s.Address.Contains(searchTerm)));
            }

            ViewBag.SearchTerm = searchTerm;
            return View(suppliers.OrderBy(s => s.SupplierName).ToList());
        }

        // GET: Supplier/Create
        public IActionResult Create()
        {
            return View();
        }

        // POST: Supplier/Create
        [HttpPost]
        public IActionResult Create(Supplier supplier)
        {
            if (!ModelState.IsValid)
            {
                return View(supplier);
            }

            _context.Suppliers.Add(supplier);
            _context.SaveChanges();
            TempData["Success"] = $"Supplier '{supplier.SupplierName}' added successfully.";
            return RedirectToAction("Index");
        }

        // GET: Supplier/Edit/5
        public IActionResult Edit(int id)
        {
            var supplier = _context.Suppliers.Find(id);
            if (supplier == null) return NotFound();
            return View(supplier);
        }

        // POST: Supplier/Edit/5
        [HttpPost]
        public IActionResult Edit(Supplier supplier)
        {
            if (!ModelState.IsValid)
            {
                return View(supplier);
            }

            _context.Suppliers.Update(supplier);
            _context.SaveChanges();
            TempData["Success"] = $"Supplier '{supplier.SupplierName}' updated successfully.";
            return RedirectToAction("Index");
        }

        // GET: Supplier/Delete/5
        public IActionResult Delete(int id)
        {
            var supplier = _context.Suppliers
                .Include(s => s.Products)
                .FirstOrDefault(s => s.SupplierId == id);
            if (supplier == null) return NotFound();

            ViewBag.ProductCount = supplier.Products.Count;
            return View(supplier);
        }

        // POST: Supplier/Delete/5
        [HttpPost, ActionName("Delete")]
        public IActionResult DeleteConfirmed(int id)
        {
            var supplier = _context.Suppliers
                .Include(s => s.Products)
                .FirstOrDefault(s => s.SupplierId == id);

            if (supplier == null)
            {
                return RedirectToAction("Index");
            }

            if (supplier.Products.Count > 0)
            {
                TempData["Error"] = $"Cannot delete '{supplier.SupplierName}': {supplier.Products.Count} product(s) use this supplier. Reassign or delete those products first.";
                return RedirectToAction("Index");
            }

            _context.Suppliers.Remove(supplier);
            _context.SaveChanges();
            TempData["Success"] = $"Supplier '{supplier.SupplierName}' deleted successfully.";
            return RedirectToAction("Index");
        }
    }
}
