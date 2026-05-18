from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models.system import SystemLog, BotState


@admin.register(SystemLog)
class SystemLogAdmin(ModelAdmin):
    list_display = ['action', 'description', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['description']
    readonly_fields = ['action', 'description', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BotState)
class BotStateAdmin(ModelAdmin):
    list_display = ['vk_id', 'state', 'updated_at']
    list_filter = ['state', 'updated_at']
    readonly_fields = ['vk_id', 'state', 'temp_data', 'updated_at']

    def has_add_permission(self, request):
        return False
