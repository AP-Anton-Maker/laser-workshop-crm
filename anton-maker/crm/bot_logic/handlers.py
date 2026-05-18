"""
State machine для обработки сообщений от клиентов.
"""

import logging
from typing import Optional, Tuple
from django.utils import timezone
from decimal import Decimal

from ..models.client import Client
from ..models.order import Order
from ..models.product import Material
from .vk_client import VKClient
from .keyboards import get_main_keyboard, get_cancel_keyboard, get_confirm_keyboard
from ..utils.calculator import CostCalculator

logger = logging.getLogger('crm.bot')


def send_message(user_id: int, message: str, keyboard: Optional[dict] = None) -> bool:
    """Отправка сообщения пользователю."""
    client = VKClient()
    return client.send_message(user_id, message, keyboard)


def process_message(client: Client, text: str, attachments: list) -> bool:
    """
    Обработка входящего сообщения от клиента.
    
    Args:
        client: Объект клиента
        text: Текст сообщения
        attachments: Список вложений
        
    Returns:
        True если успешно обработано
    """
    # Обновление информации о клиенте
    if attachments and not client.first_name:
        vk_client = VKClient()
        user_info = vk_client.get_user_info(client.vk_id)
        if user_info:
            client.first_name = user_info.get('first_name', '')
            client.last_name = user_info.get('last_name', '')
            client.save(update_fields=['first_name', 'last_name'])
    
    # Обработка по состояниям
    state = client.bot_state
    
    if text == '❌ Отмена':
        client.bot_state = 'START'
        client.save(update_fields=['bot_state'])
        return send_message(client.vk_id, '✅ Отменено. Главное меню:', get_main_keyboard())
    
    if state == 'START':
        return handle_start_state(client, text)
    elif state == 'WAITING_DESC':
        return handle_waiting_desc(client, text)
    elif state == 'WAITING_FILE':
        return handle_waiting_file(client, text, attachments)
    elif state == 'CONFIRM_ORDER':
        return handle_confirm_order(client, text)
    
    # Fallback
    return send_message(client.vk_id, '❓ Не понял. Выберите действие:', get_main_keyboard())


def handle_start_state(client: Client, text: str) -> bool:
    """Обработка состояния START."""
    
    if text == '🆕 Новый заказ':
        client.bot_state = 'WAITING_DESC'
        client.save(update_fields=['bot_state'])
        return send_message(
            client.vk_id, 
            '✍️ Напишите техническое задание:\n\nОпишите, что нужно изготовить (материал, размеры, количество).',
            get_cancel_keyboard()
        )
    
    elif text == '💰 Прайс-лист':
        materials = Material.objects.filter(is_active=True)[:10]
        price_list = "📋 Прайс-лист:\n\n"
        for mat in materials:
            price_list += f"{mat.icon} {mat.name}: {mat.price_per_unit} ₽/{mat.unit}\n"
        price_list += "\n*Точную стоимость рассчитаем по макету*"
        return send_message(client.vk_id, price_list, get_main_keyboard())
    
    elif text == '📍 Контакты':
        contact_msg = (
            "📍 Наши контакты:\n\n"
            "🌐 Сайт: anton-maker.ru\n"
            "📧 Email: info@anton-maker.ru\n"
            "⏰ Режим работы: Пн-Пт 10:00-19:00\n\n"
            "📍 Адрес мастерской: г. Москва (уточняйте)"
        )
        return send_message(client.vk_id, contact_msg, get_main_keyboard())
    
    elif text == '❓ Помощь':
        help_msg = (
            "❓ Как сделать заказ:\n\n"
            "1. Нажмите «Новый заказ»\n"
            "2. Опишите, что нужно изготовить\n"
            "3. Прикрепите файл с макетом\n"
            "4. Подтвердите заказ\n\n"
            "Менеджер свяжется с вами для уточнения деталей."
        )
        return send_message(client.vk_id, help_msg, get_main_keyboard())
    
    return send_message(client.vk_id, 'Выберите действие из меню:', get_main_keyboard())


def handle_waiting_desc(client: Client, text: str) -> bool:
    """Обработка состояния WAITING_DESC."""
    
    if len(text) < 10:
        return send_message(
            client.vk_id, 
            'Описание слишком короткое. Пожалуйста, опишите подробнее:',
            get_cancel_keyboard()
        )
    
    # Создание заказа
    order = Order.objects.create(
        client=client,
        description=text,
        status='NEW'
    )
    
    client.bot_state = 'WAITING_FILE'
    client.save(update_fields=['bot_state'])
    
    return send_message(
        client.vk_id,
        f'✅ Заказ #{order.order_number} создан!\n\n'
        f'📎 Теперь прикрепите файл с макетом (чертеж, эскиз, фото).\n\n'
        f'Или напишите "без файла", если макета нет.',
        get_cancel_keyboard()
    )


def handle_waiting_file(client: Client, text: str, attachments: list) -> bool:
    """Обработка состояния WAITING_FILE."""
    
    # Получаем последний незавершенный заказ
    order = Order.objects.filter(
        client=client, 
        status='NEW'
    ).order_by('-created_at').first()
    
    if not order:
        client.bot_state = 'START'
        client.save(update_fields=['bot_state'])
        return send_message(client.vk_id, '❌ Заказ не найден. Начните заново:', get_main_keyboard())
    
    # Обработка текста "без файла"
    if text.lower() == 'без файла':
        client.bot_state = 'START'
        client.save(update_fields=['bot_state'])
        
        # Уведомление админу
        notify_admin(order)
        
        return send_message(
            client.vk_id,
            f'✅ Заказ #{order.order_number} принят!\n\n'
            f'Менеджер свяжется с вами в ближайшее время для уточнения деталей и расчета стоимости.',
            get_main_keyboard()
        )
    
    # Обработка вложений
    if attachments:
        attachment = attachments[0]
        
        if attachment.get('type') in ['doc', 'photo']:
            url = None
            filename = f"order_{order.order_number}"
            
            if attachment['type'] == 'doc':
                url = attachment['doc'].get('url')
                filename += '.pdf'
            elif attachment['type'] == 'photo':
                sizes = attachment['photo'].get('sizes', [])
                if sizes:
                    url = sizes[-1].get('url')
                    filename += '.jpg'
            
            if url:
                vk_client = VKClient()
                file_path = vk_client.download_file(url, filename)
                
                if file_path:
                    order.layout_file = file_path
                    order.save(update_fields=['layout_file'])
    
    # Переход в начало
    client.bot_state = 'START'
    client.save(update_fields=['bot_state'])
    
    # Уведомление админу
    notify_admin(order)
    
    return send_message(
        client.vk_id,
        f'✅ Заказ #{order.order_number} принят!\n\n'
        f'👨‍💼 Менеджер свяжется с вами в ближайшее время для:\n'
        f'• Уточнения деталей\n'
        f'• Расчета точной стоимости\n'
        f'• Согласования сроков\n\n'
        f'Спасибо за заказ!',
        get_main_keyboard()
    )


def handle_confirm_order(client: Client, text: str) -> bool:
    """Обработка состояния CONFIRM_ORDER."""
    
    if text == '✅ Подтвердить':
        # Найти последний заказ
        order = Order.objects.filter(
            client=client,
            status='NEW'
        ).order_by('-created_at').first()
        
        if order:
            notify_admin(order)
            
            client.bot_state = 'START'
            client.save(update_fields=['bot_state'])
            
            return send_message(
                client.vk_id,
                f'✅ Заказ подтвержден!\n\n'
                f'Номер: #{order.order_number}\n'
                f'Сумма: {order.final_price or "уточняется"} ₽\n\n'
                f'Мы приступим к работе в ближайшее время.',
                get_main_keyboard()
            )
    
    elif text == '❌ Отменить':
        order = Order.objects.filter(
            client=client,
            status='NEW'
        ).order_by('-created_at').first()
        
        if order:
            order.cancel_order()
        
        client.bot_state = 'START'
        client.save(update_fields=['bot_state'])
        
        return send_message(client.vk_id, '❌ Заказ отменен.', get_main_keyboard())
    
    return send_message(client.vk_id, 'Выберите действие:', get_confirm_keyboard())


def notify_admin(order: Order) -> None:
    """
    Отправка уведомления администратору о новом заказе.
    """
    from django.conf import settings
    
    admin_id = settings.ADMIN_VK_ID
    if not admin_id:
        logger.warning("ADMIN_VK_ID не настроен")
        return
    
    client = order.client
    message = (
        f"🔔 Новый заказ #{order.order_number}!\n\n"
        f"👤 Клиент: {client.full_name}\n"
        f"🆔 VK: {client.vk_id}\n"
        f"📝 Описание: {order.description[:100]}...\n"
        f"📎 Файл: {'есть' if order.layout_file else 'нет'}\n\n"
        f"Проверьте админку: https://anton-maker.ru/admin/crm/order/{order.id}/change/"
    )
    
    vk_client = VKClient()
    vk_client.send_message(int(admin_id), message)
    logger.info(f"Admin notified about order #{order.order_number}")
