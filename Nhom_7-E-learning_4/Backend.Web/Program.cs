// File: Backend.Web/Program.cs
using Backend.Web.Services;

var builder = WebApplication.CreateBuilder(args);

// MVC
builder.Services.AddControllersWithViews();

// Session
builder.Services.AddSession(options =>
{
	options.IdleTimeout = TimeSpan.FromHours(2);
	options.Cookie.HttpOnly = true;
	options.Cookie.IsEssential = true;
});

// HttpClient for ApiClient
var apiBaseUrl = builder.Configuration["Api:BaseUrl"];
if (string.IsNullOrWhiteSpace(apiBaseUrl))
	throw new Exception("Missing config: Api:BaseUrl in Backend.Web/appsettings.json");

// ép format chuẩn: phải có scheme và dấu /
if (!apiBaseUrl.StartsWith("http://") && !apiBaseUrl.StartsWith("https://"))
	throw new Exception("Api:BaseUrl must start with http:// or https://");

if (!apiBaseUrl.EndsWith("/"))
	apiBaseUrl += "/";

builder.Services.AddHttpClient<ApiClient>(client =>
{
	client.BaseAddress = new Uri(apiBaseUrl);
});

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
	app.UseExceptionHandler("/Home/Error");
	app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();

app.UseSession();      // ✅ trước
app.UseAuthorization();

app.MapControllerRoute(
	name: "default",
	pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();
