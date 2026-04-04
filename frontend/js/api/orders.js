/**
 * API модуль для работы с заказами.
 * Обертки над fetch для взаимодействия с FastAPI бэкендом.
 */

const API_BASE_URL = "http://localhost:8000/api";

/**
 * Получение списка заказов
 * @param {string} statusFilter - Фильтр по статусу ('all' или конкретный статус)
 * @returns {Promise<Array>} Массив заказов
 */
export async function getOrders(statusFilter = 'all') {
    let url = `${API_BASE_URL}/orders/`;
    if (statusFilter !== 'all') {
        url += `?status=${statusFilter}`;
    }

    try {
        const response = await fetch(url, {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });

        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Ошибка при получении заказов:", error);
        throw error;
    }
}

/**
 * Создание нового заказа
 * @param {Object} orderData - Данные заказа (client_id, service_name, parameters, total_price и т.д.)
 * @returns {Promise<Object>} Созданный заказ
 */
export async function createOrder(orderData) {
    try {
        const response = await fetch(`${API_BASE_URL}/order/create`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(orderData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Ошибка при создании заказа");
        }

        return data;
    } catch (error) {
        console.error("Ошибка при создании заказа:", error);
        throw error;
    }
}

/**
 * Обновление статуса заказа
 * @param {number} orderId - ID заказа
 * @param {string} status - Новый статус (PROCESSING, DONE и т.д.)
 * @returns {Promise<Object>} Обновленный заказ
 */
export async function updateOrderStatus(orderId, status) {
    try {
        const response = await fetch(`${API_BASE_URL}/order/status`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ order_id: orderId, status })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Ошибка при обновлении статуса");
        }

        return data;
    } catch (error) {
        console.error("Ошибка при обновлении статуса:", error);
        throw error;
    }
}
