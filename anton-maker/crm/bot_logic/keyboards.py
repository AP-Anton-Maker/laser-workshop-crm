"""
Генерация JSON-клавиатур для ВКонтакте.
"""

from typing import List, Dict, Any


def get_main_keyboard() -> Dict[str, Any]:
    """Главное меню бота."""
    return {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {"type": "text", "label": "🆕 Новый заказ"},
                    "color": "primary"
                }
            ],
            [
                {
                    "action": {"type": "text", "label": "💰 Прайс-лист"},
                    "color": "secondary"
                },
                {
                    "action": {"type": "text", "label": "📍 Контакты"},
                    "color": "secondary"
                }
            ],
            [
                {
                    "action": {"type": "text", "label": "❓ Помощь"},
                    "color": "secondary"
                }
            ]
        ]
    }


def get_cancel_keyboard() -> Dict[str, Any]:
    """Клавиатура с кнопкой отмены."""
    return {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {"type": "text", "label": "❌ Отмена"},
                    "color": "negative"
                }
            ]
        ]
    }


def get_confirm_keyboard() -> Dict[str, Any]:
    """Клавиатура подтверждения заказа."""
    return {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {"type": "text", "label": "✅ Подтвердить"},
                    "color": "positive"
                },
                {
                    "action": {"type": "text", "label": "❌ Отменить"},
                    "color": "negative"
                }
            ]
        ]
    }


def get_back_keyboard() -> Dict[str, Any]:
    """Клавиатура с кнопкой назад."""
    return {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {"type": "text", "label": "⬅️ Назад"},
                    "color": "secondary"
                }
            ]
        ]
    }


def get_inline_open_link(url: str, label: str = "🔗 Открыть") -> Dict[str, Any]:
    """Inline-кнопка со ссылкой."""
    return {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {
                        "type": "open_link",
                        "url": url,
                        "label": label
                    }
                }
            ]
        ]
    }
