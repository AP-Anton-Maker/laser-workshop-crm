import logging
import json
import re
from django.core.management.base import BaseCommand
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from bot.vk_client import vk, longpoll
from vk_api.longpoll import VkEventType
from bot.models import Client, Order, PriceListItem, Setting, ChatMessage
from bot.calculator import calculate_price
from bot.fsm import get_user_state, set_user_state, clear_user_state

logger = logging.getLogger(__name__)

def send_vk_message(user_id, text, keyboard=None):
    vk.messages.send(user_id=user_id, message=text, random_id=get_random_id(), keyboard=keyboard)

def get_or_create_client(vk_id):
    client, created = Client.objects.get_or_create(vk_id=vk_id)
    if created or not client.name:
        try:
            user_info = vk.users.get(user_ids=vk_id)[0]
            client.name = f"{user_info['first_name']} {user_info['last_name']}"
            client.save(update_fields=['name'])
        except Exception as e:
            logger.error(f"Ошибка получения имени ВК: {e}")
            client.name = "Клиент"
            client.save(update_fields=['name'])
    return client

def get_setting(key):
    try:
        return Setting.objects.get(key=key).value
    except Setting.DoesNotExist:
        return None

# Очистка старой клавиатуры внизу экрана
def get_empty_keyboard():
    return VkKeyboard.get_empty_keyboard()

# ТИХИЕ INLINE-КЛАВИАТУРЫ
def get_main_keyboard():
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button('📋 Каталог', color=VkKeyboardColor.PRIMARY, payload=json.dumps({'cmd': 'catalog'}))
    keyboard.add_callback_button('🧮 Рассчитать', color=VkKeyboardColor.PRIMARY, payload=json.dumps({'cmd': 'calculate'}))
    keyboard.add_line()
    keyboard.add_callback_button('💰 Баланс', color=VkKeyboardColor.PRIMARY, payload=json.dumps({'cmd': 'balance'}))
    keyboard.add_callback_button('📞 Мастер', color=VkKeyboardColor.SECONDARY, payload=json.dumps({'cmd': 'master'}))
    keyboard.add_line()
    keyboard.add_callback_button('❓ Помощь', color=VkKeyboardColor.SECONDARY, payload=json.dumps({'cmd': 'help'}))
    return keyboard.get_keyboard()

def get_order_confirmation_keyboard():
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button('✅ Оформить', color=VkKeyboardColor.POSITIVE, payload=json.dumps({'cmd': 'confirm_order'}))
    keyboard.add_callback_button('❌ Отмена', color=VkKeyboardColor.NEGATIVE, payload=json.dumps({'cmd': 'cancel_order'}))
    return keyboard.get_keyboard()

class Command(BaseCommand):
    help = 'Запуск умного помощника VK'

    def handle(self, *args, **options):
        logger.info("✅ Умный помощник запущен (Тихий режим)")
        for event in longpoll.listen():
            try:
                event_type_str = getattr(event.type, 'name', str(event.type)).lower()
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    self.handle_message(event)
                elif event_type_str == 'message_event':
                    self.handle_callback(event)
            except Exception as e:
                logger.error(f"Ошибка: {e}", exc_info=True)

    def handle_message(self, event):
        user_id = event.user_id
        original_text = (event.text or '').strip()
        text = re.sub(r'[^\w\s]', '', original_text).lower().strip()
        client = get_or_create_client(user_id)

        vacation_mode = get_setting('vacation_mode')
        if vacation_mode == '1':
            msg = get_setting('vacation_message') or "🔧 Мастер временно не принимает заказы. Ответит, как только вернётся."
            send_vk_message(user_id, msg)
            return

        ChatMessage.objects.create(client=client, vk_id=user_id, message_text=original_text, is_admin=False)

        state, data = get_user_state(user_id)

        # Выход из любых режимов словами
        if text in ['отмена', 'стоп', 'назад', 'выйти', 'меню']:
            clear_user_state(user_id)
            # Отправляем пустое меню вниз (чтобы стереть старое) и инлайн меню в чат
            send_vk_message(user_id, "Действие отменено. Главное меню 👇", keyboard=get_empty_keyboard())
            send_vk_message(user_id, "Меню:", keyboard=get_main_keyboard())
            return

        if text in ['привет', 'начать']:
            clear_user_state(user_id)
            send_vk_message(user_id, f"✨ Привет, {client.name}! Я — умный помощник.", keyboard=get_empty_keyboard())
            send_vk_message(user_id, "Выберите действие 👇", keyboard=get_main_keyboard())
            return

        # Режим тишины
        if state == 'waiting_for_master':
            return # Бот молчит, общается мастер

        # Активация мастера текстом
        if text in ['человек', 'менеджер']:
            send_vk_message(user_id, "📞 Переключаю на мастера!\nЯ отключаюсь. (Для перезапуска напишите «отмена»).")
            set_user_state(user_id, 'waiting_for_master')
            return

        # Если бот ждет параметры
        if state == 'awaiting_params':
            service = data.get('service')
            if not service:
                send_vk_message(user_id, "Ошибка. Начните заново с /start")
                clear_user_state(user_id)
                return
            params = data.get('params', {})
            parts = text.replace(',', '.').split()
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

        # Если написали обычный текст (отвечаем инлайн кнопками)
        send_vk_message(
            user_id,
            "🤖 Я сохранил сообщение, мастер скоро ответит.\n\n"
            "Воспользуйтесь меню 👇 (или напишите «человек»)",
            keyboard=get_main_keyboard()
        )

    # ОБРАБОТКА ТИХИХ НАЖАТИЙ (CALLBACK)
    def handle_callback(self, event):
        user_id = event.user_id
        client = get_or_create_client(user_id)
        
        # Гасим индикатор загрузки на кнопке у клиента
        try:
            vk.messages.sendMessageEventAnswer(event_id=event.event_id, user_id=user_id, peer_id=event.peer_id)
        except Exception:
            pass

        # Если бот спал, будим
        state, data = get_user_state(user_id)
        if state == 'waiting_for_master':
            clear_user_state(user_id)

        try:
            payload = json.loads(event.payload)
        except Exception:
            send_vk_message(user_id, "Ошибка команды.", keyboard=get_main_keyboard())
            return

        cmd = payload.get('cmd')
        
        # ЛОГИКА ГЛАВНОГО МЕНЮ И ПОДТВЕРЖДЕНИЙ
        if cmd == 'catalog':
            services = PriceListItem.objects.filter(is_active=True)
            if services:
                reply = "📋 Каталог:\n" + "\n".join([f"• {s.name} — {s.base_price}₽/{s.unit}" for s in services])
            else:
                reply = "Услуг пока нет."
            send_vk_message(user_id, reply, keyboard=get_main_keyboard())
            clear_user_state(user_id)
            
        elif cmd == 'balance':
            send_vk_message(user_id, f"💰 Твой кэшбэк: {client.cashback_balance:.2f}₽", keyboard=get_main_keyboard())
            clear_user_state(user_id)
            
        elif cmd == 'master':
            send_vk_message(user_id, "📞 Переключаю на мастера!\nБот переведен в спящий режим. Мастер скоро ответит.\n(Для перезапуска бота напишите «отмена»)")
            set_user_state(user_id, 'waiting_for_master')
            
        elif cmd == 'help':
            send_vk_message(user_id, "❓ Я умею: считать цены, показывать каталог. Выберите действие:", keyboard=get_main_keyboard())
            
        elif cmd == 'calculate':
            services = PriceListItem.objects.filter(is_active=True)[:10]
            if not services:
                send_vk_message(user_id, "Услуги временно не добавлены.")
                return
            keyboard = VkKeyboard(inline=True)
            for i, s in enumerate(services):
                if i > 0 and i % 2 == 0:
                    keyboard.add_line()
                keyboard.add_callback_button(label=s.name[:40], color=VkKeyboardColor.PRIMARY, payload=json.dumps({'service_id': s.id}))
            keyboard.add_line()
            keyboard.add_callback_button('❌ Назад', color=VkKeyboardColor.NEGATIVE, payload=json.dumps({'cmd': 'cancel_order'}))
            send_vk_message(user_id, "Выбери услугу 👇:", keyboard=keyboard.get_keyboard())
            set_user_state(user_id, 'awaiting_service')

        elif cmd == 'confirm_order':
            if state == 'awaiting_confirmation' and data:
                order = Order.objects.create(
                    client=client,
                    service_name=data['service']['name'],
                    service_type=data['service']['calc_type'],
                    parameters=data['params'],
                    total_price=data['price'],
                    status='NEW'
                )
                send_vk_message(user_id, f"✅ Заказ #{order.id} создан! Мастер скоро свяжется.", keyboard=get_main_keyboard())
                clear_user_state(user_id)
            else:
                send_vk_message(user_id, "Данные заказа потеряны.", keyboard=get_main_keyboard())

        elif cmd == 'cancel_order':
            clear_user_state(user_id)
            send_vk_message(user_id, "Действие отменено.", keyboard=get_main_keyboard())

        # ЛОГИКА ВЫБОРА КОНКРЕТНОЙ УСЛУГИ ИЗ СПИСКА
        elif 'service_id' in payload:
            try:
                service = PriceListItem.objects.get(id=payload['service_id'])
            except PriceListItem.DoesNotExist:
                send_vk_message(user_id, "Услуга не найдена.", keyboard=get_main_keyboard())
                return

            set_user_state(user_id, 'awaiting_params', {
                'service': {'id': service.id, 'name': service.name, 'calc_type': service.calc_type, 'base_price': float(service.base_price), 'min_price': float(service.min_price)},
                'params': {}
            })
            param_msg = {
                'area_cm2': 'Введи длину и ширину (см) через пробел',
                'photo_raster': 'Введи длину и ширину (см) через пробел',
                'meter_thickness': 'Введи метры реза и толщину (мм) через пробел',
                'per_char': 'Введи количество символов',
                'per_minute': 'Введи время в минутах',
                'fixed': 'Введи количество штук',
                'vector_length': 'Введи длину вектора (м)',
                'cylindrical': 'Введи диаметр (см) и длину (см) через пробел',
                'volume_3d': 'Введи площадь (см²) и глубину (мм) через пробел',
                'complex': 'Введи стоимость материала и метры реза через пробел',
                'setup_batch': 'Введи стоимость настройки, цену за шт и количество через пробел'
            }.get(service.calc_type, 'Введи параметры')
            
            # Добавляем кнопку "Отмена" к запросу параметров
            keyboard = VkKeyboard(inline=True)
            keyboard.add_callback_button('❌ Отмена', color=VkKeyboardColor.NEGATIVE, payload=json.dumps({'cmd': 'cancel_order'}))
            send_vk_message(user_id, f"Выбрано: {service.name}\n\n{param_msg}", keyboard=keyboard.get_keyboard())
EOFimport logging
import json
import re
from django.core.management.base import BaseCommand
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from bot.vk_client import vk, longpoll
from vk_api.longpoll import VkEventType
from bot.models import Client, Order, PriceListItem, Setting, ChatMessage
from bot.calculator import calculate_price
from bot.fsm import get_user_state, set_user_state, clear_user_state

logger = logging.getLogger(__name__)

def send_vk_message(user_id, text, keyboard=None):
    vk.messages.send(user_id=user_id, message=text, random_id=get_random_id(), keyboard=keyboard)

def get_or_create_client(vk_id):
    client, created = Client.objects.get_or_create(vk_id=vk_id)
    if created or not client.name:
        try:
            user_info = vk.users.get(user_ids=vk_id)[0]
            client.name = f"{user_info['first_name']} {user_info['last_name']}"
            client.save(update_fields=['name'])
        except Exception as e:
            logger.error(f"Ошибка получения имени ВК: {e}")
            client.name = "Клиент"
            client.save(update_fields=['name'])
    return client

def get_setting(key):
    try:
        return Setting.objects.get(key=key).value
    except Setting.DoesNotExist:
        return None

def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('📋 Каталог', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🧮 Рассчитать', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('💰 Баланс', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('📞 Связаться с мастером', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('❓ Помощь', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def get_order_confirmation_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('✅ Оформить', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('❌ Отмена', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

class Command(BaseCommand):
    help = 'Запуск умного помощника VK'

    def handle(self, *args, **options):
        logger.info("✅ Умный помощник запущен")
        for event in longpoll.listen():
            try:
                event_type_str = getattr(event.type, 'name', str(event.type)).lower()
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    self.handle_message(event)
                elif event_type_str == 'message_event':
                    self.handle_callback(event)
            except Exception as e:
                logger.error(f"Ошибка: {e}", exc_info=True)

    def handle_message(self, event):
        user_id = event.user_id
        original_text = (event.text or '').strip()
        text = re.sub(r'[^\w\s]', '', original_text).lower().strip()
        client = get_or_create_client(user_id)

        vacation_mode = get_setting('vacation_mode')
        if vacation_mode == '1':
            msg = get_setting('vacation_message') or "🔧 Мастер временно не принимает заказы. Ответит, как только вернётся."
            send_vk_message(user_id, msg)
            return

        ChatMessage.objects.create(client=client, vk_id=user_id, message_text=original_text, is_admin=False)

        state, data = get_user_state(user_id)

        # 1. ГЛОБАЛЬНЫЕ КОМАНДЫ (Работают всегда, могут разбудить бота)
        if text in ['отмена', 'стоп', 'назад', 'выйти', 'меню']:
            clear_user_state(user_id)
            send_vk_message(user_id, "Авто-бот снова включен 🤖\nВозврат в главное меню 👇", keyboard=get_main_keyboard())
            return

        if text in ['привет', 'начать']:
            clear_user_state(user_id)
            send_vk_message(user_id, f"✨ Привет, {client.name}! Я — умный помощник мастера. Чем могу помочь?", keyboard=get_main_keyboard())
            return

        # 2. РЕЖИМ ТИШИНЫ (Бот не мешает общению с мастером)
        if state == 'waiting_for_master':
            # Бот ничего не отвечает. Сообщение уже сохранилось в базу. 
            return

        # 3. ВКЛЮЧЕНИЕ РЕЖИМА ТИШИНЫ
        if text in ['связаться с мастером', 'мастер', 'человек', 'менеджер']:
            send_vk_message(user_id, "📞 Переключаю на мастера!\n\nБот переведен в спящий режим, чтобы не мешать вашей беседе. Мастер скоро прочитает сообщения и ответит.\n\n(Чтобы снова включить бота, напишите «отмена»)")
            set_user_state(user_id, 'waiting_for_master')
            return

        # 4. ОБРАБОТКА КОМАНД БОТА
        if text == 'каталог':
            services = PriceListItem.objects.filter(is_active=True)
            if services:
                reply = "📋 Наши услуги:\n" + "\n".join([f"• {s.name} — {s.base_price}₽/{s.unit}" for s in services])
            else:
                reply = "Услуги временно не добавлены. Напиши мастеру."
            send_vk_message(user_id, reply)
            clear_user_state(user_id)
        elif text == 'баланс':
            send_vk_message(user_id, f"💰 Твой кэшбэк: {client.cashback_balance:.2f}₽")
            clear_user_state(user_id)
        elif text == 'рассчитать':
            services = PriceListItem.objects.filter(is_active=True)[:10]
            if not services:
                send_vk_message(user_id, "Услуги временно не добавлены.")
                return
            
            keyboard = VkKeyboard(inline=True)
            for i, s in enumerate(services):
                if i > 0 and i % 2 == 0:
                    keyboard.add_line()
                keyboard.add_callback_button(
                    label=s.name[:40],
                    color=VkKeyboardColor.PRIMARY,
                    payload=json.dumps({'service_id': s.id})
                )
            
            send_vk_message(user_id, "Выбери услугу (или напиши «отмена»):", keyboard=keyboard.get_keyboard())
            set_user_state(user_id, 'awaiting_service')
        elif text == 'помощь':
            send_vk_message(user_id, "❓ Я умею: считать цены, показывать каталог и баланс.\n\nЕсли нужен живой человек — нажми «Связаться с мастером».")
        else:
            if state == 'awaiting_service':
                send_vk_message(user_id, "Пожалуйста, выбери услугу из кнопок.")
            elif state == 'awaiting_params':
                service = data.get('service')
                if not service:
                    send_vk_message(user_id, "Ошибка: услуга не найдена. Начните заново с /start")
                    clear_user_state(user_id)
                    return
                params = data.get('params', {})
                parts = text.replace(',', '.').split()
                calc_type = service['calc_type']

                try:
                    if calc_type in ('area_cm2', 'photo_raster'):
                        if len(parts) >= 2:
                            params['length'], params['width'] = float(parts[0]), float(parts[1])
                        else:
                            send_vk_message(user_id, "Введи длину и ширину (см) через пробел")
                            return
                    elif calc_type == 'meter_thickness':
                        if len(parts) >= 2:
                            params['meters'], params['thickness'] = float(parts[0]), float(parts[1])
                        else:
                            send_vk_message(user_id, "Введи метры реза и толщину (мм) через пробел")
                            return
                    elif calc_type == 'setup_batch':
                        if len(parts) >= 3:
                            params['setup_cost'], params['per_unit_price'], params['quantity'] = float(parts[0]), float(parts[1]), float(parts[2])
                        else:
                            send_vk_message(user_id, "Введи стоимость настройки, цену за шт и количество")
                            return
                    elif calc_type == 'cylindrical':
                        if len(parts) >= 2:
                            params['diameter'], params['length'] = float(parts[0]), float(parts[1])
                        else:
                            send_vk_message(user_id, "Введи диаметр (см) и длину (см) через пробел")
                            return
                    elif calc_type == 'volume_3d':
                        if len(parts) >= 2:
                            params['area'], params['depth'] = float(parts[0]), float(parts[1])
                        else:
                            send_vk_message(user_id, "Введи площадь (см²) и глубину (мм) через пробел")
                            return
                    elif calc_type == 'complex':
                        if len(parts) >= 2:
                            params['material_cost'], params['cutting_meters'] = float(parts[0]), float(parts[1])
                        else:
                            send_vk_message(user_id, "Введи стоимость материала и метры реза через пробел")
                            return
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
                    send_vk_message(user_id, "⚠️ Ошибка: используйте только цифры (например: 10 20.5). Попробуй ещё раз.")
                    return
            elif state == 'awaiting_confirmation':
                service = data.get('service')
                params = data.get('params', {})
                price = data.get('price')
                if not service or price is None:
                    send_vk_message(user_id, "Ошибка: данные заказа потеряны. Начните заново.")
                    clear_user_state(user_id)
                    return
                if 'оформить' in text:
                    order = Order.objects.create(
                        client=client,
                        service_name=service['name'],
                        service_type=service['calc_type'],
                        parameters=params,
                        total_price=price,
                        status='NEW'
                    )
                    send_vk_message(user_id, f"✅ Заказ #{order.id} создан! Мастер скоро свяжется.")
                    clear_user_state(user_id)
                    send_vk_message(user_id, "Что ещё сделать?", keyboard=get_main_keyboard())
                else:
                    send_vk_message(user_id, "❌ Заказ отменён.")
                    clear_user_state(user_id)
                    send_vk_message(user_id, "Выбери действие:", keyboard=get_main_keyboard())
            else:
                # Если человек пишет обычный текст без режима общения с мастером
                send_vk_message(
                    user_id,
                    "🤖 Я — бот-помощник и понимаю только команды с кнопок.\n\n"
                    "Если вам нужен живой человек, нажмите кнопку «Связаться с мастером» (или напишите «человек»), и я отключусь, чтобы не мешать.",
                    keyboard=get_main_keyboard()
                )

    def handle_callback(self, event):
        user_id = event.user_id
        
        # Если клиент нажал инлайн кнопку, значит он снова хочет общаться с ботом. Будим его.
        state, _ = get_user_state(user_id)
        if state == 'waiting_for_master':
            clear_user_state(user_id)
            
        try:
            vk.messages.sendMessageEventAnswer(event_id=event.event_id, user_id=user_id, peer_id=event.peer_id)
        except Exception as e:
            logger.error(f"Не удалось отправить ответ на callback: {e}")

        try:
            payload = json.loads(event.payload)
        except (json.JSONDecodeError, TypeError):
            send_vk_message(user_id, "⚠️ Ошибка обработки команды. Попробуйте ещё раз.")
            return

        service_id = payload.get('service_id')
        if service_id:
            try:
                service = PriceListItem.objects.get(id=service_id)
            except PriceListItem.DoesNotExist:
                send_vk_message(user_id, "⚠️ Услуга не найдена. Выберите другую.")
                return

            set_user_state(user_id, 'awaiting_params', {
                'service': {
                    'id': service.id,
                    'name': service.name,
                    'calc_type': service.calc_type,
                    'base_price': float(service.base_price),
                    'min_price': float(service.min_price)
                },
                'params': {}
            })
            param_msg = {
                'area_cm2': 'Введи длину и ширину (см) через пробел',
                'photo_raster': 'Введи длину и ширину (см) через пробел',
                'meter_thickness': 'Введи метры реза и толщину (мм) через пробел',
                'per_char': 'Введи количество символов',
                'per_minute': 'Введи время в минутах',
                'fixed': 'Введи количество штук',
                'vector_length': 'Введи длину вектора (м)',
                'cylindrical': 'Введи диаметр (см) и длину (см) через пробел',
                'volume_3d': 'Введи площадь (см²) и глубину (мм) через пробел',
                'complex': 'Введи стоимость материала и метры реза через пробел',
                'setup_batch': 'Введи стоимость настройки, цену за шт и количество через пробел'
            }.get(service.calc_type, 'Введи параметры')
            send_vk_message(user_id, param_msg)
        else:
            send_vk_message(user_id, "Неизвестная команда")
