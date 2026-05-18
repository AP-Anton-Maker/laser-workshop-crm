from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from unfold.admin import ModelAdmin
from ..models.order import Order


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ['pk', 'client', 'status_badge', 'material', 'final_price', 'created_at']
    list_filter = ['status', 'material', 'created_at']
    search_fields = ['client__full_name', 'description']
    readonly_fields = ['created_at', 'completed_at', 'print_ticket_link']
    fieldsets = [
        (None, {'fields': ['client', 'material', 'status']}),
        ('Описание', {'fields': ['description', 'layout_file']}),
        ('Цена', {'fields': ['estimated_price', 'final_price']}),
        ('Даты', {'fields': ['created_at', 'completed_at']}),
        ('Действия', {'fields': ['print_ticket_link']}),
    ]

    def status_badge(self, obj):
        colors = {
            'NEW': 'blue',
            'IN_PROGRESS': 'yellow',
            'DONE': 'green',
            'CANCELLED': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            f'<span style="background-color: {color}; color: white; padding: 3px 10px; border-radius: 5px;">{{}}</span>',
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'

    def print_ticket_link(self, obj):
        url = reverse('order_ticket', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Печать ТЗ</a>', url)
    print_ticket_link.short_description = 'Печать'

    @admin.action(description='Отметить как выполненные')
    def mark_done(self, request, queryset):
        from datetime import datetime
        queryset.update(status='DONE', completed_at=datetime.now())
    actions = ['mark_done']
