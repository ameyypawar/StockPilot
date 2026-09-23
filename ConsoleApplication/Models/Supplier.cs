using System;

namespace InventoryManagementSystem.Models
{
    // Encapsulation: private fields with a validating property setter.
    public class Supplier
    {
        private int _supplierId;
        private string _supplierName;
        private string _contactNumber;

        public int SupplierId
        {
            get => _supplierId;
            set => _supplierId = value;
        }

        public string SupplierName
        {
            get => _supplierName;
            set
            {
                if (string.IsNullOrWhiteSpace(value))
                    throw new ArgumentException("Supplier name cannot be empty.");
                _supplierName = value;
            }
        }

        public string ContactNumber
        {
            get => _contactNumber;
            set => _contactNumber = value;
        }

        public Supplier(int supplierId, string supplierName, string contactNumber)
        {
            SupplierId = supplierId;
            SupplierName = supplierName;
            ContactNumber = contactNumber;
        }

        public override string ToString()
        {
            return $"[{SupplierId}] {SupplierName} ({ContactNumber})";
        }
    }
}
