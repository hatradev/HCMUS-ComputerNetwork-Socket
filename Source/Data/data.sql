IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'FOODORDER')
BEGIN
	CREATE DATABASE FOODORDER;
END
GO

USE FOODORDER
GO


CREATE TABLE account(
    [table_name] [int] NULL,
    [password] [nvarchar](50) NULL
);
GO


CREATE TABLE menu(
	[id] [int] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](50) NULL,
	[price] [int] NULL,
	[note] [text] NULL
);
GO

CREATE TABLE orderlist(
	[table_name] [int] NULL,
	[food_name] [nvarchar](50) NULL,
	[amount] [int] NULL,
	[status] [int] NULL,
	[cash_type] [nvarchar](50) NULL,
	[time_order] [nvarchar](50) NULL
);
GO

insert account values ('0','admin')
insert account values ('1','orderfood')
insert account values ('2','orderfood')
insert account values ('3','orderfood')
insert account values ('4','orderfood')
insert account values ('5','orderfood')
GO

insert menu values ('1','Banh cuon',25000,NULL)
insert menu values ('2','Banh can',20000,NULL)
insert menu values ('3','Mi quang',35000,NULL)
insert menu values ('4','Cafe den',27000,NULL)
insert menu values ('5','Cafe sua',30000,NULL)
insert menu values ('6','Bun thit nuong',30000,NULL)
insert menu values ('7','Kem trai cay',25000,NULL)
insert menu values ('8','Che trai cay',30000,NULL)
insert menu values ('9','Banh trang nuong',20000,NULL)
insert menu values ('10','Com ga',45000,NULL)
insert menu values ('11','Com tam',50000,NULL)
insert menu values ('12','Hu tieu',35000,NULL)
GO

