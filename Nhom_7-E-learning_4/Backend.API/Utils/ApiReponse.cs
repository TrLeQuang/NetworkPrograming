namespace Backend.API.Utils
{
	public class ApiResponse<T>
	{
		public bool Success { get; set; }
		public string Code { get; set; } = "OK";
		public string Message { get; set; } = "";
		public T? Data { get; set; }
		public object? Errors { get; set; }

		public static ApiResponse<T> Ok(T? data, string message = "OK")
		{
			return new ApiResponse<T>
			{
				Success = true,
				Message = message,
				Data = data
			};
		}

		public static ApiResponse<T> Fail(string message, string code = "ERROR", object? errors = null)
		{
			return new ApiResponse<T>
			{
				Success = false,
				Code = code,
				Message = message,
				Errors = errors
			};
		}
	}
}
