# 外部数据库配置指南

本系统支持连接多种外部数据库：SQLite、MySQL、PostgreSQL

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

## 数据库配置选项

### 选项1：SQLite（默认，无需额外配置）

`.env` 文件：
```env
DATABASE_TYPE=sqlite
SQLITE_DB_PATH=lost_found.db
```

### 选项2：MySQL

#### 安装MySQL驱动
```bash
pip install pymysql
```

#### 创建数据库
```sql
CREATE DATABASE lost_found CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 配置 `.env` 文件
```env
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=lost_found
```

#### 启动应用
```bash
python app.py
```

### 选项3：PostgreSQL

#### 安装PostgreSQL驱动
```bash
pip install psycopg2-binary
```

#### 创建数据库
```sql
CREATE DATABASE lost_found;
```

#### 配置 `.env` 文件
```env
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=lost_found
```

#### 启动应用
```bash
python app.py
```

## 云数据库配置示例

### 阿里云RDS MySQL
```env
DATABASE_TYPE=mysql
MYSQL_HOST=rm-xxxxx.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=lost_found
```

### 腾讯云PostgreSQL
```env
DATABASE_TYPE=postgresql
POSTGRES_HOST=pg-xxxxx.postgres.tencentcdb.com
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=lost_found
```

### 华为云GaussDB
```env
DATABASE_TYPE=postgresql
POSTGRES_HOST=xxxxx.gaussdb.huaweicloud.com
POSTGRES_PORT=8000
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=lost_found
```

## 数据库迁移

如果从SQLite迁移到MySQL/PostgreSQL：

### 方法1：使用数据导出导入

1. 导出SQLite数据
```bash
python export_sqlite_data.py
```

2. 在目标数据库中导入数据

### 方法2：使用ORM迁移

```python
from app import app, db, User, LostItem

# 读取SQLite数据
sqlite_conn = sqlite3.connect('lost_found.db')
# ... 迁移逻辑
```

## 常见问题

### Q: 连接MySQL失败
A: 检查以下几点：
1. MySQL服务是否启动
2. 用户名密码是否正确
3. 数据库是否已创建
4. 防火墙是否允许连接

### Q: 连接PostgreSQL失败
A: 检查以下几点：
1. PostgreSQL服务是否启动
2. pg_hba.conf 是否允许连接
3. 数据库是否已创建
4. 用户权限是否足够

### Q: 字符编码问题
A: 确保数据库使用UTF-8编码：
```sql
-- MySQL
ALTER DATABASE lost_found CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- PostgreSQL
CREATE DATABASE lost_found ENCODING 'UTF8';
```

## 安全建议

1. **不要将 `.env` 文件提交到版本控制**
2. **使用强密码**
3. **限制数据库用户权限**
4. **定期备份数据库**
5. **使用SSL连接生产数据库**

## 性能优化

### MySQL优化
```env
# 在MySQL配置文件中添加
[mysqld]
max_connections=200
innodb_buffer_pool_size=1G
```

### PostgreSQL优化
```env
# 在postgresql.conf中添加
shared_buffers = 256MB
max_connections = 200
```
