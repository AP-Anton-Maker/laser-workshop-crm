from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.http import JsonResponse
from .models import Client, Order, InventoryItem, PromoCode, CashbackTransaction, ChatMessage, PriceListItem, Setting, UserSession
from .vk_client import vk
from vk_api.utils import get_random_id

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'vk_id', 'total_orders', 'total_spent', 'cashback_balance')
    search_fields = ('name', 'vk_id')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'service_name', 'total_price', 'status', 'created_at')
    list_filter = ('status',)
    actions = ['mark_processing', 'mark_done', 'mark_delivered']

    def mark_processing(self, request, queryset):
        queryset.update(status='PROCESSING')
    mark_processing.short_description = "В работу"

    def mark_done(self, request, queryset):
        for order in queryset:
            if order.status != 'DONE':
                order.status = 'DONE'
                order.save()
                cashback = order.total_price * 0.05
                order.client.cashback_balance += cashback
                order.client.save()
                CashbackTransaction.objects.create(
                    client=order.client, order=order, amount=cashback, operation_type='earned'
                )
    mark_done.short_description = "Готов (начислить кэшбэк)"

    def mark_delivered(self, request, queryset):
        queryset.update(status='DELIVERED')
    mark_delivered.short_description = "Выдан"

@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_type', 'quantity', 'min_quantity', 'price_per_unit')
    list_filter = ('item_type',)

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'current_uses', 'max_uses', 'is_active')
    list_editable = ('is_active',)

@admin.register(CashbackTransaction)
class CashbackAdmin(admin.ModelAdmin):
    list_display = ('client', 'amount', 'operation_type', 'created_at')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('client', 'message_preview', 'is_admin', 'timestamp', 'reply_button')
    list_filter = ('is_admin', 'timestamp')
    search_fields = ('client__name', 'message_text')
    readonly_fields = ('timestamp',)

    def message_preview(self, obj):
        return obj.message_text[:60] + ('...' if len(obj.message_text) > 60 else '')
    message_preview.short_description = 'Сообщение'

    def reply_button(self, obj):
        from django.utils.html import format_html
        return format_html('<a href="/admin/chat/{}">💬 Ответить</a>', obj.client.id)
    reply_button.short_description = 'Действие'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('chat/<int:client_id>/', self.chat_view, name='chat_view'),
            path('send_message/', self.send_message, name='send_message'),
        ]
        return custom_urls + urls

    def chat_view(self, request, client_id):
        client = Client.objects.get(id=client_id)
        messages = ChatMessage.objects.filter(client=client).order_by('timestamp')
        context = {
            'client': client,
            'messages': messages,
            'opts': self.model._meta,
            'title': f'Чат с {client.name}',
        }
        return TemplateResponse(request, 'admin/chat_messages.html', context)

    def send_message(self, request):
        if request.method == 'POST':
            client_id = request.POST.get('client_id')
            text = request.POST.get('message')
            client = Client.objects.get(id=client_id)
            if client.vk_id:
                vk.messages.send(user_id=client.vk_id, message=text, random_id=get_random_id())
                ChatMessage.objects.create(client=client, vk_id=client.vk_id, message_text=text, is_admin=True)
                return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'error'}, status=400)

@admin.register(PriceListItem)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ('name', 'calc_type', 'base_price', 'min_price', 'is_active')
    list_editable = ('is_active',)

@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('vk_id', 'state', 'updated_at')
