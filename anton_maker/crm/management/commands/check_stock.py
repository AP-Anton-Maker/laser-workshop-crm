from django.core.management.base import BaseCommand
from crm.models.inventory import Material


class Command(BaseCommand):
    help = 'Проверка запасов материалов'

    def handle(self, *args, **options):
        low_stock = Material.objects.filter(in_stock__lte=5, is_active=True)
        
        if low_stock.exists():
            self.stdout.write(self.style.WARNING('⚠️ Материалы с низким запасом:'))
            for material in low_stock:
                self.stdout.write(f'  - {material.name}: {material.in_stock} шт. (мин: {material.min_stock_level})')
        else:
            self.stdout.write(self.style.SUCCESS('✓ Все материалы в наличии'))
