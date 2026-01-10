using Backend.API.Data;
using Microsoft.Data.SqlClient;

namespace Backend.API.Repositories
{
	public class BlogRepository
	{
		private readonly DbConnectionFactory _db;

		public BlogRepository(DbConnectionFactory db)
		{
			_db = db;
		}

		public int Create(int authorId, string title, string content, string? thumbnailUrl)
		{
			using var conn = _db.Create();
			conn.Open();

			using var cmd = conn.CreateCommand();
			cmd.CommandText = @"
INSERT INTO Blogs (Title, Content, ThumbnailUrl, AuthorId, IsDeleted, CreatedAt, UpdatedAt)
OUTPUT INSERTED.Id
VALUES (@Title, @Content, @ThumbnailUrl, @AuthorId, 0, SYSUTCDATETIME(), SYSUTCDATETIME());
";
			cmd.Parameters.Add(new SqlParameter("@Title", title));
			cmd.Parameters.Add(new SqlParameter("@Content", content));
			cmd.Parameters.Add(new SqlParameter("@ThumbnailUrl", (object?)thumbnailUrl ?? DBNull.Value));
			cmd.Parameters.Add(new SqlParameter("@AuthorId", authorId));

			return (int)cmd.ExecuteScalar();
		}

		public object? GetById(int id)
		{
			using var conn = _db.Create();
			conn.Open();

			using var cmd = conn.CreateCommand();
			cmd.CommandText = @"
SELECT b.Id, b.Title, b.Content, b.ThumbnailUrl, b.AuthorId, u.FullName AS AuthorName,
       b.CreatedAt, b.UpdatedAt
FROM Blogs b
JOIN Users u ON u.Id = b.AuthorId
WHERE b.Id=@Id AND b.IsDeleted=0;
";
			cmd.Parameters.Add(new SqlParameter("@Id", id));

			using var reader = cmd.ExecuteReader();
			if (!reader.Read()) return null;

			return new
			{
				id = reader.GetInt32(0),
				title = reader.GetString(1),
				content = reader.GetString(2),
				thumbnailUrl = reader.IsDBNull(3) ? null : reader.GetString(3),
				authorId = reader.GetInt32(4),
				authorName = reader.GetString(5),
				createdAt = reader.GetDateTime(6),
				updatedAt = reader.GetDateTime(7)
			};
		}

		public List<object> Search(string? q, string sortBy, string sortDir)
		{
			// sort whitelist
			var sortCol = sortBy.ToLower() switch
			{
				"title" => "b.Title",
				"createdat" => "b.CreatedAt",
				"updatedat" => "b.UpdatedAt",
				_ => "b.CreatedAt"
			};
			var dir = sortDir.ToLower() == "asc" ? "ASC" : "DESC";

			using var conn = _db.Create();
			conn.Open();

			using var cmd = conn.CreateCommand();
			cmd.CommandText = $@"
SELECT b.Id, b.Title, b.ThumbnailUrl, b.AuthorId, u.FullName AS AuthorName, b.CreatedAt, b.UpdatedAt
FROM Blogs b
JOIN Users u ON u.Id = b.AuthorId
WHERE b.IsDeleted=0
  AND (@Q IS NULL OR b.Title LIKE '%' + @Q + '%' OR b.Content LIKE '%' + @Q + '%')
ORDER BY {sortCol} {dir};
";
			cmd.Parameters.Add(new SqlParameter("@Q", (object?)q ?? DBNull.Value));

			var list = new List<object>();
			using var reader = cmd.ExecuteReader();
			while (reader.Read())
			{
				list.Add(new
				{
					id = reader.GetInt32(0),
					title = reader.GetString(1),
					thumbnailUrl = reader.IsDBNull(2) ? null : reader.GetString(2),
					authorId = reader.GetInt32(3),
					authorName = reader.GetString(4),
					createdAt = reader.GetDateTime(5),
					updatedAt = reader.GetDateTime(6)
				});
			}
			return list;
		}

		public bool Update(int id, string title, string content, string? thumbnailUrl)
		{
			using var conn = _db.Create();
			conn.Open();

			using var cmd = conn.CreateCommand();
			cmd.CommandText = @"
UPDATE Blogs
SET Title=@Title, Content=@Content, ThumbnailUrl=@ThumbnailUrl, UpdatedAt=SYSUTCDATETIME()
WHERE Id=@Id AND IsDeleted=0;
";
			cmd.Parameters.Add(new SqlParameter("@Id", id));
			cmd.Parameters.Add(new SqlParameter("@Title", title));
			cmd.Parameters.Add(new SqlParameter("@Content", content));
			cmd.Parameters.Add(new SqlParameter("@ThumbnailUrl", (object?)thumbnailUrl ?? DBNull.Value));

			return cmd.ExecuteNonQuery() > 0;
		}

		public bool SoftDelete(int id)
		{
			using var conn = _db.Create();
			conn.Open();

			using var cmd = conn.CreateCommand();
			cmd.CommandText = @"
UPDATE Blogs SET IsDeleted=1, UpdatedAt=SYSUTCDATETIME()
WHERE Id=@Id AND IsDeleted=0;
";
			cmd.Parameters.Add(new SqlParameter("@Id", id));

			return cmd.ExecuteNonQuery() > 0;
		}
	}
}
