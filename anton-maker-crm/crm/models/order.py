from django.db import models
from decimal import Decimal
from typing import Optional
from datetime import datetime
import os


class Order(models.Model):
    """
    Модель заказа.
    Управляет жизненным циклом заказов от создания до отгрузки.
    """
    
    # Статусы заказа (Kanban-style)
    STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('IN_PROGRESS', 'В производстве'),
        ('QUALITY_CHECK', 'Контроль качества'),
        ('READY', 'Готов к выдаче'),
        ('SHIPPED', 'Отгружен'),
        ('CANCELLED', 'Отменен'),
    ]
    
    # Срочность
    URGENCY_CHOICES = [
        ('standard', 'Стандартный (5-7 дней)'),
        ('express', 'Срочный (2-3 дня)'),
        ('super_express', 'Очень срочный (1 день)'),
    ]
    
    # Связи
    client = models.ForeignKey(
        'crm.Client',
        on_delete=models.PROTECT,
        related_name='orders',
        help_text='Клиент, сделавший заказ'
    )
    product = models.ForeignKey(
        'crm.Product',
        on_delete=models.PROTECT,
        related_name='orders',
        null=True,
        blank=True,
        help_text='Изделие'
    )
    
    # Параметры заказа
    quantity = models.PositiveIntegerField(
        'Количество',
        default=1,
        help_text='Количество изделий'
    )
    description = models.TextField(
        'Описание ТЗ',
        blank=True,
        help_text='Техническое задание от клиента'
    )
    urgency = models.CharField(
        'Срочность',
        max_length=20,
        choices=URGENCY_CHOICES,
        default='standard',
        help_text='Срочность выполнения'
    )
    
    # Файлы
    layout_file = models.FileField(
        'Файл макета',
        upload_to='layouts/',
        blank=True,
        null=True,
        help_text='Исходный файл макета от клиента'
    )
    
    # Расчеты
    calculated_price = models.DecimalField(
        'Расчетная цена',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Автоматически рассчитанная стоимость'
    )
    final_price = models.DecimalField(
        'Итоговая цена',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Финальная стоимость для клиента'
    )
    cost_breakdown = models.JSONField(
        'Детализация стоимости',
        default=dict,
        blank=True,
        help_text='JSON с разбивкой по статьям затрат'
    )
    
    # Статус и даты
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW',
        db_index=True,
        help_text='Текущий статус заказа'
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    started_at = models.DateTimeField(
        'Начало производства',
        null=True,
        blank=True,
        help_text='Когда начали производство'
    )
    completed_at = models.DateTimeField(
        'Завершение',
        null=True,
        blank=True,
        help_text='Когда завершили производство'
    )
    shipped_at = models.DateTimeField(
        'Отгрузка',
        null=True,
        blank=True,
        help_text='Когда отгрузили клиенту'
    )
    
    # Дополнительно
    notes = models.TextField(
        'Заметки',
        blank=True,
        help_text='Внутренние заметки менеджера'
    )
    manager_notes = models.TextField(
        'Комментарий менеджера',
        blank=True,
        help_text='Комментарий для клиента'
    )
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        return f'Заказ #{self.id} - {self.client}'
    
    def save(self, *args, **kwargs) -> None:
        """Автоматическое обновление дат при смене статуса."""
        if self.pk:
            old = Order.objects.filter(pk=self.pk).first()
            if old and old.status != self.status:
                now = datetime.now()
                
                if self.status == 'IN_PROGRESS' and not self.started_at:
                    self.started_at = now
                elif self.status == 'READY' and not self.completed_at:
                    self.completed_at = now
                elif self.status == 'SHIPPED' and not self.shipped_at:
                    self.shipped_at = now
        
        super().save(*args, **kwargs)
    
    def calculate_price(self) -> Decimal:
        """
        Рассчитать стоимость заказа через CostCalculator.
        
        Returns:
            Decimal: Рассчитанная стоимость
        """
        from crm.utils.cost_calculator import CostCalculator
        
        if not self.product:
            return Decimal('0.00')
        
        calculator = CostCalculator(
            product=self.product,
            quantity=self.quantity,
            urgency=self.urgency
        )
        
        breakdown = calculator.get_breakdown()
        self.calculated_price = breakdown['retail_price']
        self.cost_breakdown = breakdown
        
        return self.calculated_price
    
    def get_job_ticket_path(self) -> str:
        """Получить путь для сохранения маршрутного листа."""
        return os.path.join('tickets', f'job_ticket_{self.id}.pdf')
    
    def generate_job_ticket_pdf(self) -> str:
        """
        Сгенерировать PDF маршрутного листа.
        
        Returns:
            str: Путь к сгенерированному файлу
        """
        from crm.utils.pdf_generator import generate_job_ticket_pdf
        
        pdf_path = self.get_job_ticket_path()
        full_path = generate_job_ticket_pdf(self, pdf_path)
        
        # Сохранить ссылку на файл в заказе
        self.layout_file = full_path
        self.save(update_fields=['layout_file'])
        
        return full_path
    
    def get_status_display_color(self) -> str:
        """Получить цвет для отображения статуса."""
        colors = {
            'NEW': 'blue',
            'IN_PROGRESS': 'yellow',
            'QUALITY_CHECK': 'purple',
            'READY': 'green',
            'SHIPPED': 'gray',
            'CANCELLED': 'red',
        }
        return colors.get(self.status, 'gray')
    
    def get_lead_time_hours(self) -> Optional[float]:
        """
        Получить время выполнения в часах.
        
        Returns:
            float: Время в часах или None
        """
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() / 3600
        return None
    
    def is_late(self) -> bool:
        """Проверить, просрочен ли заказ."""
        if not self.created_at:
            return False
        
        # Стандартные сроки в днях
        deadlines = {
            'standard': 7,
            'express': 3,
            'super_express': 1,
        }
        
        deadline_days = deadlines.get(self.urgency, 7)
        
        from datetime import timedelta
        deadline = self.created_at + timedelta(days=deadline_days)
        
        return datetime.now() > deadline and self.status not in ['READY', 'SHIPPED']
