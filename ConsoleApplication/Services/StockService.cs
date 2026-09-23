using System;
using System.Collections.Generic;
using System.Linq;
using InventoryManagementSystem.Exceptions;
using InventoryManagementSystem.Models;

namespace InventoryManagementSystem.Services
{
    // Collections: List<Stock>/List<StockTransaction>; Exception handling via InsufficientStockException.
    public class StockService
    {
        private List<Stock> _stocks = new List<Stock>();
        private List<StockTransaction> _transactions = new List<StockTransaction>();
        private int _nextStockId = 1;
        private int _nextTransactionId = 1;

        public void InitializeStock(Product product, int initialQuantity, int reorderLevel)
        {
            Stock stock = new Stock(_nextStockId, product, initialQuantity, reorderLevel);
            _stocks.Add(stock);
            _nextStockId++;
            Console.WriteLine($"Stock initialized for '{product.ProductName}'.");
        }

        public void StockIn(int productId, int quantity, string performedBy)
        {
            if (quantity <= 0)
                throw new ArgumentException("Quantity must be greater than zero.");

            Stock stock = _stocks.FirstOrDefault(s => s.Product.ProductId == productId);
            if (stock == null)
            {
                Console.WriteLine("Stock record not found for this product.");
                return;
            }

            stock.QuantityAvailable += quantity;
            stock.Product.Quantity = stock.QuantityAvailable;

            var transaction = new StockTransaction(_nextTransactionId, stock.Product, TransactionType.StockIn, quantity, performedBy);
            _transactions.Add(transaction);
            _nextTransactionId++;

            Console.WriteLine($"Stock in: {quantity} units added to '{stock.Product.ProductName}'.");
        }

        public void StockOut(int productId, int quantity, string performedBy)
        {
            if (quantity <= 0)
                throw new ArgumentException("Quantity must be greater than zero.");

            Stock stock = _stocks.FirstOrDefault(s => s.Product.ProductId == productId);
            if (stock == null)
            {
                Console.WriteLine("Stock record not found for this product.");
                return;
            }

            if (quantity > stock.QuantityAvailable)
                throw new InsufficientStockException(stock.Product.ProductName, quantity, stock.QuantityAvailable);

            stock.QuantityAvailable -= quantity;
            stock.Product.Quantity = stock.QuantityAvailable;

            var transaction = new StockTransaction(_nextTransactionId, stock.Product, TransactionType.StockOut, quantity, performedBy);
            _transactions.Add(transaction);
            _nextTransactionId++;

            Console.WriteLine($"Stock out: {quantity} units removed from '{stock.Product.ProductName}'.");
        }

        public Stock? GetStock(int productId)
        {
            return _stocks.FirstOrDefault(s => s.Product.ProductId == productId);
        }

        public void RemoveStock(int productId)
        {
            var stock = _stocks.FirstOrDefault(s => s.Product.ProductId == productId);
            if (stock != null)
                _stocks.Remove(stock);
        }

        public void SetQuantity(int productId, int qty)
        {
            var stock = _stocks.FirstOrDefault(s => s.Product.ProductId == productId);
            if (stock != null)
                stock.QuantityAvailable = qty;
        }

        public List<Stock> GetLowStockItems()
        {
            return _stocks.Where(s => s.IsLowStock()).ToList();
        }

        public List<StockTransaction> GetAllTransactions()
        {
            return _transactions;
        }

        public void DisplayAllStock()
        {
            if (_stocks.Count == 0)
            {
                Console.WriteLine("No stock records available.");
                return;
            }

            foreach (var stock in _stocks)
            {
                Console.WriteLine(stock.ToString());
            }
        }

        public void DisplayTransactionHistory()
        {
            if (_transactions.Count == 0)
            {
                Console.WriteLine("No transactions recorded yet.");
                return;
            }

            foreach (var t in _transactions)
            {
                Console.WriteLine(t.ToString());
            }
        }
    }
}
