using System;
using System.Linq;
using InventoryManagementSystem.Data;
using InventoryManagementSystem.Exceptions;
using InventoryManagementSystem.Models;
using InventoryManagementSystem.Reports;
using InventoryManagementSystem.Services;
using InventoryManagementSystem.Utilities;

namespace InventoryManagementSystem
{
    class Program
    {
        static ProductService productService = new ProductService();
        static StockService stockService = new StockService();
        static MasterDataService masterData = new MasterDataService();
        static UserService userService = new UserService();
        static ReportService reportService;

        static void Main(string[] args)
        {
            reportService = new ReportService(productService, stockService);

            Console.WriteLine("=============================================");
            Console.WriteLine("  StockPilot - Inventory Management System");
            Console.WriteLine("=============================================");

            SampleData.Seed(productService, stockService, masterData);

            if (!Login())
            {
                return;
            }

            bool running = true;
            while (running)
            {
                Console.WriteLine("\n===== MAIN MENU =====");
                Console.WriteLine($"Logged in as: {userService.CurrentUser?.Name} ({RoleName()})");
                Console.WriteLine("1. Product Management");
                Console.WriteLine("2. Stock Management");
                Console.WriteLine("3. Reports");
                Console.WriteLine("4. View Users");
                Console.WriteLine("5. Exit");
                Console.Write("Enter your choice: ");

                string choice = InputHelper.ReadLine();

                switch (choice)
                {
                    case "1":
                        ProductMenu();
                        break;
                    case "2":
                        StockMenu();
                        break;
                    case "3":
                        ReportsMenu();
                        break;
                    case "4":
                        userService.DisplayAllUsers();
                        break;
                    case "5":
                        running = false;
                        Console.WriteLine("Goodbye!");
                        break;
                    default:
                        Console.WriteLine("Invalid choice. Try again.");
                        break;
                }
            }
        }

        // ---------------- LOGIN ----------------
        static bool Login()
        {
            for (int attempt = 1; attempt <= 3; attempt++)
            {
                Console.Write("Login - enter username (admin/staff/viewer): ");
                string username = InputHelper.ReadLine();
                var user = userService.Login(username.Trim());
                if (user != null)
                {
                    Console.WriteLine($"Welcome, {user.Name}!");
                    return true;
                }
                Console.WriteLine("Invalid username. Please try again.");
            }
            Console.WriteLine("Too many failed login attempts. Exiting.");
            return false;
        }

        static string RoleName()
        {
            return userService.CurrentUser switch
            {
                Admin => "Admin",
                Staff => "Staff",
                User => "Viewer",
                _ => "Unknown"
            };
        }

        // ---------------- PRODUCT MENU ----------------
        static void ProductMenu()
        {
            bool back = false;
            while (!back)
            {
                Console.WriteLine("\n----- Product Management -----");
                Console.WriteLine("1. Add Product");
                Console.WriteLine("2. Update Product");
                Console.WriteLine("3. Delete Product");
                Console.WriteLine("4. Search Product");
                Console.WriteLine("5. View All Products");
                Console.WriteLine("6. Back to Main Menu");
                Console.Write("Enter your choice: ");

                string choice = InputHelper.ReadLine();

                try
                {
                    switch (choice)
                    {
                        case "1":
                            if (!userService.CanModify)
                            {
                                Console.WriteLine("Access denied: viewers cannot modify data.");
                                break;
                            }
                            AddProductFlow();
                            break;

                        case "2":
                            if (!userService.CanModify)
                            {
                                Console.WriteLine("Access denied: viewers cannot modify data.");
                                break;
                            }
                            UpdateProductFlow();
                            break;

                        case "3":
                            if (!userService.CanModify)
                            {
                                Console.WriteLine("Access denied: viewers cannot modify data.");
                                break;
                            }
                            DeleteProductFlow();
                            break;

                        case "4":
                            Console.Write("Enter search keyword: ");
                            string keyword = InputHelper.ReadLine();
                            var results = productService.SearchProduct(keyword);
                            if (results.Count == 0)
                                Console.WriteLine("No matching products found.");
                            else
                                results.ForEach(p => Console.WriteLine(p.ToString()));
                            break;

                        case "5":
                            productService.DisplayAllProducts();
                            break;

                        case "6":
                            back = true;
                            break;

                        default:
                            Console.WriteLine("Invalid choice.");
                            break;
                    }
                }
                catch (FormatException)
                {
                    Console.WriteLine("Invalid input format. Please enter the correct data type.");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"An error occurred: {ex.Message}");
                }
            }
        }

        static void AddProductFlow()
        {
            Console.Write("Enter product name: ");
            string name = InputHelper.ReadLine();
            Console.Write("Enter price: ");
            decimal price = Convert.ToDecimal(InputHelper.ReadLine());
            Console.Write("Enter quantity: ");
            int qty = Convert.ToInt32(InputHelper.ReadLine());
            Console.Write("Enter reorder level for this product: ");
            int reorderLevel = Convert.ToInt32(InputHelper.ReadLine());

            Console.WriteLine("\nExisting categories:");
            foreach (var c in masterData.GetAllCategories())
                Console.WriteLine("  " + c.ToString());
            Console.Write("Enter category name (existing or new): ");
            string categoryName = InputHelper.ReadLine();

            Console.WriteLine("\nExisting suppliers:");
            foreach (var s in masterData.GetAllSuppliers())
                Console.WriteLine("  " + s.ToString());
            Console.Write("Enter supplier name (existing or new): ");
            string supplierName = InputHelper.ReadLine();

            Category category = masterData.GetOrCreateCategory(categoryName);
            Supplier supplier = masterData.GetOrCreateSupplier(supplierName);

            productService.AddProduct(name, price, qty, category, supplier);

            var addedProduct = productService.GetAllProducts()[^1];
            stockService.InitializeStock(addedProduct, qty, reorderLevel);

            Console.WriteLine("\n----- Product Added Successfully -----");
            Console.WriteLine(addedProduct.ToString());
            Console.WriteLine("---------------------------------------");
        }

        static void UpdateProductFlow()
        {
            var allProducts = productService.GetAllProducts();
            if (allProducts.Count == 0)
            {
                Console.WriteLine("No products available to update.");
                return;
            }

            Console.WriteLine("\n----- Select Product to Update -----");
            foreach (var p in allProducts)
                Console.WriteLine(p.ToString());
            Console.Write("\nEnter product ID to update: ");
            int updateId = Convert.ToInt32(InputHelper.ReadLine());

            var productToUpdate = productService.GetById(updateId);
            if (productToUpdate == null)
            {
                Console.WriteLine("Product not found.");
                return;
            }

            Console.WriteLine($"\nCurrent details: {productToUpdate.ToString()}");

            Console.Write($"Enter new name (leave blank to keep '{productToUpdate.ProductName}'): ");
            string newName = InputHelper.ReadLine();
            if (string.IsNullOrWhiteSpace(newName)) newName = productToUpdate.ProductName;

            Console.Write($"Enter new price (leave blank to keep {productToUpdate.Price}): ");
            string priceInput = InputHelper.ReadLine();
            decimal newPrice = string.IsNullOrWhiteSpace(priceInput) ? productToUpdate.Price : Convert.ToDecimal(priceInput);

            Console.Write($"Enter new quantity (leave blank to keep {productToUpdate.Quantity}): ");
            string qtyInput = InputHelper.ReadLine();
            int newQty = string.IsNullOrWhiteSpace(qtyInput) ? productToUpdate.Quantity : Convert.ToInt32(qtyInput);

            Console.Write($"Enter new category (leave blank to keep '{productToUpdate.Category?.CategoryName}'): ");
            string newCategoryName = InputHelper.ReadLine();
            Category newCategory = string.IsNullOrWhiteSpace(newCategoryName)
                ? productToUpdate.Category
                : masterData.GetOrCreateCategory(newCategoryName);

            Console.Write($"Enter new supplier (leave blank to keep '{productToUpdate.Supplier?.SupplierName}'): ");
            string newSupplierName = InputHelper.ReadLine();
            Supplier newSupplier = string.IsNullOrWhiteSpace(newSupplierName)
                ? productToUpdate.Supplier
                : masterData.GetOrCreateSupplier(newSupplierName);

            productService.UpdateProduct(updateId, newName, newPrice, newQty, newCategory, newSupplier);
            stockService.SetQuantity(updateId, newQty);

            Console.WriteLine("\n----- Updated Product -----");
            Console.WriteLine(productToUpdate.ToString());
            Console.WriteLine("----------------------------");
        }

        static void DeleteProductFlow()
        {
            var productsForDelete = productService.GetAllProducts();
            if (productsForDelete.Count == 0)
            {
                Console.WriteLine("No products available to delete.");
                return;
            }

            Console.WriteLine("\n----- Select Product to Delete -----");
            foreach (var p in productsForDelete)
                Console.WriteLine(p.ToString());
            Console.Write("\nEnter product ID to delete: ");
            int deleteId = Convert.ToInt32(InputHelper.ReadLine());

            if (productService.DeleteProduct(deleteId))
                stockService.RemoveStock(deleteId);
        }

        // ---------------- STOCK MENU ----------------
        static void StockMenu()
        {
            bool back = false;
            while (!back)
            {
                Console.WriteLine("\n----- Stock Management -----");
                Console.WriteLine("1. Stock In");
                Console.WriteLine("2. Stock Out");
                Console.WriteLine("3. View All Stock");
                Console.WriteLine("4. View Transaction History");
                Console.WriteLine("5. Back to Main Menu");
                Console.Write("Enter your choice: ");

                string choice = InputHelper.ReadLine();

                try
                {
                    switch (choice)
                    {
                        case "1":
                            stockService.DisplayAllStock();
                            Console.Write("\nEnter product ID to stock in: ");
                            int inId = Convert.ToInt32(InputHelper.ReadLine());
                            Console.Write("Enter quantity to add: ");
                            int inQty = Convert.ToInt32(InputHelper.ReadLine());
                            Console.Write("Performed by (blank = current user): ");
                            string inBy = InputHelper.ReadLine();
                            if (string.IsNullOrWhiteSpace(inBy)) inBy = userService.CurrentUser?.Name ?? "Unknown";
                            stockService.StockIn(inId, inQty, inBy);
                            break;

                        case "2":
                            stockService.DisplayAllStock();
                            Console.Write("\nEnter product ID to stock out: ");
                            int outId = Convert.ToInt32(InputHelper.ReadLine());
                            Console.Write("Enter quantity to remove: ");
                            int outQty = Convert.ToInt32(InputHelper.ReadLine());
                            Console.Write("Performed by (blank = current user): ");
                            string outBy = InputHelper.ReadLine();
                            if (string.IsNullOrWhiteSpace(outBy)) outBy = userService.CurrentUser?.Name ?? "Unknown";
                            stockService.StockOut(outId, outQty, outBy);
                            break;

                        case "3":
                            stockService.DisplayAllStock();
                            break;

                        case "4":
                            stockService.DisplayTransactionHistory();
                            break;

                        case "5":
                            back = true;
                            break;

                        default:
                            Console.WriteLine("Invalid choice.");
                            break;
                    }
                }
                catch (InsufficientStockException ex)
                {
                    Console.WriteLine(ex.Message);
                }
                catch (FormatException)
                {
                    Console.WriteLine("Invalid input format. Please enter the correct data type.");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"An error occurred: {ex.Message}");
                }
            }
        }

        // ---------------- REPORTS MENU ----------------
        static void ReportsMenu()
        {
            bool back = false;
            while (!back)
            {
                Console.WriteLine("\n----- Reports -----");
                Console.WriteLine("1. Product Catalog Report");
                Console.WriteLine("2. Stock Summary Report");
                Console.WriteLine("3. Low Stock Report");
                Console.WriteLine("4. Transaction History Report");
                Console.WriteLine("5. Inventory Value Report");
                Console.WriteLine("6. Category-wise Summary");
                Console.WriteLine("7. Back to Main Menu");
                Console.Write("Enter your choice: ");

                string choice = InputHelper.ReadLine();

                switch (choice)
                {
                    case "1":
                        reportService.GenerateProductCatalogReport();
                        break;
                    case "2":
                        reportService.GenerateStockSummaryReport();
                        break;
                    case "3":
                        reportService.GenerateLowStockReport();
                        break;
                    case "4":
                        reportService.GenerateTransactionReport();
                        break;
                    case "5":
                        reportService.GenerateInventoryValueReport();
                        break;
                    case "6":
                        reportService.GenerateCategoryWiseReport();
                        break;
                    case "7":
                        back = true;
                        break;
                    default:
                        Console.WriteLine("Invalid choice.");
                        break;
                }
            }
        }
    }
}
