from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crm.models.order import Order
from crm.models.inventory import Material


class Command(BaseCommand):
    help = 'Ежедневная сводка по заказам и запасам'

    def handle(self, *args, **options):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        new_orders = Order.objects.filter(created_at__date=today).count()
        done_orders = Order.objects.filter(status='DONE', completed_at__date=today).count()
        
        low_stock = Material.objects.filter(in_stock__lte=5, is_active=True)
        
        self.stdout.write(f'📊 Ежедневная сводка ({today}):')
        self.stdout.write(f'  Новых заказов: {new_orders}')
        self.stdout.write(f'  Выполнено: {done_orders}')
        
        if low_stock.exists():
            self.stdout.write('\n⚠️ Материалы с низким запасом:')
            for material in low_stock:
                self.stdout.write(f'  - {material.name}: {material.in_stock} шт.')
        else:
            self.stdout.write('\n✓ Запасы в норме')
