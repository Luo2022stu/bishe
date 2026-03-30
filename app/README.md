# 校园智能找寻平台

一个功能完善的校园智能找寻平台，支持用户注册登录、发布失物信息、搜索筛选等功能。

## 功能特点

- 👤 用户注册和登录系统
- 🔐 角色权限管理（普通用户/管理员）
- 📝 发布失物招领信息
- 🔍 搜索和筛选失物
- 📊 跟踪物品状态（待认领/已认领/已归还）
- 🛡️ 权限控制（用户只能操作自己的物品，管理员可操作所有物品）
- 📱 响应式设计，支持移动端
- 💾 数据持久化存储

## 技术栈

### 后端
- Python 3.x
- Flask - Web框架
- Flask-SQLAlchemy - ORM
- Flask-CORS - 跨域支持
- SQLite - 数据库

### 前端
- HTML5
- CSS3
- JavaScript (ES6+)

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
python app.py
```

后端服务将在 `http://localhost:5000` 启动

首次启动会自动创建默认管理员账户：
- 用户名：`admin`
- 密码：`admin123`

### 3. 打开前端页面

在浏览器中打开 `index.html` 文件，或使用以下命令启动本地服务器：

```bash
# 使用Python启动简单HTTP服务器
python -m http.server 8000

# 然后在浏览器访问
# http://localhost:8000
```

## 用户角色

### 普通用户
- 注册和登录
- 发布失物招领信息
- 查看所有失物信息
- 搜索和筛选失物
- 更新和删除自己发布的物品
- 认领或标记归还物品

### 管理员
- 拥有普通用户的所有权限
- 可以更新和删除任何用户发布的物品
- 可以查看和管理所有用户
- 可以修改用户角色

## API接口

### 用户认证

#### 用户注册
```
POST /api/auth/register
Content-Type: application/json

{
  "username": "用户名",
  "email": "邮箱",
  "password": "密码"
}
```

#### 用户登录
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "用户名",
  "password": "密码"
}
```

#### 获取当前用户信息
```
GET /api/auth/user
Headers: Authorization: Bearer <token>
```

### 物品管理

#### 获取所有物品
```
GET /api/items
```

#### 创建新物品
```
POST /api/items
Content-Type: application/json
Headers: Authorization: Bearer <token> (可选)

{
  "title": "物品名称",
  "category": "物品类别",
  "location": "发现地点",
  "contact": "联系方式",
  "description": "详细描述"
}
```

#### 更新物品状态
```
PUT /api/items/:id
Content-Type: application/json
Headers: Authorization: Bearer <token>

{
  "status": "claimed"  // pending, claimed, returned
}
```

#### 删除物品
```
DELETE /api/items/:id
Headers: Authorization: Bearer <token>
```

#### 搜索物品
```
GET /api/items/search?keyword=关键词&category=类别
```

### 管理员接口

#### 获取所有用户
```
GET /api/admin/users
Headers: Authorization: Bearer <token>
```

#### 更新用户角色
```
PUT /api/admin/users/:id/role
Content-Type: application/json
Headers: Authorization: Bearer <token>

{
  "role": "admin"  // user, admin
}
```

## 使用说明

1. **注册账号**：点击"登录/注册"按钮，填写用户名、邮箱和密码进行注册
2. **登录系统**：使用注册的账号登录，或使用默认管理员账号（admin/admin123）
3. **发布信息**：登录后填写物品信息并发布
4. **搜索物品**：在搜索框输入关键词或选择类别进行筛选
5. **认领物品**：点击"认领"或"已归还"按钮更新物品状态
6. **删除信息**：点击"删除"按钮移除已处理的信息（仅限自己发布的物品或管理员）

## 权限说明

- 未登录用户：只能查看失物信息，无法发布、修改或删除
- 普通用户：可以发布信息，只能修改和删除自己发布的物品
- 管理员：可以修改和删除任何物品，可以管理用户角色

## 项目结构

```
BiShe/
├── app.py              # Flask后端应用
├── index.html          # 前端页面
├── styles.css          # 样式文件
├── script.js           # 前端逻辑
├── requirements.txt    # Python依赖
├── README.md          # 项目说明
└── lost_found.db      # SQLite数据库（自动生成）
```

## 注意事项

- 确保后端服务已启动（运行 `python app.py`）
- 首次运行会自动创建数据库文件和默认管理员账户
- 建议使用现代浏览器访问
- Token存储在localStorage中，清除浏览器数据会退出登录
- 密码使用SHA256加密存储
