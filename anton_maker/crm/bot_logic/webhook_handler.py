import json
from django.http import HttpResponse
from django.views import View
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .handlers import process_message
from ..models.client import Client


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    def post(self, request):
        data = json.loads(request.body)
        
        if data.get('secret') != settings.VK_SECRET_KEY:
            return HttpResponse('error', status=403)
        
        if 'type' not in data:
            return HttpResponse('error', status=400)
        
        if data['type'] == 'confirmation':
            return HttpResponse(settings.VK_CONFIRMATION_CODE)
        
        if data['type'] == 'message_new':
            message = data['object']['message']
            user_id = message['from_id']
            text = message.get('text', '')
            
            client, created = Client.objects.get_or_create(
                vk_id=user_id,
                defaults={'full_name': message.get('from_name', 'Unknown')}
            )
            
            if created:
                client.full_name = message.get('from_name', 'Unknown')
                client.save()
            
            response_text = process_message(client, text, message.get('attachments', []))
            
            if response_text:
                from .vk_client import VKClient
                vk = VKClient()
                vk.send_message(user_id, response_text)
            
            return HttpResponse('ok')
        
        return HttpResponse('ok')
