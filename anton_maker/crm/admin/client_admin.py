from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models.client import Client


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = ['full_name', 'vk_id', 'phone', 'notify_enabled', 'created_at']
    list_filter = ['notify_enabled', 'created_at']
    search_fields = ['full_name', 'phone', 'vk_id']
    readonly_fields = ['vk_id', 'created_at']
    fieldsets = [
        (None, {'fields': ['vk_id', 'full_name', 'phone']}),
        ('Настройки', {'fields': ['bot_state', 'notify_enabled']}),
        ('Информация', {'fields': ['created_at'], 'classes': ['collapse']}),
    ]
