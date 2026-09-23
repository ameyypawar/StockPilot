using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.AspNetCore.Mvc.ModelBinding.Validation;

namespace InventoryManagement.Web.Models
{
    public class Product
    {
        public int ProductId { get; set; }

        [Required, MaxLength(150)]
        public string ProductName { get; set; } = string.Empty;

        [Column(TypeName = "decimal(10,2)")]
        [Range(0, 9999999)]
        public decimal Price { get; set; }

        [Required, MaxLength(20)]
        public string Unit { get; set; } = "pcs";

        public int CategoryId { get; set; }

        [ValidateNever]
        public Category Category { get; set; } = null!;

        public int SupplierId { get; set; }

        [ValidateNever]
        public Supplier Supplier { get; set; } = null!;

        [ValidateNever]
        public Stock? Stock { get; set; }

        [ValidateNever]
        public ICollection<StockTransaction> Transactions { get; set; } = new List<StockTransaction>();
    }
}
