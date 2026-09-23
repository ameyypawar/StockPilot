using Microsoft.AspNetCore.Mvc;

namespace InventoryManagement.Web.Controllers
{
    // Protected by the global SessionAuthFilter (no [AllowAnonymous] here).
    public class PwaController : Controller
    {
        public IActionResult Index()
        {
            return View();
        }

        public IActionResult Search()
        {
            return View();
        }

        public IActionResult Stock()
        {
            return View();
        }

        public IActionResult LowStock()
        {
            return View();
        }
    }
}
