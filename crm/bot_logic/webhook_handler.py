import json
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

from ..models import Client
from .handlers import process_message

@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if data['type'] == 'confirmation':
            return HttpResponse(settings.VK_CONFIRMATION_CODE)

        if data['type'] == 'message_new':
            object_data = data['object']['message']
            user_id = object_data['from_id']
            text = object_data['text']
            attachments = object_data.get('attachments', [])

            client, created = Client.objects.get_or_create(vk_id=user_id)

            process_message(client, text, attachments)

        return HttpResponse('ok')
