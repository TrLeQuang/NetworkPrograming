USE E_LEARNING_DB;
GO

-- ====== Users ======
IF OBJECT_ID('dbo.Users','U') IS NOT NULL DROP TABLE dbo.Users;
GO
CREATE TABLE dbo.Users (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Email NVARCHAR(255) NOT NULL UNIQUE,
    PasswordHash NVARCHAR(255) NOT NULL,
    FullName NVARCHAR(100) NOT NULL,
    Role NVARCHAR(20) NOT NULL DEFAULT 'USER',
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

-- ====== Blogs ======
IF OBJECT_ID('dbo.Blogs','U') IS NOT NULL DROP TABLE dbo.Blogs;
GO
CREATE TABLE dbo.Blogs (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Title NVARCHAR(200) NOT NULL,
    Content NVARCHAR(MAX) NOT NULL,
    ThumbnailUrl NVARCHAR(500) NULL,
    AuthorId INT NOT NULL,
    IsDeleted BIT NOT NULL DEFAULT 0,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,
    CONSTRAINT FK_Blogs_Users FOREIGN KEY (AuthorId) REFERENCES dbo.Users(Id)
);
GO

-- ====== Seed users ======
INSERT INTO dbo.Users (Email, PasswordHash, FullName, Role)
VALUES
('admin@gmail.com', '123456', 'Admin', 'ADMIN'),
('user@gmail.com', '123456', 'User', 'USER');
GO

SELECT TOP 10 * FROM Blogs ORDER BY Id DESC;

SELECT Id, Title, IsDeleted FROM Blogs WHERE Id = 1;

SELECT COUNT(*) AS UsersCount FROM Users;

SELECT * FROM dbo.Users;
SELECT * FROM dbo.Blogs;
