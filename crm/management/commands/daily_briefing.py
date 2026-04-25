import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Sum
from crm.models import Order
from crm.bot_logic.vk_api_client import VKClient

class Command(BaseCommand):
    help = 'Отправляет ежедневный отчет о готовых заказах администратору в ВК'

    def handle(self, *args, **options):
        today = datetime.date.today()
        
        # Считаем сумму заказов со статусом READY за сегодня
        stats = Order.objects.filter(
            status='READY',
            created_at__date=today
        ).aggregate(total=Sum('final_price'))
        
        total_sum = stats['total'] or 0
        count = Order.objects.filter(status='READY', created_at__date=today).count()

        message = (
            f"📊 **Ежедневный отчет ({today})**\n"
            f"Выполнено заказов: {count}\n"
            f"Выручка за день: {total_sum} ₽"
        )

        admin_id = getattr(settings, 'VK_ADMIN_ID', None)
        if admin_id:
            vk = VKClient()
            vk.send_message(admin_id, message)
            self.stdout.write(self.style.SUCCESS(f"Отчет отправлен админу {admin_id}"))
        else:
            self.stdout.write(self.style.WARNING("VK_ADMIN_ID не настроен в settings.py"))
