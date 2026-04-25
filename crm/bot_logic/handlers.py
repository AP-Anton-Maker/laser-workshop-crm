from django.conf import settings
from .vk_api_client import VKClient
from .keyboards import get_main_keyboard, get_cancel_keyboard
from ..models import Order, Material

vk_client = VKClient()

def process_message(client, text, attachments):
    """
    Главная стейт-машина бота.
    client: Объект модели Client
    text: Текст сообщения
    attachments: Список вложений от ВК
    """
    
    user_id = client.vk_id
    state = client.bot_state

    # 1. Обработка команды "Отмена" в любом состоянии
    if text.strip().lower() == 'отмена' or text.strip().lower() == 'cancel':
        client.bot_state = 'START'
        client.save()
        vk_client.send_message(user_id, "❌ Действие отменено. Возврат в главное меню.", get_main_keyboard())
        return

    # 2. Состояние START (Ожидание выбора)
    if state == 'START':
        if text == "📏 Новый заказ":
            client.bot_state = 'WAITING_DESC'
            client.save()
            vk_client.send_message(
                user_id, 
                "📝 Отлично! Опишите ваш заказ:\n- Материал\n- Размеры/Длина\n- Тираж\n\nИли напишите 'Отмена', чтобы выйти.",
                get_cancel_keyboard()
            )
        elif text == "💰 Прайс-лист":
            materials = Material.objects.filter(in_stock=True)
            if materials:
                msg = "📋 **Актуальный прайс:**\n"
                for m in materials:
                    msg += f"• {m.name}: {m.price_per_meter} ₽/м\n"
                vk_client.send_message(user_id, msg, get_main_keyboard())
            else:
                vk_client.send_message(user_id, "Прайс временно недоступен.", get_main_keyboard())
        else:
            vk_client.send_message(user_id, "Выберите действие из меню:", get_main_keyboard())

    # 3. Состояние WAITING_DESC (Ожидание описания)
    elif state == 'WAITING_DESC':
        if not text:
            vk_client.send_message(user_id, "Пожалуйста, напишите текстовое описание заказа.", get_cancel_keyboard())
            return

        Order.objects.create(
            client=client,
            description=text,
            status='NEW'
        )
        
        client.bot_state = 'WAITING_FILE'
        client.save()
        
        vk_client.send_message(
            user_id, 
            "📎 Описание сохранено. Теперь прикрепите файл с макетом (DXF, AI, PDF) или напишите 'Без файла'.",
            get_cancel_keyboard()
        )

    # 4. Состояние WAITING_FILE (Ожидание файла)
    elif state == 'WAITING_FILE':
        if text.lower() == 'без файла':
            last_order = Order.objects.filter(client=client).latest('created_at')
            last_order.save()
            
            client.bot_state = 'START'
            client.save()
            
            notify_admin(f"Новый заказ #{last_order.id} от {client.full_name} (Без файла)")
            vk_client.send_message(user_id, "✅ Заказ принят в работу! Менеджер свяжется с вами.", get_main_keyboard())
            return

        doc_attachment = None
        for att in attachments:
            if att['type'] == 'doc':
                doc_attachment = att['doc']
                break
        
        if doc_attachment:
            file_url = doc_attachment['url']
            file_name = doc_attachment['title']
            
            relative_path = vk_client.download_file(file_url, file_name)
            
            if relative_path:
                last_order = Order.objects.filter(client=client).latest('created_at')
                last_order.layout_file = relative_path
                last_order.save()
                
                client.bot_state = 'START'
                client.save()
                
                notify_admin(f"Новый заказ #{last_order.id} от {client.full_name}. Файл: {file_name}")
                vk_client.send_message(user_id, "✅ Файл получен! Заказ передан мастерам.", get_main_keyboard())
            else:
                vk_client.send_message(user_id, "❌ Ошибка при скачивании файла. Попробуйте отправить снова или напишите 'Отмена'.", get_cancel_keyboard())
        else:
            vk_client.send_message(user_id, "Я не нашел прикрепленного документа. Пожалуйста, пришлите файл макета или напишите 'Без файла'.", get_cancel_keyboard())

def notify_admin(message):
    """Отправляет уведомление администратору."""
    admin_id = getattr(settings, 'VK_ADMIN_ID', None)
    if admin_id:
        vk_client.send_message(admin_id, f"🔔 {message}")
