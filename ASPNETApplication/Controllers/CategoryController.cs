using Microsoft.AspNetCore.Mvc;
using InventoryManagement.Web.Data;
using InventoryManagement.Web.Models;
using Microsoft.EntityFrameworkCore;
using System.Linq;

namespace InventoryManagement.Web.Controllers
{
    public class CategoryController : Controller
    {
        private readonly ApplicationDbContext _context;

        public CategoryController(ApplicationDbContext context)
        {
            _context = context;
        }

        // GET: Category
        public IActionResult Index(string searchTerm)
        {
            var categories = _context.Categories
                .Include(c => c.Products)
                .AsQueryable();

            if (!string.IsNullOrEmpty(searchTerm))
            {
                categories = categories.Where(c => c.CategoryName.Contains(searchTerm));
            }

            ViewBag.SearchTerm = searchTerm;
            return View(categories.OrderBy(c => c.CategoryName).ToList());
        }

        // GET: Category/Create
        public IActionResult Create()
        {
            return View();
        }

        // POST: Category/Create
        [HttpPost]
        public IActionResult Create(Category category)
        {
            if (_context.Categories.Any(c => c.CategoryName == category.CategoryName))
            {
                ModelState.AddModelError("CategoryName", "A category with this name already exists.");
            }

            if (!ModelState.IsValid)
            {
                return View(category);
            }

            _context.Categories.Add(category);
            _context.SaveChanges();
            TempData["Success"] = $"Category '{category.CategoryName}' added successfully.";
            return RedirectToAction("Index");
        }

        // GET: Category/Edit/5
        public IActionResult Edit(int id)
        {
            var category = _context.Categories.Find(id);
            if (category == null) return NotFound();
            return View(category);
        }

        // POST: Category/Edit/5
        [HttpPost]
        public IActionResult Edit(Category category)
        {
            if (_context.Categories.Any(c => c.CategoryName == category.CategoryName && c.CategoryId != category.CategoryId))
            {
                ModelState.AddModelError("CategoryName", "A category with this name already exists.");
            }

            if (!ModelState.IsValid)
            {
                return View(category);
            }

            _context.Categories.Update(category);
            _context.SaveChanges();
            TempData["Success"] = $"Category '{category.CategoryName}' updated successfully.";
            return RedirectToAction("Index");
        }

        // GET: Category/Delete/5
        public IActionResult Delete(int id)
        {
            var category = _context.Categories
                .Include(c => c.Products)
                .FirstOrDefault(c => c.CategoryId == id);
            if (category == null) return NotFound();

            ViewBag.ProductCount = category.Products.Count;
            return View(category);
        }

        // POST: Category/Delete/5
        [HttpPost, ActionName("Delete")]
        public IActionResult DeleteConfirmed(int id)
        {
            var category = _context.Categories
                .Include(c => c.Products)
                .FirstOrDefault(c => c.CategoryId == id);

            if (category == null)
            {
                return RedirectToAction("Index");
            }

            if (category.Products.Count > 0)
            {
                TempData["Error"] = $"Cannot delete '{category.CategoryName}': {category.Products.Count} product(s) use this category. Reassign or delete those products first.";
                return RedirectToAction("Index");
            }

            _context.Categories.Remove(category);
            _context.SaveChanges();
            TempData["Success"] = $"Category '{category.CategoryName}' deleted successfully.";
            return RedirectToAction("Index");
        }
    }
}
