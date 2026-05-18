from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crm.models import Material, Order
from crm.bot_logic.vk_client import VKClient
from django.conf import settings
from decimal import Decimal


class Command(BaseCommand):
    help = 'Проверка остатков материалов и отправка алертов'

    def handle(self, *args, **options):
        alert_messages = []
        
        # Получаем все активные материалы
        materials = Material.objects.filter(is_active=True)
        
        for material in materials:
            # Считаем необходимый материал для активных заказов
            active_orders = Order.objects.filter(
                status__in=['NEW', 'IN_PROGRESS'],
                material=material
            )
            
            # Суммарная площадь необходимых материалов (в см²)
            total_needed = Decimal('0')
            for order in active_orders:
                if order.width and order.height:
                    area = order.width * order.height  # см²
                    quantity = order.quantity or 1
                    total_needed += area * quantity
            
            # Проверяем остаток
            if material.in_stock is not None and total_needed > 0:
                # Если остаток меньше необходимого + запас 20%
                required_with_reserve = total_needed * Decimal('1.2')
                
                if material.in_stock < required_with_reserve:
                    message = (
                        f"⚠️ ВНИМАНИЕ: Материал '{material.name}'\n\n"
                        f"📦 Остаток на складе: {material.in_stock} {material.unit}\n"
                        f"📋 Необходимо для заказов: {total_needed:.1f} {material.unit}\n"
                        f"📈 С запасом (20%): {required_with_reserve:.1f} {material.unit}\n\n"
                        f"Рекомендуется дозакупить: {required_with_reserve - material.in_stock:.1f} {material.unit}"
                    )
                    alert_messages.append(message)
                    self.stdout.write(self.style.WARNING(f'Материал {material.name}: недостаток!'))
        
        # Отправляем алерты администратору
        if alert_messages and hasattr(settings, 'ADMIN_VK_ID') and settings.ADMIN_VK_ID:
            try:
                vk_client = VKClient()
                for message in alert_messages:
                    vk_client.send_message(settings.ADMIN_VK_ID, message)
                self.stdout.write(self.style.SUCCESS(f'Отправлено {len(alert_messages)} алертов администратору'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка отправки алертов: {e}'))
        elif alert_messages:
            self.stdout.write(self.style.WARNING('Есть алерты, но ADMIN_VK_ID не настроен'))
        else:
            self.stdout.write(self.style.SUCCESS('Все материалы в достаточном количестве'))
