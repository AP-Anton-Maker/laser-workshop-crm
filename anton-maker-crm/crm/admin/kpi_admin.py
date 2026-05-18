from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from crm.models import ProductionKPI
from decimal import Decimal


@admin.register(ProductionKPI)
class ProductionKPIAdmin(ModelAdmin):
    """
    Админка для KPI производства.
    Дашборд метрик бережливого производства.
    """
    
    list_display = [
        'date',
        'oee_badge',
        'availability',
        'performance',
        'quality',
        'waste_percentage',
        'completed_orders',
        'downtime_minutes',
    ]
    list_filter = ['date']
    readonly_fields = [
        'oee',
        'created_at',
        'updated_at',
    ]
    fieldsets = [
        ('OEE Компоненты', {
            'fields': ['availability', 'performance', 'quality', 'oee'],
            'description': 'Общая эффективность оборудования (OEE = A × P × Q)'
        }),
        ('Метрики качества', {
            'fields': ['waste_percentage', 'defective_orders'],
        }),
        ('Производительность', {
            'fields': ['lead_time_hours', 'total_orders', 'completed_orders', 'wip_count'],
        }),
        ('Простои', {
            'fields': ['downtime_minutes', 'downtime_reason'],
        }),
        ('Метаданные', {
            'fields': ['notes', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    date_hierarchy = 'date'
    ordering = ['-date']
    
    def oee_badge(self, obj: ProductionKPI) -> str:
        """Цветной индикатор OEE."""
        oee = float(obj.oee)
        
        if oee >= 85:
            color = '#22c55e'  # Зеленый -世界级
            icon = '🏆'
        elif oee >= 70:
            color = '#3b82f6'  # Синий - Хорошо
            icon = '✓'
        elif oee >= 50:
            color = '#eab308'  # Желтый - Требует внимания
            icon = '⚠️'
        else:
            color = '#ef4444'  # Красный - Критично
            icon = '❌'
        
        return format_html(
            '<span style="color: white; background-color: {}; padding: 4px 12px; border-radius: 12px; font-weight: bold;">{} {:.1f}%</span>',
            color,
            icon,
            oee
        )
    oee_badge.short_description = 'OEE'
    
    def save_model(self, request, obj: ProductionKPI, form, change) -> None:
        """Автоматический расчет OEE при сохранении."""
        obj.calculate_oee()
        super().save_model(request, obj, form, change)
