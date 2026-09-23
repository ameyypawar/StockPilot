namespace InventoryManagement.Web.Models
{
    public static class StockStatus
    {
        public const string Ok = "OK";
        public const string Low = "Low";
        public const string Out = "Out";

        public static string For(int qty, int reorder)
        {
            if (qty <= 0) return Out;
            if (qty <= reorder) return Low;
            return Ok;
        }

        public static string BadgeCss(string status)
        {
            return status switch
            {
                Out => "bg-danger",
                Low => "bg-warning text-dark",
                _ => "bg-success",
            };
        }
    }
}
