using Microsoft.AspNetCore.Mvc;

namespace Backend.API.Controllers
{
	[ApiController]
	[Route("api/health")]
	public class HealthController : ControllerBase
	{
		[HttpGet]
		public IActionResult Get()
		{
			return Ok(new
			{
				success = true,
				message = "Backend.API is running"
			});
		}
	}
}
