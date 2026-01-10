// File: Backend.Web/Controllers/BlogController.cs
using Backend.Web.Models;
using Backend.Web.Services;
using Microsoft.AspNetCore.Mvc;

namespace Backend.Web.Controllers
{
	public class BlogController : Controller
	{
		private readonly ApiClient _api;

		public BlogController(ApiClient api)
		{
			_api = api;
		}

		private string? GetToken() => HttpContext.Session.GetString("token");

		// GET: /Blog
		[HttpGet]
		public async Task<IActionResult> Index(string? search, string? sortBy, string? sortDir)
		{
			var token = GetToken();
			if (string.IsNullOrWhiteSpace(token))
				return RedirectToAction("Login", "Auth");

			var res = await _api.GetBlogsAsync(token, search, sortBy, sortDir);
			if (!res.Success)
			{
				ViewBag.Error = res.Message ?? "Cannot load blogs.";
				return View(new List<BlogListItem>());
			}

			ViewBag.Search = search ?? "";
			ViewBag.SortBy = sortBy ?? "";
			ViewBag.SortDir = sortDir ?? "";
			return View(res.Data ?? new List<BlogListItem>());
		}

		// GET: /Blog/Details/5
		[HttpGet]
		public async Task<IActionResult> Details(int id)
		{
			var token = GetToken();
			if (string.IsNullOrWhiteSpace(token))
				return RedirectToAction("Login", "Auth");

			var res = await _api.GetBlogByIdAsync(token, id);
			if (!res.Success || res.Data == null)
			{
				ViewBag.Error = res.Message ?? "Blog not found.";
				return RedirectToAction("Index");
			}

			return View(res.Data);
		}

		// GET: /Blog/Create
		[HttpGet]
		public IActionResult Create()
		{
			var token = GetToken();
			if (string.IsNullOrWhiteSpace(token))
				return RedirectToAction("Login", "Auth");

			return View(new CreateBlogRequest());
		}

		// POST: /Blog/Create
		[HttpPost]
		[ValidateAntiForgeryToken]
		public async Task<IActionResult> Create(CreateBlogRequest model, IFormFile? thumbnailFile)
		{
			var token = GetToken();
			if (string.IsNullOrWhiteSpace(token))
				return RedirectToAction("Login", "Auth");

			// upload file trước, lấy Url nhét vào ThumbnailUrl
			if (thumbnailFile != null && thumbnailFile.Length > 0)
			{
				var up = await _api.UploadBlogThumbnailAsync(token, thumbnailFile);
				if (up.Success && up.Data != null && !string.IsNullOrWhiteSpace(up.Data.Url))
					model.ThumbnailUrl = up.Data.Url;
				else
					ViewBag.Error = up.Message ?? "Upload failed.";
			}

			var res = await _api.CreateBlogAsync(token, model);
			if (!res.Success)
			{
				ViewBag.Error = res.Message ?? "Create failed.";
				return View(model);
			}

			return RedirectToAction("Index");
		}

		// GET: /Blog/Edit/5
		[HttpGet]
		public async Task<IActionResult> Edit(int id)
		{
			var token = GetToken();
			if (string.IsNullOrWhiteSpace(token))
				return RedirectToAction("Login", "Auth");

			var res = await _api.GetBlogByIdAsync(token, id);
			if (!res.Success || res.Data == null)
				return RedirectToAction("Index");

			var vm = new UpdateBlogRequest
			{
				Title = res.Data.Title,
				Content = res.Data.Content,
				ThumbnailUrl = res.Data.ThumbnailUrl
			};

			ViewBag.BlogId = id;
			return View(vm);
		}

		// POST: /Blog/Edit/5
		[HttpPost]
		[ValidateAntiForgeryToken]
		public async Task<IActionResult> Edit(int id, UpdateBlogRequest model, IFormFile? thumbnailFile)
		{
			var token = GetToken();
			if (string.IsNullOrWhiteSpace(token))
				return RedirectToAction("Login", "Auth");

			if (thumbnailFile != null && thumbnailFile.Length > 0)
			{
				var up = await _api.UploadBlogThumbnailAsync(token, thumbnailFile);
				if (up.Success && up.Data != null && !string.IsNullOrWhiteSpace(up.Data.Url))
					model.ThumbnailUrl = up.Data.Url;
				else
					ViewBag.Error = up.Message ?? "Upload failed.";
			}

			var res = await _api.UpdateBlogAsync(token, id, model);
			if (!res.Success)
			{
				ViewBag.Error = res.Message ?? "Update failed.";
				ViewBag.BlogId = id;
				return View(model);
			}

			return RedirectToAction("Index");
		}

		// POST: /Blog/Delete/5
		[HttpPost]
		[ValidateAntiForgeryToken]
		public async Task<IActionResult> Delete(int id)
		{
			var token = GetToken();
			if (string.IsNullOrWhiteSpace(token))
				return RedirectToAction("Login", "Auth");

			var res = await _api.DeleteBlogAsync(token, id);
			if (!res.Success)
				TempData["Error"] = res.Message ?? "Delete failed.";

			return RedirectToAction("Index");
		}
	}
}
