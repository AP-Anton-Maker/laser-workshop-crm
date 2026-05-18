from django.conf import settings
from .keyboards import get_main_keyboard, get_cancel_keyboard, get_confirm_keyboard
from ..models.order import Order
from ..models.inventory import Material
from ..utils.calculator import calculate_price


def process_message(client, text, attachments):
    state = client.bot_state
    
    if text == '/start' or text == '':
        client.bot_state = 'START'
        client.save()
        return f"👋 {client.full_name}, добро пожаловать!\n\nВыберите действие в меню."
    
    if state == 'START':
        if text == '📝 Новый заказ' or text == '/new':
            client.bot_state = 'WAIT_DESC'
            client.save()
            return "📝 Опишите ваш заказ:\n- Что нужно изготовить?\n- Размеры?\n- Материал?\n\nИли отправьте /cancel для отмены."
        elif text == '📊 Статус заказа' or text == '/status':
            orders = Order.objects.filter(client=client).order_by('-created_at')[:3]
            if not orders:
                return "У вас пока нет заказов."
            result = "📊 Ваши последние заказы:\n"
            for order in orders:
                result += f"\n№{order.pk}: {order.get_status_display()} - {order.final_price} ₽"
            return result
        elif text == '📞 Контакты' or text == '/contacts':
            return "📞 Контакты:\nТелефон: +7 (XXX) XXX-XX-XX\nАдрес: г. Москва, ул. Примерная, 1"
        else:
            return f"👋 {client.full_name}, выберите действие из меню."
    
    elif state == 'WAIT_DESC':
        if text == '/cancel':
            client.bot_state = 'START'
            client.save()
            return "❌ Заказ отменён."
        
        client.temp_description = text
        client.bot_state = 'WAIT_FILE'
        client.save()
        return "📁 Отправьте файл макета (фото, чертеж) или напишите /skip если файла нет."
    
    elif state == 'WAIT_FILE':
        if text == '/cancel':
            client.bot_state = 'START'
            client.save()
            return "❌ Заказ отменён."
        
        layout_file = None
        if attachments:
            for att in attachments:
                if att['type'] == 'photo':
                    photo_url = att['photo']['sizes'][-1]['url']
                    from .vk_client import VKClient
                    vk = VKClient()
                    layout_file = vk.download_file(photo_url, f'order_{client.vk_id}_{attachments[0]["photo"]["id"]}.jpg')
                    break
        
        material = Material.objects.filter(is_active=True).first()
        estimated_price = calculate_price(100, material.price_per_unit if material else 0)
        
        order = Order.objects.create(
            client=client,
            material=material,
            description= getattr(client, 'temp_description', text),
            layout_file=layout_file,
            estimated_price=estimated_price,
            final_price=estimated_price,
        )
        
        client.bot_state = 'START'
        client.temp_description = ''
        client.save()
        
        if hasattr(settings, 'VK_ADMIN_ID') and settings.VK_ADMIN_ID:
            try:
                from .vk_client import VKClient
                vk_admin = VKClient()
                vk_admin.send_message(
                    int(settings.VK_ADMIN_ID),
                    f"🔔 Новый заказ #{order.pk}\nКлиент: {client.full_name}\nСумма: {estimated_price} ₽"
                )
            except:
                pass
        
        return f"✅ Заказ №{order.pk} создан!\nПредварительная стоимость: {estimated_price} ₽\n\nМенеджер свяжется с вами в ближайшее время."
    
    return "Что-то пошло не так. Напишите /start для начала."
