using System;

namespace InventoryManagementSystem.Exceptions
{
    // Exception handling: custom exception for a Stock Out that exceeds available quantity.
    public class InsufficientStockException : Exception
    {
        public string ProductName { get; }
        public int Requested { get; }
        public int Available { get; }

        public InsufficientStockException(string productName, int requested, int available)
            : base($"Insufficient stock for '{productName}'. Requested {requested}, available {available}.")
        {
            ProductName = productName;
            Requested = requested;
            Available = available;
        }
    }
}
