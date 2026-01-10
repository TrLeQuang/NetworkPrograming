using System.Text.Json.Serialization;

namespace Backend.Web.Models
{
	public class LoginRequest
	{
		[JsonPropertyName("email")]
		public string Email { get; set; } = "";

		[JsonPropertyName("password")]
		public string Password { get; set; } = "";
	}

	public class LoginData
	{
		// ✅ API trả "accessToken"
		[JsonPropertyName("accessToken")]
		public string AccessToken { get; set; } = "";

		[JsonPropertyName("expiresInMinutes")]
		public int ExpiresInMinutes { get; set; }

		[JsonPropertyName("user")]
		public UserProfile? User { get; set; }
	}

	public class UserProfile
	{
		[JsonPropertyName("id")]
		public int Id { get; set; }

		[JsonPropertyName("email")]
		public string Email { get; set; } = "";

		[JsonPropertyName("fullName")]
		public string FullName { get; set; } = "";

		[JsonPropertyName("role")]
		public string Role { get; set; } = "";
	}
}
