"""
Вспомогательные функции валидации.
"""

import re
from django.core.exceptions import ValidationError
from decimal import Decimal


def validate_phone(value: str) -> str:
    """
    Валидация номера телефона.
    
    Args:
        value: Номер телефона
        
    Returns:
        str: Нормализованный номер
        
    Raises:
        ValidationError: Если номер невалиден
    """
    if not value:
        return value
    
    # Удаляем все нецифровые символы кроме +
    cleaned = re.sub(r'[^\d+]', '', value)
    
    # Проверка на наличие хотя бы 10 цифр
    digits = re.sub(r'[^\d]', '', cleaned)
    if len(digits) < 10:
        raise ValidationError('Номер телефона должен содержать минимум 10 цифр')
    
    # Добавляем +7 если номер начинается с 7 или 8 и нет +
    if not cleaned.startswith('+'):
        if digits.startswith('7') and len(digits) == 11:
            cleaned = '+7' + digits[1:]
        elif digits.startswith('8') and len(digits) == 11:
            cleaned = '+7' + digits[1:]
        elif len(digits) == 10:
            cleaned = '+7' + digits
    
    return cleaned


def validate_positive_decimal(value: Decimal, field_name: str = 'Значение') -> None:
    """
    Валидация положительного Decimal.
    
    Args:
        value: Значение для проверки
        field_name: Название поля для сообщения об ошибке
        
    Raises:
        ValidationError: Если значение отрицательное
    """
    if value < 0:
        raise ValidationError(f'{field_name} не может быть отрицательным')


def validate_dimensions(
    length: Decimal,
    width: Decimal,
    height: Decimal,
    max_mm: int = 3000
) -> None:
    """
    Валидация габаритов изделия.
    
    Args:
        length: Длина в мм
        width: Ширина в мм
        height: Высота/толщина в мм
        max_mm: Максимальный размер в мм
        
    Raises:
        ValidationError: Если габариты некорректны
    """
    dimensions = [
        ('Длина', length),
        ('Ширина', width),
        ('Толщина', height),
    ]
    
    for name, value in dimensions:
        if value < 0:
            raise ValidationError(f'{name} не может быть отрицательной')
        
        if value > max_mm:
            raise ValidationError(
                f'{name} превышает максимально допустимый размер ({max_mm} мм)'
            )


def validate_file_extension(filename: str, allowed_extensions: list) -> None:
    """
    Валидация расширения файла.
    
    Args:
        filename: Имя файла
        allowed_extensions: Список разрешенных расширений
        
    Raises:
        ValidationError: Если расширение недопустимо
    """
    if not filename:
        raise ValidationError('Файл не указан')
    
    extension = filename.split('.')[-1].lower()
    
    if extension not in allowed_extensions:
        raise ValidationError(
            f'Недопустимое расширение файла. Разрешены: {", ".join(allowed_extensions)}'
        )


ALLOWED_LAYOUT_EXTENSIONS = ['pdf', 'dxf', 'dwg', 'svg', 'png', 'jpg', 'jpeg', 'ai', 'eps']


def validate_layout_file(file) -> None:
    """
    Валидация файла макета.
    
    Args:
        file: Файловый объект
        
    Raises:
        ValidationError: Если файл некорректен
    """
    if not file:
        raise ValidationError('Файл макета обязателен')
    
    filename = file.name if hasattr(file, 'name') else str(file)
    validate_file_extension(filename, ALLOWED_LAYOUT_EXTENSIONS)
    
    # Проверка размера (максимум 50 МБ)
    max_size = 50 * 1024 * 1024  # 50 MB
    
    try:
        file.seek(0, 2)  # Перемещаемся в конец
        size = file.tell()
        file.seek(0)  # Возвращаемся в начало
        
        if size > max_size:
            raise ValidationError(f'Размер файла не должен превышать 50 МБ')
    except (AttributeError, IOError):
        pass  # Если не можем проверить размер, пропускаем
