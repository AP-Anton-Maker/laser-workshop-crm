// Базовый URL API (Определяем автоматически порт 8000 на текущем IP)
const API_BASE = `http://${window.location.hostname}:8000/api`;

// --- Авторизация ---
let token = localStorage.getItem('access_token');

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('current-date').textContent = new Date().toLocaleDateString('ru-RU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    
    if (token) {
        showApp();
    } else {
        showLogin();
    }
});

// Обертка для запросов к API с токеном
async function apiFetch(endpoint, options = {}) {
    const headers = {
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };
    if (!(options.body instanceof FormData) && typeof options.body === 'object') {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    
    if (response.status === 401) {
        logout();
        throw new Error('Не авторизован');
    }
    return response;
}

// Логика входа
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const errorMsg = document.getElementById('login-error');

    // FastAPI OAuth2PasswordRequestForm требует x-www-form-urlencoded
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (res.ok) {
            const data = await res.json();
            token = data.access_token;
            localStorage.setItem('access_token', token);
            errorMsg.style.display = 'none';
            showApp();
        } else {
            errorMsg.style.display = 'block';
        }
    } catch (err) {
        errorMsg.style.display = 'block';
        errorMsg.textContent = "Ошибка соединения с сервером";
    }
});

function logout() {
    token = null;
    localStorage.removeItem('access_token');
    showLogin();
}

document.getElementById('btn-logout').addEventListener('click', logout);

// Управление экранами
function showLogin() {
    document.getElementById('login-view').style.display = 'flex';
    document.getElementById('app-view').style.display = 'none';
}

function showApp() {
    document.getElementById('login-view').style.display = 'none';
    document.getElementById('app-view').style.display = 'block';
    loadDashboard(); // Грузим дашборд по умолчанию
}

// --- Навигация по боковому меню ---
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        // Убираем активный класс
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        // Скрываем все секции
        document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
        
        // Активируем нужную
        const target = e.currentTarget.dataset.target;
        e.currentTarget.classList.add('active');
        document.getElementById(target).classList.add('active');

        // Загружаем данные в зависимости от вкладки
        if (target === 'dashboard') loadDashboard();
        if (target === 'orders') loadOrders();
        if (target === 'clients') loadClients();
        if (target === 'chat') loadChatClients();
    });
});

// --- ДАШБОРД (AI и Аналитика) ---
async function loadDashboard() {
    try {
        // Запрашиваем обычную аналитику
        const resAnalytics = await apiFetch('/analytics/');
        const analytics = await resAnalytics.json();
        
        document.getElementById('stat-orders').textContent = analytics.total_orders;
        document.getElementById('stat-revenue').textContent = `${analytics.total_revenue.toLocaleString('ru-RU')} ₽`;
        document.getElementById('stat-profit').textContent = `${analytics.total_profit.toLocaleString('ru-RU')} ₽`;

        // Запрашиваем прогноз ИИ
        const resForecast = await apiFetch('/forecast/');
        const forecast = await resForecast.json();
        
        const aiEl = document.getElementById('stat-ai-forecast');
        const trendEl = document.getElementById('stat-ai-trend');
        
        if (forecast.status === 'success') {
            aiEl.textContent = `~ ${forecast.predicted_revenue.toLocaleString('ru-RU')} ₽`;
            if (forecast.trend === 'up') trendEl.innerHTML = '<span style="color: var(--success)"><i class="fa-solid fa-arrow-trend-up"></i> Ожидается рост продаж</span>';
            else if (forecast.trend === 'down') trendEl.innerHTML = '<span style="color: var(--danger)"><i class="fa-solid fa-arrow-trend-down"></i> Ожидается спад</span>';
            else trendEl.innerHTML = '<span style="color: var(--primary)"><i class="fa-solid fa-arrow-right-long"></i> Стабильный тренд</span>';
        } else {
            aiEl.textContent = 'Мало данных';
            trendEl.textContent = forecast.message;
        }
    } catch (e) {
        console.error("Ошибка загрузки дашборда", e);
    }
}

// --- КЛИЕНТЫ ---
async function loadClients() {
    const res = await apiFetch('/clients/');
    const clients = await res.json();
    const tbody = document.querySelector('#clients-table tbody');
    tbody.innerHTML = '';
    
    clients.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${c.name}</strong></td>
            <td>${c.vk_id ? `<i class="fa-brands fa-vk" style="color: #0077FF;"></i> ${c.vk_id}` : '—'}</td>
            <td>${c.phone || '—'}</td>
            <td><span style="background: #e0e7ff; color: #3730a3; padding: 2px 8px; border-radius: 10px; font-size: 12px;">${c.notes || 'Новый'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// --- ЗАКАЗЫ (и система кэшбэка) ---
async function loadOrders() {
    const res = await apiFetch('/orders/');
    const orders = await res.json();
    const tbody = document.querySelector('#orders-table tbody');
    tbody.innerHTML = '';
    
    orders.forEach(o => {
        const tr = document.createElement('tr');
        const statusColors = {
            'new': 'gray', 'in_progress': 'blue', 'ready': 'orange', 'delivered': 'green'
        };
        const statusText = {
            'new': 'Новый', 'in_progress': 'В работе', 'ready': 'Готов', 'delivered': 'Выдан (+Кэшбэк)'
        };
        
        tr.innerHTML = `
            <td>#${o.id}</td>
            <td>Клиент ID: ${o.client_id}</td>
            <td>${o.description}</td>
            <td><strong>${o.price} ₽</strong></td>
            <td>
                <select class="form-control status-select" data-id="${o.id}" style="color: ${statusColors[o.status]}; font-weight: bold; padding: 5px;">
                    <option value="new" ${o.status==='new'?'selected':''}>Новый</option>
                    <option value="in_progress" ${o.status==='in_progress'?'selected':''}>В работе</option>
                    <option value="ready" ${o.status==='ready'?'selected':''}>Готов</option>
                    <option value="delivered" ${o.status==='delivered'?'selected':''}>Выдан</option>
                </select>
            </td>
            <td><button class="btn btn-danger" onclick="alert('В разработке')"><i class="fa-solid fa-trash"></i></button></td>
        `;
        tbody.appendChild(tr);
    });

    // Обработчик смены статуса (вызывает начисление кэшбэка на бэкенде)
    document.querySelectorAll('.status-select').forEach(sel => {
        sel.addEventListener('change', async (e) => {
            const orderId = e.target.dataset.id;
            const newStatus = e.target.value;
            await apiFetch(`/orders/${orderId}/action/status?new_status=${newStatus}`, { method: 'POST' });
            alert(`Статус изменен! Если заказ "Выдан", клиенту начислен кэшбэк.`);
        });
    });
}

// --- ЧАТ ВК ---
let currentChatClientId = null;

async function loadChatClients() {
    const res = await apiFetch('/clients/');
    const clients = await res.json();
    const list = document.getElementById('chat-client-list');
    list.innerHTML = '';
    
    // Показываем только клиентов с ВК
    const vkClients = clients.filter(c => c.vk_id);
    
    vkClients.forEach(c => {
        const div = document.createElement('div');
        div.className = 'chat-client-item';
        div.innerHTML = `<strong>${c.name}</strong><br><small style="color: var(--text-muted)">VK: ${c.vk_id}</small>`;
        div.onclick = () => openChat(c.id, c.name);
        list.appendChild(div);
    });
}

async function openChat(clientId, clientName) {
    currentChatClientId = clientId;
    document.getElementById('chat-window').style.display = 'flex';
    document.getElementById('chat-current-client').textContent = `Диалог: ${clientName}`;
    
    const res = await apiFetch(`/chat/${clientId}`);
    const messages = await res.json();
    const container = document.getElementById('chat-messages-container');
    container.innerHTML = '';
    
    messages.forEach(m => {
        const div = document.createElement('div');
        div.className = `msg-bubble ${m.direction === 'in' ? 'msg-in' : 'msg-out'}`;
        div.textContent = m.text;
        container.appendChild(div);
    });
    
    container.scrollTop = container.scrollHeight;
}

document.getElementById('btn-send-msg').addEventListener('click', async () => {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text || !currentChatClientId) return;
    
    input.value = '';
    await apiFetch(`/chat/${currentChatClientId}/send`, {
        method: 'POST',
        body: { text: text }
    });
    
    // Обновляем чат
    openChat(currentChatClientId, document.getElementById('chat-current-client').textContent.replace('Диалог: ', ''));
});

// --- КАЛЬКУЛЯТОР ---
document.getElementById('btn-calc-modal').addEventListener('click', () => {
    document.getElementById('modal-calc').classList.add('active');
});

document.querySelector('.close-modal[data-modal="modal-calc"]').addEventListener('click', () => {
    document.getElementById('modal-calc').classList.remove('active');
});

document.getElementById('btn-do-calc').addEventListener('click', async () => {
    const req = {
        method: document.getElementById('calc-method').value,
        base_rate: parseFloat(document.getElementById('calc-rate').value),
        width_mm: parseFloat(document.getElementById('calc-w').value),
        height_mm: parseFloat(document.getElementById('calc-h').value),
        is_rush: document.getElementById('calc-rush').checked
    };
    
    const res = await apiFetch('/calculator/calculate', { method: 'POST', body: req });
    const result = await res.json();
    
    document.getElementById('calc-result').textContent = `Итого: ${result.final_price} ₽`;
});

// --- БЭКАПЫ ---
document.getElementById('btn-backup').addEventListener('click', async () => {
    try {
        const res = await apiFetch('/backup/download');
        const blob = await res.blob();
        
        // Создаем ссылку для скачивания файла (ZIP)
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `laser_crm_backup_${new Date().toISOString().slice(0,10)}.zip`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        alert("Ошибка при создании бэкапа!");
    }
});
