# 校园失物招领系统

## 📁 项目结构

```
d:/BiShe/
├── app/                    # 项目主目录
│   ├── app.py            # 后端 Flask 服务
│   ├── .env              # 环境配置
│   ├── lost_found.db     # SQLite 数据库
│   ├── static/           # 前端静态文件
│   │   ├── index.html    # 首页
│   │   ├── login.html    # 登录注册
│   │   ├── found.html    # 失物招领
│   │   ├── lost.html     # 失物找寻
│   │   ├── items.html   # 物品列表
│   │   ├── script.js     # 前端逻辑
│   │   └── styles.css    # 样式文件
│   └── ... (其他工具脚本)
├── start.bat             # 一键启动脚本
└── 开题报告.docx
```

## 🚀 快速启动

### 方式1：使用启动脚本（推荐）

双击运行 `start.bat` 文件，后端服务将自动启动。

### 方式2：手动启动

打开终端，执行：

```bash
cd d:/BiShe/app
python app.py
```

## 🌐 访问地址

后端启动成功后，在浏览器中访问：

- **首页**: http://localhost:5000/
- **登录注册**: http://localhost:5000/login.html
- **失物招领**: http://localhost:5000/found.html
- **失物找寻**: http://localhost:5000/lost.html
- **物品列表**: http://localhost:5000/items.html

## 📊 数据库

当前使用 SQLite 数据库，数据库文件位于 `app/lost_found.db`。

### 查看数据

```bash
cd d:/BiShe/app
python check_data.py
```

### 创建管理员账户

```bash
cd d:/BiShe/app
python create_admin.py
```

默认管理员：
- 用户名: `admin`
- 密码: `admin123`

## 👥 用户角色

### 普通用户
- 发布失物招领信息
- 发布失物找寻信息
- 管理自己发布的物品

### 管理员
- 拥有普通用户所有权限
- 管理所有用户的物品
- 删除任意物品

## ⚙️ 环境配置

编辑 `app/.env` 文件：

```env
# 数据库配置
DATABASE_TYPE=sqlite

# 或使用 SQL Server（需要先配置）
DATABASE_TYPE=mssql
MSSQL_HOST=localhost
MSSQL_PORT=1433
MSSQL_USER=用户名
MSSQL_PASSWORD=密码
MSSQL_DATABASE=lost_found
MSSQL_DRIVER=ODBC+Driver+17+for+SQL+Server
```

## 🔧 常见问题

### 1. 显示 "localhost 拒绝访问"
**原因**: 后端服务未启动
**解决**: 运行 `start.bat` 或手动执行 `python app.py`

### 2. 数据库连接失败
**检查**:
- `.env` 文件配置是否正确
- SQL Server 是否已安装并运行（如果使用 SQL Server）
- 数据库文件是否存在（SQLite 模式下）

### 3. 注册用户不显示在数据库
**原因**: `.env` 中配置的数据库类型与实际使用的不一致
**解决**: 确保 `.env` 中 `DATABASE_TYPE=sqlite`

## 📝 技术栈

- **后端**: Python 3.x + Flask + Flask-SQLAlchemy
- **前端**: HTML5 + CSS3 + JavaScript (ES6+)
- **数据库**: SQLite / MySQL / PostgreSQL / SQL Server
- **API**: RESTful API
- **定位**: Geolocation API + OpenStreetMap Nominatim
