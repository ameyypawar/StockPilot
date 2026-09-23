using System;

namespace InventoryManagementSystem.Models
{
    // Encapsulation: validating setter guards QuantityAvailable against negative values.
    public class Stock
    {
        private int _stockId;
        private int _quantityAvailable;
        private int _reorderLevel;

        public int StockId
        {
            get => _stockId;
            set => _stockId = value;
        }

        public Product Product { get; set; }

        public int QuantityAvailable
        {
            get => _quantityAvailable;
            set
            {
                if (value < 0)
                    throw new ArgumentException("Quantity available cannot be negative.");
                _quantityAvailable = value;
            }
        }

        public int ReorderLevel
        {
            get => _reorderLevel;
            set => _reorderLevel = value;
        }

        public Stock(int stockId, Product product, int quantityAvailable, int reorderLevel)
        {
            StockId = stockId;
            Product = product;
            QuantityAvailable = quantityAvailable;
            ReorderLevel = reorderLevel;
        }

        public bool IsLowStock()
        {
            return QuantityAvailable <= ReorderLevel;
        }

        public override string ToString()
        {
            string alert = IsLowStock() ? " ⚠ LOW STOCK" : "";
            return $"[{StockId}] {Product?.ProductName} | Available: {QuantityAvailable} | Reorder Level: {ReorderLevel}{alert}";
        }
    }
}
