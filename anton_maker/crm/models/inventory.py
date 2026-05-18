from django.db import models


class Material(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за единицу'
    )
    in_stock = models.PositiveIntegerField(default=0, verbose_name='В наличии')
    min_stock_level = models.PositiveIntegerField(
        default=5,
        verbose_name='Минимальный уровень'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.price_per_unit} ₽)'

    @property
    def is_low_stock(self):
        return self.in_stock <= self.min_stock_level


class QuickReply(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название')
    text = models.TextField(verbose_name='Текст ответа')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Быстрый ответ'
        verbose_name_plural = 'Быстрые ответы'

    def __str__(self):
        return self.title
