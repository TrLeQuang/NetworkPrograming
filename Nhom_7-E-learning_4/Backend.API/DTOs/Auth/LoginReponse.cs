namespace Backend.API.DTOs.Auth
{
	public class LoginResponse
	{
		public string AccessToken { get; set; } = "";
		public int ExpiresInMinutes { get; set; }
		public UserDto User { get; set; } = new();
	}

	public class UserDto
	{
		public int Id { get; set; }
		public string Email { get; set; } = "";
		public string FullName { get; set; } = "";
		public string Role { get; set; } = "";
	}
}
