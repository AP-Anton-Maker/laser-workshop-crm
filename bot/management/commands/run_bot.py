import logging
import json
import re  # ИСПРАВЛЕНО: добавлена библиотека для работы с текстом
from django.core.management.base import BaseCommand
from vk_api.utils import get_random_id
from bot.vk_client import vk, longpoll
from vk_api.longpoll import VkEventType
from bot.models import Client, Order, PriceListItem, Setting, ChatMessage
from bot.calculator import calculate_price
from bot.fsm import get_user_state, set_user_state, clear_user_state
from bot.keyboards import create_inline_keyboard, create_regular_keyboard

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
    buttons = [
        [{'label': '📋 Каталог', 'color': 'primary'}, {'label': '🧮 Рассчитать', 'color': 'primary'}],
        [{'label': '💰 Баланс', 'color': 'primary'}, {'label': '📞 Связаться с мастером', 'color': 'secondary'}],
        [{'label': '❓ Помощь', 'color': 'secondary'}]
    ]
    return create_regular_keyboard(buttons, one_time=False)

def get_order_confirmation_keyboard():
    return create_regular_keyboard([[{'label': '✅ Оформить', 'color': 'positive'}, {'label': '❌ Отмена', 'color': 'negative'}]], one_time=True)

class Command(BaseCommand):
    help = 'Запуск умного помощника VK'

    def handle(self, *args, **options):
        logger.info("✅ Умный помощник запущен")
        for event in longpoll.listen():
            try:
                # ИСПРАВЛЕНО: Безопасная проверка типов событий для сообщений и кнопок
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
        
        # Теперь re.sub будет работать отлично
        text = re.sub(r'[^\w\s]', '', original_text).lower().strip()
        
        client = get_or_create_client(user_id)

        vacation_mode = get_setting('vacation_mode')
        if vacation_mode == '1':
            msg = get_setting('vacation_message') or "🔧 Мастер временно не принимает заказы. Ответит, как только вернётся."
            send_vk_message(user_id, msg)
            return

        ChatMessage.objects.create(client=client, vk_id=user_id, message_text=original_text, is_admin=False)

        if text in ['привет', 'начать']:
            keyboard = get_main_keyboard()
            send_vk_message(user_id, f"✨ Привет, {client.name}! Я — умный помощник мастера. Чем могу помочь?", keyboard=keyboard)
            clear_user_state(user_id)
        elif text == 'каталог':
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
            services = PriceListItem.objects.filter(is_active=True)
            if not services:
                send_vk_message(user_id, "Услуги временно не добавлены.")
                return
            buttons = [[{'label': s.name, 'payload': {'service_id': s.id}}] for s in services]
            keyboard = create_inline_keyboard(buttons)
            send_vk_message(user_id, "Выбери услугу:", keyboard=keyboard)
            set_user_state(user_id, 'awaiting_service')
        elif text in ['связаться с мастером', 'мастер']:
            send_vk_message(user_id, "📞 Напиши свой вопрос, я передам мастеру.\nДля выхода из режима диалога напиши «отмена».")
            set_user_state(user_id, 'waiting_for_master')
        elif text == 'помощь':
            send_vk_message(user_id, "❓ Я умею: каталог, рассчитать, баланс, связаться с мастером. Напиши 'привет' для меню.")
        else:
            state, data = get_user_state(user_id)
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
                            params['length'] = float(parts[0])
                            params['width'] = float(parts[1])
                        else:
                            send_vk_message(user_id, "Введи длину и ширину (см) через пробел")
                            return
                    elif calc_type == 'meter_thickness':
                        if len(parts) >= 2:
                            params['meters'] = float(parts[0])
                            params['thickness'] = float(parts[1])
                        else:
                            send_vk_message(user_id, "Введи метры реза и толщину (мм) через пробел")
                            return
                    elif calc_type == 'setup_batch':
                        if len(parts) >= 3:
                            params['setup_cost'] = float(parts[0])
                            params['per_unit_price'] = float(parts[1])
                            params['quantity'] = float(parts[2])
                        else:
                            send_vk_message(user_id, "Введи стоимость настройки, цену за шт и количество")
                            return
                    elif calc_type == 'cylindrical':
                        if len(parts) >= 2:
                            params['diameter'] = float(parts[0])
                            params['length'] = float(parts[1])
                        else:
                            send_vk_message(user_id, "Введи диаметр (см) и длину (см) через пробел")
                            return
                    elif calc_type == 'volume_3d':
                        if len(parts) >= 2:
                            params['area'] = float(parts[0])
                            params['depth'] = float(parts[1])
                        else:
                            send_vk_message(user_id, "Введи площадь (см²) и глубину (мм) через пробел")
                            return
                    elif calc_type == 'complex':
                        if len(parts) >= 2:
                            params['material_cost'] = float(parts[0])
                            params['cutting_meters'] = float(parts[1])
                        else:
                            send_vk_message(user_id, "Введи стоимость материала и метры реза через пробел")
                            return
                    elif calc_type == 'per_minute':
                        if len(parts) >= 1:
                            params['minutes'] = float(parts[0])
                        else:
                            send_vk_message(user_id, "Введи время в минутах")
                            return
                    elif calc_type == 'per_char':
                        if len(parts) >= 1:
                            params['chars'] = float(parts[0])
                        else:
                            send_vk_message(user_id, "Введи количество символов")
                            return
                    elif calc_type == 'vector_length':
                        if len(parts) >= 1:
                            params['vector_meters'] = float(parts[0])
                        else:
                            send_vk_message(user_id, "Введи длину вектора (м)")
                            return
                    elif calc_type == 'fixed':
                        if len(parts) >= 1:
                            params['quantity'] = float(parts[0])
                        else:
                            send_vk_message(user_id, "Введи количество штук")
                            return
                    else:
                        params['quantity'] = float(parts[0]) if parts else 1
                    
                    data['params'] = params
                    price = calculate_price(calc_type, params, service['base_price'], service['min_price'])
                    data['price'] = price
                    set_user_state(user_id, 'awaiting_confirmation', data)
                    keyboard = get_order_confirmation_keyboard()
                    send_vk_message(user_id, f"💰 Стоимость: {price:.2f}₽\nОформить заказ?", keyboard=keyboard)
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
                    keyboard = get_main_keyboard()
                    send_vk_message(user_id, "Что ещё сделать?", keyboard=keyboard)
                else:
                    send_vk_message(user_id, "❌ Заказ отменён.")
                    clear_user_state(user_id)
                    keyboard = get_main_keyboard()
                    send_vk_message(user_id, "Выбери действие:", keyboard=keyboard)
            
            elif state == 'waiting_for_master':
                if text == 'отмена':
                    clear_user_state(user_id)
                    keyboard = get_main_keyboard()
                    send_vk_message(user_id, "Режим диалога завершен. Чем ещё помочь?", keyboard=keyboard)
                else:
                    send_vk_message(user_id, "Сообщение передано мастеру. (Для выхода напиши «отмена»)")
            else:
                keyboard = get_main_keyboard()
                send_vk_message(
                    user_id, 
                    "🤖 Я — автоматический помощник и понимаю только команды с кнопок.\n\n"
                    "Но не переживай, я сохранил твое сообщение! Мастер прочитает его и обязательно ответит.\n\n"
                    "А пока можешь воспользоваться меню 👇", 
                    keyboard=keyboard
                )

    def handle_callback(self, event):
        user_id = event.user_id
        
        try:
            vk.messages.sendMessageEventAnswer(
                event_id=event.event_id,
                user_id=user_id,
                peer_id=event.peer_id
            )
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
