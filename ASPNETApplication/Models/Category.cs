using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Mvc.ModelBinding.Validation;

namespace InventoryManagement.Web.Models
{
    public class Category
    {
        public int CategoryId { get; set; }

        [Required, MaxLength(100)]
        public string CategoryName { get; set; } = string.Empty;

        [MaxLength(250)]
        public string? Description { get; set; }

        [ValidateNever]
        public ICollection<Product> Products { get; set; } = new List<Product>();
    }
}
