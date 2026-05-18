from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from crm.models import Inventory, InventoryTransaction


@admin.register(Inventory)
class InventoryAdmin(ModelAdmin):
    """Админка для складских остатков."""
    
    list_display = [
        'material_name',
        'quantity',
        'reserved',
        'available_display',
        'location',
        'stock_status',
        'last_checked',
    ]
    list_filter = ['unit', 'location']
    search_fields = ['material__name', 'material__code']
    readonly_fields = ['updated_at', 'get_available_quantity']
    fieldsets = [
        (None, {
            'fields': ['material', 'location']
        }),
        ('Остатки', {
            'fields': ['quantity', 'reserved', 'unit', 'get_available_quantity']
        }),
        ('Метаданные', {
            'fields': ['last_checked', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    actions = ['adjust_stock', 'export_selected']
    ordering = ['material']
    
    def material_name(self, obj: Inventory) -> str:
        return obj.material.name
    material_name.short_description = 'Материал'
    
    def available_display(self, obj: Inventory) -> str:
        return f'{obj.get_available_quantity():,.3f}'
    available_display.short_description = 'Доступно'
    
    def stock_status(self, obj: Inventory) -> str:
        if obj.is_low_stock():
            return format_html(
                '<span style="color: red;">⚠️ Низкий</span>'
            )
        return format_html(
            '<span style="color: green;">✓ Норма</span>'
        )
    stock_status.short_description = 'Статус'
    
    def get_available_quantity(self, obj: Inventory) -> str:
        return f'{obj.get_available_quantity():,.3f} {obj.unit}'
    get_available_quantity.short_description = 'Доступное кол-во'
    
    @admin.action(description='Корректировка остатков')
    def adjust_stock(self, request, queryset):
        """Форма корректировки остатков."""
        # В реальной реализации здесь будет форма
        pass


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(ModelAdmin):
    """Админка для движений склада."""
    
    list_display = [
        'created_at',
        'material',
        'transaction_type_badge',
        'quantity',
        'inventory_location',
        'order_link',
        'user',
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['material__name', 'notes', 'user']
    readonly_fields = ['created_at']
    fieldsets = [
        (None, {
            'fields': ['transaction_type', 'material', 'quantity']
        }),
        ('Связи', {
            'fields': ['inventory', 'order'],
            'classes': ['collapse']
        }),
        ('Информация', {
            'fields': ['user', 'notes', 'created_at'],
        }),
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def transaction_type_badge(self, obj: InventoryTransaction) -> str:
        colors = {
            'IN': '#22c55e',
            'OUT': '#ef4444',
            'ADJUSTMENT': '#3b82f6',
            'RESERVE': '#eab308',
            'UNRESERVE': '#a855f7',
        }
        color = colors.get(obj.transaction_type, '#6b7280')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_transaction_type_display()
        )
    transaction_type_badge.short_description = 'Тип'
    
    def inventory_location(self, obj: InventoryTransaction) -> str:
        return obj.inventory.location if obj.inventory else '-'
    inventory_location.short_description = 'Место'
    
    def order_link(self, obj: InventoryTransaction) -> str:
        if obj.order:
            return format_html(
                '<a href="/admin/crm/order/{}/change/" target="_blank">#{}</a>',
                obj.order.id,
                obj.order.id
            )
        return '-'
    order_link.short_description = 'Заказ'
