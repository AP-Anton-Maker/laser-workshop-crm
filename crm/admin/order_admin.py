from unfold.admin import ModelAdmin
from django.contrib import admin
from django.utils.html import format_html
from ..models import Order

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("id", "client_short", "material_short", "status_badge", "final_price", "created_at")
    list_filter = ("status", "material")
    search_fields = ("client__full_name", "client__vk_id", "description")
    readonly_fields = ("created_at", "updated_at")
    actions = ("mark_as_in_progress",)

    def client_short(self, obj):
        return obj.client.full_name
    client_short.short_description = "Клиент"

    def material_short(self, obj):
        return obj.material.name if obj.material else "—"
    material_short.short_description = "Материал"

    def status_badge(self, obj):
        colors = {
            "NEW": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
            "IN_PROGRESS": "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
            "READY": "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
            "CANCELLED": "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
        }
        color_class = colors.get(obj.status, "bg-gray-100 text-gray-800")
        return format_html(
            f'<span class="px-2 py-1 rounded-full text-xs font-bold {color_class}">{obj.get_status_display()}</span>'
        )
    status_badge.short_description = "Статус"

    @admin.action(description="Изменить статус на «В работе»")
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status="IN_PROGRESS")
        self.message_user(request, f"{updated} заказов переведено в работу.")

    fieldsets = (
        (
            "Клиент",
            {
                "fields": ("client",),
                "classes": ("tab",),
            },
        ),
        (
            "ТЗ и Файлы",
            {
                "fields": ("description", "cut_length", "layout_file"),
                "classes": ("tab",),
            },
        ),
        (
            "Финансы и Статус",
            {
                "fields": ("material", "final_price", "status", "created_at", "updated_at"),
                "classes": ("tab",),
            },
        ),
    )
