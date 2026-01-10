// File: Backend.API/Program.cs

using System.Text;
using Backend.API.Data;
using Backend.API.Repositories;
using Backend.API.Services.Auth;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// =========================
// Add services
// =========================
builder.Services.AddControllers();

// ✅ DI: Database
builder.Services.AddSingleton<DbConnectionFactory>();

// ✅ DI: Repositories (Scoped is safer for request-based work)
builder.Services.AddScoped<BlogRepository>();

// ✅ DI services (Day 2)
builder.Services.AddScoped<AuthService>();
builder.Services.AddScoped<JwtTokenService>();

// =========================
// JWT Auth
// =========================
var jwt = builder.Configuration.GetSection("Jwt");
var key = jwt["Key"] ?? "";

builder.Services
	.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
	.AddJwtBearer(options =>
	{
		options.TokenValidationParameters = new TokenValidationParameters
		{
			ValidateIssuer = true,
			ValidateAudience = true,
			ValidateLifetime = true,
			ValidateIssuerSigningKey = true,

			ValidIssuer = jwt["Issuer"],
			ValidAudience = jwt["Audience"],
			IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(key)),
			ClockSkew = TimeSpan.Zero
		};
	});

// =========================
// Swagger
// =========================
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
	c.SwaggerDoc("v1", new OpenApiInfo { Title = "Backend.API", Version = "v1" });

	c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
	{
		Name = "Authorization",
		Description = "Enter: Bearer {your JWT token}",
		In = ParameterLocation.Header,
		Type = SecuritySchemeType.Http,
		Scheme = "bearer",
		BearerFormat = "JWT"
	});

	c.AddSecurityRequirement(new OpenApiSecurityRequirement
	{
		{
			new OpenApiSecurityScheme
			{
				Reference = new OpenApiReference
				{
					Type = ReferenceType.SecurityScheme,
					Id = "Bearer"
				}
			},
			new List<string>()
		}
	});
});

var app = builder.Build();

// =========================
// Configure middleware
// =========================
if (app.Environment.IsDevelopment())
{
	app.UseSwagger();
	app.UseSwaggerUI();

	// ✅ NEW: Redirect "/" to Swagger (avoid 404 at https://localhost:7092/)
	app.MapGet("/", () => Results.Redirect("/swagger"));
	// hoặc nếu bạn thích:
	// app.MapGet("/", () => Results.Redirect("/swagger/index.html"));
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();
