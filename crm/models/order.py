import os
from django.db import models
from .client import Client
from .inventory import Material

class Order(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Новое'),
        ('IN_PROGRESS', 'В работе'),
        ('READY', 'Готово'),
        ('CANCELLED', 'Отменено'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders', verbose_name="Клиент")
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Материал")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW', verbose_name="Статус")
    description = models.TextField(blank=True, verbose_name="Описание заказа / ТЗ")
    
    cut_length = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Длина реза (м)")
    layout_file = models.FileField(upload_to='layouts/%Y/%m/', null=True, blank=True, verbose_name="Файл макета")
    
    final_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Итоговая цена (₽)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} от {self.client.full_name} ({self.get_status_display()})"

    def get_layout_filename(self):
        if self.layout_file:
            return os.path.basename(self.layout_file.name)
        return None
