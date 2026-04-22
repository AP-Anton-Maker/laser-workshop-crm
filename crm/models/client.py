from django.db import models

class Client(models.fields.Model):
    vk_id = models.CharField(max_length=50, unique=True, verbose_name="ID ВКонтакте")
    full_name = models.CharField(max_length=200, verbose_name="Имя клиента", blank=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True)
    
    # Система лояльности
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Всего потрачено (руб)")
    cashback_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Баланс кэшбэка")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "1. Клиенты"

    def __str__(self):
        return f"{self.full_name or 'Новый клиент'} (ВК: {self.vk_id})"
