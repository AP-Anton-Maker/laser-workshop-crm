from django.db import models
from decimal import Decimal


class ProductionKPI(models.Model):
    """
    Модель метрик бережливого производства.
    Хранит ежедневные показатели OEE и другие KPI.
    """
    
    date = models.DateField(
        'Дата',
        unique=True,
        db_index=True,
        help_text='Дата отчета'
    )
    
    # OEE компоненты (в процентах, 0-100)
    availability = models.DecimalField(
        'Доступность (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Время доступности оборудования'
    )
    performance = models.DecimalField(
        'Производительность (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Скорость работы относительно плановой'
    )
    quality = models.DecimalField(
        'Качество (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Доля годных изделий'
    )
    
    # Рассчитанный OEE
    oee = models.DecimalField(
        'OEE (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Общая эффективность оборудования'
    )
    
    # Другие метрики
    waste_percentage = models.DecimalField(
        'Отходы (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Процент отходов от общего материала'
    )
    lead_time_hours = models.DecimalField(
        'Время выполнения (часы)',
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Среднее время выполнения заказа'
    )
    wip_count = models.PositiveIntegerField(
        'Незавершенное производство',
        default=0,
        help_text='Количество заказов в работе'
    )
    
    # Производство
    total_orders = models.PositiveIntegerField(
        'Всего заказов',
        default=0,
        help_text='Общее количество заказов за день'
    )
    completed_orders = models.PositiveIntegerField(
        'Завершено заказов',
        default=0,
        help_text='Количество завершенных заказов'
    )
    defective_orders = models.PositiveIntegerField(
        'Брак',
        default=0,
        help_text='Количество бракованных заказов'
    )
    
    # Простои (в минутах)
    downtime_minutes = models.PositiveIntegerField(
        'Простои (мин)',
        default=0,
        help_text='Общее время простоев'
    )
    downtime_reason = models.TextField(
        'Причины простоев',
        blank=True,
        help_text='Основные причины простоев'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    notes = models.TextField(
        'Заметки',
        blank=True,
        help_text='Дополнительные комментарии'
    )
    
    class Meta:
        verbose_name = 'KPI производства'
        verbose_name_plural = 'KPI производства'
        ordering = ['-date']
    
    def __str__(self) -> str:
        return f'KPI за {self.date}: OEE={self.oee}%'
    
    def calculate_oee(self) -> Decimal:
        """
        Рассчитать OEE как произведение трех компонентов.
        
        Формула: OEE = Availability × Performance × Quality / 10000
        
        Returns:
            Decimal: Значение OEE в процентах
        """
        oee_value = (
            self.availability * 
            self.performance * 
            self.quality / Decimal('10000')
        )
        self.oee = oee_value.quantize(Decimal('0.01'))
        return self.oee
    
    def save(self, *args, **kwargs) -> None:
        """Автоматический расчет OEE при сохранении."""
        self.calculate_oee()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_today_kpi(cls):
        """Получить KPI за сегодня."""
        from datetime import date
        return cls.objects.filter(date=date.today()).first()
    
    @classmethod
    def get_average_oee(cls, days: int = 7) -> Decimal:
        """
        Получить средний OEE за период.
        
        Args:
            days: Количество дней
            
        Returns:
            Decimal: Средний OEE
        """
        from datetime import timedelta, date
        
        start_date = date.today() - timedelta(days=days)
        
        avg = cls.objects.filter(
            date__gte=start_date
        ).aggregate(
            avg_oee=models.Avg('oee')
        )['avg_oee']
        
        return avg or Decimal('0.00')
