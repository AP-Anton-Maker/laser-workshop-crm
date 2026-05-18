from django.core.mail import send_mail
from django.conf import settings
from .models.system import SystemLog


def notify_admin_about_order(order):
    """Уведомление админа о новом заказе (email)."""
    subject = f'Новый заказ #{order.pk}'
    message = f'''
    Клиент: {order.client.full_name}
    Телефон: {order.client.phone or 'Не указан'}
    Описание: {order.description}
    Сумма: {order.final_price} ₽
    '''
    
    if hasattr(settings, 'ADMIN_EMAIL') and settings.ADMIN_EMAIL:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_EMAIL])
    
    SystemLog.objects.create(
        action='ORDER_CREATED',
        description=f'Заказ #{order.pk} на сумму {order.final_price} ₽'
    )


def notify_client_order_status(client, status, order_id):
    """Уведомление клиента о статусе заказа (VK)."""
    from crm.bot_logic.vk_client import VKClient
    
    vk = VKClient()
    messages = {
        'NEW': 'Ваш заказ принят в работу.',
        'IN_PROGRESS': 'Ваш заказ в работе.',
        'DONE': 'Ваш заказ готов к выдаче!',
        'CANCELLED': 'Ваш заказ отменён.',
    }
    
    text = messages.get(status, f'Статус заказа изменён на: {status}')
    vk.send_message(client.vk_id, f'Заказ #{order_id}: {text}')
