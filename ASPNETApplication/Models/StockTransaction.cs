using System;
using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Mvc.ModelBinding.Validation;

namespace InventoryManagement.Web.Models
{
    public enum TransactionType
    {
        StockIn,
        StockOut
    }

    public class StockTransaction
    {
        [Key]
        public int TransactionId { get; set; }

        public int ProductId { get; set; }

        [ValidateNever]
        public Product Product { get; set; } = null!;

        public TransactionType Type { get; set; }

        [Range(1, int.MaxValue)]
        public int Quantity { get; set; }

        public DateTime TransactionDate { get; set; } = DateTime.Now;

        [Required, MaxLength(100)]
        public string PerformedBy { get; set; } = string.Empty;

        [MaxLength(250)]
        public string? Remarks { get; set; }
    }
}
