using System;
using System.Collections.Generic;
using System.Linq;
using InventoryManagementSystem.Models;

namespace InventoryManagementSystem.Services
{
    // Collections: List<Product> backing store; Search module; Exception handling on add/update.
    public class ProductService
    {
        private List<Product> _products = new List<Product>();
        private int _nextId = 1;

        public void AddProduct(string name, decimal price, int quantity, Category category, Supplier supplier)
        {
            try
            {
                Product product = new Product(_nextId, name, price, quantity, category, supplier);
                _products.Add(product);
                _nextId++;
                Console.WriteLine($"Product '{name}' added successfully.");
            }
            catch (ArgumentException ex)
            {
                Console.WriteLine($"Error adding product: {ex.Message}");
            }
        }

        public void UpdateProduct(int productId, string name, decimal price, int quantity, Category category, Supplier supplier)
        {
            try
            {
                Product product = _products.FirstOrDefault(p => p.ProductId == productId);
                if (product == null)
                {
                    Console.WriteLine("Product not found.");
                    return;
                }

                product.ProductName = name;
                product.Price = price;
                product.Quantity = quantity;
                product.Category = category;
                product.Supplier = supplier;
                Console.WriteLine($"Product '{name}' updated successfully.");
            }
            catch (ArgumentException ex)
            {
                Console.WriteLine($"Error updating product: {ex.Message}");
            }
        }

        public bool DeleteProduct(int productId)
        {
            Product product = _products.FirstOrDefault(p => p.ProductId == productId);
            if (product == null)
            {
                Console.WriteLine("Product not found.");
                return false;
            }

            _products.Remove(product);
            Console.WriteLine($"Product '{product.ProductName}' deleted successfully.");
            return true;
        }

        public Product? GetById(int productId)
        {
            return _products.FirstOrDefault(p => p.ProductId == productId);
        }

        public List<Product> SearchProduct(string keyword)
        {
            string k = keyword.ToLower();
            return _products
                .Where(p => p.ProductName.ToLower().Contains(k)
                    || (p.Category?.CategoryName.ToLower().Contains(k) ?? false)
                    || (p.Supplier?.SupplierName.ToLower().Contains(k) ?? false))
                .ToList();
        }

        public List<Product> GetAllProducts()
        {
            return _products;
        }

        public void DisplayAllProducts()
        {
            if (_products.Count == 0)
            {
                Console.WriteLine("No products available.");
                return;
            }

            foreach (var product in _products)
            {
                Console.WriteLine(product.ToString());
            }
        }
    }
}
