from django.db import models
from decimal import Decimal
from typing import Optional


class Client(models.Model):
    """
    Модель клиента.
    Хранит информацию о клиентах из ВКонтакте и других источников.
    """
    
    # Идентификаторы
    vk_id = models.BigIntegerField(
        'VK ID',
        unique=True,
        blank=True,
        null=True,
        help_text='ID пользователя ВКонтакте'
    )
    telegram_id = models.BigIntegerField(
        'Telegram ID',
        blank=True,
        null=True,
        help_text='ID пользователя Telegram'
    )
    
    # Контактная информация
    full_name = models.CharField(
        'ФИО',
        max_length=255,
        blank=True,
        help_text='Полное имя клиента'
    )
    phone = models.CharField(
        'Телефон',
        max_length=20,
        blank=True,
        help_text='Номер телефона'
    )
    email = models.EmailField(
        'Email',
        blank=True,
        help_text='Электронная почта'
    )
    
    # Состояние бота
    bot_state = models.CharField(
        'Состояние бота',
        max_length=50,
        default='START',
        choices=[
            ('START', 'Главное меню'),
            ('WAITING_DESC', 'Ожидание описания'),
            ('WAITING_FILE', 'Ожидание файла'),
            ('WAITING_PHONE', 'Ожидание телефона'),
        ],
        help_text='Текущее состояние в диалоге с ботом'
    )
    
    # Финансы
    total_spent = models.DecimalField(
        'Всего потрачено',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Общая сумма всех заказов клиента'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        'Дата регистрации',
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    is_active = models.BooleanField(
        'Активен',
        default=True,
        help_text='Активность клиента'
    )
    notes = models.TextField(
        'Заметки',
        blank=True,
        help_text='Дополнительная информация о клиенте'
    )
    
    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vk_id']),
            models.Index(fields=['telegram_id']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self) -> str:
        if self.full_name:
            return self.full_name
        elif self.vk_id:
            return f'VK User {self.vk_id}'
        elif self.telegram_id:
            return f'TG User {self.telegram_id}'
        return f'Client #{self.id}'
    
    def update_total_spent(self) -> None:
        """Пересчитать общую сумму потраченных средств."""
        from .order import Order
        total = Order.objects.filter(
            client=self,
            status__in=['READY', 'SHIPPED']
        ).aggregate(
            total=models.Sum('final_price')
        )['total'] or Decimal('0.00')
        
        self.total_spent = total
        self.save(update_fields=['total_spent'])
    
    def get_order_count(self) -> int:
        """Получить количество заказов клиента."""
        return self.orders.count()
