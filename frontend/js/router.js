/**
 * Простой роутер для переключения вкладок без перезагрузки страницы.
 * Управляет классами .active у кнопок меню и секций контента.
 */
export function initRouter() {
    const tabs = document.querySelectorAll(".tab");
    const sections = document.querySelectorAll(".content-section");

    tabs.forEach(tab => {
        tab.addEventListener("click", (e) => {
            e.preventDefault();
            
            const targetId = tab.getAttribute("data-tab");
            if (!targetId) return;

            // Снимаем активный класс со всех вкладок и секций
            tabs.forEach(t => t.classList.remove("active"));
            sections.forEach(s => s.classList.remove("active"));

            // Добавляем активный класс текущей вкладке
            tab.classList.add("active");
            
            // Показываем нужную секцию
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.classList.add("active");
                
                // Специфичная логика: если открыли вкладку заказов - обновляем таблицу
                if (targetId === "orders-section" && typeof window.renderOrdersTable === 'function') {
                    window.renderOrdersTable();
                }
                
                // Если есть другие динамические компоненты (склад, клиенты), можно добавить аналогично
            }
        });
    });
}
