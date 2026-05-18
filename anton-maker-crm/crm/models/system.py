from django.db import models


class QuickReply(models.Model):
    """
    Модель быстрых ответов для бота.
    Шаблоны ответов для частых вопросов клиентов.
    """
    
    name = models.CharField(
        'Название',
        max_length=100,
        help_text='Название шаблона'
    )
    keyword = models.CharField(
        'Ключевое слово',
        max_length=50,
        unique=True,
        help_text='Слово для активации ответа'
    )
    message = models.TextField(
        'Сообщение',
        help_text='Текст ответа'
    )
    is_active = models.BooleanField(
        'Активен',
        default=True
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Быстрый ответ'
        verbose_name_plural = 'Быстрые ответы'
        ordering = ['keyword']
    
    def __str__(self) -> str:
        return f'{self.name} ({self.keyword})'


class Notification(models.Model):
    """
    Модель уведомлений.
    Журнал отправленных уведомлений операторам и админам.
    """
    
    NOTIFICATION_TYPES = [
        ('NEW_ORDER', 'Новый заказ'),
        ('LOW_STOCK', 'Низкий остаток'),
        ('ORDER_READY', 'Заказ готов'),
        ('EQUIPMENT_DOWN', 'Простой оборудования'),
        ('QUALITY_ISSUE', 'Проблема с качеством'),
        ('DAILY_REPORT', 'Ежедневный отчет'),
    ]
    
    CHANNEL_CHOICES = [
        ('VK', 'ВКонтакте'),
        ('TELEGRAM', 'Telegram'),
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
    ]
    
    notification_type = models.CharField(
        'Тип уведомления',
        max_length=30,
        choices=NOTIFICATION_TYPES,
        db_index=True,
        help_text='Тип события'
    )
    channel = models.CharField(
        'Канал отправки',
        max_length=20,
        choices=CHANNEL_CHOICES,
        help_text='Куда отправлено'
    )
    recipient_id = models.CharField(
        'Получатель',
        max_length=100,
        help_text='ID получателя (VK ID, Telegram ID, email)'
    )
    message = models.TextField(
        'Сообщение',
        help_text='Текст уведомления'
    )
    is_sent = models.BooleanField(
        'Отправлено',
        default=False,
        help_text='Статус отправки'
    )
    sent_at = models.DateTimeField(
        'Дата отправки',
        null=True,
        blank=True
    )
    error_message = models.TextField(
        'Ошибка',
        blank=True,
        help_text='Текст ошибки при отправке'
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True,
        db_index=True
    )
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification_type', '-created_at']),
            models.Index(fields=['is_sent', '-created_at']),
        ]
    
    def __str__(self) -> str:
        status = '✓' if self.is_sent else '✗'
        return f'{status} {self.get_notification_type_display()} → {self.recipient_id}'
    
    def mark_sent(self) -> None:
        """Отметить как отправленное."""
        from datetime import datetime
        self.is_sent = True
        self.sent_at = datetime.now()
        self.save(update_fields=['is_sent', 'sent_at'])
    
    def mark_failed(self, error: str) -> None:
        """Отметить как неудачное."""
        self.error_message = error
        self.save(update_fields=['error_message'])


class Settings(models.Model):
    """
    Модель системных настроек.
    Хранит глобальные параметры системы.
    """
    
    key = models.CharField(
        'Ключ',
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Уникальный ключ настройки'
    )
    value = models.TextField(
        'Значение',
        blank=True,
        help_text='Значение настройки (JSON или текст)'
    )
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Описание настройки'
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    updated_by = models.CharField(
        'Кем обновлено',
        max_length=100,
        blank=True,
        help_text='Пользователь, изменивший настройку'
    )
    
    class Meta:
        verbose_name = 'Системная настройка'
        verbose_name_plural = 'Системные настройки'
        ordering = ['key']
    
    def __str__(self) -> str:
        return f'{self.key}: {self.value[:50] if self.value else ""}'
    
    @classmethod
    def get_value(cls, key: str, default=None):
        """
        Получить значение настройки по ключу.
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
            
        Returns:
            Значение настройки или default
        """
        setting = cls.objects.filter(key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set_value(cls, key: str, value: str, description: str = '') -> 'Settings':
        """
        Установить значение настройки.
        
        Args:
            key: Ключ настройки
            value: Значение
            description: Описание
            
        Returns:
            Settings: Объект настройки
        """
        setting, _ = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description,
            }
        )
        return setting
