from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crm.models import Order, Client, ProductionKPI
from crm.bot_logic.vk_client import VKClient
from django.conf import settings
from decimal import Decimal


class Command(BaseCommand):
    help = 'Еженедельный отчет для администратора ВКонтакте'

    def handle(self, *args, **options):
        today = timezone.now().date()
        last_week = today - timedelta(days=7)
        
        # Статистика за неделю
        new_orders_count = Order.objects.filter(
            created_at__gte=last_week
        ).count()
        
        completed_orders = Order.objects.filter(
            status='READY',
            updated_at__gte=last_week
        )
        completed_count = completed_orders.count()
        revenue = sum(order.final_price or Decimal('0') for order in completed_orders)
        
        # Новые клиенты
        new_clients = Client.objects.filter(
            created_at__gte=last_week
        ).count()
        
        # Средняя стоимость заказа
        avg_order_value = revenue / completed_count if completed_count > 0 else Decimal('0')
        
        # Топ материалов
        top_materials = Order.objects.filter(
            created_at__gte=last_week
        ).values('material__name').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        
        # Формируем сообщение
        message = (
            f"📊 Еженедельный отчет за период {last_week.strftime('%d.%m')} - {today.strftime('%d.%m.%Y')}\n\n"
            f"🆕 Новых заказов: {new_orders_count}\n"
            f"✅ Выполнено заказов: {completed_count}\n"
            f"💰 Выручка: {revenue} ₽\n"
            f"📈 Средний чек: {avg_order_value:.0f} ₽\n"
            f"👥 Новых клиентов: {new_clients}\n\n"
        )
        
        if top_materials:
            message += "🏆 Популярные материалы:\n"
            for i, mat in enumerate(top_materials, 1):
                message += f"{i}. {mat['material__name'] or 'Без материала'} ({mat['count']} зак.)\n"
        
        message += "\nAnton Maker CRM"
        
        # Отправляем администратору
        if hasattr(settings, 'ADMIN_VK_ID') and settings.ADMIN_VK_ID:
            try:
                vk_client = VKClient()
                vk_client.send_message(settings.ADMIN_VK_ID, message)
                self.stdout.write(self.style.SUCCESS(f'Отчет отправлен администратору {settings.ADMIN_VK_ID}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка отправки отчета: {e}'))
        else:
            self.stdout.write(self.style.WARNING('ADMIN_VK_ID не настроен'))
        
        self.stdout.write(self.style.SUCCESS('Еженедельный отчет сгенерирован'))
