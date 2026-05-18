from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from unfold.admin import ModelAdmin
from ..models.order import Order


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    """
    Админка для управления заказами.
    Канбан-статусы, печать ТЗ, фильтрация.
    """
    
    list_display = [
        'order_number',
        'client_name',
        'status_badge',
        'urgency',
        'material_short',
        'quantity',
        'final_price_display',
        'created_at',
        'is_late_indicator',
    ]
    list_filter = [
        'status',
        'urgency',
        'material',
        'created_at',
    ]
    search_fields = [
        'order_number',
        'client__first_name',
        'client__last_name',
        'client__vk_id',
        'description',
    ]
    readonly_fields = [
        'order_number',
        'created_at',
        'updated_at',
        'started_at',
        'completed_at',
        'shipped_at',
        'calculated_price',
        'production_time_hours',
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'order_number',
                'client',
                'status',
                'urgency',
            )
        }),
        ('Описание', {
            'fields': ('description',)
        }),
        ('Параметры изделия', {
            'fields': (
                'material',
                'length_mm',
                'width_mm',
                'thickness_mm',
                'quantity',
            )
        }),
        ('Файлы', {
            'fields': (
                'layout_file',
                'technical_file',
            )
        }),
        ('Стоимость', {
            'fields': (
                'calculated_price',
                'final_price',
                'discount_percent',
            )
        }),
        ('Заметки', {
            'fields': (
                'notes',
                'internal_notes',
            )
        }),
        ('Даты и статистика', {
            'fields': (
                'created_at',
                'updated_at',
                'started_at',
                'completed_at',
                'shipped_at',
                'production_time_hours',
            ),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 20
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    actions = [
        'start_work_action',
        'complete_work_action',
        'mark_ready_action',
        'ship_order_action',
        'cancel_order_action',
        'print_job_tickets',
    ]
    
    @admin.display(description='№')
    def order_number(self, obj: Order) -> str:
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:crm_order_change', args=[obj.pk]),
            obj.order_number
        )
    
    @admin.display(description='Клиент')
    def client_name(self, obj: Order) -> str:
        return obj.client.full_name
    
    @admin.display(description='Статус')
    def status_badge(self, obj: Order) -> str:
        badges = {
            'NEW': '<span style="background:#3b82f6;color:white;padding:2px 8px;border-radius:4px;">🆕 Новый</span>',
            'IN_PROGRESS': '<span style="background:#f59e0b;color:white;padding:2px 8px;border-radius:4px;">🔨 В работе</span>',
            'QUALITY_CHECK': '<span style="background:#8b5cf6;color:white;padding:2px 8px;border-radius:4px;">🔍 Контроль</span>',
            'READY': '<span style="background:#10b981;color:white;padding:2px 8px;border-radius:4px;">✅ Готов</span>',
            'SHIPPED': '<span style="background:#6b7280;color:white;padding:2px 8px;border-radius:4px;">📦 Отправлен</span>',
            'CANCELLED': '<span style="background:#ef4444;color:white;padding:2px 8px;border-radius:4px;">❌ Отменен</span>',
        }
        return format_html(badges.get(obj.status, obj.status))
    
    @admin.display(description='Материал')
    def material_short(self, obj: Order) -> str:
        return str(obj.material) if obj.material else '—'
    
    @admin.display(description='Цена')
    def final_price_display(self, obj: Order) -> str:
        if obj.final_price:
            return f"{obj.final_price:,.0f} ₽"
        return '—'
    
    @admin.display(description='⚠️')
    def is_late_indicator(self, obj: Order) -> str:
        if obj.is_late:
            return '🔴'
        return ''
    
    @admin.action(description='🔨 Начать работу')
    def start_work_action(self, request, queryset):
        for order in queryset.filter(status='NEW'):
            order.start_work()
        self.message_user(request, f"Начата работа над {queryset.filter(status='NEW').count()} заказами")
    
    @admin.action(description='✅ Завершить работу')
    def complete_work_action(self, request, queryset):
        for order in queryset.filter(status='IN_PROGRESS'):
            order.complete_work()
        self.message_user(request, f"Завершена работа над {queryset.filter(status='IN_PROGRESS').count()} заказами")
    
    @admin.action(description='✓ Готов к выдаче')
    def mark_ready_action(self, request, queryset):
        for order in queryset.filter(status='QUALITY_CHECK'):
            order.mark_ready()
        self.message_user(request, f"Отмечено готовых заказов: {queryset.filter(status='QUALITY_CHECK').count()}")
    
    @admin.action(description='📦 Отправить клиенту')
    def ship_order_action(self, request, queryset):
        for order in queryset.filter(status='READY'):
            order.ship_order()
        self.message_user(request, f"Отправлено заказов: {queryset.filter(status='READY').count()}")
    
    @admin.action(description='❌ Отменить заказы')
    def cancel_order_action(self, request, queryset):
        for order in queryset.filter(status__in=['NEW', 'IN_PROGRESS']):
            order.cancel_order()
        self.message_user(request, f"Отменено заказов: {queryset.filter(status__in=['NEW', 'IN_PROGRESS']).count()}")
    
    @admin.action(description='🖨 Печать маршрутных листов')
    def print_job_tickets(self, request, queryset):
        if queryset.count() == 0:
            self.message_user(request, "Выберите заказы для печати", level='warning')
            return
        
        # Redirect to print view
        order_ids = ','.join(str(o.id) for o in queryset)
        return format_html(
            '<script>window.open("/admin/print-tickets/?ids={}", "_blank");</script>',
            order_ids
        )
