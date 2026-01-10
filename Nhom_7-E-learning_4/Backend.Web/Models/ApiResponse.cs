using System.Text.Json.Serialization;

namespace Backend.Web.Models
{
	public class ApiResponse<T>
	{
		[JsonPropertyName("success")]
		public bool Success { get; set; }

		[JsonPropertyName("code")]
		public string? Code { get; set; }

		[JsonPropertyName("message")]
		public string? Message { get; set; }

		[JsonPropertyName("data")]
		public T? Data { get; set; }

		[JsonPropertyName("errors")]
		public object? Errors { get; set; }
	}
}
