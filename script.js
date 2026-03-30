const API_BASE = 'http://localhost:5000/api';
let currentUser = null;
let authToken = null;
let currentListType = 'found'; // 'found' 或 'lost'

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查当前页面
    const currentPage = window.location.pathname.split('/').pop();

    // 首页：加载统计数据
    if (currentPage === 'index.html' || currentPage === '') {
        loadStats();
        checkLoginStatus();
    }
    // 登录注册页：只检查登录状态
    else if (currentPage === 'login.html') {
        checkLoginStatus();
    }
    // 物品列表页：加载物品列表
    else if (currentPage === 'items.html') {
        checkLoginStatus();
        fetchItems(currentListType);

        // 搜索输入框回车事件
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    searchItems();
                }
            });
        }
    }
    // 其他页面（found.html, lost.html）
    else {
        checkLoginStatus();
    }
});

// 获取物品列表（供 items.html 使用）
async function fetchItems(type = 'found') {
    currentListType = type;
    try {
        const response = await fetch(`${API_BASE}/items`);
        const items = await response.json();

        // 根据类型过滤
        const filteredItems = items.filter(item => item.type === type);
        displayItems(filteredItems);
    } catch (error) {
        console.error('加载物品失败:', error);
        showError('加载物品失败，请检查后端服务是否启动');
    }
}

// 获取地理位置
function getLocation(type) {
    if (!navigator.geolocation) {
        alert('您的浏览器不支持地理位置功能');
        return;
    }

    const locationInput = document.getElementById(`${type}Location`);
    const latitudeInput = document.getElementById(`${type}Latitude`);
    const longitudeInput = document.getElementById(`${type}Longitude`);
    const locationBtn = document.querySelector(`#${type}Location`).parentElement.querySelector('.btn-location');

    locationInput.value = '正在获取位置...';
    locationBtn.disabled = true;

    // 设置超时时间（5秒）
    const timeoutId = setTimeout(() => {
        locationInput.value = '获取超时，请重试';
        latitudeInput.value = '';
        longitudeInput.value = '';
        locationBtn.disabled = false;
        alert('获取位置超时，请检查网络连接或GPS信号');
    }, 5000);

    navigator.geolocation.getCurrentPosition(
        (position) => {
            clearTimeout(timeoutId);
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            // 保存经纬度
            latitudeInput.value = lat;
            longitudeInput.value = lng;

            // 先显示经纬度
            locationInput.value = `已获取位置：${lat.toFixed(6)}, ${lng.toFixed(6)}`;

            // 使用逆地理编码获取地址（带超时）
            reverseGeocodeWithTimeout(lat, lng, 3000).then(address => {
                locationInput.value = address || `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                locationBtn.disabled = false;
            }).catch(() => {
                // 逆地理编码失败，只显示经纬度
                locationInput.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                locationBtn.disabled = false;
            });
        },
        (error) => {
            clearTimeout(timeoutId);
            locationBtn.disabled = false;

            let errorMsg = '获取位置失败';
            let suggestion = '';

            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMsg = '用户拒绝了位置请求';
                    suggestion = '\n\n请在浏览器设置中允许位置访问，或手动输入地址。';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMsg = '位置信息不可用';
                    suggestion = '\n\n请检查GPS是否开启，或手动输入地址。';
                    break;
                case error.TIMEOUT:
                    errorMsg = '请求超时';
                    suggestion = '\n\n请检查网络连接，或手动输入地址。';
                    break;
                default:
                    errorMsg = `位置获取错误 (${error.code})`;
                    suggestion = '\n\n请手动输入地址。';
            }

            alert(errorMsg + suggestion);
            locationInput.value = '';
            latitudeInput.value = '';
            longitudeInput.value = '';
        },
        {
            enableHighAccuracy: false,  // 改为false，提高定位速度
            timeout: 5000,              // 5秒超时
            maximumAge: 600000           // 使用10分钟内的缓存位置
        }
    );
}

// 逆地理编码（带超时）
async function reverseGeocodeWithTimeout(lat, lng, timeoutMs = 3000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&accept-language=zh-CN`,
            { signal: controller.signal }
        );
        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        return data.display_name || null;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            console.log('逆地理编码超时');
        } else {
            console.error('逆地理编码失败:', error);
        }
        return null;
    }
}

// 逆地理编码（使用免费API）- 保留原函数作为备用
async function reverseGeocode(lat, lng) {
    return reverseGeocodeWithTimeout(lat, lng);
}

// 检查登录状态
function checkLoginStatus() {
    authToken = localStorage.getItem('authToken');
    if (authToken) {
        fetchCurrentUser();
    }
}

// 获取当前用户信息
async function fetchCurrentUser() {
    try {
        const response = await fetch(`${API_BASE}/auth/user`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            updateUserInfo();
        } else {
            logout();
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
        logout();
    }
}

// 更新用户信息显示
function updateUserInfo() {
    const userInfo = document.getElementById('userInfo');
    if (currentUser) {
        const roleText = currentUser.role === 'admin' ? '管理员' : '用户';
        userInfo.innerHTML = `
            <div class="user-details">
                <span class="user-name">👤 ${currentUser.username}</span>
                <span class="user-role">${roleText}</span>
            </div>
            <button class="btn-logout" onclick="logout()">退出登录</button>
        `;
    } else {
        userInfo.innerHTML = `
            <button class="btn btn-secondary" onclick="openAuthModal()">登录 / 注册</button>
        `;
    }
}

// 打开认证模态框（已废弃，使用页面跳转）
function openAuthModal() {
    window.location.href = 'login.html';
}

// 关闭认证模态框（已废弃）
function closeAuthModal() {
    // 页面跳转模式不需要此功能
}

// 显示登录表单
function showLoginForm() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
}

// 显示注册表单
function showRegisterForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

// 处理登录
async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.token;
            localStorage.setItem('authToken', authToken);
            currentUser = data.user;
            alert('登录成功！');

            // 调用页面定义的登录成功回调
            if (typeof onLoginSuccess === 'function') {
                onLoginSuccess();
            } else {
                window.location.href = 'index.html';
            }
        } else {
            alert(data.error || '登录失败');
        }
    } catch (error) {
        console.error('登录失败:', error);
        alert('登录失败，请检查网络连接');
    }
}

// 发送验证码
let countdownTimer = null;

async function sendVerificationCode() {
    const phone = document.getElementById('regPhone').value;
    
    // 验证手机号格式
    if (!phone || !/^1[3-9]\d{9}$/.test(phone)) {
        alert('请输入正确的手机号');
        return;
    }
    
    const sendBtn = document.getElementById('sendCodeBtn');
    
    try {
        const response = await fetch(`${API_BASE}/auth/send-code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ phone })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`验证码已发送！验证码：${data.code}
（实际应用中验证码将通过短信发送）`);
            
            // 开始倒计时
            let seconds = 60;
            sendBtn.disabled = true;
            sendBtn.textContent = `${seconds}秒后重发`;
            
            countdownTimer = setInterval(() => {
                seconds--;
                sendBtn.textContent = `${seconds}秒后重发`;
                
                if (seconds <= 0) {
                    clearInterval(countdownTimer);
                    sendBtn.disabled = false;
                    sendBtn.textContent = '获取验证码';
                }
            }, 1000);
        } else {
            alert(data.error || '发送验证码失败');
        }
    } catch (error) {
        console.error('发送验证码失败:', error);
        alert('发送验证码失败，请检查网络连接');
    }
}

// 处理注册
async function handleRegister(e) {
    e.preventDefault();

    const username = document.getElementById('regUsername').value;
    const phone = document.getElementById('regPhone').value;
    const code = document.getElementById('regCode').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;
    const role = document.getElementById('regRole').value;

    // 验证手机号格式
    if (!phone || !/^1[3-9]\d{9}$/.test(phone)) {
        alert('请输入正确的手机号');
        return;
    }

    // 验证验证码
    if (!code || code.length !== 6) {
        alert('请输入6位验证码');
        return;
    }

    if (password !== confirmPassword) {
        alert('两次输入的密码不一致');
        return;
    }

    if (password.length < 6) {
        alert('密码长度至少为6位');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, phone, code, email, password, role })
        });

        const data = await response.json();

        if (response.ok) {
            const roleName = role === 'admin' ? '管理员' : '普通用户';
            alert(`注册成功！您已注册为${roleName}，请登录`);
            // 清除倒计时
            if (countdownTimer) {
                clearInterval(countdownTimer);
                countdownTimer = null;
            }
            document.getElementById('sendCodeBtn').disabled = false;
            document.getElementById('sendCodeBtn').textContent = '获取验证码';
            showLoginForm();
        } else {
            alert(data.error || '注册失败');
        }
    } catch (error) {
        console.error('注册失败:', error);
        alert('注册失败，请检查网络连接');
    }
}

// 角色切换提示
function handleRoleChange() {
    const role = document.getElementById('regRole').value;
    const hint = document.getElementById('roleHint');

    if (role === 'admin') {
        hint.textContent = '管理员：可管理所有用户的物品信息，拥有最高权限';
    } else {
        hint.textContent = '普通用户：可发布和管理自己的物品信息';
    }
}

// 退出登录
function logout() {
    currentUser = null;
    authToken = null;
    localStorage.removeItem('authToken');
    updateUserInfo();
    loadItems();
}

// 加载统计数据（首页使用）
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/items`);
        const items = await response.json();

        const foundCount = items.filter(item => item.type === 'found').length;
        const lostCount = items.filter(item => item.type === 'lost').length;

        // 获取用户数
        const usersResponse = await fetch(`${API_BASE}/auth/users`);
        const usersCount = usersResponse.ok ? (await usersResponse.json()).length : 0;

        document.getElementById('statFound').textContent = foundCount;
        document.getElementById('statLost').textContent = lostCount;
        document.getElementById('statUsers').textContent = usersCount;
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

// 切换列表类型（供 items.html 使用）
function switchList(type) {
    currentListType = type;

    // 更新标签按钮状态
    document.querySelectorAll('.list-tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    // 重新加载列表
    fetchItems(type);
}

// 搜索物品
async function searchItems() {
    const keyword = document.getElementById('searchInput').value;
    const category = document.getElementById('categoryFilter').value;
    
    try {
        let url = `${API_BASE}/items/search?keyword=${encodeURIComponent(keyword)}`;
        if (category) {
            url += `&category=${encodeURIComponent(category)}`;
        }
        
        const response = await fetch(url);
        const items = await response.json();
        displayItems(items);
    } catch (error) {
        console.error('搜索失败:', error);
        showError('搜索失败，请稍后重试');
    }
}

// 显示物品列表
function displayItems(items) {
    const container = document.getElementById('itemsList');
    
    if (items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 60px; margin-bottom: 20px;">📦</div>
                <p>暂无失物招领信息</p>
                <p style="font-size: 14px; margin-top: 10px;">发布第一条信息吧！</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = items.map(item => {
        const canEdit = currentUser && (currentUser.role === 'admin' || item.user_id === currentUser.id);
        const typeText = item.type === 'found' ? '🔍 失物招领' : '📢 失物找寻';
        const locationText = item.type === 'found' ? '发现地点' : '丢失地点';

        return `
        <div class="item-card">
            <div class="item-header">
                <div class="item-title">${escapeHtml(item.title)}</div>
                <span class="item-type">${typeText}</span>
            </div>

            <div class="item-header" style="margin-top: 10px;">
                <span class="item-category">${escapeHtml(item.category)}</span>
            </div>

            <div class="item-info">
                <span>📍</span>
                <span>${locationText}：${escapeHtml(item.location)}</span>
                ${item.latitude && item.longitude ? `
                    <a href="https://www.google.com/maps?q=${item.latitude},${item.longitude}" target="_blank" style="margin-left: 10px; color: #667eea; text-decoration: none;">
                        🗺️ 查看地图
                    </a>
                ` : ''}
            </div>

            <div class="item-info">
                <span>📞</span>
                <span>联系方式：${escapeHtml(item.contact)}</span>
            </div>

            <div class="item-description">
                ${escapeHtml(item.description)}
            </div>

            <div class="item-footer">
                <div>
                    <span class="item-status status-${item.status}">
                        ${getStatusText(item.status)}
                    </span>
                    <span class="item-time" style="margin-left: 10px;">
                        ${formatTime(item.created_at)}
                    </span>
                </div>

                ${canEdit ? `
                <div class="item-actions">
                    ${item.status === 'pending' ? `
                        <button class="btn btn-small btn-success" onclick="updateStatus(${item.id}, 'claimed')">
                            认领
                        </button>
                        <button class="btn btn-small btn-success" onclick="updateStatus(${item.id}, 'returned')">
                            已归还
                        </button>
                    ` : ''}
                    <button class="btn btn-small btn-danger" onclick="deleteItem(${item.id})">
                        删除
                    </button>
                </div>
                ` : ''}
            </div>
        </div>
    `}).join('');
}

// 处理失物招领表单提交（found.html 使用）
async function handlePublishFound(e) {
    e.preventDefault();

    if (!currentUser) {
        alert('请先登录后再发布信息');
        window.location.href = 'login.html';
        return;
    }

    const formData = {
        type: 'found',
        title: document.getElementById('foundTitle').value,
        category: document.getElementById('foundCategory').value,
        location: document.getElementById('foundLocation').value,
        contact: document.getElementById('foundContact').value,
        description: document.getElementById('foundDescription').value,
        latitude: document.getElementById('foundLatitude').value,
        longitude: document.getElementById('foundLongitude').value
    };

    await publishItem(formData);
}

// 处理失物找寻表单提交（lost.html 使用）
async function handlePublishLost(e) {
    e.preventDefault();

    if (!currentUser) {
        alert('请先登录后再发布信息');
        window.location.href = 'login.html';
        return;
    }

    const formData = {
        type: 'lost',
        title: document.getElementById('lostTitle').value,
        category: document.getElementById('lostCategory').value,
        location: document.getElementById('lostLocation').value,
        contact: document.getElementById('lostContact').value,
        description: document.getElementById('lostDescription').value,
        latitude: document.getElementById('lostLatitude').value,
        longitude: document.getElementById('lostLongitude').value
    };

    await publishItem(formData);
}

// 发布物品（通用函数）
async function publishItem(formData) {
    try {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        const response = await fetch(`${API_BASE}/items`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('发布成功！');
            // 重置表单
            const type = formData.type;
            document.getElementById(`${type}Form`).reset();
            // 跳转到物品列表页
            window.location.href = 'items.html';
        } else {
            const data = await response.json();
            alert(data.error || '发布失败，请重试');
        }
    } catch (error) {
        console.error('发布失败:', error);
        alert('发布失败，请检查网络连接');
    }
}

// 删除旧的 handleSubmit 函数（已由 handlePublishFound 和 handlePublishLost 替代）
// async function handleSubmit(e, type) { ... }

// 更新物品状态
async function updateStatus(itemId, status) {
    if (!confirm(`确定要将状态更改为"${getStatusText(status)}"吗？`)) {
        return;
    }

    try {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        const response = await fetch(`${API_BASE}/items/${itemId}`, {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify({ status })
        });

        if (response.ok) {
            alert('状态更新成功！');
            fetchItems(currentListType);
        } else {
            const data = await response.json();
            alert(data.error || '状态更新失败');
        }
    } catch (error) {
        console.error('更新失败:', error);
        alert('更新失败，请稍后重试');
    }
}

// 删除物品
async function deleteItem(itemId) {
    if (!confirm('确定要删除这条信息吗？')) {
        return;
    }

    try {
        const headers = {};

        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        const response = await fetch(`${API_BASE}/items/${itemId}`, {
            method: 'DELETE',
            headers: headers
        });

        if (response.ok) {
            alert('删除成功！');
            fetchItems(currentListType);
        } else {
            const data = await response.json();
            alert(data.error || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请稍后重试');
    }
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'pending': '待认领',
        'claimed': '已认领',
        'returned': '已归还'
    };
    return statusMap[status] || status;
}

// 格式化时间
function formatTime(timeString) {
    const date = new Date(timeString);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    
    return date.toLocaleDateString('zh-CN');
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 显示错误信息
function showError(message) {
    const container = document.getElementById('itemsList');
    container.innerHTML = `
        <div class="empty-state">
            <div style="font-size: 60px; margin-bottom: 20px;">⚠️</div>
            <p>${message}</p>
        </div>
    `;
}
