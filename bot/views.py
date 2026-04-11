from django.shortcuts import render
from django.http import JsonResponse
from .models import ChatMessage, Client
from .vk_client import vk
from vk_api.utils import get_random_id

def chat_history(request, vk_id):
    messages = ChatMessage.objects.filter(vk_id=vk_id).order_by('-timestamp')[:100]
    data = [{'message_text': m.message_text, 'is_admin': m.is_admin, 'timestamp': m.timestamp} for m in messages]
    return JsonResponse(data, safe=False)

def send_message(request):
    if request.method == 'POST':
        vk_id = request.POST.get('vk_id')
        text = request.POST.get('message')
        client = Client.objects.get(vk_id=vk_id)
        if client.vk_id:
            vk.messages.send(user_id=client.vk_id, message=text, random_id=get_random_id())
            ChatMessage.objects.create(client=client, vk_id=client.vk_id, message_text=text, is_admin=True)
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)
