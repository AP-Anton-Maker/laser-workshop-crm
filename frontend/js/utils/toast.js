/**
 * Утилита для показа всплывающих уведомлений (Toasts).
 * @param {string} message - Текст сообщения
 * @param {string} type - Тип: 'success', 'error', 'info', 'warning'
 */
export function showToast(message, type = "success") {
    // Создаем контейнер, если его нет
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    
    // Иконки в зависимости от типа
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';

    toast.innerHTML = `<span>${icon} ${message}</span>`;

    container.appendChild(toast);

    // Анимация появления (через CSS класс или стили)
    toast.style.animation = "slideIn 0.3s ease-out forwards";

    // Удаление через 3 секунды
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            // Очистка контейнера если пуст
            if (container.children.length === 0) {
                container.remove();
            }
        }, 300);
    }, 3000);
}
