import json


def get_main_keyboard():
    keyboard = {
        "one_time": False,
        "inline": False,
        "buttons": [
            [{"action": {"type": "text", "label": "📝 Новый заказ", "payload": '{"cmd": "new_order"}'}}],
            [{"action": {"type": "text", "label": "📊 Статус заказа", "payload": '{"cmd": "status"}'}}],
            [{"action": {"type": "text", "label": "📞 Контакты", "payload": '{"cmd": "contacts"}'}}],
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)


def get_cancel_keyboard():
    keyboard = {
        "one_time": False,
        "inline": False,
        "buttons": [
            [{"action": {"type": "text", "label": "❌ Отмена", "payload": '{"cmd": "cancel"}'}}],
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)


def get_confirm_keyboard():
    keyboard = {
        "one_time": False,
        "inline": False,
        "buttons": [
            [{"action": {"type": "text", "label": "✅ Подтвердить", "payload": '{"cmd": "confirm"}'}}],
            [{"action": {"type": "text", "label": "❌ Отмена", "payload": '{"cmd": "cancel"}'}}],
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)
