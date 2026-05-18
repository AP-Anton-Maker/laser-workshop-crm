"""
Генерация PDF документов (маршрутные листы).
Использует WeasyPrint для рендеринга HTML в PDF.
"""

import os
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML, CSS


def generate_job_ticket_pdf(order, output_path: str) -> str:
    """
    Сгенерировать PDF маршрутного листа для заказа.
    
    Args:
        order: Объект Order
        output_path: Относительный путь для сохранения файла
        
    Returns:
        str: Полный путь к сгенерированному файлу
    """
    # Подготовка контекста
    context = {
        'order': order,
        'client': order.client,
        'product': order.product,
        'operations': [],
    }
    
    # Получаем операции для изделия
    if order.product:
        context['operations'] = list(
            order.product.product_operations
            .select_related('operation')
            .order_by('sequence')
        )
    
    # Рендерим HTML шаблон
    html_string = render_to_string('orders/job_ticket.html', context)
    
    # Создаем директорию если не существует
    full_output_dir = os.path.join(settings.MEDIA_ROOT, 'tickets')
    os.makedirs(full_output_dir, exist_ok=True)
    
    # Полный путь к файлу
    full_output_path = os.path.join(settings.MEDIA_ROOT, output_path)
    
    # Генерируем PDF
    html = HTML(string=html_string, base_url=settings.BASE_DIR)
    
    # Опционально: CSS для печати
    css = CSS(string='''
        @page {
            size: A4;
            margin: 1cm;
        }
        body {
            font-family: "DejaVu Sans", Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.4;
        }
    ''')
    
    html.write_pdf(full_output_path, stylesheets=[css])
    
    return full_output_path
