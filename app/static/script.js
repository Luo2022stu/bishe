const API_BASE = '/api';  // 使用相对路径，自动适配当前域名
let currentUser = null;
let authToken = null;
let currentListType = 'found'; // 'found' 或 'lost'
let currentPostId = null; // 当前查看的帖子ID
let chatRefreshInterval = null; // 聊天未读消息刷新定时器

// 初始化页面时设置定时刷新
document.addEventListener('DOMContentLoaded', function() {
    // 每5秒刷新一次聊天未读消息
    if (authToken || localStorage.getItem('authToken')) {
        startChatRefreshTimer();
    }
});

// 启动聊天刷新定时器
function startChatRefreshTimer() {
    if (chatRefreshInterval) {
        clearInterval(chatRefreshInterval);
    }
    chatRefreshInterval = setInterval(() => {
        loadUnreadChatCount();
    }, 30000); // 改为30秒刷新一次，减少频繁请求
}

// 停止聊天刷新定时器
function stopChatRefreshTimer() {
    if (chatRefreshInterval) {
        clearInterval(chatRefreshInterval);
        chatRefreshInterval = null;
    }
}

// 将base64图片转换为data URI格式
function formatImageUrl(base64Data) {
    if (!base64Data) return '';

    // 检查是否已经是完整的data URI
    if (base64Data.startsWith('data:image')) {
        return base64Data;
    }

    // 检测图片类型
    let imageType = 'image/jpeg'; // 默认为jpeg
    if (base64Data.startsWith('/9j/')) {
        imageType = 'image/jpeg';
    } else if (base64Data.startsWith('iVBORw0KGgo')) {
        imageType = 'image/png';
    } else if (base64Data.startsWith('R0lGODdh') || base64Data.startsWith('R0lGODlh')) {
        imageType = 'image/gif';
    } else if (base64Data.startsWith('UklGR')) {
        imageType = 'image/webp';
    }

    return `data:${imageType};base64,${base64Data}`;
}

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
    // 失物招领和失物找寻页：加载物品列表（在各自页面中处理）
    else if (currentPage === 'found.html' || currentPage === 'lost.html') {
        checkLoginStatus();
        // loadPageItems 在各自页面的 script 标签中调用
    }
    // 论坛页：加载帖子列表
    else if (currentPage === 'forum.html') {
        checkLoginStatus();
        loadPosts();
    }
    // 其他页面
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

// 加载页面物品列表（供 found.html 和 lost.html 使用）
async function loadPageItems(type) {
    const listId = type === 'found' ? 'foundItemsList' : 'lostItemsList';
    const container = document.getElementById(listId);

    try {
        const response = await fetch(`${API_BASE}/items`);
        const items = await response.json();

        // 根据类型过滤
        const filteredItems = items.filter(item => item.type === type);

        if (filteredItems.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div style="font-size: 60px; margin-bottom: 20px;">📭</div>
                    <p>暂无${type === 'found' ? '招领' : '找寻'}物品</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filteredItems.map(item => `
            <div class="item-card clickable" onclick="goToItemDetail('${item.type}', ${item.id}, '${escapeHtml(item.title).replace(/'/g, "\\'")}')">
                ${item.images && item.images.length > 0 ? `
                    <div class="item-thumbnail">
                        <img src="${formatImageUrl(item.images[0])}" alt="${escapeHtml(item.title)}" onerror="this.parentElement.style.display='none'">
                        ${item.images.length > 1 ? `<span class="image-count">+${item.images.length - 1}</span>` : ''}
                    </div>
                ` : ''}
                <h3>${escapeHtml(item.title)}</h3>
                <div class="item-meta">
                    <span>📍 ${escapeHtml(item.location)}</span>
                    <span>📂 ${escapeHtml(item.category)}</span>
                    <span>🕐 ${formatTime(item.created_at)}</span>
                </div>
                <div class="item-description">${escapeHtml(item.description)}</div>
                <div class="item-stats">
                    <span>👁️ ${item.view_count || 0}</span>
                    <span>❤️ ${item.like_count || 0}</span>
                    <span class="item-status status-${item.status}">
                        ${getStatusText(item.status)}
                    </span>
                </div>
                <div class="item-contact">
                    <strong>联系方式:</strong> ${escapeHtml(item.contact)}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载物品失败:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 60px; margin-bottom: 20px;">⚠️</div>
                <p>加载失败，请检查后端服务是否启动</p>
            </div>
        `;
    }
}

// 基于IP地址获取大致位置（备用方案）
async function getIPBasedLocation(locationInput, latitudeInput, longitudeInput) {
    try {
        // 使用免费的 IP 地理位置 API
        const response = await fetch('https://ipapi.co/json/');
        const data = await response.json();

        if (data && data.city) {
            let locationStr = data.city;
            if (data.region) locationStr += ', ' + data.region;
            if (data.country_name) locationStr += ', ' + data.country_name;

            locationInput.value = locationStr;
            latitudeInput.value = data.latitude || '';
            longitudeInput.value = data.longitude || '';

            console.log('[IP定位] 成功:', locationStr);
        } else {
            locationInput.value = '';
            locationInput.placeholder = 'IP定位失败，请手动输入地址';
        }
    } catch (error) {
        console.error('[IP定位] 失败:', error);
        locationInput.value = '';
        locationInput.placeholder = 'IP定位失败，请手动输入地址';
        alert('IP定位失败，请手动输入地址');
    }
}

// 获取地理位置
function getLocation(type) {
    console.log('[定位] 开始获取位置...');

    if (!navigator.geolocation) {
        alert('您的浏览器不支持地理位置功能\n\n请手动输入地址。');
        return;
    }

    // 检查当前是否使用 HTTPS 或 localhost
    const isSecure = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
    console.log('[定位] 当前协议:', location.protocol);
    console.log('[定位] 主机名:', location.hostname);
    console.log('[定位] 是否安全连接:', isSecure);

    if (!isSecure) {
        console.warn('[定位] 警告：当前网站未使用 HTTPS，定位功能可能无法使用');
        if (confirm('警告：定位功能通常需要 HTTPS 连接才能使用。\n\n当前访问地址：' + location.href + '\n\n建议：\n- 使用 localhost:5000 访问\n- 或配置 HTTPS\n\n仍要尝试获取位置吗？')) {
            // 用户确认继续
        } else {
            return;
        }
    }

    const locationInput = document.getElementById(`${type}Location`);
    const latitudeInput = document.getElementById(`${type}Latitude`);
    const longitudeInput = document.getElementById(`${type}Longitude`);
    const locationBtn = document.querySelector(`#${type}Location`).parentElement.querySelector('.btn-location');

    locationInput.value = '正在获取位置...';
    locationBtn.disabled = true;

    // 设置超时时间（30秒）
    const timeoutId = setTimeout(() => {
        locationInput.value = '获取超时，请重试';
        latitudeInput.value = '';
        longitudeInput.value = '';
        locationBtn.disabled = false;
        if (confirm('获取位置超时。\n\n可能原因：\n1. 浏览器未授权位置访问\n2. GPS未开启或信号弱\n3. 网络连接问题\n4. 当前网站未使用HTTPS（非localhost）\n\n提示：\n- 您可以手动输入地址\n- 到室外空旷处重试\n- 检查浏览器位置权限设置\n\n是否手动输入地址？')) {
            locationInput.focus();
        }
    }, 30000);

    navigator.geolocation.getCurrentPosition(
        (position) => {
            clearTimeout(timeoutId);
            console.log('[定位] 位置获取成功:', position.coords);
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            // 保存经纬度
            latitudeInput.value = lat;
            longitudeInput.value = lng;

            // 先显示经纬度
            locationInput.value = `已获取位置：${lat.toFixed(6)}, ${lng.toFixed(6)}`;

            // 使用逆地理编码获取地址（带超时，延长到10秒）
            locationInput.value += ' (正在获取地址...)';
            reverseGeocodeWithTimeout(lat, lng, 10000).then(address => {
                if (address) {
                    console.log('[定位] 地址解析成功:', address);
                    locationInput.value = address;
                } else {
                    console.warn('[定位] 地址解析失败，使用经纬度');
                    locationInput.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                }
                locationBtn.disabled = false;
            }).catch((err) => {
                console.error('[定位] 地址解析错误:', err);
                // 逆地理编码失败，只显示经纬度
                locationInput.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                locationBtn.disabled = false;
            });
        },
        (error) => {
            clearTimeout(timeoutId);
            console.error('[定位] 位置获取失败:', error);
            locationBtn.disabled = false;

            let errorMsg = '获取位置失败';
            let suggestion = '';
            let showRetry = false;
            let showIPGeoOption = false;

            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMsg = '位置权限被拒绝';
                    suggestion = '\n\n解决方案：\n1. 点击浏览器地址栏左侧的"锁"或"位置"图标\n2. 选择"允许"或"总是允许"位置访问\n3. 刷新页面后重试';
                    showRetry = true;
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMsg = '位置信息不可用';
                    suggestion = '\n\n可能原因：\n- GPS未开启\n- 位置服务被禁用\n- 设备不支持定位\n- 信号接收不良\n\n解决方案：\n- 检查设备GPS设置\n- 移动到室外空旷处\n- 尝试使用WiFi连接';
                    showIPGeoOption = true;
                    break;
                case error.TIMEOUT:
                    errorMsg = '请求超时';
                    suggestion = '\n\n定位时间过长，请检查：\n- 网络连接是否正常\n- GPS信号是否足够强\n- 是否在室内（建议到室外）\n- 是否使用了VPN（建议关闭）\n\n解决方案：\n- 到室外空旷处重试\n- 关闭VPN后再试\n- 使用WiFi连接\n- 或直接手动输入地址';
                    showRetry = true;
                    showIPGeoOption = true;
                    break;
                default:
                    errorMsg = `位置获取错误 (${error.code})`;
            }

            alert(errorMsg + suggestion);

            // 提供选项：重试、使用IP定位、手动输入
            if (showIPGeoOption) {
                const options = [
                    '重新尝试定位',
                    '手动输入地址',
                    '跳过（不填写位置）'
                ];

                if (error.code === error.TIMEOUT) {
                    options.splice(1, 0, '使用IP地址大致定位（可能不准确）');
                }

                const choice = prompt(`请选择操作：\n\n1 - ${options[0]}\n2 - ${options[1]}${options[2] ? '\n3 - ' + options[2] : ''}\n\n请输入数字选择：`);

                if (choice === '1') {
                    // 重新尝试
                    getLocation(type);
                } else if (choice === '2' && options.length === 4) {
                    // 使用IP定位（仅在超时时显示）
                    locationInput.value = '正在通过IP获取大致位置...';
                    getIPBasedLocation(locationInput, latitudeInput, longitudeInput);
                } else if (choice === '2' || (choice === '3' && options.length === 4)) {
                    // 手动输入地址
                    locationInput.value = '';
                    locationInput.focus();
                    locationInput.placeholder = '请手动输入地址，如：北京市海淀区XX路XX号';
                } else if (choice === '3' || choice === '4') {
                    // 跳过
                    locationInput.value = '';
                } else {
                    locationInput.value = '';
                    latitudeInput.value = '';
                    longitudeInput.value = '';
                }
            } else {
                locationInput.value = '';
                latitudeInput.value = '';
                longitudeInput.value = '';

                if (showRetry && confirm('是否重新尝试获取位置？')) {
                    getLocation(type);
                }
            }
        },
        {
            enableHighAccuracy: true,   // 启用高精度定位
            timeout: 60000,             // 60秒超时（延长到60秒）
            maximumAge: 10000           // 使用10秒内的缓存位置，提高速度
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
        return null;
    }
}

// 逆地理编码（使用免费API）- 保留原函数作为备用
async function reverseGeocode(lat, lng) {
    return reverseGeocodeWithTimeout(lat, lng);
}

// 检查登录状态
function checkLoginStatus() {
    try {
        console.log('[登录] 检查登录状态');
        authToken = localStorage.getItem('authToken');
        console.log('[登录] token:', authToken ? '存在' : '不存在');
        if (authToken) {
            fetchCurrentUser();
            // 启动聊天未读消息刷新定时器
            startChatRefreshTimer();
        } else {
            // 未登录时停止定时器
            stopChatRefreshTimer();
        }
    } catch (error) {
        console.error('[登录] 读取登录状态失败:', error);
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
            // 加载未读通知数量
            loadUnreadNotificationCount();
            // 加载聊天未读数量
            loadUnreadChatCount();
            // 启动聊天刷新定时器
            startChatRefreshTimer();
        } else {
            // 只在真正需要认证时才退出登录
            if (response.status === 401) {
                logout();
            } else {
                // 其他错误保留 token，可能是网络问题
                console.warn('获取用户信息失败，状态码:', response.status);
            }
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
        // 网络错误不自动退出，保留 token
    }
}

// 加载未读通知数量
async function loadUnreadNotificationCount() {
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE}/notifications`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            // 根据用户角色过滤通知后计算未读数量
            let filteredNotifications = [];
            if (currentUser && currentUser.role === 'admin') {
                // 管理员只看待审核通知、反馈通知和系统通知
                filteredNotifications = data.notifications.filter(n => n.type === 'pending_audit' || n.type === 'feedback' || n.type === 'system');
            } else {
                // 普通用户看审核结果通知、反馈回复通知和系统通知
                filteredNotifications = data.notifications.filter(n => n.type === 'audit' || n.type === 'feedback' || n.type === 'system');
            }
            // 计算过滤后的未读通知数量
            const unreadCount = filteredNotifications.filter(n => !n.is_read).length;
            updateDropdownNotificationBadge(unreadCount);
        }
    } catch (error) {
        console.error('加载未读通知数量失败:', error);
    }
}

// 更新下拉菜单通知徽章
function updateDropdownNotificationBadge(count) {
    const badge = document.getElementById('dropdownNotificationBadge');
    if (!badge) return;

    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}

// 加载聊天未读数量
async function loadUnreadChatCount() {
    if (!authToken) return;

    // 检查页面是否可见，避免在后台频繁请求
    if (document.hidden) return;

    try {
        const response = await fetch(`${API_BASE}/chat/unread-count`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            // 添加超时控制
            signal: AbortSignal.timeout(5000)
        });

        if (response.ok) {
            const data = await response.json();
            updateChatBadge(data.total);
        }
    } catch (error) {
        // 仅在非网络变化错误时输出日志
        if (error.name !== 'AbortError' && !error.message.includes('NetworkError') && !error.message.includes('Failed to fetch')) {
            console.error('加载聊天未读数量失败:', error);
        }
    }
}

// 更新聊天徽章
function updateChatBadge(count) {
    const badge = document.getElementById('chatBadge');
    if (!badge) return;

    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}


// 更新用户信息显示
function updateUserInfo() {
    const userInfo = document.getElementById('userInfo');
    const userDropdown = document.getElementById('userDropdown');
    const notificationEntry = document.getElementById('notificationEntry');

    if (currentUser) {
        // 隐藏登录按钮，显示用户下拉菜单和通知按钮
        if (userInfo) userInfo.style.display = 'none';
        if (userDropdown) userDropdown.style.display = 'block';
        if (notificationEntry) notificationEntry.style.display = 'block';

        // 设置用户真实姓名（如果存在），否则使用用户名
        const userNameElement = document.getElementById('userName');
        if (userNameElement) {
            userNameElement.textContent = currentUser.name || currentUser.username;
        }
    } else {
        // 显示登录按钮，隐藏用户下拉菜单和通知按钮
        if (userInfo) {
            userInfo.style.display = 'block';
            userInfo.innerHTML = `
                <button class="btn btn-secondary" onclick="openAuthModal()">登录 / 注册</button>
            `;
        }
        if (userDropdown) userDropdown.style.display = 'none';
        if (notificationEntry) notificationEntry.style.display = 'none';
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
            try {
                localStorage.setItem('authToken', authToken);
            } catch (e) {
                console.error('保存token失败:', e);
            }
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

    // 停止聊天刷新定时器
    stopChatRefreshTimer();

    // 如果当前在物品列表页或个人中心页面，跳转到首页
    const currentPage = window.location.pathname.split('/').pop();
    if (currentPage === 'profile.html' || currentPage === 'found.html' || currentPage === 'lost.html' || currentPage === 'items.html') {
        window.location.href = 'index.html';
    } else {
        window.location.reload();
    }
}

// 加载统计数据（首页使用）
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();

        document.getElementById('statFound').textContent = stats.found_count;
        document.getElementById('statLost').textContent = stats.lost_count;
        document.getElementById('statPosts').textContent = stats.posts_count;
        document.getElementById('statUsers').textContent = stats.users_count;
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

// 切换列表类型（供 items.html 使用）
function switchList(type, event) {
    currentListType = type;

    // 更新标签按钮状态
    document.querySelectorAll('.list-tab-btn').forEach(btn => btn.classList.remove('active'));
    if (event && event.target) {
        event.target.classList.add('active');
    } else {
        // 如果没有event参数，根据type找到对应的按钮
        const buttons = document.querySelectorAll('.list-tab-btn');
        if (type === 'found' && buttons[0]) {
            buttons[0].classList.add('active');
        } else if (type === 'lost' && buttons[1]) {
            buttons[1].classList.add('active');
        }
    }

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
        <div class="item-card clickable" data-item-id="${item.id}" onclick="goToItemDetail('${item.type}', ${item.id}, '${escapeHtml(item.title).replace(/'/g, "\\'")}')">
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

                <div class="item-interactions" onclick="event.stopPropagation()">
                    <button class="interaction-btn ${item.is_liked ? 'liked' : ''}" onclick="toggleItemLike(${item.id}, '${item.type}')">
                        <span class="interaction-icon">${item.is_liked ? '❤️' : '🤍'}</span>
                        <span class="interaction-count" id="like-count-${item.id}">${item.like_count || 0}</span>
                    </button>
                    <button class="interaction-btn" onclick="shareItem(${item.id}, '${escapeHtml(item.title).replace(/'/g, "\\'")}')">
                        <span class="interaction-icon">🔗</span>
                        <span>推荐</span>
                    </button>
                    ${canEdit ? `
                    <button class="btn btn-small btn-danger" onclick="deleteItem(${item.id})">
                        删除
                    </button>
                    ` : ''}
                </div>
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

    const latitude = document.getElementById('foundLatitude').value;
    const longitude = document.getElementById('foundLongitude').value;

    const formData = {
        type: 'found',
        title: document.getElementById('foundTitle').value,
        category: document.getElementById('foundCategory').value,
        location: document.getElementById('foundLocation').value,
        contact: document.getElementById('foundContact').value,
        description: document.getElementById('foundDescription').value,
        latitude: latitude ? parseFloat(latitude) : null,
        longitude: longitude ? parseFloat(longitude) : null,
        images: uploadedImages.found.map(img => img.file)
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

    const latitude = document.getElementById('lostLatitude').value;
    const longitude = document.getElementById('lostLongitude').value;

    const formData = {
        type: 'lost',
        title: document.getElementById('lostTitle').value,
        category: document.getElementById('lostCategory').value,
        location: document.getElementById('lostLocation').value,
        contact: document.getElementById('lostContact').value,
        description: document.getElementById('lostDescription').value,
        latitude: latitude ? parseFloat(latitude) : null,
        longitude: longitude ? parseFloat(longitude) : null,
        images: uploadedImages.lost.map(img => img.file)
    };

    await publishItem(formData);
}

// 发布物品（通用函数）
async function publishItem(formData) {
    // 验证必填字段
    if (!formData.title || !formData.category || !formData.location || !formData.contact || !formData.description) {
        alert('请填写所有必填项');
        return;
    }

    try {
        const hasImages = formData.images && formData.images.length > 0;

        const headers = {};
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        } else {
            alert('请先登录');
            window.location.href = 'login.html';
            return;
        }

        let body;
        if (hasImages) {
            // 使用FormData上传图片
            body = new FormData();
            body.append('type', formData.type);
            body.append('title', formData.title);
            body.append('category', formData.category);
            body.append('location', formData.location);
            body.append('contact', formData.contact);
            body.append('description', formData.description);
            if (formData.latitude) body.append('latitude', formData.latitude);
            if (formData.longitude) body.append('longitude', formData.longitude);
            formData.images.forEach((img, index) => {
                body.append(`image${index}`, img);
            });
        } else {
            // 使用JSON格式
            headers['Content-Type'] = 'application/json';
            body = JSON.stringify(formData);
        }

        const response = await fetch(`${API_BASE}/items`, {
            method: 'POST',
            headers: headers,
            body: body
        });

        if (response.ok) {
            await response.json();
            alert('发布成功！');
            // 重置表单和图片
            const type = formData.type;
            document.getElementById(`${type}Form`).reset();
            uploadedImages[type] = [];
            renderImagePreview(type);
            // 跳转到物品列表页
            window.location.href = 'items.html';
        } else {
            const data = await response.json();
            const errorMsg = data.error || '发布失败，请重试';
            alert(`发布失败: ${errorMsg}\n\n请检查:\n1. 是否已登录\n2. 网络连接是否正常\n3. 后端服务是否已启动`);
        }
    } catch (error) {
        alert(`发布失败: ${error.message}\n\n请检查:\n1. 网络连接是否正常\n2. 后端服务是否已启动 (http://localhost:5000)\n3. 浏览器控制台查看详细错误`);
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

// 图片上传和预览
const uploadedImages = {
    found: [],
    lost: []
};

function previewImages(input, type) {
    const previewContainer = document.getElementById(`${type}ImagePreview`);
    const files = input.files;

    // 检查是否超过5张
    const currentCount = uploadedImages[type].length;
    const newCount = files.length;
    if (currentCount + newCount > 5) {
        alert(`最多只能上传5张图片，当前已有${currentCount}张`);
        return;
    }

    // 处理新上传的图片
    Array.from(files).forEach(file => {
        if (!file.type.startsWith('image/')) {
            alert('请选择图片文件');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            const imageData = {
                file: file,
                preview: e.target.result,
                id: Date.now() + Math.random()
            };
            uploadedImages[type].push(imageData);
            renderImagePreview(type);
        };
        reader.readAsDataURL(file);
    });

    // 清空input，允许重复选择同一文件
    input.value = '';
}

function renderImagePreview(type) {
    const previewContainer = document.getElementById(`${type}ImagePreview`);
    previewContainer.innerHTML = uploadedImages[type].map(img => `
        <div class="image-preview-item">
            <img src="${img.preview}" alt="预览">
            <button type="button" class="image-preview-remove" onclick="removeImage('${type}', ${img.id})">✕</button>
        </div>
    `).join('');
}

function removeImage(type, imageId) {
    uploadedImages[type] = uploadedImages[type].filter(img => img.id !== imageId);
    renderImagePreview(type);
}

// AI识别功能
async function recognizeImage(file) {
    const formData = new FormData();
    formData.append('image', file);

    try {
        const response = await fetch(`${API_BASE}/ai/recognize`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('识别失败');
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('AI识别错误:', error);
        throw error;
    }
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

/* ==================== 社区交流功能 ==================== */

// 加载帖子列表
async function loadPosts() {
    const category = document.getElementById('categoryFilter')?.value || '';
    const keyword = document.getElementById('searchInput')?.value || '';

    try {
        let url = `${API_BASE}/posts`;
        const params = [];
        if (category) params.push(`category=${encodeURIComponent(category)}`);
        if (keyword) params.push(`keyword=${encodeURIComponent(keyword)}`);
        if (params.length > 0) url += '?' + params.join('&');

        const response = await fetch(url);
        const posts = await response.json();
        displayPosts(posts);
    } catch (error) {
        console.error('加载帖子失败:', error);
        const container = document.getElementById('postsContainer');
        container.innerHTML = `
            <div class="empty-state">
                <div class="icon">💬</div>
                <p>加载失败，请检查后端服务是否启动</p>
            </div>
        `;
    }
}

// 显示帖子列表
function displayPosts(posts) {
    const container = document.getElementById('postsContainer');

    if (!posts || posts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="icon">📭</div>
                <p>暂无帖子，快来发布第一条吧！</p>
            </div>
        `;
        return;
    }

    // 按浏览量排序
    const sortedPosts = [...posts].sort((a, b) => b.view_count - a.view_count);

    // 获取当前用户ID
    let currentUserId = null;
    if (authToken && authToken.startsWith('token_')) {
        try {
            currentUserId = parseInt(authToken.split('_')[1]);
        } catch (e) {
            console.error('解析用户ID失败:', e);
        }
    }

    // 显示全部帖子（只显示标题，可点击查看详情）
    container.innerHTML = sortedPosts.map(post => {
        // 判断是否是当前用户的帖子
        const isOwner = currentUserId && post.user_id === currentUserId;

        return `
        <div class="post-card simple-post ${isOwner ? 'my-post' : ''}" onclick="viewPost(${post.id})">
            <div class="post-header">
                <div class="post-title">
                    <h3>${escapeHtml(post.title)}</h3>
                    <span class="post-category" data-category="${post.category}">${post.category}</span>
                </div>
            </div>
            <div class="post-meta">
                <span class="post-author-tag">👤 贴主: ${escapeHtml(post.username)}</span>
                <span>🕐 ${formatTime(post.created_at)}</span>
                <span>👁️ ${post.view_count} 浏览</span>
            </div>
        </div>
    `}).join('');
}

// 筛选帖子
function filterPosts() {
    loadPosts();
}

// 搜索帖子
function searchPosts() {
    const keyword = document.getElementById('searchInput').value.trim();
    const category = document.getElementById('categoryFilter')?.value || '';

    // 构建搜索关键词
    let searchKeyword = keyword;
    if (category) {
        searchKeyword = `${category} ${keyword}`.trim();
    }

    if (searchKeyword) {
        window.location.href = `search-results.html?keyword=${encodeURIComponent(searchKeyword)}`;
    } else {
        alert('请输入搜索关键词');
    }
}

function handleSearchKeypress(event) {
    if (event.key === 'Enter') {
        searchPosts();
    }
}

// 显示发布帖子弹窗
function showCreatePostModal() {
    if (!authToken) {
        alert('请先登录');
        window.location.href = 'login.html';
        return;
    }
    document.getElementById('createPostModal').style.display = 'flex';
}

// 关闭发布帖子弹窗
function closeCreatePostModal() {
    document.getElementById('createPostModal').style.display = 'none';
    document.getElementById('createPostForm').reset();
}

// 处理发布帖子
async function handleCreatePost(event) {
    event.preventDefault();

    const title = document.getElementById('postTitle').value.trim();
    const category = document.getElementById('postCategory').value;
    const content = document.getElementById('postContent').value.trim();
    const imageInput = document.getElementById('postImage');

    if (!title || !content) {
        alert('标题和内容不能为空');
        return;
    }

    try {
        // 检查是否已登录
        if (!authToken) {
            alert('请先登录');
            window.location.href = 'login.html';
            return;
        }

        console.log('[发布帖子] 开始发布，authToken:', authToken);

        // 检查是否有有效的图片上传
        if (imageInput.files.length > 0 && imageInput.files[0].name) {
            console.log('[发布帖子] 检测到图片，使用FormData上传');
            // 使用 FormData 上传带图片的帖子
            const formData = new FormData();
            formData.append('title', title);
            formData.append('category', category);
            formData.append('content', content);
            formData.append('image', imageInput.files[0]);

            console.log('[发布帖子] FormData内容:', {
                title: title,
                category: category,
                content: content.substring(0, 50) + '...',
                hasImage: true,
                imageName: imageInput.files[0].name
            });

            const response = await fetch(`${API_BASE}/posts`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                },
                body: formData
            });

            console.log('[发布帖子] 响应状态:', response.status, response.statusText);

            const data = await response.json();
            console.log('[发布帖子] 响应数据:', data);

            if (response.ok) {
                alert('发布成功！');
                closeCreatePostModal();
                loadPosts();
            } else {
                alert(data.error || '发布失败');
            }
        } else {
            console.log('[发布帖子] 无图片，使用JSON上传');
            // 没有图片，使用 JSON 上传
            const response = await fetch(`${API_BASE}/posts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({ title, category, content })
            });

            console.log('[发布帖子] 响应状态:', response.status, response.statusText);

            const data = await response.json();
            console.log('[发布帖子] 响应数据:', data);

            if (response.ok) {
                alert('发布成功！');
                closeCreatePostModal();
                loadPosts();
            } else {
                alert(data.error || '发布失败');
            }
        }
    } catch (error) {
        console.error('发布失败:', error);
        console.error('错误堆栈:', error.stack);
        alert('发布失败，请稍后重试');
    }
}

// 查看帖子详情
function viewPost(postId) {
    console.log(`[帖子] 跳转到帖子详情，ID: ${postId}`);
    // 跳转到帖子详情页面
    window.location.href = `post-detail.html?id=${postId}`;
}

// 显示帖子详情
function displayPostDetail(post) {
    const canEdit = currentUser && (currentUser.id === post.user_id || currentUser.role === 'admin');

    // 存储当前帖子ID，用于评论回复
    currentPostId = post.id;

    // 记录浏览历史
    trackBrowseHistory('post', post.id, post.title);

    document.getElementById('postDetailTitle').textContent = post.title;
    document.getElementById('postDetailContent').innerHTML = `
        <div class="post-detail-header">
            <span class="post-category" data-category="${post.category}">${post.category}</span>
            <div class="post-detail-meta">
                👤 ${escapeHtml(post.username)} · 🕐 ${formatTime(post.created_at)} · 👁️ ${post.view_count}
            </div>
        </div>

        ${post.image ? `
        <div class="post-detail-image">
            <img src="${formatImageUrl(post.image)}" alt="帖子图片" />
        </div>
        ` : ''}

        <div class="post-detail-body">${escapeHtml(post.content)}</div>

        <div class="post-actions">
            <button class="btn btn-secondary" onclick="toggleLike(${post.id})" id="likeBtn">
                ❤️ ${post.like_count}
            </button>
            ${!canEdit ? `
                <button class="btn btn-warning" onclick="showReportModal('post', ${post.id})" id="reportBtn">
                    🚫 举报
                </button>
            ` : ''}
            ${canEdit ? `
                <button class="btn btn-secondary" onclick="deletePost(${post.id})">
                    🗑️ 删除
                </button>
            ` : ''}
        </div>

        <div class="comments-section">
            <h3>💬 评论 (${post.comment_count})</h3>
            <div class="comment-input">
                <textarea id="commentContent" placeholder="发表你的评论..."></textarea>
                <button class="btn btn-primary" id="submitCommentBtn-${post.id}">发布</button>
            </div>
            <div class="comments-list" id="commentsList">
                ${displayComments(post.comments || [])}
            </div>
        </div>
    `;

    // 重新绑定提交按钮事件
    const submitBtn = document.getElementById(`submitCommentBtn-${post.id}`);
    if (submitBtn) {
        console.log(`绑定评论按钮: submitCommentBtn-${post.id}`);
        submitBtn.onclick = () => {
            console.log('评论按钮被点击');
            createComment(post.id);
        };
    } else {
        console.error('找不到评论按钮元素');
    }

    // 为评论输入框添加回车键提交功能
    const commentInput = document.getElementById('commentContent');
    if (commentInput) {
        commentInput.addEventListener('keydown', (e) => {
            // Ctrl+Enter 或 Cmd+Enter 提交评论
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                createComment(post.id);
            }
        });
    }
}

// 检查帖子点赞状态
async function checkPostLikeStatus(postId) {
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE}/posts/${postId}/like/check`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.liked) {
                const likeBtn = document.getElementById('likeBtn');
                if (likeBtn) {
                    likeBtn.classList.add('liked');
                }
            }
        }
    } catch (error) {
        console.error('检查点赞状态失败:', error);
    }
}

// 检查帖子举报状态
async function checkPostReportStatus(postId) {
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE}/report/check?target_type=post&target_id=${postId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.reported) {
                const reportBtn = document.getElementById('reportBtn');
                if (reportBtn) {
                    reportBtn.disabled = true;
                    reportBtn.textContent = '✓ 已举报';
                    reportBtn.classList.add('disabled');
                }
            }
        }
    } catch (error) {
        console.error('检查举报状态失败:', error);
    }
}

// 显示评论列表
function displayComments(comments) {
    if (!comments || comments.length === 0) {
        return '<p style="color: #999; text-align: center; padding: 20px;">暂无评论</p>';
    }

    return comments.map(comment => `
        <div class="comment" id="comment-${comment.id}">
            <div class="comment-header">
                <span class="comment-author">${escapeHtml(comment.username)}</span>
                <span class="comment-time">${formatTime(comment.created_at)}</span>
            </div>
            <div class="comment-content">${escapeHtml(comment.content)}</div>
            <div class="comment-actions">
                <button onclick="toggleCommentLike(${comment.id})" id="likeBtn-${comment.id}">👍 ${comment.like_count}</button>
                <button onclick="showReplyInput(${comment.id})">↩️ 回复</button>
                ${currentUser && (currentUser.id === comment.user_id || currentUser.role === 'admin' || currentUser.id === currentPostId) ? `
                    <button onclick="deleteComment(${comment.id})" style="color: #ff6b6b;">🗑️ 删除</button>
                ` : ''}
            </div>
            <div class="comment-reply" id="replyForm-${comment.id}" style="display: none;">
                <div class="reply-input">
                    <textarea id="replyContent-${comment.id}" placeholder="回复..."></textarea>
                    <button class="btn btn-primary" onclick="createReply(${comment.id})">回复</button>
                </div>
            </div>
            ${comment.replies && comment.replies.length > 0 ? `
                <div class="replies-list">
                    ${comment.replies.map(reply => `
                        <div class="reply">
                            <div class="comment-header">
                                <span class="comment-author">${escapeHtml(reply.username)}</span>
                                <span class="comment-time">${formatTime(reply.created_at)}</span>
                            </div>
                            <div class="comment-content">${escapeHtml(reply.content)}</div>
                            ${currentUser && (currentUser.id === reply.user_id || currentUser.role === 'admin' || currentUser.id === currentPostId) ? `
                                <div class="comment-actions">
                                    <button onclick="toggleCommentLike(${reply.id})" id="likeBtn-${reply.id}">👍 ${reply.like_count}</button>
                                    <button onclick="deleteComment(${reply.id})" style="color: #ff6b6b;">🗑️ 删除</button>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `).join('');
}

// 点赞/取消点赞
async function toggleLike(postId) {
    if (!authToken) {
        alert('请先登录');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/posts/${postId}/like`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            const likeBtn = document.getElementById('likeBtn');
            likeBtn.textContent = `❤️ ${data.like_count}`;
            if (data.liked) {
                likeBtn.classList.add('liked');
            } else {
                likeBtn.classList.remove('liked');
            }
        }
    } catch (error) {
        console.error('点赞失败:', error);
    }
}

// 显示举报弹窗
function showReportModal(targetType, targetId) {
    if (!authToken) {
        alert('请先登录');
        window.location.href = 'login.html';
        return;
    }

    const modal = document.createElement('div');
    modal.className = 'report-modal-overlay';
    modal.innerHTML = `
        <div class="report-modal" onclick="event.stopPropagation()">
            <div class="report-modal-header">
                <h3>🚫 举报内容</h3>
                <button class="close-btn" onclick="closeReportModal()">×</button>
            </div>
            <div class="report-modal-body">
                <div class="form-group">
                    <label>举报原因:</label>
                    <textarea id="reportReason" rows="4" placeholder="请详细说明举报原因（不超过200字）" maxlength="200"></textarea>
                </div>
                <div class="report-tips">
                    <p>⚠️ 注意:</p>
                    <ul>
                        <li>恶意举报可能会降低您的信用分</li>
                        <li>同一内容只能举报一次</li>
                        <li>被举报的内容作者将被扣除10分信用分</li>
                        <li>信用分降到0将被禁言一周</li>
                    </ul>
                </div>
            </div>
            <div class="report-modal-footer">
                <button class="btn btn-secondary" onclick="closeReportModal()">取消</button>
                <button class="btn btn-danger" onclick="submitReport('${targetType}', ${targetId})">提交举报</button>
            </div>
        </div>
    `;
    modal.onclick = (e) => {
        if (e.target === modal) closeReportModal();
    };
    document.body.appendChild(modal);
}

// 关闭举报弹窗
function closeReportModal() {
    const modal = document.querySelector('.report-modal-overlay');
    if (modal) modal.remove();
}

// 提交举报
async function submitReport(targetType, targetId) {
    const reason = document.getElementById('reportReason').value.trim();

    if (!reason) {
        alert('请填写举报原因');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                target_type: targetType,
                target_id: targetId,
                reason: reason
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert('举报提交成功！');
            closeReportModal();

            // 禁用举报按钮
            const reportBtn = document.getElementById('reportBtn');
            if (reportBtn) {
                reportBtn.disabled = true;
                reportBtn.textContent = '✓ 已举报';
                reportBtn.classList.add('disabled');
            }
        } else {
            alert(data.error || '举报失败');
        }
    } catch (error) {
        console.error('举报失败:', error);
        alert('举报失败，请稍后重试');
    }
}

// 创建评论
async function createComment(postId) {
    console.log(`[评论] 开始，postId: ${postId}`);

    if (!authToken) {
        console.error('[评论] 未登录，authToken 为空');
        alert('请先登录');
        window.location.href = 'login.html';
        return;
    }

    const content = document.getElementById('commentContent').value.trim();

    if (!content) {
        console.warn('[评论] 评论内容为空');
        alert('评论内容不能为空');
        return;
    }

    console.log(`[评论] 正在为帖子 ${postId} 添加评论，内容: "${content}"`);
    console.log(`[评论] API_URL: ${API_BASE}/posts/${postId}/comments`);

    try {
        const response = await fetch(`${API_BASE}/posts/${postId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ content })
        });

        console.log(`[评论] 响应状态: ${response.status}`);

        if (response.ok) {
            const data = await response.json();
            console.log(`[评论] 评论成功，返回数据:`, data);
            document.getElementById('commentContent').value = '';
            await viewPost(postId); // 重新加载帖子详情
        } else {
            const data = await response.json();
            console.error(`[评论] 失败:`, data);
            alert(data.error || '评论失败');
        }
    } catch (error) {
        console.error('[评论] 网络错误:', error);
        alert('评论失败，请检查网络连接或稍后重试');
    }
}

// 显示回复输入框
function showReplyInput(commentId) {
    const replyForm = document.getElementById(`replyForm-${commentId}`);
    replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';

    // 为回复输入框添加回车键提交功能
    const replyInput = document.getElementById(`replyContent-${commentId}`);
    if (replyInput) {
        // 移除旧的事件监听器（如果存在）
        replyInput.removeEventListener('keydown', replyInput.keydownHandler);

        // 添加新的事件监听器
        replyInput.keydownHandler = (e) => {
            // Ctrl+Enter 或 Cmd+Enter 提交回复
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                createReply(commentId);
            }
        };
        replyInput.addEventListener('keydown', replyInput.keydownHandler);
    }
}

// 创建回复
async function createReply(parentId) {
    console.log(`[回复] 开始，parentId: ${parentId}, currentPostId: ${currentPostId}`);

    if (!authToken) {
        console.error('[回复] 未登录，authToken 为空');
        alert('请先登录');
        window.location.href = 'login.html';
        return;
    }

    if (!currentPostId) {
        console.error('[回复] currentPostId 为空');
        alert('帖子信息已过期，请刷新页面重试');
        return;
    }

    const content = document.getElementById(`replyContent-${parentId}`).value.trim();

    if (!content) {
        console.warn('[回复] 回复内容为空');
        alert('回复内容不能为空');
        return;
    }

    console.log(`[回复] 正在回复评论 ${parentId}，帖子 ${currentPostId}`);

    try {
        const response = await fetch(`${API_BASE}/posts/${currentPostId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ content, parent_id: parentId })
        });

        console.log(`[回复] 响应状态: ${response.status}`);

        if (response.ok) {
            const data = await response.json();
            console.log(`[回复] 回复成功，返回数据:`, data);
            document.getElementById(`replyContent-${parentId}`).value = '';
            await viewPost(currentPostId);
        } else {
            const data = await response.json();
            console.error(`[回复] 失败:`, data);
            alert(data.error || '回复失败');
        }
    } catch (error) {
        console.error('[回复] 网络错误:', error);
        alert('回复失败，请检查网络连接或稍后重试');
    }
}

// 删除评论
async function deleteComment(commentId) {
    if (!confirm('确定要删除这条评论吗？')) {
        return;
    }

    if (!currentPostId) {
        alert('帖子信息已过期，请刷新页面重试');
        return;
    }

    console.log(`[删除评论] 正在删除评论 ${commentId}，帖子 ${currentPostId}`);

    try {
        const response = await fetch(`${API_BASE}/comments/${commentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        console.log(`[删除评论] 响应状态: ${response.status}`);

        if (response.ok) {
            console.log(`[删除评论] 删除成功，重新加载帖子详情`);
            await viewPost(currentPostId); // 重新加载帖子详情
        } else {
            const data = await response.json();
            console.error(`[删除评论] 失败:`, data);
            alert(data.error || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请检查网络连接或稍后重试');
    }
}

// 物品点赞/取消点赞
async function toggleItemLike(itemId, itemType) {
    if (!authToken) {
        alert('请先登录');
        window.location.href = 'login.html';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/items/${itemId}/like`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            const likeCountEl = document.getElementById(`like-count-${itemId}`);
            if (likeCountEl) {
                likeCountEl.textContent = data.like_count || 0;
            }

            // 更新按钮状态
            const btn = likeCountEl?.closest('.interaction-btn');
            if (btn) {
                if (data.liked) {
                    btn.classList.add('liked');
                    btn.querySelector('.interaction-icon').textContent = '❤️';
                } else {
                    btn.classList.remove('liked');
                    btn.querySelector('.interaction-icon').textContent = '🤍';
                }
            }
        } else {
            alert(data.error || '操作失败');
        }
    } catch (error) {
        console.error('点赞失败:', error);
        alert('操作失败，请检查网络');
    }
}

// 物品推荐
async function shareItem(itemId, title) {
    if (navigator.share) {
        try {
            await navigator.share({
                title: title,
                text: `来看看这个失物招领信息：${title}`,
                url: window.location.href
            });
        } catch (error) {
            console.log('分享已取消');
        }
    } else {
        // 复制链接到剪贴板
        const url = window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            alert('链接已复制到剪贴板！');
        }).catch(() => {
            alert('请手动复制链接分享');
        });
    }
}

// 帖子点赞/取消点赞
async function togglePostLike(postId) {
    if (!authToken) {
        alert('请先登录');
        window.location.href = 'login.html';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/posts/${postId}/like`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            const likeCountEl = document.getElementById(`post-like-count-${postId}`);
            if (likeCountEl) {
                likeCountEl.textContent = data.like_count || 0;
            }

            // 更新按钮状态
            const btn = likeCountEl?.closest('.interaction-btn');
            if (btn) {
                if (data.liked) {
                    btn.classList.add('liked');
                    btn.querySelector('.interaction-icon').textContent = '❤️';
                } else {
                    btn.classList.remove('liked');
                    btn.querySelector('.interaction-icon').textContent = '🤍';
                }
            }
        } else {
            alert(data.error || '操作失败');
        }
    } catch (error) {
        console.error('点赞失败:', error);
        alert('操作失败，请检查网络');
    }
}

// 帖子推荐
async function sharePost(postId, title) {
    if (navigator.share) {
        try {
            await navigator.share({
                title: title,
                text: `来看看这篇帖子：${title}`,
                url: `${window.location.origin}/forum.html#post-${postId}`
            });
        } catch (error) {
            console.log('分享已取消');
        }
    } else {
        // 复制链接到剪贴板
        const url = `${window.location.origin}/forum.html#post-${postId}`;
        navigator.clipboard.writeText(url).then(() => {
            alert('链接已复制到剪贴板！');
        }).catch(() => {
            alert('请手动复制链接分享');
        });
    }
}

// 评论点赞/取消点赞
async function toggleCommentLike(commentId) {
    if (!authToken) {
        alert('请先登录');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/comments/${commentId}/like`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            const likeBtn = document.getElementById(`likeBtn-${commentId}`);
            if (likeBtn) {
                likeBtn.textContent = `👍 ${data.like_count}`;
                if (data.liked) {
                    likeBtn.classList.add('liked');
                } else {
                    likeBtn.classList.remove('liked');
                }
            }
        }
    } catch (error) {
        console.error('点赞失败:', error);
    }
}

// 删除帖子
async function deletePost(postId) {
    if (!confirm('确定要删除这条帖子吗？')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/posts/${postId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            alert('删除成功');
            closePostDetailModal();
            loadPosts();
        } else {
            const data = await response.json();
            alert(data.error || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请稍后重试');
    }
}

// 关闭帖子详情弹窗
function closePostDetailModal() {
    document.getElementById('postDetailModal').classList.remove('show');
}

// 记录浏览历史
async function trackBrowseHistory(itemType, itemId, title) {
    if (!authToken) {
        return; // 未登录不记录
    }

    try {
        await fetch(`${API_BASE}/track`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                item_type: itemType,
                item_id: itemId,
                title: title
            })
        });
    } catch (error) {
        console.error('记录浏览历史失败:', error);
        // 静默失败，不影响用户体验
    }
}

// 跳转到物品详情页（先记录浏览历史）
async function goToItemDetail(itemType, itemId, title) {
    // 先记录浏览历史（异步，不等待）
    trackBrowseHistory(itemType, itemId, title);

    // 跳转到详情页
    window.location.href = `item-detail.html?id=${itemId}`;
}

// 主页搜索功能
// 执行首页搜索
async function performHomeSearch() {
    const keyword = document.getElementById('homeSearchInput').value.trim();

    if (!keyword) {
        alert('请输入搜索关键词');
        return;
    }

    // 跳转到搜索结果页面
    window.location.href = `search-results.html?keyword=${encodeURIComponent(keyword)}`;
}

// 处理首页搜索框回车事件
function handleHomeSearchKeypress(event) {
    if (event.key === 'Enter') {
        performHomeSearch();
    }
}

// 查看物品详情（跳转到对应页面）
function viewItemDetail(itemId) {
    // 跳转到物品详情页面
    window.location.href = `item-detail.html?id=${itemId}`;
}






