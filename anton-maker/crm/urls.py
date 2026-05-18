"""
URL Configuration для CRM приложения.
"""

from django.urls import path
from .views import (
    CalculatorView,
    PublicCalculatorView,
    WebhookView,
    PrintTicketsView,
    error_404,
    error_500,
)

app_name = 'crm'

urlpatterns = [
    # Публичный калькулятор
    path('calculator/', PublicCalculatorView.as_view(), name='public_calculator'),
    
    # Калькулятор в админке
    path('admin-calculator/', CalculatorView.as_view(), name='admin_calculator'),
    
    # VK Webhook
    path('webhook/', WebhookView.as_view(), name='webhook'),
    
    # Печать маршрутных листов
    path('print-tickets/', PrintTicketsView.as_view(), name='print_tickets'),
]
