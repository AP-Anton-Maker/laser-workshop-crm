"""
Webhook handler для ВКонтакте.
Принимает и маршрутизирует события от VK API.
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from ..models.client import Client
from .handlers import process_message
from .keyboards import get_main_keyboard

logger = logging.getLogger('crm.bot')


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    """
    Django View для обработки вебхуков ВКонтакте.
    
    URL: /webhook/
    """
    
    def post(self, request, *args, **kwargs) -> HttpResponse:
        """Обработка POST-запроса от VK."""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook request")
            return HttpResponse("Invalid JSON", status=400)
        
        event_type = data.get('type')
        obj = data.get('object', {})
        
        logger.debug(f"VK Webhook event: {event_type}")
        
        # Обработка подтверждения вебхука
        if event_type == 'confirmation':
            return self.handle_confirmation()
        
        # Обработка нового сообщения
        elif event_type == 'message_new':
            return self.handle_message_new(obj)
        
        # Другие типы событий (можно добавить обработку)
        elif event_type == 'message_reply':
            logger.debug(f"Message reply: {obj}")
        
        # Ответ "ok" для всех остальных событий
        return JsonResponse({'response': 'ok'})
    
    def handle_confirmation(self) -> HttpResponse:
        """
        Обработка запроса подтверждения вебхука.
        VK отправляет этот тип при первой настройке.
        """
        confirmation_code = settings.VK_CONFIRMATION_CODE
        
        if not confirmation_code:
            logger.error("VK_CONFIRMATION_CODE not set in settings")
            return HttpResponse("Confirmation code not configured", status=500)
        
        logger.info("Webhook confirmation requested")
        return HttpResponse(confirmation_code)
    
    def handle_message_new(self, obj: dict) -> JsonResponse:
        """
        Обработка нового сообщения.
        
        Args:
            obj: Объект сообщения от VK
            
        Returns:
            JSON ответ
        """
        # Извлечение данных
        message_data = obj.get('message', {})
        user_id = message_data.get('from_id') or obj.get('from_id')
        text = message_data.get('text', '')
        attachments = message_data.get('attachments', [])
        
        if not user_id:
            logger.warning("No user_id in message")
            return JsonResponse({'response': 'ok'})
        
        # Поиск или создание клиента
        client, created = Client.objects.get_or_create(
            vk_id=user_id,
            defaults={
                'first_name': message_data.get('from_name', ''),
            }
        )
        
        # Проверка блокировки
        if client.is_blocked:
            logger.info(f"Blocked user {user_id} tried to send message")
            return JsonResponse({'response': 'ok'})
        
        # Обновление имени если есть
        if not client.first_name and message_data.get('from_name'):
            client.first_name = message_data['from_name']
            client.save(update_fields=['first_name'])
        
        # Обработка сообщения
        try:
            process_message(client, text, attachments)
        except Exception as e:
            logger.error(f"Error processing message from {user_id}: {e}", exc_info=True)
        
        return JsonResponse({'response': 'ok'})


def send_keyboard(user_id: int, keyboard: dict, message: str) -> bool:
    """
    Отправка сообщения с клавиатурой.
    Вспомогательная функция для использования вне handlers.
    """
    from .vk_client import VKClient
    
    client = VKClient()
    return client.send_message(user_id, message, keyboard)
