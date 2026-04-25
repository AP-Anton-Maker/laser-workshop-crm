from django.db import models

class Material(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название материала")
    price_per_meter = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена за пог. метр (₽)")
    in_stock = models.BooleanField(default=True, verbose_name="В наличии")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Склад материалов"
        ordering = ['name']

    def __str__(self):
        status = "✓" if self.in_stock else "✗"
        return f"{self.name} — {self.price_per_meter} ₽/м [{status}]"
