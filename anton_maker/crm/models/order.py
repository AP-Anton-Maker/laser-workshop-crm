from django.db import models
from .client import Client
from .inventory import Material


class Order(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('IN_PROGRESS', 'В работе'),
        ('DONE', 'Готов'),
        ('CANCELLED', 'Отменён'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='Клиент')
    material = models.ForeignKey(
        Material,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Материал'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW',
        verbose_name='Статус'
    )
    description = models.TextField(verbose_name='Описание заказа')
    layout_file = models.ImageField(
        upload_to='layouts/',
        blank=True,
        null=True,
        verbose_name='Файл макета'
    )
    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Расчётная цена'
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Итоговая цена'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата выполнения')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.pk} - {self.client.full_name}'
