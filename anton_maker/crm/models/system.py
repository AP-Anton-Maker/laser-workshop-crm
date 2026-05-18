from django.db import models


class SystemLog(models.Model):
    ACTION_CHOICES = [
        ('ORDER_CREATED', 'Заказ создан'),
        ('ORDER_UPDATED', 'Заказ обновлён'),
        ('ORDER_DONE', 'Заказ завершён'),
        ('STOCK_ALERT', 'Предупреждение о запасах'),
        ('BOT_MESSAGE', 'Сообщение бота'),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name='Действие')
    description = models.TextField(verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время')

    class Meta:
        verbose_name = 'Системный лог'
        verbose_name_plural = 'Системные логи'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_action_display()} - {self.created_at}'


class BotState(models.Model):
    STATE_CHOICES = [
        ('START', 'Начало'),
        ('WAIT_DESC', 'Ожидание описания'),
        ('WAIT_FILE', 'Ожидание файла'),
        ('WAIT_CONFIRM', 'Ожидание подтверждения'),
    ]

    vk_id = models.BigIntegerField(unique=True, verbose_name='VK ID')
    state = models.CharField(max_length=20, default='START', choices=STATE_CHOICES, verbose_name='Состояние')
    temp_data = models.JSONField(default=dict, blank=True, verbose_name='Временные данные')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Состояние бота'
        verbose_name_plural = 'Состояния ботов'

    def __str__(self):
        return f'VK {self.vk_id}: {self.get_state_display()}'
