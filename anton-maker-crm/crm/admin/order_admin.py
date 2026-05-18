from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from crm.models import Order
from datetime import datetime


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    """
    Админка для модели Order.
    Канбан-статусы, печать ТЗ, управление заказами.
    """
    
    list_display = [
        'id',
        'client_name',
        'product_name',
        'quantity',
        'final_price_display',
        'status_badge',
        'urgency',
        'created_at',
        'is_late_indicator',
    ]
    list_filter = [
        'status',
        'urgency',
        'created_at',
        'completed_at',
    ]
    search_fields = [
        'id',
        'client__full_name',
        'client__vk_id',
        'product__name',
        'description',
    ]
    readonly_fields = [
        'calculated_price',
        'cost_breakdown_display',
        'created_at',
        'updated_at',
        'started_at',
        'completed_at',
        'shipped_at',
        'get_lead_time_hours',
        'generate_job_ticket_link',
    ]
    fieldsets = [
        (None, {
            'fields': ['client', 'product', 'quantity', 'description']
        }),
        ('Параметры', {
            'fields': ['urgency', 'status']
        }),
        ('Файлы', {
            'fields': ['layout_file', 'generate_job_ticket_link'],
        }),
        ('Расчеты', {
            'fields': ['calculated_price', 'final_price', 'cost_breakdown_display'],
        }),
        ('Даты производства', {
            'fields': ['created_at', 'started_at', 'completed_at', 'shipped_at', 'get_lead_time_hours'],
            'classes': ['collapse']
        }),
        ('Заметки', {
            'fields': ['notes', 'manager_notes'],
            'classes': ['collapse']
        }),
    ]
    actions = [
        'mark_in_progress',
        'mark_quality_check',
        'mark_ready',
        'mark_shipped',
        'mark_cancelled',
        'print_job_tickets',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def client_name(self, obj: Order) -> str:
        """Имя клиента."""
        return obj.client.full_name or f'VK {obj.client.vk_id}'
    client_name.short_description = 'Клиент'
    
    def product_name(self, obj: Order) -> str:
        """Название изделия."""
        return obj.product.name if obj.product else '-'
    product_name.short_description = 'Изделие'
    
    def final_price_display(self, obj: Order) -> str:
        """Отображение цены."""
        return f'{obj.final_price:,.2f} ₽'
    final_price_display.short_description = 'Цена'
    
    def status_badge(self, obj: Order) -> str:
        """Цветной бейдж статуса."""
        colors = {
            'NEW': '#3b82f6',
            'IN_PROGRESS': '#eab308',
            'QUALITY_CHECK': '#a855f7',
            'READY': '#22c55e',
            'SHIPPED': '#6b7280',
            'CANCELLED': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 4px 12px; border-radius: 12px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def is_late_indicator(self, obj: Order) -> str:
        """Индикатор просрочки."""
        if obj.is_late():
            return format_html(
                '<span style="color: red;">⚠️ Просрочен</span>'
            )
        return format_html(
            '<span style="color: green;">✓ В срок</span>'
        )
    is_late_indicator.short_description = 'Срок'
    
    def cost_breakdown_display(self, obj: Order) -> str:
        """Отображение детализации стоимости."""
        if not obj.cost_breakdown:
            return '-'
        
        breakdown = obj.cost_breakdown
        html = '<div style="font-size: 12px; line-height: 1.6;">'
        html += f'<strong>Материал:</strong> {breakdown.get("material_cost", 0):,.2f} ₽<br>'
        html += f'<strong>Работа:</strong> {breakdown.get("labor_cost", 0):,.2f} ₽<br>'
        html += f'<strong>Накладные:</strong> {breakdown.get("overhead", 0):,.2f} ₽<br>'
        html += f'<strong>Резерв на брак:</strong> {breakdown.get("defect_reserve", 0):,.2f} ₽<br>'
        html += f'<strong>Себестоимость:</strong> {breakdown.get("sebestoimost", 0):,.2f} ₽<br>'
        html += f'<strong>Наценка:</strong> {breakdown.get("markup", 0):,.2f} ₽<br>'
        html += f'<strong style="font-size: 14px;">ИТОГО:</strong> {breakdown.get("retail_price", 0):,.2f} ₽'
        html += '</div>'
        return format_html(html)
    cost_breakdown_display.short_description = 'Детализация'
    cost_breakdown_display.allow_tags = True
    
    def get_lead_time_hours(self, obj: Order) -> str:
        """Время выполнения в часах."""
        hours = obj.get_lead_time_hours()
        if hours:
            return f'{hours:.1f} ч'
        return '-'
    get_lead_time_hours.short_description = 'Время вып.'
    
    def generate_job_ticket_link(self, obj: Order) -> str:
        """Ссылка на генерацию маршрутного листа."""
        url = f'/admin/orders/{obj.id}/job_ticket/'
        return format_html(
            '<a href="{}" target="_blank" style="color: blue; text-decoration: underline;">📄 Печать ТЗ</a>',
            url
        )
    generate_job_ticket_link.short_description = 'Маршрутный лист'
    
    @admin.action(description='В производство')
    def mark_in_progress(self, request, queryset):
        """Перевести заказы в производство."""
        queryset.update(status='IN_PROGRESS')
    
    @admin.action(description='Контроль качества')
    def mark_quality_check(self, request, queryset):
        """Перевести на контроль качества."""
        queryset.update(status='QUALITY_CHECK')
    
    @admin.action(description='Готов к выдаче')
    def mark_ready(self, request, queryset):
        """Отметить как готовый."""
        queryset.update(status='READY')
    
    @admin.action(description='Отгружен')
    def mark_shipped(self, request, queryset):
        """Отметить как отгруженный."""
        queryset.update(status='SHIPPED')
    
    @admin.action(description='Отменен')
    def mark_cancelled(self, request, queryset):
        """Отменить заказы."""
        queryset.update(status='CANCELLED')
    
    @admin.action(description='Печать маршрутных листов')
    def print_job_tickets(self, request, queryset):
        """Сгенерировать и скачать маршрутные листы."""
        from crm.utils.pdf_generator import generate_job_ticket_pdf
        from django.http import HttpResponse
        
        # Генерируем PDF для первого заказа (для примера)
        if queryset.exists():
            order = queryset.first()
            pdf_path = order.generate_job_ticket_pdf()
            
            # В реальном приложении здесь будет объединение нескольких PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="job_tickets.pdf"'
            
            with open(pdf_path, 'rb') as f:
                response.write(f.read())
            
            return response
