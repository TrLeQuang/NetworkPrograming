using Backend.API.Data;
using Microsoft.AspNetCore.Mvc;

namespace Backend.API.Controllers
{
	[ApiController]
	[Route("api/db-test")]
	public class DbTestController : ControllerBase
	{
		private readonly DbConnectionFactory _db;

		public DbTestController(DbConnectionFactory db)
		{
			_db = db;
		}

		[HttpGet("users-count")]
		public IActionResult CountUsers()
		{
			using var conn = _db.Create();
			conn.Open();

			var cmd = conn.CreateCommand();
			cmd.CommandText = "SELECT COUNT(*) FROM Users";

			var count = (int)cmd.ExecuteScalar();

			return Ok(new
			{
				success = true,
				users = count
			});
		}
	}
}
