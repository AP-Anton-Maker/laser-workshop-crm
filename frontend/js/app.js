/**
 * Главная точка входа приложения.
 * Инициализирует модули после загрузки DOM.
 */
import { initRouter } from './router.js';
import { renderOrdersTable } from './components/orders_ui.js';
import { showToast } from './utils/toast.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Laser CRM App started");
    
    // 1. Инициализация навигации (вкладки)
    initRouter();
    
    // 2. Приветственное уведомление
    showToast("Система готова к работе", "info");
    
    // Примечание: Первоначальная загрузка заказов происходит автоматически 
    // внутри router.js при клике на вкладку, либо можно вызвать здесь, 
    // если вкладка заказов активна по умолчанию в HTML.
    // Для надежности оставим триггер в роутере.
});
