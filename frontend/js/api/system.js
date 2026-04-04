import { getToken } from './auth.js';

const API_BASE_URL = "http://localhost:8000/api";

/**
 * Получение системных настроек
 */
export async function getSettings() {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/system/settings`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        }
    });

    if (!response.ok) {
        throw new Error("Ошибка при получении настроек");
    }

    return await response.json();
}

/**
 * Обновление системных настроек
 * @param {Object} data - { is_vacation_mode: bool, vacation_end_date: str, vacation_message: str }
 */
export async function updateSettings(data) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/system/settings`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Ошибка при сохранении настроек");
    }

    return await response.json();
}
