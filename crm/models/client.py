from django.db import models

class Client(models.Model):
    vk_id = models.BigIntegerField(unique=True, verbose_name="ID ВКонтакте")
    full_name = models.CharField(max_length=255, verbose_name="ФИО / Никнейм")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Всего потрачено (₽)")
    bot_state = models.CharField(max_length=50, default='START', verbose_name="Состояние бота (State)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} (VK: {self.vk_id})"
