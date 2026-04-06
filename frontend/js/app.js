document.addEventListener('DOMContentLoaded', () => {
    // --- DOM ЭЛЕМЕНТЫ ---
    const loginView = document.getElementById('login-view');
    const appView = document.getElementById('app-view');
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');
    const logoutBtn = document.getElementById('logout-btn');
    const navItems = document.querySelectorAll('.nav-menu li');
    const sections = document.querySelectorAll('main section');
    
    // Глобальные состояния
    let chartInstance = null;
    let currentChatClientId = null;
    let chatPollingInterval = null;

    // --- ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ ---
    async function initApp() {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                await window.API.getMe(); // Проверяем валидность токена
                loginView.style.display = 'none';
                appView.style.display = 'flex';
                loadDashboard(); // Загружаем первую вкладку
            } catch (e) {
                showLogin();
            }
        } else {
            showLogin();
        }
    }

    function showLogin() {
        loginView.style.display = 'flex';
        appView.style.display = 'none';
    }

    // --- АВТОРИЗАЦИЯ ---
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const user = document.getElementById('login-username').value;
        const pass = document.getElementById('login-password').value;
        
        try {
            loginError.style.display = 'none';
            const response = await window.API.login(user, pass);
            localStorage.setItem('token', response.access_token);
            initApp();
        } catch (error) {
            loginError.textContent = 'Ошибка: ' + error.message;
            loginError.style.display = 'block';
        }
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        if (chatPollingInterval) clearInterval(chatPollingInterval);
        window.location.reload();
    });

    // --- SPA РОУТИНГ ---
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            if (item.id === 'open-calc-btn') {
                document.getElementById('modal-calc').classList.add('active');
                return;
            }

            // Переключаем активные классы меню
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Переключаем секции
            const target = item.getAttribute('data-target');
            sections.forEach(sec => sec.classList.remove('active'));
            document.getElementById(target).classList.add('active');

            // Очищаем поллинг чата, если ушли с вкладки
            if (target !== 'chat' && chatPollingInterval) {
                clearInterval(chatPollingInterval);
                chatPollingInterval = null;
            }

            // Загрузка данных для конкретной вкладки
            if (target === 'dashboard') loadDashboard();
            if (target === 'orders') loadOrders();
            if (target === 'chat') loadChatClients();
        });
    });

    // --- ДАШБОРД (Chart.js и AI Прогноз) ---
    async function loadDashboard() {
        try {
            const forecast = await window.API.getForecast();
            document.getElementById('kpi-forecast').textContent = `${forecast.forecast} ₽`;
            
            const trendEl = document.getElementById('kpi-trend');
            if (forecast.trend === 'up') trendEl.innerHTML = '<span style="color:var(--success-color)">▲ Тренд растущий</span>';
            else if (forecast.trend === 'down') trendEl.innerHTML = '<span style="color:var(--danger-color)">▼ Тренд падающий</span>';
            else trendEl.innerHTML = '<span style="color:#f1c40f">▬ Тренд стабилен</span>';

            const orders = await window.API.getOrders();
            const activeOrders = orders.filter(o => o.status === 'NEW' || o.status === 'PROCESSING').length;
            document.getElementById('kpi-active-orders').textContent = activeOrders;

            renderChart(orders);
        } catch (e) {
            console.error("Ошибка загрузки дашборда:", e);
        }
    }

    function renderChart(orders) {
        const ctx = document.getElementById('revenueChart');
        if (chartInstance) chartInstance.destroy();

        // Агрегируем выручку по статусам (пример простой аналитики)
        let doneSum = 0, processingSum = 0;
        orders.forEach(o => {
            if (o.status === 'DONE' || o.status === 'DELIVERED') doneSum += o.price;
            if (o.status === 'PROCESSING') processingSum += o.price;
        });

        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Завершенные (Выручка)', 'В работе (Потенциал)'],
                datasets: [{
                    label: 'Сумма (₽)',
                    data: [doneSum, processingSum],
                    backgroundColor: ['#03dac6', '#f1c40f'],
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#333' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // --- ЗАКАЗЫ (Таблица и Кэшбэк) ---
    async function loadOrders() {
        const tbody = document.getElementById('orders-tbody');
        tbody.innerHTML = '<tr><td colspan="6">Загрузка...</td></tr>';
        try {
            const orders = await window.API.getOrders();
            tbody.innerHTML = '';
            orders.forEach(order => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>#${order.id}</td>
                    <td><i class="fa-solid fa-user"></i> ${order.client_id}</td>
                    <td>${order.description}</td>
                    <td style="font-weight: bold;">${order.price} ₽</td>
                    <td>
                        <select class="status-select status-${order.status}" data-id="${order.id}">
                            <option value="NEW" ${order.status === 'NEW' ? 'selected' : ''}>Новый</option>
                            <option value="PROCESSING" ${order.status === 'PROCESSING' ? 'selected' : ''}>В работе</option>
                            <option value="DONE" ${order.status === 'DONE' ? 'selected' : ''}>Готов</option>
                            <option value="DELIVERED" ${order.status === 'DELIVERED' ? 'selected' : ''}>Выдан</option>
                        </select>
                    </td>
                    <td>
                        <button class="btn-danger" style="padding: 5px 10px; font-size: 12px;"><i class="fa-solid fa-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            // Обработчик смены статуса
            document.querySelectorAll('.status-select').forEach(select => {
                select.addEventListener('change', async (e) => {
                    const orderId = e.target.getAttribute('data-id');
                    const newStatus = e.target.value;
                    try {
                        await window.API.changeOrderStatus(orderId, newStatus);
                        e.target.className = `status-select status-${newStatus}`;
                        if (newStatus === 'DELIVERED') {
                            alert('Заказ выдан! Клиенту начислен кэшбэк 5%.');
                        }
                    } catch (error) {
                        alert('Ошибка смены статуса: ' + error.message);
                        loadOrders(); // Откат
                    }
                });
            });
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="6" style="color: red;">Ошибка загрузки</td></tr>';
        }
    }

    // --- ЧАТ ВК ---
    async function loadChatClients() {
        const listEl = document.getElementById('chat-client-list');
        listEl.innerHTML = '<div style="padding:15px;">Загрузка...</div>';
        try {
            const clients = await window.API.getClients();
            listEl.innerHTML = '';
            clients.forEach(client => {
                const div = document.createElement('div');
                div.className = 'chat-client-item';
                div.innerHTML = `<strong>${client.name}</strong><br><small style="color:var(--text-secondary)">VK ID: ${client.vk_id || 'Нет'}</small>`;
                div.addEventListener('click', () => {
                    document.querySelectorAll('.chat-client-item').forEach(el => el.classList.remove('active'));
                    div.classList.add('active');
                    openChat(client);
                });
                listEl.appendChild(div);
            });
        } catch (e) {
            console.error(e);
        }
    }

    async function openChat(client) {
        currentChatClientId = client.id;
        document.getElementById('chat-current-client-name').textContent = `Чат: ${client.name}`;
        document.getElementById('chat-input').disabled = false;
        document.getElementById('chat-send-btn').disabled = false;
        
        await fetchMessages();

        // Поллинг новых сообщений каждые 3 секунды
        if (chatPollingInterval) clearInterval(chatPollingInterval);
        chatPollingInterval = setInterval(fetchMessages, 3000);
    }

    async function fetchMessages() {
        if (!currentChatClientId) return;
        try {
            const messages = await window.API.getChatHistory(currentChatClientId);
            const container = document.getElementById('chat-messages-container');
            
            // Простая проверка: если количество не изменилось, не перерисовываем (чтобы избежать мерцания)
            if (container.children.length === messages.length) return;

            container.innerHTML = '';
            messages.forEach(msg => {
                const div = document.createElement('div');
                div.className = `msg ${msg.direction === 'in' ? 'msg-in' : 'msg-out'}`;
                div.textContent = msg.text;
                container.appendChild(div);
            });
            // Автопрокрутка вниз
            container.scrollTop = container.scrollHeight;
        } catch (e) {
            console.error(e);
        }
    }

    document.getElementById('chat-send-btn').addEventListener('click', async () => {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text || !currentChatClientId) return;
        
        input.disabled = true;
        try {
            await window.API.sendChatMessage(currentChatClientId, text);
            input.value = '';
            await fetchMessages();
        } catch (e) {
            alert('Ошибка отправки: ' + e.message);
        } finally {
            input.disabled = false;
            input.focus();
        }
    });

    // --- БЭКАПЫ ---
    document.getElementById('btn-download-backup').addEventListener('click', async (e) => {
        const btn = e.target;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Создание архива...';
        btn.disabled = true;
        
        try {
            const blob = await window.API.downloadBackup();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const dateStr = new Date().toISOString().slice(0,10).replace(/-/g, "");
            a.download = `laser_crm_backup_${dateStr}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (error) {
            alert('Ошибка создания бэкапа: ' + error.message);
        } finally {
            btn.innerHTML = '<i class="fa-solid fa-download"></i> Сгенерировать и скачать';
            btn.disabled = false;
        }
    });

    // --- КАЛЬКУЛЯТОР (Модалка) ---
    const calcModal = document.getElementById('modal-calc');
    const calcMethodSelect = document.getElementById('calc-method');
    const dynamicInputsContainer = document.getElementById('calc-dynamic-inputs');

    document.getElementById('close-calc-modal').addEventListener('click', () => {
        calcModal.classList.remove('active');
    });

    calcMethodSelect.addEventListener('change', (e) => {
        const method = e.target.value;
        let html = '';
        if (method === 'area_cm2') {
            html = `
                <div style="display:flex; gap:10px; margin-bottom:15px;">
                    <div style="flex:1"><label>Ширина (мм)</label><input type="number" id="calc-w" required></div>
                    <div style="flex:1"><label>Высота (мм)</label><input type="number" id="calc-h" required></div>
                </div>`;
        } else if (method === 'meter_thickness') {
            html = `
                <div style="display:flex; gap:10px; margin-bottom:15px;">
                    <div style="flex:1"><label>Длина реза (м)</label><input type="number" step="0.1" id="calc-m" required></div>
                    <div style="flex:1"><label>Толщина (мм)</label><input type="number" step="0.1" id="calc-t" required></div>
                </div>`;
        } else if (method === 'per_minute') {
            html = `<label>Минуты работы</label><input type="number" id="calc-min" required>`;
        }
        dynamicInputsContainer.innerHTML = html;
    });

    // Инициализация полей по умолчанию
    calcMethodSelect.dispatchEvent(new Event('change'));

    document.getElementById('calc-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const payload = {
            method: calcMethodSelect.value,
            base_price: parseFloat(document.getElementById('calc-base-price').value),
            quantity: parseInt(document.getElementById('calc-qty').value),
            is_urgent: document.getElementById('calc-urgent').checked
        };

        // Собираем динамические поля
        if (payload.method === 'area_cm2') {
            payload.width_mm = parseFloat(document.getElementById('calc-w').value);
            payload.height_mm = parseFloat(document.getElementById('calc-h').value);
        } else if (payload.method === 'meter_thickness') {
            payload.meters_cut = parseFloat(document.getElementById('calc-m').value);
            payload.thickness_mm = parseFloat(document.getElementById('calc-t').value);
        } else if (payload.method === 'per_minute') {
            payload.minutes = parseFloat(document.getElementById('calc-min').value);
        }

        try {
            const price = await window.API.calculate(payload);
            document.getElementById('calc-result').textContent = `${price} ₽`;
        } catch (error) {
            alert('Ошибка расчета: ' + error.message);
        }
    });

    // Старт
    initApp();
});
