using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Backend.API.Controllers
{
	[ApiController]
	[Route("api/upload")]
	public class UploadController : ControllerBase
	{
		private readonly IWebHostEnvironment _env;

		public UploadController(IWebHostEnvironment env)
		{
			_env = env;
		}

		// Upload thumbnail for blog
		[Authorize]
		[HttpPost("blog-thumbnail")]
		[RequestSizeLimit(10_000_000)] // 10MB
		public async Task<IActionResult> UploadBlogThumbnail(IFormFile file)
		{
			if (file == null || file.Length == 0)
				return BadRequest(new { success = false, message = "File is required" });

			var allowed = new[] { ".jpg", ".jpeg", ".png", ".webp" };
			var ext = Path.GetExtension(file.FileName).ToLowerInvariant();
			if (!allowed.Contains(ext))
				return BadRequest(new { success = false, message = "Only jpg/jpeg/png/webp allowed" });

			var uploadsDir = Path.Combine(_env.WebRootPath, "uploads");
			if (!Directory.Exists(uploadsDir))
				Directory.CreateDirectory(uploadsDir);

			var fileName = $"{Guid.NewGuid():N}{ext}";
			var savePath = Path.Combine(uploadsDir, fileName);

			using (var stream = new FileStream(savePath, FileMode.Create))
			{
				await file.CopyToAsync(stream);
			}

			// public url
			var url = $"{Request.Scheme}://{Request.Host}/uploads/{fileName}";
			return Ok(new { success = true, url, fileName });
		}
	}
}
