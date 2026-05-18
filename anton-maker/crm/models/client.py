from django.db import models
from django.utils import timezone


class Client(models.Model):
    """
    Модель клиента - пользователя ВКонтакте.
    Хранит информацию о клиенте и состояние бота.
    """
    
    BOT_STATES = [
        ('START', '🏠 Главное меню'),
        ('WAITING_DESC', '✍️ Ожидание описания'),
        ('WAITING_FILE', '📎 Ожидание файла'),
        ('CONFIRM_ORDER', '✅ Подтверждение заказа'),
    ]
    
    vk_id = models.BigIntegerField(
        "VK ID", 
        unique=True, 
        db_index=True,
        help_text="Уникальный идентификатор пользователя ВКонтакте"
    )
    first_name = models.CharField("Имя", max_length=100, blank=True)
    last_name = models.CharField("Фамилия", max_length=100, blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    bot_state = models.CharField(
        "Состояние бота", 
        max_length=20, 
        choices=BOT_STATES, 
        default='START'
    )
    total_spent = models.DecimalField(
        "Всего потрачено (₽)", 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Общая сумма всех заказов клиента"
    )
    orders_count = models.PositiveIntegerField(
        "Количество заказов", 
        default=0
    )
    created_at = models.DateTimeField("Дата регистрации", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    last_order_date = models.DateTimeField("Дата последнего заказа", null=True, blank=True)
    notes = models.TextField("Заметки", blank=True)
    is_vip = models.BooleanField("VIP клиент", default=False)
    is_blocked = models.BooleanField("Заблокирован", default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        indexes = [
            models.Index(fields=['vk_id']),
            models.Index(fields=['bot_state']),
            models.Index(fields=['is_vip']),
        ]
    
    def __str__(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return f"{name or f'VK#{self.vk_id}'} (ID: {self.vk_id})"
    
    @property
    def full_name(self) -> str:
        """Полное имя клиента."""
        return f"{self.first_name} {self.last_name}".strip() or f"Пользователь #{self.vk_id}"
    
    def increment_orders(self, amount: float) -> None:
        """Увеличить счетчик заказов и общую сумму."""
        self.orders_count += 1
        self.total_spent += amount
        self.last_order_date = timezone.now()
        self.save(update_fields=['orders_count', 'total_spent', 'last_order_date'])
