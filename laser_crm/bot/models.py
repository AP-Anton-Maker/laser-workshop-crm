from django.db import models

class Client(models.Model):
    vk_id = models.BigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cashback_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_segment = models.CharField(max_length=50, default='new')
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('PROCESSING', 'В работе'),
        ('DONE', 'Готов'),
        ('DELIVERED', 'Выдан'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=200)
    service_type = models.CharField(max_length=50)
    parameters = models.JSONField(default=dict)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.IntegerField(default=0)
    promo_code = models.CharField(max_length=50, blank=True)
    cashback_used = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    planned_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Заказ #{self.id} - {self.client.name}"

class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    item_type = models.CharField(max_length=50)
    quantity = models.FloatField()
    unit = models.CharField(max_length=20, default='шт')
    min_quantity = models.FloatField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.IntegerField()
    max_uses = models.IntegerField(default=100)
    current_uses = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

class CashbackTransaction(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    operation_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    vk_id = models.BigIntegerField()
    message_text = models.TextField()
    is_admin = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class PriceListItem(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    calc_type = models.CharField(max_length=50)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Setting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()

    def __str__(self):
        return self.key

class UserSession(models.Model):
    vk_id = models.BigIntegerField(unique=True)
    state = models.CharField(max_length=50)
    data = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)
