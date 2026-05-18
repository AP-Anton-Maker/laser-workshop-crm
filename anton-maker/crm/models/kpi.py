from django.db import models
from django.utils import timezone
from decimal import Decimal
from typing import Optional


class ProductionKPI(models.Model):
    """
    Модель для отслеживания метрик бережливого производства (Lean 4.0).
    Расчет OEE (Overall Equipment Effectiveness) и других показателей.
    """
    
    date = models.DateField(
        "Дата", 
        unique=True, 
        db_index=True,
        default=timezone.now
    )
    
    # OEE компоненты
    availability_percent = models.DecimalField(
        "Доступность (%)", 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('100'),
        help_text="Время работы / Плановое время"
    )
    performance_percent = models.DecimalField(
        "Производительность (%)", 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('100'),
        help_text="Фактический выпуск / Плановый выпуск"
    )
    quality_percent = models.DecimalField(
        "Качество (%)", 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('100'),
        help_text="Годные изделия / Всего изделий"
    )
    
    # Дополнительные метрики
    waste_percent = models.DecimalField(
        "Процент отходов (%)", 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0'),
        help_text="Отходы производства"
    )
    lead_time_hours = models.DecimalField(
        "Время выполнения заказа (часы)", 
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    wip_count = models.PositiveIntegerField(
        "Незавершенное производство (шт)", 
        default=0,
        help_text="Количество заказов в работе"
    )
    
    # Статистика за день
    total_orders = models.PositiveIntegerField("Всего заказов", default=0)
    completed_orders = models.PositiveIntegerField("Завершено заказов", default=0)
    cancelled_orders = models.PositiveIntegerField("Отменено заказов", default=0)
    total_revenue = models.DecimalField(
        "Выручка за день (₽)", 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0')
    )
    material_cost = models.DecimalField(
        "Затраты на материалы (₽)", 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0')
    )
    labor_hours = models.DecimalField(
        "Затрачено человеко-часов", 
        max_digits=6, 
        decimal_places=2, 
        default=Decimal('0')
    )
    
    # Примечания
    notes = models.TextField("Примечания", blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "KPI производства"
        verbose_name_plural = "KPI производства"
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self) -> str:
        oee = self.calculate_oee()
        return f"{self.date.strftime('%d.%m.%Y')} — OEE: {oee}%"
    
    @property
    def oee(self) -> Decimal:
        """Рассчитать OEE (Overall Equipment Effectiveness)."""
        return self.calculate_oee()
    
    def calculate_oee(self) -> Decimal:
        """
        Расчет общего коэффициента эффективности оборудования.
        
        Формула: OEE = Availability × Performance × Quality
        
        Returns:
            Значение OEE в процентах (0-100)
        """
        avail = self.availability_percent / Decimal('100')
        perf = self.performance_percent / Decimal('100')
        qual = self.quality_percent / Decimal('100')
        
        oee = avail * perf * qual * Decimal('100')
        return oee.quantize(Decimal('0.01'))
    
    @classmethod
    def get_or_create_today(cls) -> 'ProductionKPI':
        """Получить или создать KPI за сегодня."""
        today = timezone.now().date()
        obj, _ = cls.objects.get_or_create(date=today)
        return obj
    
    def update_from_orders(self) -> None:
        """
        Обновить метрики на основе заказов за дату.
        Должен вызываться периодически через CRON.
        """
        from .order import Order
        
        start_of_day = timezone.datetime.combine(
            self.date, 
            timezone.datetime.min.time()
        ).replace(tzinfo=timezone.get_current_timezone())
        
        end_of_day = start_of_day + timezone.timedelta(days=1)
        
        orders = Order.objects.filter(
            created_at__gte=start_of_day,
            created_at__lt=end_of_day
        )
        
        self.total_orders = orders.count()
        self.completed_orders = orders.filter(status='READY').count()
        self.cancelled_orders = orders.filter(status='CANCELLED').count()
        self.wip_count = Order.objects.filter(
            status__in=['NEW', 'IN_PROGRESS', 'QUALITY_CHECK']
        ).exclude(created_at__gte=start_of_day).count()
        
        # Выручка от завершенных заказов
        completed = orders.filter(status='READY')
        self.total_revenue = sum(
            order.final_price or Decimal('0') 
            for order in completed
        )
        
        # Качество (отношение завершенных к общему числу)
        if self.total_orders > 0:
            self.quality_percent = (
                Decimal(self.completed_orders) / 
                Decimal(self.total_orders) * 
                Decimal('100')
            ).quantize(Decimal('0.01'))
        
        self.save()
    
    @classmethod
    def get_average_oee(cls, days: int = 7) -> Optional[Decimal]:
        """
        Получить средний OEE за последние N дней.
        
        Args:
            days: Количество дней для усреднения
            
        Returns:
            Среднее значение OEE или None если нет данных
        """
        cutoff_date = timezone.now().date() - timezone.timedelta(days=days)
        
        avg = cls.objects.filter(
            date__gte=cutoff_date
        ).aggregate(
            avg_availability=models.Avg('availability_percent'),
            avg_performance=models.Avg('performance_percent'),
            avg_quality=models.Avg('quality_percent')
        )
        
        if all([avg['avg_availability'], avg['avg_performance'], avg['avg_quality']]):
            oee = (
                Decimal(str(avg['avg_availability'])) / Decimal('100') *
                Decimal(str(avg['avg_performance'])) / Decimal('100') *
                Decimal(str(avg['avg_quality'])) / Decimal('100') *
                Decimal('100')
            )
            return oee.quantize(Decimal('0.01'))
        
        return None
