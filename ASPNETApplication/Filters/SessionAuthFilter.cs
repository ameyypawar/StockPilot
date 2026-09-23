using System.Linq;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;

namespace InventoryManagement.Web.Filters
{
    public class SessionAuthFilter : IActionFilter
    {
        public void OnActionExecuting(ActionExecutingContext context)
        {
            if (context.ActionDescriptor.EndpointMetadata.OfType<IAllowAnonymous>().Any())
            {
                return;
            }

            var userId = context.HttpContext.Session.GetInt32("UserId");
            if (userId == null)
            {
                var request = context.HttpContext.Request;
                if (request.Path.StartsWithSegments("/api"))
                {
                    context.Result = new UnauthorizedObjectResult(new { error = "Session expired. Please log in again." });
                    return;
                }

                var routeValues = new RouteValueDictionary();
                if (request.Method == "GET")
                {
                    routeValues["returnUrl"] = request.Path + request.QueryString;
                }

                context.Result = new RedirectToActionResult("Login", "Account", routeValues);
            }
        }

        public void OnActionExecuted(ActionExecutedContext context)
        {
        }
    }
}
