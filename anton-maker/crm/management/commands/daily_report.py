from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crm.models import Order, Client, ProductionKPI
from crm.bot_logic.vk_client import VKClient
from django.conf import settings
from decimal import Decimal


class Command(BaseCommand):
    help = 'Ежедневный отчет для администратора ВКонтакте'

    def handle(self, *args, **options):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Статистика за вчера
        new_orders_count = Order.objects.filter(
            created_at__date=yesterday
        ).count()
        
        completed_orders = Order.objects.filter(
            status='READY',
            updated_at__date=yesterday
        )
        completed_count = completed_orders.count()
        revenue = sum(order.final_price or Decimal('0') for order in completed_orders)
        
        # Новые клиенты
        new_clients = Client.objects.filter(
            created_at__date=yesterday
        ).count()
        
        # Формируем сообщение
        message = (
            f"📊 Ежедневный отчет за {yesterday.strftime('%d.%m.%Y')}\n\n"
            f"🆕 Новых заказов: {new_orders_count}\n"
            f"✅ Выполнено заказов: {completed_count}\n"
            f"💰 Выручка: {revenue} ₽\n"
            f"👥 Новых клиентов: {new_clients}\n\n"
            f"Anton Maker CRM"
        )
        
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
        
        self.stdout.write(self.style.SUCCESS('Ежедневный отчет сгенерирован'))
