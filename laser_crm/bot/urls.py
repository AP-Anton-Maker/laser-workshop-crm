from django.urls import path
from . import views

urlpatterns = [
    path('chat/history/<int:vk_id>/', views.chat_history),
    path('chat/send/', views.send_message),
]
