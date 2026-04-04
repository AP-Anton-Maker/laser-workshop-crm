const API_BASE_URL = "http://localhost:8000/api";

/**
 * Авторизация пользователя
 * @param {string} username 
 * @param {string} password 
 * @returns {Promise<Object>} Данные токена
 */
export async function login(username, password) {
    // OAuth2 требует формат form-data, а не JSON
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: formData
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Неверный логин или пароль");
    }

    const data = await response.json();
    
    // Сохраняем токен
    localStorage.setItem('crm_token', data.access_token);
    
    return data;
}

/**
 * Выход из системы
 */
export function logout() {
    localStorage.removeItem('crm_token');
    window.location.reload();
}

/**
 * Получение текущего токена
 * @returns {string|null}
 */
export function getToken() {
    return localStorage.getItem('crm_token');
}

/**
 * Получение заголовков для авторизованных запросов
 * @returns {Object}
 */
export function getAuthHeaders() {
    const token = getToken();
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };
}
