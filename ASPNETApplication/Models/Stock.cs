using System;
using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Mvc.ModelBinding.Validation;

namespace InventoryManagement.Web.Models
{
    public class Stock
    {
        public int StockId { get; set; }

        public int ProductId { get; set; }

        [ValidateNever]
        public Product Product { get; set; } = null!;

        [Range(0, int.MaxValue)]
        public int QuantityAvailable { get; set; }

        [Range(0, int.MaxValue)]
        public int ReorderLevel { get; set; }

        public DateTime LastUpdated { get; set; } = DateTime.Now;
    }
}
