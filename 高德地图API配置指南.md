# 高德地图API配置指南

本指南说明如何配置高德地图API，实现在地图上直接定位功能。

## 功能说明

集成了高德地图API，支持：
- ✅ 在地图上可视化选择位置
- ✅ 可调整1-50米的范围标记
- ✅ 自动获取当前位置
- ✅ 拖拽标记调整位置
- ✅ 逆地理编码自动获取地址
- ✅ 响应式设计，支持移动端

## 准备工作

### 1. 注册高德开放平台账号

1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 点击右上角"注册"
3. 填写注册信息完成账号注册
4. 实名认证（个人或企业）

### 2. 创建应用获取密钥

1. 登录高德开放平台
2. 进入 [应用管理](https://console.amap.com/dev/key/app)
3. 点击"创建新应用"
4. 填写应用信息：
   - 应用名称：如"校园失物招领系统"
   - 应用类型：选择"Web端（JS API）"
   - 应用描述：如"用于校园失物招领系统定位"
5. 点击"添加Key"
6. 填写Key信息：
   - Key名称：如"网页定位"
   - 服务平台：选择"Web端(JS API)"
   - 绑定域名IP：填写你的域名（如 `localhost` 或你的服务器IP）
7. 创建成功后，复制**Key**（一串32位的字符串）

## 配置步骤

### 方式一：修改HTML文件（快速测试）

直接修改 `publish_lost.html` 和 `publish_found.html` 中的API Key：

```html
<!-- 找到这一行 -->
<script src="https://webapi.amap.com/maps?v=2.0&key=YOUR_AMAP_KEY"></script>

<!-- 替换为 -->
<script src="https://webapi.amap.com/maps?v=2.0&key=your_actual_key_here"></script>
```

### 方式二：使用环境变量（推荐生产环境）

创建 `config.js` 文件，在页面加载前配置：

```javascript
// config.js
window.AMAP_KEY = 'your_actual_key_here';
```

然后在HTML中引用：

```html
<script src="config.js"></script>
<script src="https://webapi.amap.com/maps?v=2.0&key=" + window.AMAP_KEY + "'></script>
```

### 方式三：后端动态加载（推荐）

在Flask中创建配置路由：

```python
# app/routes.py
@app.route('/config')
def get_config():
    """获取前端配置"""
    return jsonify({
        'amap_key': os.getenv('AMAP_KEY', '')
    })
```

前端JavaScript动态加载：

```javascript
// 在页面加载前获取配置
fetch('/config')
    .then(response => response.json())
    .then(config => {
        // 动态加载高德地图API
        const script = document.createElement('script');
        script.src = `https://webapi.amap.com/maps?v=2.0&key=${config.amap_key}`;
        document.head.appendChild(script);
    });
```

## 使用说明

### 发布失物/招领时使用地图

1. 填写物品基本信息
2. 点击"📍 地图定位"按钮
3. 地图弹窗打开后：
   - **选择位置**：在地图上点击想要标记的位置
   - **调整范围**：拖动滑块设置1-50米的范围半径
   - **精确定位**：拖拽红色标记到准确位置
   - **当前位置**：首次打开会尝试自动定位到当前位置
4. 点击"确定位置"确认
5. 系统自动填充地址、经纬度和范围

### 功能特性

#### 1. 地图标记
- **蓝色标记**：您的当前位置（GPS定位）
- **红色标记**：您选择的位置（可拖拽）
- **紫色圆圈**：范围半径（1-50米可调）

#### 2. 交互操作
- **点击地图**：在点击位置添加/移动标记
- **拖拽标记**：精确定位到准确位置
- **调整滑块**：实时更新范围圆圈大小
- **缩放地图**：使用滚轮或地图工具条缩放
- **平移地图**：按住鼠标左键拖动

#### 3. 地址自动填充
- 确认位置后，系统会调用逆地理编码
- 将经纬度转换为可读的地址格式
- 如果编码失败，显示经纬度坐标

## 常见问题

### 1. 地图无法显示？

检查以下几点：
1. **API Key是否正确**：确保替换了`YOUR_AMAP_KEY`为实际密钥
2. **域名/IP是否绑定**：在高德控制台检查绑定的域名/IP
3. **网络连接**：检查是否能访问高德地图API
4. **控制台错误**：按F12查看浏览器控制台错误信息

### 2. 无法获取当前位置？

可能原因：
- **非HTTPS环境**：定位功能需要HTTPS（localhost除外）
- **浏览器权限**：允许浏览器访问位置信息
- **位置服务关闭**：检查设备的位置服务是否开启

解决方案：
```javascript
// 检查浏览器是否支持定位
if (!navigator.geolocation) {
    alert('您的浏览器不支持定位功能');
}
```

### 3. 如何查看免费额度？

高德地图API免费额度：
- **日调用量**：每日免费100万次
- **并发数**：50 QPS（每秒查询数）
- **QPS超限**：超出限制会返回错误

查看用量：
1. 登录高德开放平台
2. 进入 [控制台](https://console.amap.com/dev/statistics/)
3. 查看每日调用统计

### 4. 绑定多个域名？

在创建Key时可以绑定多个域名，用英文逗号分隔：
```
localhost,example.com,www.example.com,192.168.1.100
```

### 5. IP地址动态变化？

如果您的服务器IP会变化：
- 方法1：绑定域名，使用域名访问
- 方法2：创建多个Key，分别绑定不同IP
- 方法3：不绑定IP（仅用于开发测试）

## 安全建议

1. **不要在前端暴露API Key**
   - 生产环境使用后端代理或环境变量
   - 不要将Key提交到版本控制系统

2. **限制域名绑定**
   - 只绑定实际使用的域名
   - 避免绑定过于宽泛（如*）

3. **监控API调用**
   - 定期查看高德控制台的调用统计
   - 发现异常调用及时处理

4. **设置域名白名单**
   - 在高德控制台设置访问白名单
   - 限制只有特定域名可以调用

## 技术细节

### 地图API版本

当前使用：Web端 JavaScript API v2.0

```javascript
// 加载地图API
<script src="https://webapi.amap.com/maps?v=2.0&key=YOUR_KEY"></script>
```

### 主要功能调用

```javascript
// 创建地图实例
const map = new AMap.Map('map', {
    zoom: 16,
    center: [116.397428, 39.90923],
    viewMode: '2D'
});

// 添加标记
const marker = new AMap.Marker({
    position: [lng, lat],
    draggable: true
});
map.add(marker);

// 添加圆圈
const circle = new AMap.Circle({
    center: [lng, lat],
    radius: 50,  // 半径（米）
    strokeColor: '#667eea',
    fillColor: '#667eea',
    fillOpacity: 0.2
});
map.add(circle);

// 地图点击事件
map.on('click', function(e) {
    const lnglat = e.lnglat;
    console.log(lnglat.getLng(), lnglat.getLat());
});
```

### 逆地理编码

将经纬度转换为地址：

```javascript
// 使用OpenStreetMap Nominatim API（免费）
fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&accept-language=zh-CN`)
    .then(response => response.json())
    .then(data => {
        console.log(data.display_name);
    });
```

## 扩展功能

### 1. 保存历史位置

```javascript
// 使用localStorage保存常用位置
function saveLocation(name, lat, lng, radius) {
    const locations = JSON.parse(localStorage.getItem('savedLocations') || '[]');
    locations.push({ name, lat, lng, radius, time: new Date() });
    localStorage.setItem('savedLocations', JSON.stringify(locations));
}

function loadSavedLocations() {
    return JSON.parse(localStorage.getItem('savedLocations') || '[]');
}
```

### 2. 地点搜索集成

可以集成高德地图的地点搜索API：

```javascript
// 使用AMap.PlaceSearch插件
AMap.plugin(['AMap.PlaceSearch'], function() {
    const placeSearch = new AMap.PlaceSearch({
        pageSize: 5,
        pageIndex: 1,
        city: '010',  // 城市代码
        map: map
    });
    
    placeSearch.search('图书馆', function(status, result) {
        console.log(result);
    });
});
```

### 3. 路径规划

显示从当前位置到目标位置的路径：

```javascript
AMap.plugin(['AMap.Driving'], function() {
    const driving = new AMap.Driving({
        map: map,
        policy: AMap.DrivingPolicy.LEAST_TIME
    });
    
    driving.search(
        new AMap.LngLat(startLng, startLat),
        new AMap.LngLat(endLng, endLat),
        function(status, result) {
            console.log(result.routes);
        }
    );
});
```

## 附录

### A. 高德地图Key申请流程图

```
1. 注册账号
   ↓
2. 实名认证
   ↓
3. 创建应用
   ↓
4. 添加Key
   ↓
5. 绑定域名/IP
   ↓
6. 获取Key并配置
```

### B. 完整配置示例

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>地图示例</title>
    <!-- 高德地图API -->
    <script src="https://webapi.amap.com/maps?v=2.0&key=your_key_here"></script>
    <style>
        #map {
            width: 100%;
            height: 400px;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // 初始化地图
        const map = new AMap.Map('map', {
            zoom: 16,
            center: [116.397428, 39.90923]
        });
    </script>
</body>
</html>
```

### C. 测试Key是否有效

创建 `test_map.html` 测试：

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>高德地图测试</title>
    <script src="https://webapi.amap.com/maps?v=2.0&key=your_key_here"></script>
</head>
<body>
    <div id="map" style="width: 600px; height: 400px;"></div>
    <script>
        const map = new AMap.Map('map', {
            zoom: 11,
            center: [116.397428, 39.90923]
        });
        
        if (map) {
            alert('地图加载成功！Key有效。');
        } else {
            alert('地图加载失败！请检查Key。');
        }
    </script>
</body>
</html>
```

在浏览器中打开此文件测试。

## 技术支持

- 高德开放平台文档：https://lbs.amap.com/api/jsapi-v2/summary
- API错误码说明：https://lbs.amap.com/api/jsapi-v2/guide/appendix/error_code
- 在线示例：https://lbs.amap.com/demo/javascript-api/example

---

**最后更新：2026年**
**版本：1.0**
