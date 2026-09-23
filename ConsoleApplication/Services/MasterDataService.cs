using System;
using System.Collections.Generic;
using InventoryManagementSystem.Models;

namespace InventoryManagementSystem.Services
{
    // Collections: case-insensitive Dictionary<string, Category/Supplier> master lookups.
    public class MasterDataService
    {
        private readonly Dictionary<string, Category> _categories = new(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, Supplier> _suppliers = new(StringComparer.OrdinalIgnoreCase);
        private int _nextCategoryId = 1;
        private int _nextSupplierId = 1;

        public Category GetOrCreateCategory(string name)
        {
            if (_categories.TryGetValue(name, out var existing))
                return existing;

            var category = new Category(_nextCategoryId++, name);
            _categories[name] = category;
            return category;
        }

        public Supplier GetOrCreateSupplier(string name, string contact = "0000000000")
        {
            if (_suppliers.TryGetValue(name, out var existing))
                return existing;

            var supplier = new Supplier(_nextSupplierId++, name, contact);
            _suppliers[name] = supplier;
            return supplier;
        }

        public List<Category> GetAllCategories()
        {
            return new List<Category>(_categories.Values);
        }

        public List<Supplier> GetAllSuppliers()
        {
            return new List<Supplier>(_suppliers.Values);
        }
    }
}
