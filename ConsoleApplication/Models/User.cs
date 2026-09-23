using System;

namespace InventoryManagementSystem.Models
{
    // Inheritance: User extends Person; overrides DisplayInfo() (Polymorphism).
    public class User : Person
    {
        public string Role { get; set; } // e.g. "Viewer"

        public User(int id, string name, string email, string role)
            : base(id, name, email)
        {
            Role = role;
        }

        public override void DisplayInfo()
        {
            base.DisplayInfo();
            Console.WriteLine($"Role: {Role}");
        }
    }
}
