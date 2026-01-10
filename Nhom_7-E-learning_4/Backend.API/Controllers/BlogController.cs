using Backend.API.DTOs.Blog;
using Backend.API.Repositories;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;

namespace Backend.API.Controllers
{
	[ApiController]
	[Route("api/blogs")]
	public class BlogController : ControllerBase
	{
		private readonly BlogRepository _repo;

		public BlogController(BlogRepository repo)
		{
			_repo = repo;
		}

		// Create (Private)
		[Authorize]
		[HttpPost]
		public IActionResult Create([FromBody] CreateBlogRequest req)
		{
			var userId = int.Parse(User.FindFirstValue(ClaimTypes.NameIdentifier)!);
			var id = _repo.Create(userId, req.Title, req.Content, req.ThumbnailUrl);

			return Ok(new { success = true, id });
		}

		// View (Public)
		[AllowAnonymous]
		[HttpGet("{id:int}")]
		public IActionResult GetById(int id)
		{
			var blog = _repo.GetById(id);
			if (blog == null) return NotFound(new { success = false, message = "Not found" });

			return Ok(new { success = true, data = blog });
		}

		// Search + Sort (Public)
		// /api/blogs?q=abc&sortBy=createdAt&sortDir=desc
		[AllowAnonymous]
		[HttpGet]
		public IActionResult Search([FromQuery] string? q, [FromQuery] string sortBy = "createdAt", [FromQuery] string sortDir = "desc")
		{
			var list = _repo.Search(q, sortBy, sortDir);
			return Ok(new { success = true, total = list.Count, data = list });
		}

		// Update (Private)
		[Authorize]
		[HttpPut("{id:int}")]
		public IActionResult Update(int id, [FromBody] UpdateBlogRequest req)
		{
			var ok = _repo.Update(id, req.Title, req.Content, req.ThumbnailUrl);
			if (!ok) return NotFound(new { success = false, message = "Not found" });

			return Ok(new { success = true });
		}

		// Delete (Private)
		[Authorize]
		[HttpDelete("{id:int}")]
		public IActionResult Delete(int id)
		{
			var ok = _repo.SoftDelete(id);
			if (!ok) return NotFound(new { success = false, message = "Not found" });

			return Ok(new { success = true });
		}
	}
}
