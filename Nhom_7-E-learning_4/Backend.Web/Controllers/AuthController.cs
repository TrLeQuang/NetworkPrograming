// File: Backend.Web/Controllers/AuthController.cs
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using Backend.Web.Services;
using Backend.Web.Models;

namespace Backend.Web.Controllers
{
	public class AuthController : Controller
	{
		private readonly ApiClient _api;

		public AuthController(ApiClient api)
		{
			_api = api;
		}

		// GET: /Auth/Login
		[HttpGet]
		public IActionResult Login()
		{
			return View(new LoginRequest());
		}

		// POST: /Auth/Login
		[HttpPost]
		[ValidateAntiForgeryToken]
		public async Task<IActionResult> Login(LoginRequest model)
		{
			if (!ModelState.IsValid)
				return View(model);

			try
			{
				var res = await _api.LoginAsync(model.Email, model.Password);

				// Debug: xem Web nhận gì từ API
				Console.WriteLine("LOGIN RES = " + JsonSerializer.Serialize(res));

				if (res == null)
				{
					ViewBag.Error = "Login failed: API returned null (check ApiClient BaseUrl).";
					return View(model);
				}

				if (!res.Success)
				{
					ViewBag.Error = res.Message ?? "Login failed.";
					return View(model);
				}

				// ✅ API trả data.accessToken (không phải Token)
				var token = res.Data?.AccessToken;
				Console.WriteLine("ACCESS TOKEN = " + token);

				if (string.IsNullOrWhiteSpace(token))
				{
					ViewBag.Error = "Login failed: accessToken is empty (check LoginData.AccessToken mapping).";
					return View(model);
				}

				// ✅ Lưu token vào Session
				HttpContext.Session.SetString("token", token);

				// ✅ User nằm trong data.user
				var user = res.Data?.User;
				if (user != null)
				{
					HttpContext.Session.SetString("fullName", user.FullName ?? "");
					HttpContext.Session.SetString("email", user.Email ?? "");
					HttpContext.Session.SetString("role", user.Role ?? "");
				}
				else
				{
					// không bắt buộc, nhưng để tránh null
					HttpContext.Session.SetString("fullName", "");
					HttpContext.Session.SetString("email", "");
					HttpContext.Session.SetString("role", "");
				}

				return RedirectToAction("Profile");
			}
			catch (Exception ex)
			{
				Console.WriteLine("LOGIN EX = " + ex);
				ViewBag.Error = "Login error: " + ex.Message;
				return View(model);
			}
		}

		// GET: /Auth/Profile
		[HttpGet]
		public async Task<IActionResult> Profile()
		{
			var token = HttpContext.Session.GetString("token");
			if (string.IsNullOrWhiteSpace(token))
			{
				return RedirectToAction("Login");
			}

			try
			{
				var res = await _api.MeAsync(token);

				// Debug
				Console.WriteLine("ME RES = " + JsonSerializer.Serialize(res));

				if (res == null)
				{
					ViewBag.Error = "Cannot load profile: API returned null.";
					return View();
				}

				if (!res.Success)
				{
					// token invalid/expired → đá về login
					HttpContext.Session.Clear();
					return RedirectToAction("Login");
				}

				// ✅ cập nhật lại session (optional)
				if (res.Data != null)
				{
					HttpContext.Session.SetString("fullName", res.Data.FullName ?? "");
					HttpContext.Session.SetString("email", res.Data.Email ?? "");
					HttpContext.Session.SetString("role", res.Data.Role ?? "");
				}

				return View(res.Data); // UserProfile
			}
			catch (Exception ex)
			{
				Console.WriteLine("ME EX = " + ex);
				ViewBag.Error = "Profile error: " + ex.Message;
				return View();
			}
		}

		// POST: /Auth/Logout
		[HttpPost]
		[ValidateAntiForgeryToken]
		public IActionResult Logout()
		{
			HttpContext.Session.Clear();
			return RedirectToAction("Login");
		}
	}
}
