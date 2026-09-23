namespace InventoryManagement.Web.ViewModels
{
    public class InventoryValueRow
    {
        public string ProductName { get; set; } = string.Empty;
        public string? CategoryName { get; set; }
        public string Unit { get; set; } = string.Empty;
        public int Quantity { get; set; }
        public decimal Price { get; set; }
        public decimal Value { get; set; }
    }
}
