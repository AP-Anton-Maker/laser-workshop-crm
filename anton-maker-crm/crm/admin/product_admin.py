from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, StackedInline
from crm.models import Material, Operation, Product, ProductOperation


class ProductOperationInline(StackedInline):
    """Inline для операций изделия."""
    
    model = ProductOperation
    extra = 0
    ordering = ['sequence']
    fields = ['operation', 'sequence', 'time_per_unit_min', 'notes']
    autocomplete_fields = ['operation']


@admin.register(Material)
class MaterialAdmin(ModelAdmin):
    """Админка для модели Material."""
    
    list_display = [
        'name',
        'code',
        'price_per_unit',
        'unit',
        'in_stock',
        'stock_status',
        'is_active',
    ]
    list_filter = ['is_active', 'unit']
    search_fields = ['name', 'code', 'supplier']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        (None, {
            'fields': ['name', 'code', 'supplier']
        }),
        ('Цена и единицы', {
            'fields': ['price_per_unit', 'unit', 'density']
        }),
        ('Отходы', {
            'fields': ['waste_factor'],
            'description': 'Процент технологических отходов при обработке'
        }),
        ('Склад', {
            'fields': ['in_stock', 'min_stock'],
            'description': 'Текущий остаток и точка заказа'
        }),
        ('Метаданные', {
            'fields': ['is_active', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    actions = ['mark_low_stock', 'export_selected']
    ordering = ['name']
    
    def stock_status(self, obj: Material) -> str:
        """Отображение статуса остатков."""
        if obj.is_low_stock():
            return format_html(
                '<span style="color: red;">⚠️ Низкий остаток</span>'
            )
        return format_html(
            '<span style="color: green;">✓ В норме</span>'
        )
    stock_status.short_description = 'Статус'
    
    @admin.action(description='Пометить как низкий остаток')
    def mark_low_stock(self, request, queryset):
        """Установить минимальный запас выше текущего."""
        for material in queryset:
            material.min_stock = material.in_stock + Decimal('10')
            material.save()
    
    @admin.action(description='Экспортировать выбранные')
    def export_selected(self, request, queryset):
        """Экспорт материалов в CSV."""
        import csv
        from django.http import HttpResponse
        from decimal import Decimal
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="materials.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Артикул', 'Название', 'Цена', 'Ед.', 'На складе', 'Мин. запас', 'Поставщик'])
        
        for material in queryset:
            writer.writerow([
                material.code,
                material.name,
                material.price_per_unit,
                material.unit,
                material.in_stock,
                material.min_stock,
                material.supplier or '',
            ])
        
        return response


@admin.register(Operation)
class OperationAdmin(ModelAdmin):
    """Админка для модели Operation."""
    
    list_display = [
        'name',
        'code',
        'hourly_rate',
        'setup_time_min',
        'is_active',
    ]
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at']
    fieldsets = [
        (None, {
            'fields': ['name', 'code', 'description']
        }),
        ('Ставка и время', {
            'fields': ['hourly_rate', 'setup_time_min']
        }),
        ('Метаданные', {
            'fields': ['is_active', 'created_at'],
            'classes': ['collapse']
        }),
    ]
    ordering = ['name']


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    """
    Админка для модели Product.
    Включает встроенный калькулятор стоимости.
    """
    
    list_display = [
        'name',
        'sku',
        'material',
        'dimensions_display',
        'get_operation_count',
        'is_active',
    ]
    list_filter = ['is_active', 'material']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = [
        'calculate_net_weight_kg',
        'created_at',
        'updated_at',
    ]
    fieldsets = [
        (None, {
            'fields': ['name', 'sku', 'description']
        }),
        ('Габариты (мм)', {
            'fields': ['length_mm', 'width_mm', 'height_mm', 'shape_factor']
        }),
        ('Материал и операции', {
            'fields': ['material', 'calculate_net_weight_kg']
        }),
        ('Метаданные', {
            'fields': ['is_active', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    inlines = [ProductOperationInline]
    ordering = ['name']
    
    def dimensions_display(self, obj: Product) -> str:
        """Отображение габаритов."""
        return f'{obj.length_mm} × {obj.width_mm} × {obj.height_mm} мм'
    dimensions_display.short_description = 'Габариты'
    
    def get_operation_count(self, obj: Product) -> int:
        """Получить количество операций."""
        return obj.product_operations.count()
    get_operation_count.short_description = 'Операций'
    
    def calculate_net_weight_kg(self, obj: Product) -> str:
        """Отображение расчетного веса."""
        weight = obj.calculate_net_weight_kg()
        return f'{weight} кг'
    calculate_net_weight_kg.short_description = 'Вес заготовки'
