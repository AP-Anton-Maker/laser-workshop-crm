from unfold.admin import ModelAdmin
from django.contrib import admin
from ..models import Client

@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = ("full_name", "vk_id", "phone", "total_spent", "bot_state", "created_at")
    list_filter = ("bot_state", "created_at")
    search_fields = ("full_name", "vk_id", "phone")
    readonly_fields = ("created_at", "total_spent")

    fieldsets = (
        (
            None,
            {
                "fields": ("vk_id", "full_name", "phone"),
                "classes": ("tab",),
            },
        ),
        (
            "Статистика",
            {
                "fields": ("total_spent", "bot_state", "created_at"),
                "classes": ("tab", "collapse"),
            },
        ),
    )
