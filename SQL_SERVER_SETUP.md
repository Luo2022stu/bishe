# SQL Server 数据库连接指南

本系统支持连接 Microsoft SQL Server 数据库。

## 前置要求

### 1. 安装 SQL Server

#### 选项A：安装 SQL Server Express（免费）
下载地址：https://www.microsoft.com/zh-cn/sql-server/sql-server-downloads

#### 选项B：使用 SQL Server Developer（免费）
下载地址：https://www.microsoft.com/zh-cn/sql-server/sql-server-downloads

### 2. 安装 ODBC 驱动

下载并安装 ODBC Driver 17 for SQL Server：
- Windows: https://go.microsoft.com/fwlink/?linkid=2249004
- Linux: https://docs.microsoft.com/zh-cn/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server

### 3. 安装 Python 驱动

```bash
pip install pyodbc
```

## 连接步骤

### 步骤1：创建数据库

使用 SQL Server Management Studio (SSMS) 或 T-SQL 创建数据库：

```sql
CREATE DATABASE lost_found;
GO
```

### 步骤2：配置 `.env` 文件

编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_TYPE=mssql

# SQL Server 配置
MSSQL_HOST=localhost
MSSQL_PORT=1433
MSSQL_USER=sa
MSSQL_PASSWORD=your_password
MSSQL_DATABASE=lost_found
MSSQL_DRIVER=ODBC+Driver+17+for+SQL+Server
```

### 步骤3：修改连接信息

根据您的实际情况修改以下参数：

- `MSSQL_HOST`: SQL Server 服务器地址
  - 本地：`localhost` 或 `127.0.0.1`
  - 远程：服务器IP或域名

- `MSSQL_PORT`: SQL Server 端口（默认1433）

- `MSSQL_USER`: 数据库用户名（通常是 `sa`）

- `MSSQL_PASSWORD`: 数据库密码

- `MSSQL_DATABASE`: 数据库名称（`lost_found`）

- `MSSQL_DRIVER`: ODBC 驱动名称
  - Windows: `ODBC+Driver+17+for+SQL+Server`
  - Linux: `ODBC+Driver+18+for+SQL+Server`

### 步骤4：启动应用

```bash
python app.py
```

成功连接后会显示：
```
✓ 使用 SQL Server 数据库: localhost:1433/lost_found
默认管理员账户已创建: admin / admin123
 * Running on http://127.0.0.1:5000
```

## 连接 Azure SQL Database

### 1. 创建 Azure SQL Database

1. 登录 Azure 门户
2. 创建 SQL Database
3. 数据库名称：`lost_found`
4. 获取连接字符串

### 2. 配置 `.env` 文件

```env
DATABASE_TYPE=mssql

# Azure SQL Database 配置
MSSQL_HOST=your_server.database.windows.net
MSSQL_PORT=1433
MSSQL_USER=your_username@your_server
MSSQL_PASSWORD=your_password
MSSQL_DATABASE=lost_found
MSSQL_DRIVER=ODBC+Driver+17+for+SQL+Server
```

### 3. 配置防火墙

在 Azure SQL Database 的"防火墙和虚拟网络"中添加：
- 允许访问的 IP 地址
- 或勾选"允许 Azure 服务和资源访问此服务器"

## 常见问题

### Q1: 连接失败，提示 "Login failed for user"

**解决方案：**
1. 检查用户名和密码是否正确
2. 确认 SQL Server 身份验证模式已启用
3. 检查用户是否有访问该数据库的权限

```sql
-- 授予权限
USE lost_found;
GO
CREATE USER your_username FOR LOGIN your_username;
ALTER ROLE db_owner ADD MEMBER your_username;
GO
```

### Q2: 提示 "Cannot open database"

**解决方案：**
1. 确认数据库已创建
2. 检查数据库名称拼写
3. 确认用户有访问该数据库的权限

### Q3: 提示 "Driver not found"

**解决方案：**
1. 确认已安装 ODBC Driver 17 for SQL Server
2. 检查驱动名称是否正确
3. Windows 下运行 `odbcad32.exe` 查看已安装的驱动

### Q4: 连接超时

**解决方案：**
1. 检查 SQL Server 服务是否运行
2. 检查防火墙设置
3. 确认端口 1433 未被占用
4. 检查 SQL Server 是否允许远程连接

```sql
-- 启用远程连接
EXEC sp_configure 'remote access', 1;
RECONFIGURE;
GO
```

### Q5: Azure SQL 连接失败

**解决方案：**
1. 检查防火墙规则
2. 确认使用正确的用户名格式：`username@servername`
3. 检查 SSL/TLS 设置
4. 确认订阅状态正常

## 测试连接

### 使用 Python 测试

```python
import pyodbc

# 连接字符串
conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=lost_found;'
    'UID=sa;'
    'PWD=your_password;'
)

try:
    conn = pyodbc.connect(conn_str)
    print('✓ 连接成功！')
    conn.close()
except Exception as e:
    print(f'✗ 连接失败: {e}')
```

### 使用 SQL Server Management Studio 测试

1. 打开 SSMS
2. 输入服务器名称、用户名、密码
3. 点击"连接"
4. 如果成功，说明配置正确

## 性能优化

### SQL Server 配置优化

```sql
-- 设置最大内存
EXEC sp_configure 'max server memory', 4096;
RECONFIGURE;
GO

-- 设置最大并发连接数
EXEC sp_configure 'max user connections', 200;
RECONFIGURE;
GO
```

### 连接池配置

在 `app.py` 中添加：

```python
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 5
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600
```

## 备份与恢复

### 备份数据库

```sql
BACKUP DATABASE lost_found
TO DISK = 'C:\backup\lost_found.bak'
WITH FORMAT,
MEDIANAME = 'SQLServerBackups',
NAME = 'Full Backup of lost_found';
GO
```

### 恢复数据库

```sql
RESTORE DATABASE lost_found
FROM DISK = 'C:\backup\lost_found.bak'
WITH REPLACE;
GO
```

## 安全建议

1. **使用强密码**
2. **限制 sa 账户使用**
3. **定期备份数据库**
4. **启用 SQL Server 审计**
5. **使用 Windows 身份验证（如果可能）**
6. **定期更新 SQL Server 补丁**
7. **限制数据库访问权限**

## 迁移数据

### 从 SQLite 迁移到 SQL Server

```python
import sqlite3
import pyodbc

# 读取 SQLite 数据
sqlite_conn = sqlite3.connect('lost_found.db')
sqlite_cursor = sqlite_conn.cursor()

# 连接 SQL Server
mssql_conn = pyodbc.connect('your_connection_string')
mssql_cursor = mssql_conn.cursor()

# 迁移用户数据
sqlite_cursor.execute('SELECT * FROM user')
users = sqlite_cursor.fetchall()

for user in users:
    mssql_cursor.execute('''
        INSERT INTO user (username, password, email, phone, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', user[1:])

mssql_conn.commit()
```

## 总结

现在您的系统已经支持 SQL Server 数据库了！根据您的需求选择：

- **本地开发**：SQL Server Express
- **生产环境**：SQL Server Standard/Enterprise
- **云部署**：Azure SQL Database

如有任何问题，请参考上述常见问题解决方案。
