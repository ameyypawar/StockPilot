using System;

namespace InventoryManagementSystem.Models
{
    public enum TransactionType
    {
        StockIn,
        StockOut
    }

    // Encapsulation: validating setter enforces Quantity > 0.
    public class StockTransaction
    {
        private int _transactionId;
        private int _quantity;

        public int TransactionId
        {
            get => _transactionId;
            set => _transactionId = value;
        }

        public Product Product { get; set; }
        public TransactionType Type { get; set; }

        public int Quantity
        {
            get => _quantity;
            set
            {
                if (value <= 0)
                    throw new ArgumentException("Transaction quantity must be greater than zero.");
                _quantity = value;
            }
        }

        public DateTime TransactionDate { get; set; }
        public string PerformedBy { get; set; } // e.g. Staff name

        public StockTransaction(int transactionId, Product product, TransactionType type, int quantity, string performedBy)
        {
            TransactionId = transactionId;
            Product = product;
            Type = type;
            Quantity = quantity;
            PerformedBy = performedBy;
            TransactionDate = DateTime.Now;
        }

        public override string ToString()
        {
            return $"[{TransactionId}] {TransactionDate:g} | {Type} | {Product?.ProductName} | Qty: {Quantity} | By: {PerformedBy}";
        }
    }
}
