namespace Backend.API.Services.Auth
{
	public class AuthService
	{
		// User giả để test (Day 3 thay bằng DB)
		private readonly List<(int Id, string Email, string Password, string FullName, string Role)> _users =
		[
			(1, "admin@gmail.com", "123456", "Admin", "ADMIN"),
			(2, "user@gmail.com", "123456", "User", "USER")
		];

		public (bool ok, int id, string email, string fullName, string role) Validate(string email, string password)
		{
			var user = _users.FirstOrDefault(u =>
				u.Email.Equals(email, StringComparison.OrdinalIgnoreCase)
				&& u.Password == password
			);

			if (user.Id == 0)
				return (false, 0, "", "", "");

			return (true, user.Id, user.Email, user.FullName, user.Role);
		}
	}
}
