from django.contrib import admin
from unfold.admin import ModelAdmin
from crm.models import QuickReply, Notification, Settings


@admin.register(QuickReply)
class QuickReplyAdmin(ModelAdmin):
    """Админка для быстрых ответов бота."""
    
    list_display = ['name', 'keyword', 'message_preview', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'keyword', 'message']
    readonly_fields = ['created_at']
    fieldsets = [
        (None, {
            'fields': ['name', 'keyword', 'message']
        }),
        ('Метаданные', {
            'fields': ['is_active', 'created_at'],
            'classes': ['collapse']
        }),
    ]
    ordering = ['keyword']
    
    def message_preview(self, obj: QuickReply) -> str:
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Сообщение'


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    """Админка для журнала уведомлений."""
    
    list_display = [
        'created_at',
        'notification_type',
        'channel',
        'recipient_id',
        'is_sent_badge',
        'sent_at',
    ]
    list_filter = ['notification_type', 'channel', 'is_sent', 'created_at']
    search_fields = ['recipient_id', 'message']
    readonly_fields = ['created_at', 'sent_at', 'error_message']
    fieldsets = [
        (None, {
            'fields': ['notification_type', 'channel', 'recipient_id']
        }),
        ('Сообщение', {
            'fields': ['message'],
        }),
        ('Статус', {
            'fields': ['is_sent', 'sent_at', 'error_message'],
        }),
        ('Метаданные', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def is_sent_badge(self, obj: Notification) -> str:
        if obj.is_sent:
            return '✓ Отправлено'
        return '✗ Ошибка'
    is_sent_badge.short_description = 'Статус'


@admin.register(Settings)
class SettingsAdmin(ModelAdmin):
    """Админка для системных настроек."""
    
    list_display = ['key', 'value_preview', 'description', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['updated_at']
    fieldsets = [
        (None, {
            'fields': ['key', 'value', 'description']
        }),
        ('Метаданные', {
            'fields': ['updated_at', 'updated_by'],
            'classes': ['collapse']
        }),
    ]
    ordering = ['key']
    
    def value_preview(self, obj: Settings) -> str:
        value = str(obj.value)
        return value[:50] + '...' if len(value) > 50 else value
    value_preview.short_description = 'Значение'
