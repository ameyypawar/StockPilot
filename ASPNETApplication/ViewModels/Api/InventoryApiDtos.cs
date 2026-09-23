using System;
using System.Collections.Generic;

namespace InventoryManagement.Web.ViewModels.Api
{
    public record ProductItemDto(
        int ProductId,
        string ProductName,
        string? CategoryName,
        string? SupplierName,
        string Unit,
        decimal Price,
        int QuantityAvailable,
        int ReorderLevel,
        string Status);

    public record StockItemDto(
        int ProductId,
        string ProductName,
        string? CategoryName,
        string Unit,
        int QuantityAvailable,
        int ReorderLevel,
        string Status,
        DateTime LastUpdated,
        int SuggestedOrderQty);

    public record ApiListResponse<T>(
        DateTime GeneratedAt,
        int Count,
        List<T> Items);
}
