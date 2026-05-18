from django.db import models
from decimal import Decimal
from typing import List, Dict, Any


class Material(models.Model):
    """
    Модель материала.
    Хранит информацию о материалах для расчета себестоимости.
    """
    
    name = models.CharField(
        'Название',
        max_length=100,
        help_text='Название материала (например, "Сталь 3мм")'
    )
    code = models.CharField(
        'Артикул',
        max_length=50,
        unique=True,
        help_text='Уникальный код материала'
    )
    price_per_unit = models.DecimalField(
        'Цена за единицу',
        max_digits=10,
        decimal_places=2,
        help_text='Цена за единицу измерения'
    )
    unit = models.CharField(
        'Единица измерения',
        max_length=20,
        choices=[
            ('kg', 'Кг'),
            ('m2', 'М²'),
            ('m', 'Метр'),
            ('pcs', 'Шт'),
        ],
        default='kg',
        help_text='Единица измерения материала'
    )
    density = models.DecimalField(
        'Плотность',
        max_digits=8,
        decimal_places=3,
        default=Decimal('7.85'),
        help_text='Плотность в кг/м³ или кг/м²'
    )
    waste_factor = models.DecimalField(
        'Коэффициент отходов (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text='Процент технологических отходов'
    )
    in_stock = models.DecimalField(
        'На складе',
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text='Текущее количество на складе'
    )
    min_stock = models.DecimalField(
        'Минимальный запас',
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text='Точка заказа (минимальный остаток)'
    )
    supplier = models.CharField(
        'Поставщик',
        max_length=255,
        blank=True,
        help_text='Название поставщика'
    )
    is_active = models.BooleanField(
        'Активен',
        default=True
    )
    created_at = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self) -> str:
        return f'{self.name} ({self.code})'
    
    def is_low_stock(self) -> bool:
        """Проверить, ниже ли остаток точки заказа."""
        return self.in_stock < self.min_stock


class Operation(models.Model):
    """
    Модель операции/работы.
    Хранит информацию о технологических операциях.
    """
    
    name = models.CharField(
        'Название',
        max_length=100,
        help_text='Название операции (например, "Лазерная резка")'
    )
    code = models.CharField(
        'Код',
        max_length=50,
        unique=True,
        help_text='Уникальный код операции'
    )
    hourly_rate = models.DecimalField(
        'Ставка в час (руб)',
        max_digits=8,
        decimal_places=2,
        help_text='Стоимость часа работы'
    )
    setup_time_min = models.IntegerField(
        'Время наладки (мин)',
        default=0,
        help_text='Время на наладку оборудования в минутах'
    )
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Подробное описание операции'
    )
    is_active = models.BooleanField(
        'Активна',
        default=True
    )
    created_at = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'
        ordering = ['name']
    
    def __str__(self) -> str:
        return f'{self.name} ({self.hourly_rate} руб/час)'


class Product(models.Model):
    """
    Модель изделия.
    Хранит информацию о продуктах и их параметрах для расчета стоимости.
    """
    
    name = models.CharField(
        'Название',
        max_length=255,
        help_text='Название изделия'
    )
    sku = models.CharField(
        'Артикул',
        max_length=50,
        unique=True,
        help_text='Уникальный артикул изделия'
    )
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Подробное описание'
    )
    
    # Геометрические параметры
    length_mm = models.DecimalField(
        'Длина (мм)',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Длина в миллиметрах'
    )
    width_mm = models.DecimalField(
        'Ширина (мм)',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Ширина в миллиметрах'
    )
    height_mm = models.DecimalField(
        'Толщина/Высота (мм)',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Толщина или высота в миллиметрах'
    )
    shape_factor = models.DecimalField(
        'Коэффициент формы',
        max_digits=5,
        decimal_places=3,
        default=Decimal('1.000'),
        help_text='Коэффициент сложности формы (1.0 - простая)'
    )
    
    # Материал и операции
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name='products',
        null=True,
        blank=True,
        help_text='Основной материал изделия'
    )
    operations = models.ManyToManyField(
        Operation,
        through='ProductOperation',
        related_name='products',
        blank=True,
        help_text='Технологические операции'
    )
    
    # Метаданные
    is_active = models.BooleanField(
        'Активно',
        default=True
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Изделие'
        verbose_name_plural = 'Изделия'
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self) -> str:
        return f'{self.name} ({self.sku})'
    
    def calculate_net_weight_kg(self) -> Decimal:
        """
        Рассчитать чистый вес изделия в килограммах.
        
        Returns:
            Decimal: Вес в кг
        """
        if not self.material:
            return Decimal('0.000')
        
        # Объем в м³ = (длина × ширина × толщина) / 1e9
        volume_m3 = (
            self.length_mm * self.width_mm * self.height_mm
        ) / Decimal('1000000000')
        
        # Вес = объем × плотность
        weight = volume_m3 * self.material.density
        
        return weight.quantize(Decimal('0.001'))
    
    def calculate_material_cost(self, quantity: int = 1) -> Decimal:
        """
        Рассчитать стоимость материала с учетом отходов.
        
        Args:
            quantity: Количество изделий
            
        Returns:
            Decimal: Стоимость материала
        """
        if not self.material:
            return Decimal('0.00')
        
        weight = self.calculate_net_weight_kg()
        waste_multiplier = Decimal('1') + self.material.waste_factor / Decimal('100')
        
        cost = weight * self.material.price_per_unit * waste_multiplier * quantity
        
        return cost.quantize(Decimal('0.01'))


class ProductOperation(models.Model):
    """
    Промежуточная модель связи Изделие-Операция.
    Определяет последовательность и время выполнения операций.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_operations'
    )
    operation = models.ForeignKey(
        Operation,
        on_delete=models.PROTECT,
        related_name='product_operations'
    )
    sequence = models.PositiveIntegerField(
        'Последовательность',
        default=1,
        help_text='Порядок выполнения операции'
    )
    time_per_unit_min = models.DecimalField(
        'Время на ед. (мин)',
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Время выполнения на одно изделие в минутах'
    )
    notes = models.TextField(
        'Примечания',
        blank=True,
        help_text='Дополнительные указания для операции'
    )
    
    class Meta:
        verbose_name = 'Операция изделия'
        verbose_name_plural = 'Операции изделий'
        ordering = ['product', 'sequence']
        unique_together = [['product', 'sequence']]
    
    def __str__(self) -> str:
        return f'{self.product.name} → {self.operation.name} (#{self.sequence})'
