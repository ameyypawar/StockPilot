using System.ComponentModel.DataAnnotations;

namespace InventoryManagement.Web.Models
{
    public class ApplicationUser
    {
        [Key]
        public int UserId { get; set; }

        [Required, MaxLength(50)]
        public string Username { get; set; } = string.Empty;

        [Required, MaxLength(256)]
        public string PasswordHash { get; set; } = string.Empty;

        [Required, MaxLength(100)]
        public string FullName { get; set; } = string.Empty;

        [MaxLength(150), EmailAddress]
        public string? Email { get; set; }

        [Required, MaxLength(20)]
        public string Role { get; set; } = "Staff";
    }
}
