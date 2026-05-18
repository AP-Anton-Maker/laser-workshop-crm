from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from ..models.kpi import ProductionKPI


@admin.register(ProductionKPI)
class ProductionKPIAdmin(ModelAdmin):
    """
    Админка для просмотра метрик бережливого производства.
    Дашборд с OEE и другими показателями.
    """
    
    list_display = [
        'date',
        'oee_badge',
        'availability_percent',
        'performance_percent',
        'quality_percent',
        'waste_percent',
        'completed_orders',
        'total_revenue',
    ]
    list_filter = ['date']
    readonly_fields = [
        'date',
        'oee',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Дата', {
            'fields': ('date',)
        }),
        ('OEE (Overall Equipment Effectiveness)', {
            'fields': (
                'oee',
                'availability_percent',
                'performance_percent',
                'quality_percent',
            ),
            'description': 'Ключевой показатель эффективности оборудования'
        }),
        ('Дополнительные метрики', {
            'fields': (
                'waste_percent',
                'lead_time_hours',
                'wip_count',
            )
        }),
        ('Статистика за день', {
            'fields': (
                'total_orders',
                'completed_orders',
                'cancelled_orders',
                'total_revenue',
                'material_cost',
                'labor_hours',
            )
        }),
        ('Примечания', {
            'fields': ('notes',)
        }),
        ('Системная информация', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-date']
    date_hierarchy = 'date'
    list_per_page = 30
    
    @admin.display(description='OEE')
    def oee_badge(self, obj: ProductionKPI) -> str:
        oee = obj.calculate_oee()
        
        if oee >= 85:
            color = '#10b981'  # green
            emoji = '🟢'
        elif oee >= 60:
            color = '#f59e0b'  # yellow
            emoji = '🟡'
        else:
            color = '#ef4444'  # red
            emoji = '🔴'
        
        return format_html(
            f'<span style="background:{color};color:white;padding:4px 12px;border-radius:4px;font-weight:bold;">'
            f'{emoji} {oee:.1f}%'
            f'</span>'
        )
    
    def has_add_permission(self, request) -> bool:
        """Запретить ручное создание - только через CRON."""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Добавить контекст со средним OEE."""
        extra_context = extra_context or {}
        avg_oee = ProductionKPI.get_average_oee(days=7)
        extra_context['avg_oee'] = avg_oee
        return super().changelist_view(request, extra_context=extra_context)
