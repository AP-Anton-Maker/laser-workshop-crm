from django.urls import path
from .bot_logic.webhook_handler import WebhookView

app_name = 'crm'

urlpatterns = [
    path('webhook/', WebhookView.as_view(), name='vk_webhook'),
]
