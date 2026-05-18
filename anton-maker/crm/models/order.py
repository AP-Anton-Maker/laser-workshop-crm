from django.db import models
from django.utils import timezone
from decimal import Decimal
from typing import Optional
import os

from .client import Client
from .product import Material


class Order(models.Model):
    """
    Модель заказа от клиента.
    Хранит всю информацию о заказе, включая файлы и расчеты.
    """
    
    STATUS_CHOICES = [
        ('NEW', '🆕 Новый'),
        ('IN_PROGRESS', '🔨 В работе'),
        ('QUALITY_CHECK', '🔍 Контроль качества'),
        ('READY', '✅ Готов'),
        ('SHIPPED', '📦 Отправлен'),
        ('CANCELLED', '❌ Отменен'),
    ]
    
    URGENCY_CHOICES = [
        ('standard', '📅 Стандартный (3-5 дней)'),
        ('rush', '⚡ Срочный (1-2 дня)'),
        ('express', '🚀 Экспресс (24 часа)'),
    ]
    
    # Основная информация
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name="Клиент"
    )
    order_number = models.CharField(
        "Номер заказа", 
        max_length=20, 
        unique=True, 
        db_index=True
    )
    description = models.TextField(
        "Описание заказа", 
        help_text="Техническое задание от клиента"
    )
    status = models.CharField(
        "Статус", 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='NEW'
    )
    urgency = models.CharField(
        "Срочность", 
        max_length=20, 
        choices=URGENCY_CHOICES, 
        default='standard'
    )
    
    # Параметры изделия
    material = models.ForeignKey(
        Material, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='orders',
        verbose_name="Материал"
    )
    length_mm = models.DecimalField(
        "Длина (мм)", 
        max_digits=8, 
        decimal_places=1, 
        null=True, 
        blank=True
    )
    width_mm = models.DecimalField(
        "Ширина (мм)", 
        max_digits=8, 
        decimal_places=1, 
        null=True, 
        blank=True
    )
    thickness_mm = models.DecimalField(
        "Толщина (мм)", 
        max_digits=6, 
        decimal_places=1, 
        null=True, 
        blank=True
    )
    quantity = models.PositiveIntegerField("Количество", default=1)
    
    # Файлы
    layout_file = models.FileField(
        "Файл макета", 
        upload_to='layouts/%Y/%m/', 
        null=True, 
        blank=True
    )
    technical_file = models.FileField(
        "Технический файл", 
        upload_to='technical/%Y/%m/', 
        null=True, 
        blank=True
    )
    
    # Расчеты стоимости
    calculated_price = models.DecimalField(
        "Расчетная стоимость (₽)", 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    final_price = models.DecimalField(
        "Итоговая стоимость (₽)", 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    discount_percent = models.DecimalField(
        "Скидка (%)", 
        max_digits=5, 
        decimal_places=1, 
        default=Decimal('0'),
        help_text="Скидка для VIP клиентов или при большом объеме"
    )
    
    # Дополнительно
    notes = models.TextField("Заметки мастера", blank=True)
    internal_notes = models.TextField(
        "Внутренние заметки", 
        blank=True,
        help_text="Не видно клиенту"
    )
    
    # Даты
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    started_at = models.DateTimeField("Начало работы", null=True, blank=True)
    completed_at = models.DateTimeField("Завершение", null=True, blank=True)
    shipped_at = models.DateTimeField("Отправка", null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        return f"Заказ #{self.order_number} — {self.client.full_name}"
    
    def save(self, *args, **kwargs) -> None:
        """Автоматическая генерация номера заказа."""
        if not self.order_number:
            today = timezone.now().strftime('%y%m%d')
            last_order = Order.objects.filter(
                order_number__startswith=today
            ).order_by('-order_number').first()
            
            if last_order:
                last_num = int(last_order.order_number.split('-')[1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.order_number = f"{today}-{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    def start_work(self) -> None:
        """Начать работу над заказом."""
        if self.status == 'NEW':
            self.status = 'IN_PROGRESS'
            self.started_at = timezone.now()
            self.save(update_fields=['status', 'started_at', 'updated_at'])
    
    def complete_work(self) -> None:
        """Завершить работу над заказом."""
        if self.status == 'IN_PROGRESS':
            self.status = 'QUALITY_CHECK'
            self.completed_at = timezone.now()
            self.save(update_fields=['status', 'completed_at', 'updated_at'])
    
    def mark_ready(self) -> None:
        """Отметить заказ как готовый."""
        if self.status == 'QUALITY_CHECK':
            self.status = 'READY'
            self.save(update_fields=['status', 'updated_at'])
    
    def ship_order(self) -> None:
        """Отметить заказ как отправленный."""
        if self.status == 'READY':
            self.status = 'SHIPPED'
            self.shipped_at = timezone.now()
            self.save(update_fields=['status', 'shipped_at', 'updated_at'])
    
    def cancel_order(self) -> None:
        """Отменить заказ."""
        self.status = 'CANCELLED'
        self.save(update_fields=['status', 'updated_at'])
    
    def get_dimensions_str(self) -> str:
        """Получить строку с размерами."""
        if all([self.length_mm, self.width_mm, self.thickness_mm]):
            return f"{self.length_mm} × {self.width_mm} × {self.thickness_mm} мм"
        elif all([self.length_mm, self.width_mm]):
            return f"{self.length_mm} × {self.width_mm} мм"
        return "Не указаны"
    
    def get_area_cm2(self) -> Optional[Decimal]:
        """Получить площадь в см²."""
        if self.length_mm and self.width_mm:
            area_mm2 = self.length_mm * self.width_mm
            return (area_mm2 / Decimal('100')).quantize(Decimal('0.01'))
        return None
    
    def calculate_material_cost(self) -> Decimal:
        """Рассчитать стоимость материала."""
        if not self.material or not self.quantity:
            return Decimal('0')
        
        area_cm2 = self.get_area_cm2() or Decimal('0')
        return self.material.calculate_price(
            float(area_cm2) * self.quantity,
            is_urgent=(self.urgency == 'rush')
        )
    
    @property
    def production_time_hours(self) -> Optional[float]:
        """Оценочное время производства в часах."""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or timezone.now()
        delta = end_time - self.started_at
        return round(delta.total_seconds() / 3600, 2)
    
    @property
    def is_late(self) -> bool:
        """Проверить, просрочен ли заказ."""
        if not self.created_at:
            return False
        
        deadlines = {
            'standard': 5,
            'rush': 2,
            'express': 1,
        }
        
        deadline_days = deadlines.get(self.urgency, 5)
        deadline = self.created_at + timezone.timedelta(days=deadline_days)
        
        return timezone.now() > deadline and self.status not in ['READY', 'SHIPPED', 'CANCELLED']
