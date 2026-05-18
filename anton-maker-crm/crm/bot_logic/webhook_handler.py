"""
Обработчик вебхуков ВКонтакте.
Принимает и маршрутизирует входящие события от VK API.
"""

import json
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from typing import Dict, Any

from .handlers import process_message
from crm.models import Client


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    """
    View для обработки вебхуков ВКонтакте.
    
    Обрабатывает:
    - confirmation (подтверждение адреса)
    - message_new (новое сообщение)
    - другие события бота
    """
    
    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Обработка POST запроса от VK."""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')
        
        event_type = data.get('type')
        event_object = data.get('object', {})
        
        # Обработка подтверждения адреса
        if event_type == 'confirmation':
            return self._handle_confirmation(data)
        
        # Обработка нового сообщения
        if event_type == 'message_new':
            return self._handle_message_new(event_object)
        
        # Другие типы событий (игнорируем)
        return JsonResponse({'response': 'ok'})
    
    def _handle_confirmation(self, data: Dict[str, Any]) -> JsonResponse:
        """
        Подтверждение адреса вебхука.
        
        VK отправляет событие confirmation для проверки владения адресом.
        Нужно вернуть код подтверждения из настроек сообщества.
        """
        group_id = data.get('group_id')
        confirmation_code = getattr(settings, 'VK_CONFIRMATION_CODE', '')
        
        return JsonResponse({'response': confirmation_code})
    
    def _handle_message_new(self, event_object: Dict[str, Any]) -> JsonResponse:
        """
        Обработка нового сообщения.
        
        Args:
            event_object: Объект события от VK
        """
        message = event_object.get('message', {})
        
        # Извлекаем данные
        user_id = message.get('from_id') or message.get('user_id')
        peer_id = message.get('peer_id')
        text = message.get('text', '')
        attachments = message.get('attachments', [])
        
        if not user_id:
            return JsonResponse({'response': 'ok'})
        
        # Получаем или создаем клиента
        client, created = Client.objects.get_or_create(
            vk_id=user_id,
            defaults={
                'full_name': self._get_user_name(message),
                'bot_state': 'START'
            }
        )
        
        # Если пользователь новый, обновляем имя
        if not created and 'first_name' in message:
            full_name = self._get_user_name(message)
            if full_name and not client.full_name:
                client.full_name = full_name
                client.save(update_fields=['full_name'])
        
        # Обрабатываем сообщение через state machine
        response_message = process_message(client, text, attachments)
        
        # Отправляем ответ пользователю
        if response_message:
            from .vk_api_client import VKClient
            vk_client = VKClient()
            
            if isinstance(response_message, dict):
                # Сообщение с клавиатурой
                vk_client.send_keyboard(
                    peer_id,
                    response_message.get('keyboard'),
                    response_message.get('message', '')
                )
            else:
                # Простое текстовое сообщение
                vk_client.send_message(peer_id, response_message)
        
        return JsonResponse({'response': 'ok'})
    
    def _get_user_name(self, message: Dict[str, Any]) -> str:
        """Извлечь имя пользователя из сообщения."""
        first_name = message.get('first_name', '')
        last_name = message.get('last_name', '')
        
        if first_name and last_name:
            return f'{first_name} {last_name}'
        elif first_name:
            return first_name
        
        return ''
