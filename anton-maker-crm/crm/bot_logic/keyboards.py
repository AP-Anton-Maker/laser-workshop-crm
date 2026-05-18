"""
Генерация клавиатур для ВКонтакте.
Создание JSON-клавиатур для бота.
"""

from typing import List, Dict, Any


def get_main_keyboard() -> Dict[str, Any]:
    """
    Получить главную клавиатуру бота.
    
    Returns:
        dict: JSON клавиатуры
    """
    return {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": '{"command": "new_order"}',
                        "label": "📝 Новый заказ"
                    }
                },
                {
                    "action": {
                        "type": "text",
                        "payload": '{"command": "price"}',
                        "label": "💰 Прайс"
                    }
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "payload": '{"command": "contacts"}',
                        "label": "📞 Контакты"
                    }
                },
                {
                    "action": {
                        "type": "text",
                        "payload": '{"command": "help"}',
                        "label": "❓ Помощь"
                    }
                }
            ]
        ]
    }


def get_cancel_keyboard() -> Dict[str, Any]:
    """
    Получить клавиатуру с кнопкой отмены.
    
    Returns:
        dict: JSON клавиатуры
    """
    return {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": '{"command": "cancel"}',
                        "label": "❌ Отмена"
                    }
                }
            ]
        ]
    }


def get_confirmation_keyboard(yes_payload: str = 'yes', no_payload: str = 'no') -> Dict[str, Any]:
    """
    Получить клавиатуру подтверждения.
    
    Args:
        yes_payload: Payload для кнопки "Да"
        no_payload: Payload для кнопки "Нет"
        
    Returns:
        dict: JSON клавиатуры
    """
    return {
        "one_time": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": f'{{"command": "{yes_payload}"}}',
                        "label": "✅ Да"
                    }
                },
                {
                    "action": {
                        "type": "text",
                        "payload": f'{{"command": "{no_payload}"}}',
                        "label": "❌ Нет"
                    }
                }
            ]
        ]
    }


def get_inline_status_keyboard(order_id: int) -> Dict[str, Any]:
    """
    Получить inline-клавиатуру для проверки статуса заказа.
    
    Args:
        order_id: ID заказа
        
    Returns:
        dict: JSON клавиатуры
    """
    return {
        "inline": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "callback",
                        "payload": f'{{"order_id": {order_id}, "action": "status"}}',
                        "label": "📊 Проверить статус"
                    }
                }
            ]
        ]
    }


def create_button(
    label: str,
    payload: str,
    color: str = 'primary'
) -> Dict[str, Any]:
    """
    Создать кнопку для клавиатуры.
    
    Args:
        label: Текст на кнопке
        payload: Данные кнопки (JSON строка)
        color: Цвет кнопки ('primary', 'secondary', 'positive', 'negative')
        
    Returns:
        dict: JSON кнопки
    """
    return {
        "action": {
            "type": "text",
            "payload": payload,
            "label": label
        },
        "color": color
    }


def create_keyboard(buttons: List[List[Dict[str, Any]]], one_time: bool = False) -> Dict[str, Any]:
    """
    Создать произвольную клавиатуру.
    
    Args:
        buttons: Список строк с кнопками
        one_time: Скрыть после использования
        
    Returns:
        dict: JSON клавиатуры
    """
    return {
        "one_time": one_time,
        "buttons": buttons
    }
