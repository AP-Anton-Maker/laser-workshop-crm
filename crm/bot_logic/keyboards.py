import json

def get_main_keyboard():
    """Клавиатура главного меню."""
    keyboard = {
        "one_time": False,
        "inline": False,
        "buttons": [
            [
                {
                    "action": {"type": "text", "label": "💰 Прайс-лист"},
                    "color": "primary"
                },
                {
                    "action": {"type": "text", "label": "📏 Новый заказ"},
                    "color": "positive"
                }
            ],
            [
                {
                    "action": {"type": "text", "label": "📞 Контакты"},
                    "color": "secondary"
                }
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def get_cancel_keyboard():
    """Клавиатура отмены действия."""
    keyboard = {
        "one_time": True,
        "inline": False,
        "buttons": [
            [
                {
                    "action": {"type": "text", "label": "❌ Отмена"},
                    "color": "negative"
                }
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def get_yes_no_keyboard():
    """Клавиатура подтверждения (Да/Нет)."""
    keyboard = {
        "one_time": True,
        "inline": False,
        "buttons": [
            [
                {
                    "action": {"type": "text", "label": "✅ Да"},
                    "color": "positive"
                },
                {
                    "action": {"type": "text", "label": "❌ Нет"},
                    "color": "negative"
                }
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)
