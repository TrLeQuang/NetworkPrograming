// File: Backend.Web/Services/ApiClient.cs
using System.Net.Http.Headers;
using System.Net.Http.Json;
using Backend.Web.Models;

namespace Backend.Web.Services
{
	public class ApiClient
	{
		private readonly HttpClient _http;

		public ApiClient(HttpClient http)
		{
			_http = http;
		}

		// =========================
		// AUTH
		// =========================
		public async Task<ApiResponse<LoginData>> LoginAsync(string email, string password)
		{
			// login không dùng token cũ
			_http.DefaultRequestHeaders.Authorization = null;

			var req = new LoginRequest
			{
				Email = email,
				Password = password
			};

			var resp = await _http.PostAsJsonAsync("api/auth/login", req);

			if (!resp.IsSuccessStatusCode)
			{
				var err = await SafeRead<ApiResponse<LoginData>>(resp);
				return err ?? new ApiResponse<LoginData>
				{
					Success = false,
					Message = $"HTTP {(int)resp.StatusCode} {resp.ReasonPhrase}"
				};
			}

			var data = await resp.Content.ReadFromJsonAsync<ApiResponse<LoginData>>();
			return data ?? new ApiResponse<LoginData> { Success = false, Message = "Empty response" };
		}

		public async Task<ApiResponse<UserProfile>> MeAsync(string token)
		{
			SetBearer(token);

			var resp = await _http.GetAsync("api/auth/me");

			if (!resp.IsSuccessStatusCode)
			{
				var err = await SafeRead<ApiResponse<UserProfile>>(resp);
				return err ?? new ApiResponse<UserProfile>
				{
					Success = false,
					Message = $"HTTP {(int)resp.StatusCode} {resp.ReasonPhrase}"
				};
			}

			var data = await resp.Content.ReadFromJsonAsync<ApiResponse<UserProfile>>();
			return data ?? new ApiResponse<UserProfile> { Success = false, Message = "Empty response" };
		}

		// =========================
		// BLOG (CRUD + Search + Sort)
		// API route bạn nói: /api/blogs
		// =========================
		public async Task<ApiResponse<List<BlogListItem>>> GetBlogsAsync(
			string token,
			string? search = null,
			string? sortBy = null,
			string? sortDir = null
		)
		{
			SetBearer(token);

			var qs = new List<string>();
			if (!string.IsNullOrWhiteSpace(search))
				qs.Add($"search={Uri.EscapeDataString(search)}");
			if (!string.IsNullOrWhiteSpace(sortBy))
				qs.Add($"sortBy={Uri.EscapeDataString(sortBy)}");
			if (!string.IsNullOrWhiteSpace(sortDir))
				qs.Add($"sortDir={Uri.EscapeDataString(sortDir)}");

			var url = "api/blogs";
			if (qs.Count > 0) url += "?" + string.Join("&", qs);

			var resp = await _http.GetAsync(url);

			if (!resp.IsSuccessStatusCode)
			{
				var err = await SafeRead<ApiResponse<List<BlogListItem>>>(resp);
				return err ?? new ApiResponse<List<BlogListItem>>
				{
					Success = false,
					Message = $"HTTP {(int)resp.StatusCode} {resp.ReasonPhrase}"
				};
			}

			var data = await resp.Content.ReadFromJsonAsync<ApiResponse<List<BlogListItem>>>();
			return data ?? new ApiResponse<List<BlogListItem>> { Success = false, Message = "Empty response" };
		}

		public async Task<ApiResponse<BlogDetail>> GetBlogByIdAsync(string token, int id)
		{
			SetBearer(token);

			var resp = await _http.GetAsync($"api/blogs/{id}");

			if (!resp.IsSuccessStatusCode)
			{
				var err = await SafeRead<ApiResponse<BlogDetail>>(resp);
				return err ?? new ApiResponse<BlogDetail>
				{
					Success = false,
					Message = $"HTTP {(int)resp.StatusCode} {resp.ReasonPhrase}"
				};
			}

			var data = await resp.Content.ReadFromJsonAsync<ApiResponse<BlogDetail>>();
			return data ?? new ApiResponse<BlogDetail> { Success = false, Message = "Empty response" };
		}

		public async Task<ApiResponse<BlogDetail>> CreateBlogAsync(string token, CreateBlogRequest req)
		{
			SetBearer(token);

			var resp = await _http.PostAsJsonAsync("api/blogs", req);

			if (!resp.IsSuccessStatusCode)
			{
				var err = await SafeRead<ApiResponse<BlogDetail>>(resp);
				return err ?? new ApiResponse<BlogDetail>
				{
					Success = false,
					Message = $"HTTP {(int)resp.StatusCode} {resp.ReasonPhrase}"
				};
			}

			var data = await resp.Content.ReadFromJsonAsync<ApiResponse<BlogDetail>>();
			return data ?? new ApiResponse<BlogDetail> { Success = false, Message = "Empty response" };
		}

		public async Task<ApiResponse<BlogDetail>> UpdateBlogAsync(string token, int id, UpdateBlogRequest req)
		{
			SetBearer(token);

			var resp = await _http.PutAsJsonAsync($"api/blogs/{id}", req);

			if (!resp.IsSuccessStatusCode)
			{
				var err = await SafeRead<ApiResponse<BlogDetail>>(resp);
				return err ?? new ApiResponse<BlogDetail>
				{
					Success = false,
					Message = $"HTTP {(int)resp.StatusCode} {resp.ReasonPhrase}"
				};
			}

			var data = await resp.Content.ReadFromJsonAsync<ApiResponse<BlogDetail>>();
			return data ?? new ApiResponse<BlogDetail> { Success = false, Message = "Empty response" };
		}

		public async Task<ApiResponse<object>> DeleteBlogAsync(string token, int id)
		{
			SetBearer(token);

			var resp = await _http.DeleteAsync($"api/blogs/{id}");

			if (!resp.IsSuccessStatusCode)
			{
				var err = await SafeRead<ApiResponse<object>>(resp);
				return err ?? new ApiResponse<object>
				{
					Success = false,
					Message = $"HTTP {(int)resp.StatusCode} {resp.ReasonPhrase}"
				};
			}

			var data = await resp.Content.ReadFromJsonAsync<ApiResponse<object>>();
			return data ?? new ApiResponse<object> { Success = true, Message = "Deleted" };
		}

		// =========================
		// UPLOAD thumbnail
		// API route trong swagger: /api/upload/blog-thumbnail
		// =========================
		public async Task<ApiResponse<UploadResult>> UploadBlogThumbnailAsync(string token, IFormFile file)
		{
			SetBearer(token);

			using var form = new MultipartFormDataContent();

			using var stream = file.OpenReadStream();
			using var fileContent = new StreamContent(stream);
			fileContent.Headers.ContentType = new MediaTypeHeaderValue(file.ContentType);

			// "file" là key phổ biến, nếu API bạn dùng key khác thì đổi tại đây
			form.Add(fileContent, "file", file.FileName);

			var resp = await _http.PostAsync("api/upload/blog-thumbnail", form);

			if (!resp.IsSuccessStatusCode)
			{
				var err = await SafeRead<ApiResponse<UploadResult>>(resp);
				return err ?? new ApiResponse<UploadResult>
				{
					Success = false,
					Message = $"HTTP {(int)resp.StatusCode} {resp.ReasonPhrase}"
				};
			}

			var data = await resp.Content.ReadFromJsonAsync<ApiResponse<UploadResult>>();
			return data ?? new ApiResponse<UploadResult> { Success = false, Message = "Empty response" };
		}

		// =========================
		// Helpers
		// =========================
		private void SetBearer(string token)
		{
			_http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
		}

		private static async Task<T?> SafeRead<T>(HttpResponseMessage resp)
		{
			try
			{
				return await resp.Content.ReadFromJsonAsync<T>();
			}
			catch
			{
				return default;
			}
		}
	}
}
