# 百度地图API配置指南

本指南说明如何配置百度地图API，实现在地图上直接定位功能。

## 功能说明

集成了百度地图API，支持：
- ✅ 在地图上可视化选择位置
- ✅ 可调整1-50米的范围标记
- ✅ 自动获取当前位置
- ✅ 拖拽标记调整位置
- ✅ 逆地理编码自动获取地址
- ✅ 响应式设计，支持移动端

## 准备工作

### 1. 注册百度地图开放平台账号

1. 访问 [百度地图开放平台](https://lbsyun.baidu.com/)
2. 点击右上角"注册"
3. 填写注册信息完成账号注册
4. 实名认证（个人或企业）

### 2. 创建应用获取密钥（AK）

1. 登录百度地图开放平台
2. 进入 [应用管理](https://lbsyun.baidu.com/apiconsole/key/create)
3. 点击"创建应用"
4. 填写应用信息：
   - 应用名称：如"校园失物招领系统"
   - 应用类型：选择"浏览器端"
   - 应用服务：勾选"JavaScript API v3.0"
   - Referer白名单：填写 `*`（开发测试）或指定域名
5. 点击"提交"
6. 创建成功后，复制**访问应用（AK）**（一串24位的字符串）

## 配置步骤

### 方式一：直接修改HTML文件（快速测试）

直接修改 `publish_lost.html` 和 `publish_found.html` 中的AK：

```html
<!-- 找到这一行 -->
<script type="text/javascript" src="https://api.map.baidu.com/api?v=3.0&ak=YOUR_BAIDU_AK"></script>

<!-- 替换为 -->
<script type="text/javascript" src="https://api.map.baidu.com/api?v=3.0&ak=your_actual_ak_here"></script>
```

### 方式二：使用环境变量（推荐生产环境）

创建 `config.js` 文件，在页面加载前配置：

```javascript
// config.js
window.BAIDU_AK = 'your_actual_ak_here';
```

然后在HTML中引用：

```html
<script src="config.js"></script>
<script type="text/javascript" src="https://api.map.baidu.com/api?v=3.0&ak=" + window.BAIDU_AK + "'></script>
```

### 方式三：后端动态加载（推荐）

在Flask中创建配置路由：

```python
# app/routes.py
@app.route('/config')
def get_config():
    """获取前端配置"""
    return jsonify({
        'baidu_ak': os.getenv('BAIDU_AK', '')
    })
```

前端JavaScript动态加载：

```javascript
// 在页面加载前获取配置
fetch('/config')
    .then(response => response.json())
    .then(config => {
        // 动态加载百度地图API
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = `https://api.map.baidu.com/api?v=3.0&ak=${config.baidu_ak}`;
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
1. **AK是否正确**：确保替换了`YOUR_BAIDU_AK`为实际密钥
2. **Referer白名单**：在百度控制台检查Referer设置
3. **网络连接**：检查是否能访问百度地图API
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

百度地图JavaScript API免费额度：
- **日调用量**：每日免费10万次
- **QPS限制**：50 QPS（每秒查询数）

查看用量：
1. 登录百度地图开放平台
2. 进入 [控制台](https://lbsyun.baidu.com/apiconsole/monitor)
3. 查看每日调用统计

### 4. Referer白名单设置？

Referer白名单用于限制访问来源：
- **开发测试**：填写 `*`（允许所有来源）
- **生产环境**：填写具体域名，如 `http://localhost:5000` 或 `http://yourdomain.com`
- **多个域名**：用英文逗号分隔：`http://localhost:5000,http://192.168.1.100:5000`

### 5. 本地开发访问方式？

如果您的服务器IP会变化：
- 方法1：使用 `localhost` 访问，白名单设为 `http://localhost:5000`
- 方法2：白名单设为 `*`，但只用于开发测试
- 方法3：使用固定IP，白名单设为对应IP

## 安全建议

1. **不要在前端暴露AK**
   - 生产环境使用后端代理或环境变量
   - 不要将AK提交到版本控制系统

2. **限制Referer白名单**
   - 只绑定实际使用的域名
   - 避免使用过于宽泛的设置（如*）

3. **监控API调用**
   - 定期查看百度控制台的调用统计
   - 发现异常调用及时处理

4. **设置IP白名单**
   - 在百度控制台设置访问白名单
   - 限制只有特定IP可以调用

## 技术细节

### 地图API版本

当前使用：百度地图 JavaScript API v3.0

```javascript
// 加载地图API
<script type="text/javascript" src="https://api.map.baidu.com/api?v=3.0&ak=YOUR_AK"></script>
```

### 主要功能调用

```javascript
// 创建地图实例
const map = new BMap.Map('map');
map.centerAndZoom(new BMap.Point(116.404, 39.915), 11);

// 添加标记
const point = new BMap.Point(116.404, 39.915);
const marker = new BMap.Marker(point);
marker.enableDragging(true);
map.addOverlay(marker);

// 添加圆圈
const circle = new BMap.Circle(point, 1000, {
    strokeColor: 'blue',
    strokeWeight: 2,
    fillColor: 'blue',
    fillOpacity: 0.3
});
map.addOverlay(circle);

// 地图点击事件
map.addEventListener('click', function(e) {
    const point = e.point;
    console.log(point.lng, point.lat);
});

// 定位
const geolocation = new BMap.Geolocation();
geolocation.getCurrentPosition(function(r) {
    if (this.getStatus() == BMAP_STATUS_SUCCESS) {
        const lng = r.point.lng;
        const lat = r.point.lat;
        map.centerAndZoom(new BMap.Point(lng, lat), 16);
    }
});

// 逆地理编码
const geocoder = new BMap.Geocoder();
const point = new BMap.Point(116.364, 39.993);
geocoder.getLocation(point, function(result) {
    console.log(result.address);
});
```

### 逆地理编码

将经纬度转换为地址：

```javascript
// 使用百度地图逆地理编码
const geocoder = new BMap.Geocoder();
const point = new BMap.Point(116.404, 39.915);

geocoder.getLocation(point, function(result) {
    if (result) {
        console.log(result.address);
        console.log(result.addressComponent);
    }
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

可以集成百度地图的地点搜索API：

```javascript
// 使用LocalSearch插件
const local = new BMap.LocalSearch(map, {
    renderOptions: { map: map, autoViewport: true }
});

local.search('图书馆', function(results) {
    console.log(results);
});
```

### 3. 路径规划

显示从当前位置到目标位置的路径：

```javascript
const driving = new BMap.DrivingRoute(map, {
    renderOptions: { map: map, autoViewport: true }
});

const start = new BMap.Point(116.404, 39.915);
const end = new BMap.Point(116.408, 39.918);
driving.search(start, end);
```

## 附录

### A. 百度地图AK申请流程图

```
1. 注册账号
   ↓
2. 实名认证
   ↓
3. 创建应用
   ↓
4. 选择应用类型（浏览器端）
   ↓
5. 填写Referer白名单
   ↓
6. 获取AK并配置
```

### B. 完整配置示例

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>百度地图示例</title>
    <script type="text/javascript" src="https://api.map.baidu.com/api?v=3.0&ak=your_ak_here"></script>
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
        const map = new BMap.Map('map');
        const point = new BMap.Point(116.404, 39.915);
        map.centerAndZoom(point, 11);
        map.enableScrollWheelZoom(true);
    </script>
</body>
</html>
```

### C. 测试AK是否有效

创建 `test_baidu_map.html` 测试：

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>百度地图测试</title>
    <script type="text/javascript" src="https://api.map.baidu.com/api?v=3.0&ak=your_ak_here"></script>
</head>
<body>
    <div id="map" style="width: 600px; height: 400px;"></div>
    <script>
        const map = new BMap.Map('map');
        const point = new BMap.Point(116.404, 39.915);
        map.centerAndZoom(point, 11);

        if (map) {
            alert('地图加载成功！AK有效。');
        } else {
            alert('地图加载失败！请检查AK。');
        }
    </script>
</body>
</html>
```

在浏览器中打开此文件测试。

## 与高德地图的区别

| 特性 | 百度地图 | 高德地图 |
|------|----------|----------|
| API版本 | JavaScript API v3.0 | JavaScript API v2.0 |
| 坐标系 | BD09 | GCJ02 |
| 免费额度 | 10万次/日 | 100万次/日 |
| 定位精度 | 较高 | 较高 |
| 文档 | 百度地图开放平台 | 高德开放平台 |

## 技术支持

- 百度地图开放平台文档：https://lbsyun.baidu.com/index.php?title=jspopular3.0
- API错误码说明：https://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-errorcode
- 在线示例：https://lbsyun.baidu.com/jsdemo.htm

---

**最后更新：2026年**
**版本：1.0**
