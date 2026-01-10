using Microsoft.Data.SqlClient;

namespace Backend.API.Data
{
	public class DbConnectionFactory
	{
		private readonly IConfiguration _config;

		public DbConnectionFactory(IConfiguration config)
		{
			_config = config;
		}

		public SqlConnection Create()
		{
			var cs = _config.GetConnectionString("Default");
			return new SqlConnection(cs);
		}
	}
}
