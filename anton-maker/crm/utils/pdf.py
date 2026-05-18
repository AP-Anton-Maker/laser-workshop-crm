"""
Генерация PDF-маршрутных листов для печати.
Использует WeasyPrint для создания документов.
"""

from io import BytesIO
from pathlib import Path
from decimal import Decimal
from typing import List, Optional
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML, CSS

from ..models.order import Order


def generate_job_ticket(order: Order) -> bytes:
    """
    Генерация маршрутного листа для одного заказа.
    
    Args:
        order: Объект заказа
        
    Returns:
        PDF файл в байтах
    """
    context = {
        'order': order,
        'generated_at': timezone.now(),
        'company_name': 'Anton Maker',
        'company_contact': 'anton-maker.ru',
    }
    
    html_string = render_to_string('orders/ticket.html', context)
    
    pdf_bytes = BytesIO()
    HTML(string=html_string).write_pdf(
        pdf_bytes,
        stylesheets=[CSS(string='''
            @page {
                size: A5 portrait;
                margin: 10mm;
            }
            body {
                font-family: "DejaVu Sans", sans-serif;
                font-size: 10pt;
                line-height: 1.4;
            }
        ''')]
    )
    pdf_bytes.seek(0)
    
    return pdf_bytes.read()


def generate_multiple_tickets(orders: List[Order]) -> bytes:
    """
    Генерация нескольких маршрутных листов на одном листе А4.
    Два листа А5 на странице А4.
    
    Args:
        orders: Список заказов
        
    Returns:
        PDF файл в байтах
    """
    context = {
        'orders': orders,
        'generated_at': timezone.now(),
        'company_name': 'Anton Maker',
        'company_contact': 'anton-maker.ru',
    }
    
    html_string = render_to_string('orders/ticket.html', context)
    
    pdf_bytes = BytesIO()
    HTML(string=html_string).write_pdf(
        pdf_bytes,
        stylesheets=[CSS(string='''
            @page {
                size: A4 portrait;
                margin: 10mm;
            }
            @media print {
                .ticket {
                    page-break-inside: avoid;
                    break-inside: avoid;
                }
            }
            body {
                font-family: "DejaVu Sans", sans-serif;
                font-size: 9pt;
                line-height: 1.3;
            }
        ''')]
    )
    pdf_bytes.seek(0)
    
    return pdf_bytes.read()


def save_ticket_to_file(order: Order, directory: Optional[Path] = None) -> Path:
    """
    Сохранение маршрутного листа в файл.
    
    Args:
        order: Объект заказа
        directory: Директория для сохранения
        
    Returns:
        Путь к сохраненному файлу
    """
    if directory is None:
        from django.conf import settings
        directory = settings.MEDIA_ROOT / 'tickets'
    
    directory.mkdir(parents=True, exist_ok=True)
    
    pdf_content = generate_job_ticket(order)
    
    filename = f"ticket_{order.order_number}.pdf"
    filepath = directory / filename
    
    with open(filepath, 'wb') as f:
        f.write(pdf_content)
    
    return filepath
