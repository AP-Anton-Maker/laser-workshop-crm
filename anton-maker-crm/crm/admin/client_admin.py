from django.contrib import admin
from unfold.admin import ModelAdmin
from crm.models import Client


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    """
    Админка для модели Client.
    Поиск, фильтры, экспорт клиентов.
    """
    
    list_display = [
        'full_name',
        'vk_id',
        'phone',
        'total_spent',
        'bot_state',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'is_active',
        'bot_state',
        'created_at',
    ]
    search_fields = [
        'full_name',
        'vk_id',
        'telegram_id',
        'phone',
        'email',
    ]
    readonly_fields = [
        'vk_id',
        'telegram_id',
        'total_spent',
        'created_at',
        'updated_at',
        'get_order_count',
    ]
    fieldsets = [
        (None, {
            'fields': ['full_name', 'phone', 'email']
        }),
        ('Идентификаторы', {
            'fields': ['vk_id', 'telegram_id'],
            'classes': ['collapse']
        }),
        ('Статус бота', {
            'fields': ['bot_state'],
        }),
        ('Финансы', {
            'fields': ['total_spent', 'get_order_count'],
        }),
        ('Метаданные', {
            'fields': ['is_active', 'notes', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    actions = ['make_inactive', 'make_active', 'export_selected']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def get_order_count(self, obj: Client) -> int:
        """Получить количество заказов клиента."""
        return obj.get_order_count()
    get_order_count.short_description = 'Заказов'
    
    @admin.action(description='Деактивировать выбранных')
    def make_inactive(self, request, queryset):
        """Деактивировать выбранных клиентов."""
        queryset.update(is_active=False)
    
    @admin.action(description='Активировать выбранных')
    def make_active(self, request, queryset):
        """Активировать выбранных клиентов."""
        queryset.update(is_active=True)
    
    @admin.action(description='Экспортировать выбранных')
    def export_selected(self, request, queryset):
        """Экспорт выбранных клиентов в CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="clients.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'ФИО', 'VK ID', 'Telegram ID', 'Телефон', 'Email', 'Всего потрачено', 'Заказов'])
        
        for client in queryset:
            writer.writerow([
                client.id,
                client.full_name or '',
                client.vk_id or '',
                client.telegram_id or '',
                client.phone or '',
                client.email or '',
                client.total_spent,
                client.get_order_count(),
            ])
        
        return response
