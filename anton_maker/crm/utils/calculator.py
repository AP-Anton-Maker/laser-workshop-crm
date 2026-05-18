from decimal import Decimal


def calculate_price(length_mm, price_per_unit, min_order=500, markup=1.2):
    """
    Расчет стоимости заказа.
    
    Args:
        length_mm: Длина реза в мм
        price_per_unit: Цена за единицу (мм)
        min_order: Минимальная стоимость заказа
        markup: Наценка
    
    Returns:
        Decimal: Итоговая стоимость
    """
    if not isinstance(price_per_unit, Decimal):
        price_per_unit = Decimal(str(price_per_unit))
    
    base_price = Decimal(str(length_mm)) * price_per_unit
    total = base_price * Decimal(str(markup))
    
    if total < Decimal(str(min_order)):
        total = Decimal(str(min_order))
    
    return total.quantize(Decimal('0.01'))
