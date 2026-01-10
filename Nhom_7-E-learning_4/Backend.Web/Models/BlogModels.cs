// File: Backend.Web/Models/BlogModels.cs
namespace Backend.Web.Models
{
	public class BlogListItem
	{
		public int Id { get; set; }
		public string Title { get; set; } = "";
		public string? ThumbnailUrl { get; set; }
		public string AuthorName { get; set; } = "";
		public DateTime CreatedAt { get; set; }
	}

	public class BlogDetail : BlogListItem
	{
		public string Content { get; set; } = "";
	}

	public class CreateBlogRequest
	{
		public string Title { get; set; } = "";
		public string Content { get; set; } = "";
		public string? ThumbnailUrl { get; set; }
	}

	public class UpdateBlogRequest
	{
		public string Title { get; set; } = "";
		public string Content { get; set; } = "";
		public string? ThumbnailUrl { get; set; }
	}

	public class UploadResult
	{
		public string Url { get; set; } = "";
	}
}
