from unfold.admin import ModelAdmin
from django.contrib import admin
from ..models import Material

@admin.register(Material)
class MaterialAdmin(ModelAdmin):
    list_display = ("name", "price_per_meter", "in_stock", "updated_at")
    list_filter = ("in_stock",)
    search_fields = ("name",)
    list_editable = ("in_stock", "price_per_meter")

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "price_per_meter", "in_stock"),
                "classes": ("tab",),
            },
        ),
    )
