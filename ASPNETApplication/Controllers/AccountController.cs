using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using InventoryManagement.Web.Data;
using InventoryManagement.Web.Models;
using System.Linq;

namespace InventoryManagement.Web.Controllers
{
    public class AccountController : Controller
    {
        private readonly ApplicationDbContext _context;
        private readonly IPasswordHasher<ApplicationUser> _hasher;

        public AccountController(ApplicationDbContext context, IPasswordHasher<ApplicationUser> hasher)
        {
            _context = context;
            _hasher = hasher;
        }

        [AllowAnonymous]
        [HttpGet]
        public IActionResult Login(string? returnUrl)
        {
            if (HttpContext.Session.GetInt32("UserId") != null)
            {
                return RedirectToAction("Index", "Dashboard");
            }

            ViewBag.ReturnUrl = returnUrl;
            return View();
        }

        [AllowAnonymous]
        [HttpPost]
        public IActionResult Login(string username, string password, string? returnUrl)
        {
            ViewBag.ReturnUrl = returnUrl;

            var trimmedUsername = (username ?? string.Empty).Trim();
            var user = _context.Users.FirstOrDefault(u => u.Username == trimmedUsername);

            if (user == null)
            {
                ViewBag.Error = "Invalid username or password.";
                return View();
            }

            PasswordVerificationResult result;
            try
            {
                result = _hasher.VerifyHashedPassword(user, user.PasswordHash, password ?? string.Empty);
            }
            catch (System.FormatException)
            {
                result = PasswordVerificationResult.Failed;
            }

            if (result == PasswordVerificationResult.Failed)
            {
                ViewBag.Error = "Invalid username or password.";
                return View();
            }

            if (result == PasswordVerificationResult.SuccessRehashNeeded)
            {
                user.PasswordHash = _hasher.HashPassword(user, password ?? string.Empty);
                _context.SaveChanges();
            }

            HttpContext.Session.SetInt32("UserId", user.UserId);
            HttpContext.Session.SetString("Username", user.Username);
            HttpContext.Session.SetString("FullName", user.FullName);
            HttpContext.Session.SetString("Role", user.Role);

            if (!string.IsNullOrEmpty(returnUrl) && Url.IsLocalUrl(returnUrl))
            {
                return Redirect(returnUrl);
            }

            return RedirectToAction("Index", "Dashboard");
        }

        public IActionResult Logout()
        {
            HttpContext.Session.Clear();
            return RedirectToAction("Login", new { loggedOut = 1 });
        }

        [HttpGet]
        public IActionResult ChangePassword()
        {
            return View();
        }

        [HttpPost]
        public IActionResult ChangePassword(string currentPassword, string newPassword, string confirmPassword)
        {
            int? userId = HttpContext.Session.GetInt32("UserId");
            if (userId == null)
            {
                return RedirectToAction("Login");
            }

            if (string.IsNullOrWhiteSpace(currentPassword) || string.IsNullOrWhiteSpace(newPassword) || string.IsNullOrWhiteSpace(confirmPassword))
            {
                ViewBag.Error = "All fields are required.";
                return View();
            }

            if (newPassword.Length < 6)
            {
                ViewBag.Error = "New password must be at least 6 characters long.";
                return View();
            }

            if (newPassword != confirmPassword)
            {
                ViewBag.Error = "New password and confirmation do not match.";
                return View();
            }

            if (newPassword == currentPassword)
            {
                ViewBag.Error = "New password must be different from the current password.";
                return View();
            }

            var user = _context.Users.FirstOrDefault(u => u.UserId == userId);
            if (user == null)
            {
                return RedirectToAction("Login");
            }

            PasswordVerificationResult result;
            try
            {
                result = _hasher.VerifyHashedPassword(user, user.PasswordHash, currentPassword);
            }
            catch (System.FormatException)
            {
                result = PasswordVerificationResult.Failed;
            }

            if (result == PasswordVerificationResult.Failed)
            {
                ViewBag.Error = "Current password is incorrect.";
                return View();
            }

            user.PasswordHash = _hasher.HashPassword(user, newPassword);
            _context.SaveChanges();

            ViewBag.Success = "Password changed successfully.";
            return View();
        }
    }
}
