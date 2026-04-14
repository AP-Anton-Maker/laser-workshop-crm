import logging
import json
import math
import vk_api
from django.conf import settings
from django.core.management.base import BaseCommand
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from bot.models import Client, Order, PriceListItem, Setting, ChatMessage
from bot.calculator import calculate_price
from bot.fsm import get_user_state, set_user_state, clear_user_state

logger = logging.getLogger(__name__)

# ================= НАСТРОЙКИ БИЗНЕСА =================
# ВПИШИТЕ СЮДА ВАШ ID ВКОНТАКТЕ (цифры), чтобы видеть админ-меню!
ADMIN_VK_ID = 12345678  

DESIGN_FEE = 500  # Стоимость отрисовки макета с нуля
URGENCY_MULTIPLIER = 1.5  # Наценка за срочность (1.5 = +50%)
DELIVERY_OPTIONS = {"🏠 Самовывоз": 0, "📦 СДЭК": 350, "✉️ Почта": 300}
CASHBACK_PERCENT = 0.05  # 5% кэшбэка
# =====================================================

vk_session = vk_api.VkApi(token=settings.VK_TOKEN)
vk = vk_session.get_api()
GROUP_ID = vk.groups.getById()[0]['id']
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

def send_vk_message(user_id, text, keyboard=None):
    vk.messages.send(user_id=user_id, message=text, random_id=get_random_id(), keyboard=keyboard)

def get_or_create_client(vk_id):
    client, created = Client.objects.get_or_create(vk_id=vk_id)
    if created or not client.name:
        try:
            user_info = vk.users.get(user_ids=vk_id)[0]
            client.name = f"{user_info['first_name']} {user_info['last_name']}"
            client.save(update_fields=['name'])
        except:
            client.name = "Клиент"
            client.save(update_fields=['name'])
    return client

def get_main_keyboard(is_admin=False):
    kb = VkKeyboard(inline=False)
    kb.add_button('🧮 Рассчитать заказ', color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button('📋 Каталог услуг', color=VkKeyboardColor.SECONDARY)
    kb.add_button('📦 Мои заказы', color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button('💰 Мой баланс', color=VkKeyboardColor.SECONDARY)
    kb.add_button('📞 Связь с мастером', color=VkKeyboardColor.PRIMARY)
    
    if is_admin:
        kb.add_line()
        kb.add_button('👑 Текущие заказы', color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()

class Command(BaseCommand):
    help = 'Запуск умного помощника VK с пошаговой воронкой'

    def handle(self, *args, **options):
        logger.info("✅ Бот запущен (Пошаговая воронка)")
        for event in longpoll.listen():
            try:
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.handle_message(event)
            except Exception as e:
                logger.error(f"Ошибка: {e}")

    def handle_message(self, event):
        user_id = event.obj.message['from_id']
        original_text = (event.obj.message.get('text') or '').strip()
        text_lower = original_text.lower()
        client = get_or_create_client(user_id)
        is_admin = (user_id == ADMIN_VK_ID)

        ChatMessage.objects.create(client=client, vk_id=user_id, message_text=original_text, is_admin=False)
        state, data = get_user_state(user_id)

        # ГЛОБАЛЬНЫЕ КОМАНДЫ ОТМЕНЫ
        if 'отмена' in text_lower or 'назад' in text_lower or 'меню' in text_lower or '❌' in text_lower:
            clear_user_state(user_id)
            send_vk_message(user_id, "Действие отменено. Главное меню 👇", keyboard=get_main_keyboard(is_admin))
            return

        if text_lower in ['привет', 'начать', 'start']:
            clear_user_state(user_id)
            msg = f"👋 Привет, {client.name}!\nВаш кэшбэк-баланс: {client.cashback_balance} руб.\n👇 Выберите действие:"
            send_vk_message(user_id, msg, keyboard=get_main_keyboard(is_admin))
            return

        if state == 'waiting_for_master':
            return

        # ================ БЛОК АДМИНА ================
        if is_admin and 'текущие заказы' in text_lower:
            orders = Order.objects.exclude(status__in=['COMPLETED', 'CANCELED']).order_by('-created_at')[:10]
            if not orders:
                send_vk_message(user_id, "Нет активных заказов.", keyboard=get_main_keyboard(is_admin))
                return
            msg = "👑 АКТИВНЫЕ ЗАКАЗЫ:\n\n"
            for o in orders:
                msg += f"🔹 #{o.id} - {o.service_name} ({o.total_price}₽) [{o.get_status_display()}]\n"
            send_vk_message(user_id, msg, keyboard=get_main_keyboard(is_admin))
            return

        # ================ БЛОК КЛИЕНТА ================
        if 'мои заказы' in text_lower:
            orders = Order.objects.filter(client=client).order_by('-created_at')[:5]
            if not orders:
                send_vk_message(user_id, "У вас пока нет заказов.", keyboard=get_main_keyboard(is_admin))
                return
            msg = "📦 ВАШИ ПОСЛЕДНИЕ ЗАКАЗЫ:\n\n"
            for o in orders:
                msg += f"🔹 Заказ #{o.id}: {o.service_name}\nСтатус: {o.get_status_display()}\nСумма: {o.total_price}₽\n\n"
            send_vk_message(user_id, msg, keyboard=get_main_keyboard(is_admin))
            return

        if 'каталог' in text_lower:
            services = PriceListItem.objects.filter(is_active=True)
            reply = "📋 Каталог:\n" + "\n".join([f"• {s.name} — от {s.base_price}₽" for s in services]) if services else "Услуг пока нет."
            send_vk_message(user_id, reply, keyboard=get_main_keyboard(is_admin))
            return

        if 'баланс' in text_lower:
            send_vk_message(user_id, f"💰 Ваш баланс: {client.cashback_balance:.2f} баллов.", keyboard=get_main_keyboard(is_admin))
            return

        if 'мастер' in text_lower or 'связь' in text_lower:
            send_vk_message(user_id, "📞 Переключаю на мастера!\nЯ отключаюсь. (Для перезапуска напишите «отмена»).", keyboard=VkKeyboard.get_empty_keyboard())
            set_user_state(user_id, 'waiting_for_master')
            # Уведомляем админа
            send_vk_message(ADMIN_VK_ID, f"🔔 Клиент @id{user_id} ({client.name}) зовёт мастера в чат!")
            return

        if 'рассчитать' in text_lower:
            services = PriceListItem.objects.filter(is_active=True)[:10]
            if not services:
                send_vk_message(user_id, "Услуги временно не добавлены.")
                return
            kb = VkKeyboard(inline=False)
            for i, s in enumerate(services):
                if i > 0 and i % 2 == 0: kb.add_line()
                kb.add_button(s.name[:40], color=VkKeyboardColor.PRIMARY)
            kb.add_line()
            kb.add_button('❌ Отмена', color=VkKeyboardColor.NEGATIVE)
            send_vk_message(user_id, "Выбери услугу 👇:", keyboard=kb.get_keyboard())
            set_user_state(user_id, 'awaiting_service')
            return

        # ================ ВОРОНКА ОФОРМЛЕНИЯ ================
        if state == 'awaiting_service':
            service = PriceListItem.objects.filter(is_active=True, name__icontains=original_text).first()
            if not service:
                send_vk_message(user_id, "Нажмите на кнопку с названием услуги.", keyboard=get_main_keyboard(is_admin))
                clear_user_state(user_id)
                return

            set_user_state(user_id, 'awaiting_params', {
                'service_name': service.name,
                'calc_type': service.calc_type,
                'base_price': float(service.base_price),
                'min_price': float(service.min_price),
                'params': {}
            })
            param_msg = "Введите параметры (например: количество, или длину и ширину через пробел):"
            kb = VkKeyboard(inline=False)
            kb.add_button('❌ Отмена', color=VkKeyboardColor.NEGATIVE)
            send_vk_message(user_id, f"Выбрано: {service.name}\n\n{param_msg}", keyboard=kb.get_keyboard())
            return

        if state == 'awaiting_params':
            try:
                parts = original_text.replace(',', '.').split()
                params = {}
                calc_type = data['calc_type']
                
                # Простейший парсинг параметров (можно расширить)
                if len(parts) >= 2:
                    params['val1'], params['val2'] = float(parts[0]), float(parts[1])
                elif len(parts) == 1:
                    params['quantity'] = float(parts[0])
                else:
                    params['quantity'] = 1

                data['params'] = params
                # Считаем голую базу
                calculated_base = calculate_price(calc_type, params, data['base_price'], data['min_price'])
                data['calculated_base'] = calculated_base

                kb = VkKeyboard(inline=False)
                kb.add_button("🎨 Готовый вектор (.cdr, .ai)", color=VkKeyboardColor.POSITIVE)
                kb.add_line()
                kb.add_button("🖌 Нужно нарисовать с нуля", color=VkKeyboardColor.SECONDARY)
                kb.add_line()
                kb.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
                send_vk_message(user_id, "В каком виде у вас макет?", keyboard=kb.get_keyboard())
                set_user_state(user_id, 'awaiting_design', data)
            except ValueError:
                send_vk_message(user_id, "⚠️ Ошибка. Введите числа.")
            return

        if state == 'awaiting_design':
            data['design_fee'] = DESIGN_FEE if "с нуля" in text_lower else 0
            
            kb = VkKeyboard(inline=False)
            kb.add_button("🔥 Да (день в день)", color=VkKeyboardColor.POSITIVE)
            kb.add_button("⏳ Нет (в порядке очереди)", color=VkKeyboardColor.SECONDARY)
            kb.add_line()
            kb.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
            send_vk_message(user_id, f"Срочный заказ? (+50% к стоимости)", keyboard=kb.get_keyboard())
            set_user_state(user_id, 'awaiting_urgency', data)
            return

        if state == 'awaiting_urgency':
            data['is_urgent'] = 'да' in text_lower
            
            kb = VkKeyboard(inline=False)
            for dev in DELIVERY_OPTIONS.keys():
                kb.add_button(dev, color=VkKeyboardColor.PRIMARY)
                kb.add_line()
            kb.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
            send_vk_message(user_id, "🚚 Выберите способ доставки:", keyboard=kb.get_keyboard())
            set_user_state(user_id, 'awaiting_delivery', data)
            return

        if state == 'awaiting_delivery':
            # Находим выбранную доставку
            delivery_cost = 0
            delivery_name = original_text
            for d_name, cost in DELIVERY_OPTIONS.items():
                if d_name in original_text:
                    delivery_cost = cost
                    delivery_name = d_name
                    break
            
            data['delivery_name'] = delivery_name
            data['delivery_cost'] = delivery_cost
            
            kb = VkKeyboard(inline=False)
            kb.add_button("Пропустить", color=VkKeyboardColor.PRIMARY)
            if client.cashback_balance > 0:
                kb.add_line()
                kb.add_button(f"Списать {int(client.cashback_balance)} баллов", color=VkKeyboardColor.POSITIVE)
            kb.add_line()
            kb.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
            
            send_vk_message(user_id, f"🎁 У вас есть {client.cashback_balance} баллов.\nЖелаете списать?", keyboard=kb.get_keyboard())
            set_user_state(user_id, 'awaiting_points', data)
            return

        if state == 'awaiting_points':
            points_used = 0
            if "списать" in text_lower:
                points_used = float(client.cashback_balance)
            data['points_used'] = points_used

            # ФИНАЛЬНЫЙ РАСЧЕТ
            raw_tot = data['calculated_base'] + data['design_fee']
            if data['is_urgent']:
                raw_tot *= URGENCY_MULTIPLIER
            
            final_price = raw_tot + data['delivery_cost'] - points_used
            if final_price < 100: final_price = 100 # Мин чек
            
            data['final_price'] = math.ceil(final_price)
            data['earned_cashback'] = int(data['final_price'] * CASHBACK_PERCENT)

            receipt = f"🧾 **ВАШ ЧЕК:**\n\n"
            receipt += f"Услуга: {data['service_name']}\n"
            if data['design_fee'] > 0: receipt += f"Отрисовка макета: {DESIGN_FEE}₽\n"
            if data['is_urgent']: receipt += f"Срочность: Наценка 50%\n"
            receipt += f"Доставка: {data['delivery_name']} ({data['delivery_cost']}₽)\n"
            if points_used > 0: receipt += f"Списано баллов: -{points_used}₽\n"
            receipt += f"----------------\n"
            receipt += f"ИТОГО К ОПЛАТЕ: {data['final_price']} ₽\n"
            receipt += f"🎁 Будет начислено кэшбэка: +{data['earned_cashback']} баллов!\n\n"
            receipt += "Подтверждаете оформление?"

            kb = VkKeyboard(inline=False)
            kb.add_button("✅ Подтверждаю", color=VkKeyboardColor.POSITIVE)
            kb.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
            
            send_vk_message(user_id, receipt, keyboard=kb.get_keyboard())
            set_user_state(user_id, 'awaiting_confirmation', data)
            return

        if state == 'awaiting_confirmation':
            if 'подтверждаю' in text_lower:
                if data:
                    # Создаем заказ в БД
                    order = Order.objects.create(
                        client=client,
                        service_name=data['service_name'],
                        service_type=data['calc_type'],
                        parameters=data['params'],
                        total_price=data['final_price'],
                        status='NEW'
                    )
                    # Списываем баллы у клиента
                    if data.get('points_used', 0) > 0:
                        client.cashback_balance -= data['points_used']
                        client.save()
                    
                    send_vk_message(user_id, f"✅ Заказ #{order.id} успешно оформлен!\nПожалуйста, прикрепите фото или макет (если есть).\nМастер скоро с вами свяжется.", keyboard=get_main_keyboard(is_admin))
                    
                    # Уведомляем админа о новом заказе
                    admin_msg = f"🔥 НОВЫЙ ЗАКАЗ #{order.id}!\nОт: @id{user_id} ({client.name})\nУслуга: {data['service_name']}\nСумма: {data['final_price']} ₽\nСрочно: {'Да' if data['is_urgent'] else 'Нет'}\nДоставка: {data['delivery_name']}"
                    send_vk_message(ADMIN_VK_ID, admin_msg)
                else:
                    send_vk_message(user_id, "Данные заказа потеряны.", keyboard=get_main_keyboard(is_admin))
            clear_user_state(user_id)
            return

        send_vk_message(user_id, "🤖 Воспользуйтесь кнопками меню 👇", keyboard=get_main_keyboard(is_admin))
EOFimport logging
import json
import re
import vk_api
from django.conf import settings
from django.core.management.base import BaseCommand
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

from bot.models import Client, Order, PriceListItem, Setting, ChatMessage
from bot.calculator import calculate_price
from bot.fsm import get_user_state, set_user_state, clear_user_state

logger = logging.getLogger(__name__)

# ВОЗВРАЩАЕМ СТАРЫЙ НАДЕЖНЫЙ LONG POLL
vk_session = vk_api.VkApi(token=settings.VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

def send_vk_message(user_id, text, keyboard=None):
    vk.messages.send(user_id=user_id, message=text, random_id=get_random_id(), keyboard=keyboard)

def get_or_create_client(vk_id):
    client, created = Client.objects.get_or_create(vk_id=vk_id)
    if created or not client.name:
        try:
            user_info = vk.users.get(user_ids=vk_id)[0]
            client.name = f"{user_info['first_name']} {user_info['last_name']}"
            client.save(update_fields=['name'])
        except:
            client.name = "Клиент"
            client.save(update_fields=['name'])
    return client

def get_setting(key):
    try:
        return Setting.objects.get(key=key).value
    except Setting.DoesNotExist:
        return None

def get_empty_keyboard():
    return VkKeyboard.get_empty_keyboard()

def get_main_keyboard():
    keyboard = VkKeyboard(inline=False) # ОБЫЧНАЯ КЛАВИАТУРА ВНИЗУ ЭКРАНА!
    keyboard.add_button('📋 Каталог', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🧮 Рассчитать', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('💰 Баланс', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('📞 Мастер', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('❓ Помощь', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def get_order_confirmation_keyboard():
    keyboard = VkKeyboard(inline=False)
    keyboard.add_button('✅ Оформить', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('❌ Отмена', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

class Command(BaseCommand):
    help = 'Запуск умного помощника VK'

    def handle(self, *args, **options):
        logger.info("✅ Бот запущен (Стабильная версия - Обычные кнопки)")
        for event in longpoll.listen():
            try:
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    self.handle_message(event)
            except Exception as e:
                logger.error(f"Ошибка: {e}")

    def handle_message(self, event):
        user_id = event.user_id
        original_text = (event.text or '').strip()
        text_lower = original_text.lower()
        client = get_or_create_client(user_id)

        vacation_mode = get_setting('vacation_mode')
        if vacation_mode == '1':
            msg = get_setting('vacation_message') or "🔧 Мастер временно не принимает заказы."
            send_vk_message(user_id, msg)
            return

        ChatMessage.objects.create(client=client, vk_id=user_id, message_text=original_text, is_admin=False)
        state, data = get_user_state(user_id)

        # ГЛОБАЛЬНЫЕ КОМАНДЫ (Отмена)
        if 'отмена' in text_lower or 'стоп' in text_lower or 'назад' in text_lower or 'выйти' in text_lower or 'меню' in text_lower or '❌' in text_lower:
            clear_user_state(user_id)
            send_vk_message(user_id, "Действие отменено. Главное меню 👇", keyboard=get_main_keyboard())
            return

        if text_lower in ['привет', 'начать', 'start']:
            clear_user_state(user_id)
            send_vk_message(user_id, f"✨ Привет, {client.name}! Выберите действие 👇", keyboard=get_main_keyboard())
            return

        if state == 'waiting_for_master':
            return

        # ГЛАВНОЕ МЕНЮ
        if 'каталог' in text_lower:
            services = PriceListItem.objects.filter(is_active=True)
            reply = "📋 Каталог:\n" + "\n".join([f"• {s.name} — {s.base_price}₽/{s.unit}" for s in services]) if services else "Услуг пока нет."
            send_vk_message(user_id, reply, keyboard=get_main_keyboard())
            return

        if 'баланс' in text_lower:
            send_vk_message(user_id, f"💰 Твой кэшбэк: {client.cashback_balance:.2f}₽", keyboard=get_main_keyboard())
            return

        if 'мастер' in text_lower or 'человек' in text_lower or 'менеджер' in text_lower:
            send_vk_message(user_id, "📞 Переключаю на мастера!\nЯ отключаюсь. (Для перезапуска напишите «отмена»).", keyboard=get_empty_keyboard())
            set_user_state(user_id, 'waiting_for_master')
            return

        if 'помощь' in text_lower:
            send_vk_message(user_id, "❓ Я умею: считать цены и показывать каталог. Выберите действие:", keyboard=get_main_keyboard())
            return

        if 'рассчитать' in text_lower:
            services = PriceListItem.objects.filter(is_active=True)[:10]
            if not services:
                send_vk_message(user_id, "Услуги временно не добавлены.")
                return
            keyboard = VkKeyboard(inline=False)
            for i, s in enumerate(services):
                if i > 0 and i % 2 == 0:
                    keyboard.add_line()
                keyboard.add_button(s.name[:40], color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button('❌ Отмена', color=VkKeyboardColor.NEGATIVE)
            
            send_vk_message(user_id, "Выбери услугу 👇:", keyboard=keyboard.get_keyboard())
            set_user_state(user_id, 'awaiting_service')
            return

        # МАШИНА СОСТОЯНИЙ
        if state == 'awaiting_service':
            service = PriceListItem.objects.filter(is_active=True, name__icontains=original_text).first()
            if not service:
                send_vk_message(user_id, "Пожалуйста, нажмите на кнопку с названием услуги.", keyboard=get_main_keyboard())
                clear_user_state(user_id)
                return

            set_user_state(user_id, 'awaiting_params', {
                'service': {'id': service.id, 'name': service.name, 'calc_type': service.calc_type, 'base_price': float(service.base_price), 'min_price': float(service.min_price)},
                'params': {}
            })
            param_msg = {
                'area_cm2': 'Введи длину и ширину (см) через пробел',
                'meter_thickness': 'Введи метры реза и толщину (мм) через пробел',
            }.get(service.calc_type, 'Введи параметры (см. подсказки выше)')
            
            keyboard = VkKeyboard(inline=False)
            keyboard.add_button('❌ Отмена', color=VkKeyboardColor.NEGATIVE)
            send_vk_message(user_id, f"Выбрано: {service.name}\n\n{param_msg}", keyboard=keyboard.get_keyboard())
            return

        if state == 'awaiting_params':
            service = data.get('service')
            if not service:
                send_vk_message(user_id, "Ошибка. Начните заново", keyboard=get_main_keyboard())
                clear_user_state(user_id)
                return
            params = data.get('params', {})
            parts = original_text.replace(',', '.').split()
            calc_type = service['calc_type']

            try:
                if calc_type in ('area_cm2', 'photo_raster'):
                    if len(parts) >= 2: params['length'], params['width'] = float(parts[0]), float(parts[1])
                    else: send_vk_message(user_id, "Введи длину и ширину (см) через пробел"); return
                elif calc_type == 'meter_thickness':
                    if len(parts) >= 2: params['meters'], params['thickness'] = float(parts[0]), float(parts[1])
                    else: send_vk_message(user_id, "Введи метры реза и толщину (мм) через пробел"); return
                elif calc_type == 'setup_batch':
                    if len(parts) >= 3: params['setup_cost'], params['per_unit_price'], params['quantity'] = float(parts[0]), float(parts[1]), float(parts[2])
                    else: send_vk_message(user_id, "Введи стоимость настройки, цену за шт и кол-во"); return
                elif calc_type == 'cylindrical':
                    if len(parts) >= 2: params['diameter'], params['length'] = float(parts[0]), float(parts[1])
                    else: send_vk_message(user_id, "Введи диаметр (см) и длину (см) через пробел"); return
                elif calc_type == 'volume_3d':
                    if len(parts) >= 2: params['area'], params['depth'] = float(parts[0]), float(parts[1])
                    else: send_vk_message(user_id, "Введи площадь (см²) и глубину (мм) через пробел"); return
                elif calc_type == 'complex':
                    if len(parts) >= 2: params['material_cost'], params['cutting_meters'] = float(parts[0]), float(parts[1])
                    else: send_vk_message(user_id, "Введи стоимость материала и метры реза через пробел"); return
                elif calc_type == 'per_minute':
                    if len(parts) >= 1: params['minutes'] = float(parts[0])
                    else: send_vk_message(user_id, "Введи время в минутах"); return
                elif calc_type == 'per_char':
                    if len(parts) >= 1: params['chars'] = float(parts[0])
                    else: send_vk_message(user_id, "Введи количество символов"); return
                elif calc_type == 'vector_length':
                    if len(parts) >= 1: params['vector_meters'] = float(parts[0])
                    else: send_vk_message(user_id, "Введи длину вектора (м)"); return
                elif calc_type == 'fixed':
                    if len(parts) >= 1: params['quantity'] = float(parts[0])
                    else: send_vk_message(user_id, "Введи количество штук"); return
                else:
                    params['quantity'] = float(parts[0]) if parts else 1

                data['params'] = params
                price = calculate_price(calc_type, params, service['base_price'], service['min_price'])
                data['price'] = price
                set_user_state(user_id, 'awaiting_confirmation', data)
                send_vk_message(user_id, f"💰 Стоимость: {price:.2f}₽\nОформить заказ?", keyboard=get_order_confirmation_keyboard())
            except ValueError:
                send_vk_message(user_id, "⚠️ Используйте только цифры. Попробуй ещё раз.")
            return

        if state == 'awaiting_confirmation':
            if 'оформить' in text_lower:
                if data:
                    order = Order.objects.create(
                        client=client,
                        service_name=data['service']['name'],
                        service_type=data['service']['calc_type'],
                        parameters=data['params'],
                        total_price=data['price'],
                        status='NEW'
                    )
                    send_vk_message(user_id, f"✅ Заказ #{order.id} создан! Мастер скоро свяжется.", keyboard=get_main_keyboard())
                else:
                    send_vk_message(user_id, "Данные заказа потеряны.", keyboard=get_main_keyboard())
            else:
                send_vk_message(user_id, "Пожалуйста, нажмите «Оформить» или «Отмена».", keyboard=get_order_confirmation_keyboard())
            clear_user_state(user_id)
            return

        send_vk_message(user_id, "🤖 Я сохранил сообщение. Воспользуйтесь меню 👇", keyboard=get_main_keyboard())
