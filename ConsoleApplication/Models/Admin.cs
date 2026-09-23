using System;

namespace InventoryManagementSystem.Models
{
    // Inheritance: Admin extends Person; overrides DisplayInfo() (Polymorphism).
    public class Admin : Person
    {
        public string AccessLevel { get; set; }

        public Admin(int id, string name, string email, string accessLevel)
            : base(id, name, email)
        {
            AccessLevel = accessLevel;
        }

        public override void DisplayInfo()
        {
            base.DisplayInfo();
            Console.WriteLine($"Role: Admin, Access Level: {AccessLevel}");
        }
    }
}
