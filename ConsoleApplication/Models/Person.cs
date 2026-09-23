using System;

namespace InventoryManagementSystem.Models
{
    // Inheritance base for Admin/Staff/User; DisplayInfo() is virtual (Polymorphism).
    public abstract class Person
    {
        // Encapsulation: private fields, public properties
        private int _id;
        private string _name;
        private string _email;

        public int Id
        {
            get => _id;
            set => _id = value;
        }

        public string Name
        {
            get => _name;
            set
            {
                if (string.IsNullOrWhiteSpace(value))
                    throw new ArgumentException("Name cannot be empty.");
                _name = value;
            }
        }

        public string Email
        {
            get => _email;
            set => _email = value;
        }

        public Person(int id, string name, string email)
        {
            Id = id;
            Name = name;
            Email = email;
        }

        // Virtual method - can be overridden by derived classes
        public virtual void DisplayInfo()
        {
            Console.WriteLine($"ID: {Id}, Name: {Name}, Email: {Email}");
        }
    }
}
