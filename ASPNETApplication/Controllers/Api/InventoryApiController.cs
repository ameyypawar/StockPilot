using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using InventoryManagement.Web.Data;
using InventoryManagement.Web.Models;
using InventoryManagement.Web.ViewModels.Api;

namespace InventoryManagement.Web.Controllers.Api
{
    // Global SessionAuthFilter returns 401 JSON for /api when not logged in
    // (no [AllowAnonymous] on this controller).
    [ApiController]
    [Route("api")]
    public class InventoryApiController : ControllerBase
    {
        private readonly ApplicationDbContext _context;

        public InventoryApiController(ApplicationDbContext context)
        {
            _context = context;
        }

        // GET api/products?q=
        [HttpGet("products")]
        public ActionResult<ApiListResponse<ProductItemDto>> GetProducts(string? q)
        {
            var query = _context.Products
                .AsNoTracking()
                .Include(p => p.Category)
                .Include(p => p.Supplier)
                .Include(p => p.Stock)
                .AsQueryable();

            if (!string.IsNullOrWhiteSpace(q))
            {
                var term = $"%{q.Trim()}%";
                query = query.Where(p =>
                    EF.Functions.Like(p.ProductName, term) ||
                    (p.Category != null && EF.Functions.Like(p.Category.CategoryName, term)) ||
                    (p.Supplier != null && EF.Functions.Like(p.Supplier.SupplierName, term)));
            }

            var items = query
                .OrderBy(p => p.ProductName)
                .ToList()
                .Select(p =>
                {
                    var qty = p.Stock?.QuantityAvailable ?? 0;
                    var reorder = p.Stock?.ReorderLevel ?? 0;
                    return new ProductItemDto(
                        p.ProductId,
                        p.ProductName,
                        p.Category?.CategoryName,
                        p.Supplier?.SupplierName,
                        p.Unit,
                        p.Price,
                        qty,
                        reorder,
                        StockStatus.For(qty, reorder));
                })
                .ToList();

            return Ok(new ApiListResponse<ProductItemDto>(DateTime.Now, items.Count, items));
        }

        // GET api/stock
        [HttpGet("stock")]
        public ActionResult<ApiListResponse<StockItemDto>> GetStock()
        {
            var items = BuildStockItems();
            return Ok(new ApiListResponse<StockItemDto>(DateTime.Now, items.Count, items));
        }

        // GET api/stock/low
        [HttpGet("stock/low")]
        public ActionResult<ApiListResponse<StockItemDto>> GetLowStock()
        {
            var items = BuildStockItems()
                .Where(s => s.Status != StockStatus.Ok)
                .ToList();
            return Ok(new ApiListResponse<StockItemDto>(DateTime.Now, items.Count, items));
        }

        private List<StockItemDto> BuildStockItems()
        {
            var stocks = _context.Stocks
                .AsNoTracking()
                .Include(s => s.Product)
                    .ThenInclude(p => p.Category)
                .ToList();

            return stocks
                .Select(s =>
                {
                    var status = StockStatus.For(s.QuantityAvailable, s.ReorderLevel);
                    var suggested = Math.Max(s.ReorderLevel * 2 - s.QuantityAvailable, 0);
                    return new StockItemDto(
                        s.ProductId,
                        s.Product.ProductName,
                        s.Product.Category?.CategoryName,
                        s.Product.Unit,
                        s.QuantityAvailable,
                        s.ReorderLevel,
                        status,
                        s.LastUpdated,
                        suggested);
                })
                .OrderBy(s => s.ProductName)
                .ToList();
        }
    }
}
