import math
from typing import Dict, Any


class SmartCalculator:
    """
    Сервис для расчета стоимости заказов на основе типа услуги и параметров.
    Все расчеты производятся на сервере для исключения подмены цены клиентом.
    """

    @staticmethod
    def calculate(calc_type: str, base_price: float, params: Dict[str, Any]) -> float:
        """
        Главный метод расчета.
        :param calc_type: Тип калькулятора (fixed, area_cm2, meter_thickness и т.д.)
        :param base_price: Базовая цена (ставка за единицу, м2, минуту и т.д.)
        :param params: Словарь параметров от фронтенда (длина, ширина, количество и т.д.)
        :return: Итоговая стоимость (float)
        """
        # Извлекаем количество для расчета оптовой скидки (по умолчанию 1)
        quantity = params.get('quantity', 1)
        if quantity < 1:
            quantity = 1

        final_price = 0.0

        # --- Логика алгоритмов ---

        if calc_type == 'fixed':
            # 1. Штучный товар: base_price * quantity
            final_price = base_price * quantity

        elif calc_type == 'area_cm2':
            # 2. Площадь (см2 -> дм2 для цены): (length/10 * width/10) * base_price
            length = params.get('length', 0)
            width = params.get('width', 0)
            area_dm2 = (length / 10.0) * (width / 10.0)
            final_price = area_dm2 * base_price * quantity

        elif calc_type == 'meter_thickness':
            # 3. Резка фанеры: meters * (base_price * (thickness / 3.0))
            meters = params.get('meters', 0)
            thickness = params.get('thickness', 3) # Дефолт 3мм
            if thickness <= 0: thickness = 3
            price_per_meter = base_price * (thickness / 3.0)
            final_price = meters * price_per_meter * quantity

        elif calc_type == 'per_minute':
            # 4. Долгая гравировка: minutes * base_price
            minutes = params.get('minutes', 0)
            final_price = minutes * base_price * quantity

        elif calc_type == 'per_char':
            # 5. Символы: chars * base_price
            chars = params.get('chars', 0)
            final_price = chars * base_price * quantity

        elif calc_type == 'vector_length':
            # 6. Пром. резка (вектор): length * base_price
            length = params.get('length', 0)
            final_price = length * base_price * quantity

        elif calc_type == 'setup_batch':
            # 7. Тираж с настройкой: setup_price + (base_price * quantity)
            # Здесь base_price - это цена за шт., а setup_price берем из params
            setup_price = params.get('setup_price', 0)
            final_price = setup_price + (base_price * quantity)

        elif calc_type == 'photo_raster':
            # 8. Фото на дереве: area * base_price * dpi_multiplier
            length = params.get('length', 0)
            width = params.get('width', 0)
            dpi = params.get('dpi', 300)
            
            # Коэффициент сложности от DPI (условно: чем выше, тем дороже)
            # Нормализуем: 300 dpi = 1.0, 600 dpi = 1.5 и т.д.
            dpi_multiplier = 1.0 + ((dpi - 300) / 600) if dpi > 300 else 1.0
            
            area_dm2 = (length / 10.0) * (width / 10.0)
            final_price = area_dm2 * base_price * dpi_multiplier * quantity

        elif calc_type == 'cylindrical':
            # 9. Ось/Кружки: (diameter * PI * length/100) * base_price
            # Длина в см, диаметр в см. Результат в см2 площади развертки
            diameter = params.get('diameter', 0)
            length_cm = params.get('length', 0)
            
            area_cm2 = diameter * math.pi * (length_cm / 100.0) # Перевод длины в метры для формулы? 
            # Уточнение по ТЗ: обычно цена за см2 развертки. 
            # Формула из ТЗ: (diameter * 3.14 * length/100). Если length в мм, то /100 даст см.
            # Пусть length в мм, diameter в мм. Тогда площадь в см2.
            # Проверим размерности: мм * мм / 100 = мм2/100 != см2. 
            # Скорее всего в ТЗ имелось в виду: (D мм * PI * L мм) / 100 = площадь в см2 (грубо)
            # Реализуем строго по ТЗ формуле:
            final_price = (diameter * math.pi * (length_cm / 100.0)) * base_price * quantity

        elif calc_type == 'volume_3d':
            # 10. 3D-клише: (length/10 * width/10) * depth * base_price
            length = params.get('length', 0)
            width = params.get('width', 0)
            depth = params.get('depth', 0) # Глубина резьбы
            
            area_dm2 = (length / 10.0) * (width / 10.0)
            final_price = area_dm2 * depth * base_price * quantity

        elif calc_type == 'material_and_cut':
            # 11. Материал + Рез: (area_cost) + (cut_cost)
            # area = (l/10 * w/10) * base_price (base_price здесь цена материала за дм2)
            # cut = cut_meters * base_price (тут нужно разделить базу или передать вторую?)
            # По ТЗ формула: ((length/10 * width/10) * base_price) + (cut_meters * base_price)
            # Значит base_price используется и для материала и для реза (или это сумма двух ставок)
            # Будем считать, что base_price в контексте этого типа - это комбинированная ставка 
            # ИЛИ в params переданы разные ставки. 
            # Строго следуем формуле из ТЗ, используя один base_price для обоих слагаемых:
            length = params.get('length', 0)
            width = params.get('width', 0)
            cut_meters = params.get('cut_meters', 0)
            
            material_cost = (length / 10.0) * (width / 10.0) * base_price
            cut_cost = cut_meters * base_price
            final_price = (material_cost + cut_cost) * quantity

        else:
            # Неизвестный тип калькулятора
            raise ValueError(f"Неизвестный тип калькулятора: {calc_type}")

        # --- Применение оптовых скидок ---
        discount_rate = 0.0
        if quantity >= 100:
            discount_rate = 0.20
        elif quantity >= 50:
            discount_rate = 0.15
        elif quantity >= 20:
            discount_rate = 0.10
        elif quantity >= 10:
            discount_rate = 0.05

        if discount_rate > 0:
            final_price = final_price * (1 - discount_rate)

        return round(final_price, 2)
