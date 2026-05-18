from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models.client import Client


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    """
    Админка для управления клиентами.
    Поиск, фильтры, экспорт данных.
    """
    
    list_display = [
        'full_name',
        'vk_id',
        'phone',
        'bot_state',
        'orders_count',
        'total_spent',
        'last_order_date',
        'is_vip',
    ]
    list_filter = [
        'bot_state',
        'is_vip',
        'is_blocked',
        'created_at',
    ]
    search_fields = [
        'first_name',
        'last_name',
        'vk_id',
        'phone',
    ]
    readonly_fields = [
        'vk_id',
        'created_at',
        'updated_at',
        'last_order_date',
        'total_spent',
        'orders_count',
    ]
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'vk_id',
                'first_name',
                'last_name',
                'phone',
            )
        }),
        ('Статус бота', {
            'fields': (
                'bot_state',
                'is_blocked',
            )
        }),
        ('Статистика', {
            'fields': (
                'orders_count',
                'total_spent',
                'last_order_date',
                'is_vip',
                'notes',
            )
        }),
        ('Даты', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 25
    ordering = ['-created_at']
    
    @admin.display(description='Клиент')
    def full_name(self, obj: Client) -> str:
        return obj.full_name
    
    @admin.display(description='Сумма', ordering='total_spent')
    def total_spent_formatted(self, obj: Client) -> str:
        return f"{obj.total_spent:,.0f} ₽"
