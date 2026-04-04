import { getOrders, updateOrderStatus } from '../api/api_client.js';
import { showToast } from '../utils/toast.js';

/**
 * Отрисовка таблицы заказов
 */
export async function renderOrdersTable() {
    const tbody = document.getElementById("orders-body");
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 20px;">Загрузка...</td></tr>';

    try {
        const orders = await getOrders();
        
        if (orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color: var(--text-secondary);">Заказов пока нет</td></tr>';
            return;
        }

        tbody.innerHTML = "";

        orders.forEach(order => {
            const tr = document.createElement("tr");
            
            const dateObj = new Date(order.created_at);
            const dateStr = dateObj.toLocaleDateString("ru-RU", { day: '2-digit', month: '2-digit', year: 'numeric' });
            
            // Определение класса статуса
            let badgeClass = "badge-new";
            const s = order.status.toUpperCase();
            if (s === "PROCESSING") badgeClass = "badge-processing";
            else if (s === "DONE" || s === "COMPLETED") badgeClass = "badge-done";
            else if (s === "CANCELLED") badgeClass = "badge-cancelled";

            // Кнопки действий
            let actionsHtml = '';
            if (s === "NEW") {
                actionsHtml = `<button class="btn btn-sm btn-primary btn-start-order" data-id="${order.id}">В работу</button>`;
            } else if (s === "PROCESSING") {
                actionsHtml = `<button class="btn btn-sm btn-success btn-complete-order" data-id="${order.id}">Готов</button>`;
            } else {
                actionsHtml = '<span class="text-muted">-</span>';
            }

            tr.innerHTML = `
                <td>#${order.id}</td>
                <td>${order.client_name || `Клиент #${order.client_id}`}</td>
                <td>${order.service_name}</td>
                <td><b>${order.total_price} ₽</b></td>
                <td><span class="badge ${badgeClass}">${s}</span></td>
                <td>${dateStr}</td>
                <td>${actionsHtml}</td>
            `;

            tbody.appendChild(tr);
        });

        attachOrderEvents();

    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--danger-color);">Ошибка: ${error.message}</td></tr>`;
        showToast("Не удалось загрузить заказы", "error");
    }
}

function attachOrderEvents() {
    document.querySelectorAll(".btn-start-order").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            const id = e.target.getAttribute("data-id");
            if (confirm("Перевести заказ в работу?")) {
                try {
                    await updateOrderStatus(id, "PROCESSING");
                    showToast("Статус обновлен", "success");
                    renderOrdersTable();
                } catch (err) {
                    showToast(err.message, "error");
                }
            }
        });
    });

    document.querySelectorAll(".btn-complete-order").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            const id = e.target.getAttribute("data-id");
            if (confirm("Подтвердить выполнение? Будет начислен кэшбэк.")) {
                try {
                    await updateOrderStatus(id, "DONE");
                    showToast("Заказ выполнен!", "success");
                    renderOrdersTable();
                } catch (err) {
                    showToast(err.message, "error");
                }
            }
        });
    });
}

window.renderOrdersTable = renderOrdersTable;
