namespace Backend.API.DTOs.Blog
{
	public class CreateBlogRequest
	{
		public string Title { get; set; } = "";
		public string Content { get; set; } = "";
		public string? ThumbnailUrl { get; set; }
	}
}
