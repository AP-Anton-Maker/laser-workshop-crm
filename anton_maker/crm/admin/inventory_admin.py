from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models.inventory import Material, QuickReply


@admin.register(Material)
class MaterialAdmin(ModelAdmin):
    list_display = ['name', 'price_per_unit', 'in_stock', 'min_stock_level', 'stock_alert', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    fieldsets = [
        (None, {'fields': ['name', 'price_per_unit']}),
        ('Запасы', {'fields': ['in_stock', 'min_stock_level']}),
        ('Настройки', {'fields': ['is_active']}),
    ]

    def stock_alert(self, obj):
        if obj.is_low_stock:
            return '⚠️ Низкий запас'
        return '✓'
    stock_alert.short_description = 'Статус'

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',)
        }


@admin.register(QuickReply)
class QuickReplyAdmin(ModelAdmin):
    list_display = ['title', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'text']
    fieldsets = [
        (None, {'fields': ['title', 'text']}),
        ('Настройки', {'fields': ['is_active']}),
    ]
