from django.urls import path
from .views import WebhookView, OrderTicketView

urlpatterns = [
    path('bot/webhook/', WebhookView.as_view(), name='webhook'),
    path('bot/ticket/<int:pk>/', OrderTicketView.as_view(), name='order_ticket'),
]
