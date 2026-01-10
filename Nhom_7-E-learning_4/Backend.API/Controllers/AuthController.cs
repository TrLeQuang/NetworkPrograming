using System.Security.Claims;
using Backend.API.DTOs.Auth;
using Backend.API.Services.Auth;
using Backend.API.Utils;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Backend.API.Controllers
{
	[ApiController]
	[Route("api/auth")]
	public class AuthController : ControllerBase
	{
		private readonly AuthService _authService;
		private readonly JwtTokenService _jwtTokenService;

		public AuthController(AuthService authService, JwtTokenService jwtTokenService)
		{
			_authService = authService;
			_jwtTokenService = jwtTokenService;
		}

		// PUBLIC: Login
		[HttpPost("login")]
		public IActionResult Login([FromBody] LoginRequest request)
		{
			if (!ModelState.IsValid)
				return BadRequest(ApiResponse<object>.Fail("Invalid request", "VALIDATION_ERROR", ModelState));

			var v = _authService.Validate(request.Email, request.Password);
			if (!v.ok)
				return Unauthorized(ApiResponse<object>.Fail("Email or password is incorrect", "INVALID_CREDENTIALS"));

			var (token, expireMinutes) = _jwtTokenService.GenerateToken(v.id, v.email, v.fullName, v.role);

			var res = new LoginResponse
			{
				AccessToken = token,
				ExpiresInMinutes = expireMinutes,
				User = new UserDto
				{
					Id = v.id,
					Email = v.email,
					FullName = v.fullName,
					Role = v.role
				}
			};

			return Ok(ApiResponse<LoginResponse>.Ok(res, "Login success"));
		}

		// PUBLIC: Logout (Day 2 demo: client tự xoá token)
		[HttpPost("logout")]
		public IActionResult Logout()
		{
			return Ok(ApiResponse<object>.Ok(null, "Logout success"));
		}

		// PRIVATE: Me (cần JWT)
		[Authorize]
		[HttpGet("me")]
		public IActionResult Me()
		{
			// sub chứa userId (đã set trong token)
			var sub = User.FindFirstValue(ClaimTypes.NameIdentifier) ?? User.FindFirstValue("sub") ?? "0";
			var email = User.FindFirstValue(ClaimTypes.Email) ?? User.FindFirstValue("email") ?? "";
			var role = User.FindFirstValue(ClaimTypes.Role) ?? "";
			var fullName = User.FindFirstValue("fullName") ?? "";

			var me = new
			{
				id = int.TryParse(sub, out var id) ? id : 0,
				email,
				fullName,
				role
			};

			return Ok(ApiResponse<object>.Ok(me, "OK"));
		}
	}
}
