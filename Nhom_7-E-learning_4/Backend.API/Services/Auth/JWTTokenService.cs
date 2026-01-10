using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.IdentityModel.Tokens;

namespace Backend.API.Services.Auth
{
	public class JwtTokenService
	{
		private readonly IConfiguration _config;

		public JwtTokenService(IConfiguration config)
		{
			_config = config;
		}

		public (string token, int expireMinutes) GenerateToken(
			int userId,
			string email,
			string fullName,
			string role)
		{
			var jwt = _config.GetSection("Jwt");
			var key = jwt["Key"]!;
			var issuer = jwt["Issuer"];
			var audience = jwt["Audience"];
			var expireMinutes = int.Parse(jwt["ExpireMinutes"]!);

			var claims = new List<Claim>
			{
				new Claim(JwtRegisteredClaimNames.Sub, userId.ToString()),
				new Claim(JwtRegisteredClaimNames.Email, email),
				new Claim("fullName", fullName),
				new Claim(ClaimTypes.Role, role)
			};

			var signingKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(key));
			var creds = new SigningCredentials(signingKey, SecurityAlgorithms.HmacSha256);

			var token = new JwtSecurityToken(
				issuer,
				audience,
				claims,
				expires: DateTime.UtcNow.AddMinutes(expireMinutes),
				signingCredentials: creds
			);

			return (new JwtSecurityTokenHandler().WriteToken(token), expireMinutes);
		}
	}
}
