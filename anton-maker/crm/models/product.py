from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Material(models.Model):
    """
    Справочник материалов с типами обработки.
    Используется в калькуляторе для расчета стоимости.
    """
    
    PROCESSING_TYPES = [
        ('engrave', '🖼 Гравировка (см²)'),
        ('cut', '✂️ Резка (м.п.)'),
        ('time', '⏱ Время (мин)'),
        ('deep', '🔨 Глубокая гравировка (см²×мм)'),
    ]
    
    name = models.CharField("Название", max_length=100)
    code = models.CharField("Артикул", max_length=30, unique=True, blank=True)
    processing_type = models.CharField(
        "Тип обработки", 
        max_length=20, 
        choices=PROCESSING_TYPES, 
        default='engrave'
    )
    price_per_unit = models.DecimalField(
        "Цена за единицу (₽)", 
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))], 
        help_text="₽/см², ₽/м или ₽/мин"
    )
    unit = models.CharField("Ед. измерения", max_length=10, default='см²')
    density_g_cm3 = models.DecimalField(
        "Плотность (г/см³)", 
        max_digits=6, 
        decimal_places=3, 
        null=True, 
        blank=True
    )
    max_thickness_mm = models.IntegerField("Макс. толщина (мм)", null=True, blank=True)
    waste_factor = models.DecimalField(
        "Тех. отходы (%)", 
        max_digits=4, 
        decimal_places=1, 
        default=Decimal('5.0'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('50'))]
    )
    complexity_factor = models.DecimalField(
        "Коэф. сложности", 
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('1.0'),
        validators=[MinValueValidator(Decimal('1.0')), MaxValueValidator(Decimal('5.0'))]
    )
    is_active = models.BooleanField("Показывать в калькуляторе", default=True)
    sort_order = models.IntegerField("Порядок сортировки", default=0)
    icon = models.CharField("Иконка (emoji)", max_length=10, default='📦')
    description = models.TextField("Описание материала", blank=True)
    
    class Meta:
        ordering = ['processing_type', 'sort_order', 'name']
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
        indexes = [
            models.Index(fields=['processing_type', 'is_active']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self) -> str:
        return f"{self.icon} {self.name} — {self.price_per_unit} ₽/{self.unit}"
    
    def calculate_price(self, quantity: float, is_urgent: bool = False) -> Decimal:
        """
        Расчет стоимости материала с учетом отходов и срочности.
        
        Args:
            quantity: Количество единиц
            is_urgent: Срочный заказ (+50%)
            
        Returns:
            Стоимость материала
        """
        base_price = self.price_per_unit * Decimal(str(quantity))
        waste_multiplier = Decimal('1') + self.waste_factor / Decimal('100')
        price = base_price * waste_multiplier * self.complexity_factor
        
        if is_urgent:
            price *= Decimal('1.5')
        
        return price.quantize(Decimal('0.01'))


class ServiceOption(models.Model):
    """
    Дополнительные услуги (чекбоксы в калькуляторе).
    """
    
    PRICE_TYPES = [
        ('fixed', 'Фиксированная (₽)'),
        ('percent_base', '% от базовой стоимости'),
        ('percent_total', '% от итоговой суммы'),
    ]
    
    name = models.CharField("Название", max_length=100)
    code = models.CharField("Код", max_length=30, unique=True)
    price_type = models.CharField(
        "Тип цены", 
        max_length=20, 
        choices=PRICE_TYPES, 
        default='fixed'
    )
    price_value = models.DecimalField(
        "Значение", 
        max_digits=8, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0'))]
    )
    icon = models.CharField("Иконка", max_length=10, default='⭐')
    description = models.CharField("Подсказка", max_length=200, blank=True)
    is_active = models.BooleanField("Активно", default=True)
    sort_order = models.IntegerField("Порядок", default=0)
    is_default = models.BooleanField("По умолчанию", default=False)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = "Доп. услуга"
        verbose_name_plural = "Доп. услуги"
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]
    
    def __str__(self) -> str:
        suffix = "₽" if self.price_type == 'fixed' else "%"
        return f"{self.icon} {self.name} (+{self.price_value}{suffix})"
    
    def calculate_price(self, base_price: Decimal, total_price: Decimal) -> Decimal:
        """
        Расчет стоимости дополнительной услуги.
        
        Args:
            base_price: Базовая стоимость заказа
            total_price: Итоговая стоимость на текущий момент
            
        Returns:
            Стоимость услуги
        """
        if self.price_type == 'fixed':
            return self.price_value
        elif self.price_type == 'percent_base':
            return (base_price * self.price_value / Decimal('100')).quantize(Decimal('0.01'))
        elif self.price_type == 'percent_total':
            return (total_price * self.price_value / Decimal('100')).quantize(Decimal('0.01'))
        return Decimal('0')


class CalculatorSettings(models.Model):
    """
    Глобальные настройки калькулятора (одна запись).
    """
    
    min_order_amount = models.DecimalField(
        "Мин. заказ (₽)", 
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('500'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    design_service_price = models.DecimalField(
        "Отрисовка макета (₽)", 
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('500')
    )
    rush_multiplier = models.DecimalField(
        "Наценка срочность", 
        max_digits=4, 
        decimal_places=2, 
        default=Decimal('1.5')
    )
    rotary_multiplier = models.DecimalField(
        "Круговая ось", 
        max_digits=4, 
        decimal_places=2, 
        default=Decimal('1.5')
    )
    margin_percent = models.DecimalField(
        "Наценка (%)", 
        max_digits=5, 
        decimal_places=1, 
        default=Decimal('30.0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    disclaimer = models.TextField(
        "Предупреждение", 
        blank=True,
        default=(
            "* Калькулятор показывает ориентировочную цену. "
            "Точную сумму мастер назовет после просмотра макета."
        )
    )
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    
    class Meta:
        verbose_name = "Настройки калькулятора"
        verbose_name_plural = "Настройки калькулятора"
    
    def __str__(self) -> str:
        return "Основные настройки"
    
    @classmethod
    def get(cls) -> 'CalculatorSettings':
        """Получить или создать настройки по умолчанию."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
