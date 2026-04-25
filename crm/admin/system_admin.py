from unfold.admin import ModelAdmin
from django.contrib import admin
from ..models import QuickReply

@admin.register(QuickReply)
class QuickReplyAdmin(ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "text")
    list_editable = ("is_active",)

    fieldsets = (
        (
            None,
            {
                "fields": ("title", "text", "is_active"),
                "classes": ("tab",),
            },
        ),
    )
