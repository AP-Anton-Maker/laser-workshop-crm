import { login, logout } from './api/api_client.js';
import { initRouter } from './router.js';
import { renderOrdersTable } from './components/orders_ui.js';
import { renderVacationSettings, checkVacationMode } from './components/vacation_ui.js';
import { showToast } from './utils/toast.js';

// DOM элементы
const loginOverlay = document.getElementById('login-overlay');
const crmApp = document.getElementById('crm-app');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const logoutBtn = document.getElementById('logout-btn');

/**
 * Проверка авторизации
 */
function checkAuth() {
    const token = localStorage.getItem('crm_token');

    if (!token) {
        // Нет токена -> Показываем вход
        loginOverlay.style.display = 'flex';
        crmApp.style.display = 'none';
    } else {
        // Токен есть -> Показываем приложение
        loginOverlay.style.display = 'none';
        crmApp.style.display = 'grid'; // Возвращаем grid layout
        
        initApp();
    }
}

/**
 * Инициализация приложения
 */
function initApp() {
    console.log("🚀 Laser CRM Initialized");
    
    // Запуск роутера
    initRouter();
    
    // Инициализация настроек отпуска
    renderVacationSettings('vacation-settings-container');
    checkVacationMode();
    
    // Приветствие
    showToast("Добро пожаловать в систему!", "success");
}

// Обработчик входа
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    loginError.style.display = 'none';
    loginError.textContent = '';
    
    try {
        await login(username, password);
        checkAuth();
    } catch (err) {
        loginError.textContent = err.message;
        loginError.style.display = 'block';
        showToast("Ошибка входа", "error");
    }
});

// Обработчик выхода
logoutBtn.addEventListener('click', () => {
    if(confirm("Вы уверены, что хотите выйти?")) {
        logout();
    }
});

// Старт
document.addEventListener('DOMContentLoaded', checkAuth);
