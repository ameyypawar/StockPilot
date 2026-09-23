using Microsoft.EntityFrameworkCore;
using InventoryManagement.Web.Models;

namespace InventoryManagement.Web.Data
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }

        public DbSet<Category> Categories { get; set; }
        public DbSet<Supplier> Suppliers { get; set; }
        public DbSet<Product> Products { get; set; }
        public DbSet<Stock> Stocks { get; set; }
        public DbSet<StockTransaction> StockTransactions { get; set; }
        public DbSet<ApplicationUser> Users { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.Entity<Category>()
                .HasIndex(c => c.CategoryName)
                .IsUnique();

            modelBuilder.Entity<Product>()
                .HasOne(p => p.Category)
                .WithMany(c => c.Products)
                .HasForeignKey(p => p.CategoryId)
                .OnDelete(DeleteBehavior.Restrict);

            modelBuilder.Entity<Product>()
                .HasOne(p => p.Supplier)
                .WithMany(s => s.Products)
                .HasForeignKey(p => p.SupplierId)
                .OnDelete(DeleteBehavior.Restrict);

            modelBuilder.Entity<Product>()
                .HasIndex(p => p.ProductName);

            modelBuilder.Entity<Product>()
                .ToTable(t => t.HasCheckConstraint("CK_Products_Price", "[Price] >= 0"));

            modelBuilder.Entity<Stock>()
                .HasOne(s => s.Product)
                .WithOne(p => p.Stock)
                .HasForeignKey<Stock>(s => s.ProductId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<Stock>()
                .ToTable(t => t.HasCheckConstraint("CK_Stocks_QuantityAvailable", "[QuantityAvailable] >= 0"));

            modelBuilder.Entity<Stock>()
                .ToTable(t => t.HasCheckConstraint("CK_Stocks_ReorderLevel", "[ReorderLevel] >= 0"));

            modelBuilder.Entity<StockTransaction>()
                .HasOne(t => t.Product)
                .WithMany(p => p.Transactions)
                .HasForeignKey(t => t.ProductId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<StockTransaction>()
                .Property(t => t.Type)
                .HasConversion<string>()
                .HasMaxLength(10);

            modelBuilder.Entity<StockTransaction>()
                .ToTable(t => t.HasCheckConstraint("CK_StockTransactions_Quantity", "[Quantity] > 0"));

            modelBuilder.Entity<StockTransaction>()
                .ToTable(t => t.HasCheckConstraint("CK_StockTransactions_Type", "[Type] IN ('StockIn','StockOut')"));

            modelBuilder.Entity<StockTransaction>()
                .HasIndex(t => t.TransactionDate);

            modelBuilder.Entity<ApplicationUser>()
                .HasIndex(u => u.Username)
                .IsUnique();
        }
    }
}
