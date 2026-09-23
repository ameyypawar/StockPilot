using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Mvc.ModelBinding.Validation;

namespace InventoryManagement.Web.Models
{
    public class Supplier
    {
        public int SupplierId { get; set; }

        [Required, MaxLength(150)]
        public string SupplierName { get; set; } = string.Empty;

        [MaxLength(20)]
        public string? ContactNumber { get; set; }

        [MaxLength(150), EmailAddress]
        public string? Email { get; set; }

        [MaxLength(250)]
        public string? Address { get; set; }

        [ValidateNever]
        public ICollection<Product> Products { get; set; } = new List<Product>();
    }
}
