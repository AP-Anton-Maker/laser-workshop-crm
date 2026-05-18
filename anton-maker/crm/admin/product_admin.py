from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from ..models.product import Material, ServiceOption, CalculatorSettings


@admin.register(Material)
class MaterialAdmin(ModelAdmin):
    """Админка для управления материалами."""
    
    list_display = [
        'icon',
        'name',
        'processing_type',
        'price_per_unit',
        'unit',
        'is_active',
        'sort_order',
    ]
    list_filter = [
        'processing_type',
        'is_active',
    ]
    search_fields = ['name', 'code']
    list_editable = ['is_active', 'sort_order']
    ordering = ['processing_type', 'sort_order', 'name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name',
                'code',
                'icon',
                'description',
            )
        }),
        ('Тип обработки и цена', {
            'fields': (
                'processing_type',
                'price_per_unit',
                'unit',
            )
        }),
        ('Параметры материала', {
            'fields': (
                'density_g_cm3',
                'max_thickness_mm',
            )
        }),
        ('Коэффициенты', {
            'fields': (
                'waste_factor',
                'complexity_factor',
            )
        }),
        ('Отображение', {
            'fields': (
                'is_active',
                'sort_order',
            )
        }),
    )
    
    @admin.display(description='Материал')
    def name_with_icon(self, obj: Material) -> str:
        return f"{obj.icon} {obj.name}"


@admin.register(ServiceOption)
class ServiceOptionAdmin(ModelAdmin):
    """Админка для дополнительных услуг."""
    
    list_display = [
        'icon',
        'name',
        'price_type',
        'price_value',
        'is_active',
        'sort_order',
    ]
    list_filter = ['price_type', 'is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name',
                'code',
                'icon',
                'description',
            )
        }),
        ('Цена', {
            'fields': (
                'price_type',
                'price_value',
            )
        }),
        ('Отображение', {
            'fields': (
                'is_active',
                'sort_order',
                'is_default',
            )
        }),
    )


@admin.register(CalculatorSettings)
class CalculatorSettingsAdmin(ModelAdmin):
    """Админка для настроек калькулятора."""
    
    fieldsets = (
        ('Основные настройки', {
            'fields': (
                'min_order_amount',
                'design_service_price',
                'margin_percent',
            )
        }),
        ('Коэффициенты', {
            'fields': (
                'rush_multiplier',
                'rotary_multiplier',
            )
        }),
        ('Тексты', {
            'fields': ('disclaimer',)
        }),
        ('Информация', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request) -> bool:
        """Запретить создание более одной записи."""
        return not CalculatorSettings.objects.exists()
