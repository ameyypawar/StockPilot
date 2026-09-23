using System;
using System.Collections.Generic;
using InventoryManagementSystem.Models;

namespace InventoryManagementSystem.Services
{
    // Collections + Polymorphism: Dictionary<string, Person> of Admin/Staff/User; DisplayAllUsers()
    // calls the virtual DisplayInfo() polymorphically for whichever role is stored.
    public class UserService
    {
        private readonly Dictionary<string, Person> _users = new(StringComparer.OrdinalIgnoreCase)
        {
            ["admin"] = new Admin(1, "Anita Deshmukh", "admin@example.com", "Full"),
            ["staff"] = new Staff(2, "Rahul Patil", "rahul@example.com", "Warehouse"),
            ["viewer"] = new User(3, "Sneha Kulkarni", "sneha@example.com", "Viewer")
        };

        public Person? CurrentUser { get; private set; }

        public Person? Login(string username)
        {
            if (_users.TryGetValue(username, out var person))
            {
                CurrentUser = person;
                return person;
            }
            return null;
        }

        public void DisplayAllUsers()
        {
            Console.WriteLine("\n----- Registered Users -----");
            foreach (var person in _users.Values)
            {
                person.DisplayInfo();
                Console.WriteLine("---");
            }
        }

        // Encapsulation of the access rule: only non-viewer roles may modify data.
        public bool CanModify => CurrentUser is not User;
    }
}
