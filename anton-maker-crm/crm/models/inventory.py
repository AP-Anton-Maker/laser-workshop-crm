from django.db import models
from decimal import Decimal
from datetime import datetime


class Inventory(models.Model):
    """
    Модель складских остатков.
    Управляет учетом материалов на складе.
    """
    
    material = models.ForeignKey(
        'crm.Material',
        on_delete=models.CASCADE,
        related_name='inventory_records',
        help_text='Материал'
    )
    quantity = models.DecimalField(
        'Количество',
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text='Текущее количество'
    )
    unit = models.CharField(
        'Единица измерения',
        max_length=20,
        choices=[
            ('kg', 'Кг'),
            ('m2', 'М²'),
            ('m', 'Метр'),
            ('pcs', 'Шт'),
        ],
        default='kg',
        help_text='Единица измерения'
    )
    location = models.CharField(
        'Место хранения',
        max_length=100,
        blank=True,
        help_text='Ячейка/место на складе'
    )
    reserved = models.DecimalField(
        'Зарезервировано',
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text='Количество в резерве под заказы'
    )
    last_checked = models.DateTimeField(
        'Последняя проверка',
        null=True,
        blank=True,
        help_text='Когда последний раз проверяли остаток'
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Складской остаток'
        verbose_name_plural = 'Складские остатки'
        ordering = ['material']
        unique_together = [['material', 'location']]
    
    def __str__(self) -> str:
        return f'{self.material.name}: {self.quantity} {self.unit}'
    
    def get_available_quantity(self) -> Decimal:
        """Получить доступное количество (без резерва)."""
        return self.quantity - self.reserved
    
    def is_low_stock(self) -> bool:
        """Проверить, ниже ли остаток точки заказа."""
        return self.get_available_quantity() < self.material.min_stock


class InventoryTransaction(models.Model):
    """
    Модель движений склада.
    Журнал всех приходных и расходных операций.
    """
    
    TRANSACTION_TYPES = [
        ('IN', 'Приход'),
        ('OUT', 'Расход'),
        ('ADJUSTMENT', 'Корректировка'),
        ('RESERVE', 'Резерв'),
        ('UNRESERVE', 'Снятие резерва'),
    ]
    
    transaction_type = models.CharField(
        'Тип операции',
        max_length=20,
        choices=TRANSACTION_TYPES,
        db_index=True,
        help_text='Тип складской операции'
    )
    material = models.ForeignKey(
        'crm.Material',
        on_delete=models.PROTECT,
        related_name='transactions',
        help_text='Материал'
    )
    quantity = models.DecimalField(
        'Количество',
        max_digits=10,
        decimal_places=3,
        help_text='Количество (положительное для прихода, отрицательное для расхода)'
    )
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.SET_NULL,
        related_name='transactions',
        null=True,
        blank=True,
        help_text='Складская запись'
    )
    order = models.ForeignKey(
        'crm.Order',
        on_delete=models.SET_NULL,
        related_name='inventory_transactions',
        null=True,
        blank=True,
        help_text='Связанный заказ'
    )
    user = models.CharField(
        'Пользователь',
        max_length=100,
        blank=True,
        help_text='Кто выполнил операцию'
    )
    notes = models.TextField(
        'Примечание',
        blank=True,
        help_text='Комментарий к операции'
    )
    created_at = models.DateTimeField(
        'Дата операции',
        auto_now_add=True,
        db_index=True
    )
    
    class Meta:
        verbose_name = 'Движение склада'
        verbose_name_plural = 'Движения склада'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['material', '-created_at']),
        ]
    
    def __str__(self) -> str:
        sign = '+' if self.transaction_type == 'IN' else '-'
        return f'{sign}{self.quantity} {self.material.name} ({self.get_transaction_type_display()})'
    
    def save(self, *args, **kwargs) -> None:
        """Автоматическое обновление остатков при создании транзакции."""
        is_new = not self.pk
        
        super().save(*args, **kwargs)
        
        if is_new and self.inventory:
            # Обновляем остаток
            if self.transaction_type in ['IN', 'UNRESERVE']:
                self.inventory.quantity += abs(self.quantity)
            elif self.transaction_type in ['OUT', 'RESERVE']:
                self.inventory.quantity -= abs(self.quantity)
            
            self.inventory.save(update_fields=['quantity'])
