using System;

namespace InventoryManagementSystem.Models
{
    // Encapsulation: private fields with a validating property setter.
    public class Category
    {
        private int _categoryId;
        private string _categoryName;

        public int CategoryId
        {
            get => _categoryId;
            set => _categoryId = value;
        }

        public string CategoryName
        {
            get => _categoryName;
            set
            {
                if (string.IsNullOrWhiteSpace(value))
                    throw new ArgumentException("Category name cannot be empty.");
                _categoryName = value;
            }
        }

        public Category(int categoryId, string categoryName)
        {
            CategoryId = categoryId;
            CategoryName = categoryName;
        }

        public override string ToString()
        {
            return $"[{CategoryId}] {CategoryName}";
        }
    }
}
