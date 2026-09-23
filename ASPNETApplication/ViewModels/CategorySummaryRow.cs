namespace InventoryManagement.Web.ViewModels
{
    public class CategorySummaryRow
    {
        public string CategoryName { get; set; } = string.Empty;
        public int ProductCount { get; set; }
        public int Units { get; set; }
        public decimal Value { get; set; }
    }
}
