"""
Views для CRM приложения.
Калькулятор, webhook, печать ТЗ.
"""

import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.conf import settings

from .models.product import Material, ServiceOption, CalculatorSettings
from .models.order import Order
from .utils.calculator import CostCalculator
from .utils.pdf import generate_job_ticket, generate_multiple_tickets
from .bot_logic.webhook import WebhookView as BotWebhookView


# Экспорт webhook view
WebhookView = BotWebhookView


class PublicCalculatorView(TemplateView):
    """Публичный калькулятор стоимости для клиентов."""
    
    template_name = 'public/calculator.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        materials = Material.objects.filter(is_active=True).order_by('processing_type', 'sort_order')
        service_options = ServiceOption.objects.filter(is_active=True).order_by('sort_order')
        calc_settings = CalculatorSettings.get()
        
        context.update({
            'materials': materials,
            'service_options': service_options,
            'calc_settings': calc_settings,
            'page_title': 'Калькулятор стоимости | Anton Maker',
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """AJAX запрос для расчета стоимости."""
        try:
            data = json.loads(request.body)
            
            material_id = data.get('material_id')
            length_mm = Decimal(str(data.get('length', 0)))
            width_mm = Decimal(str(data.get('width', 0)))
            quantity = int(data.get('quantity', 1))
            is_urgent = data.get('is_urgent', False)
            service_ids = data.get('services', [])
            
            if not material_id or not (length_mm and width_mm):
                return JsonResponse({'error': 'Недостаточно данных'}, status=400)
            
            material = get_object_or_404(Material, pk=material_id, is_active=True)
            
            # Расчет площади в см²
            area_cm2 = float((length_mm * width_mm) / Decimal('100'))
            
            # Получение выбранных услуг
            services = list(ServiceOption.objects.filter(
                id__in=service_ids, 
                is_active=True
            ))
            
            # Расчет
            calculator = CostCalculator(
                material=material,
                area_cm2=area_cm2,
                quantity=quantity,
                is_urgent=is_urgent,
                service_options=services,
            )
            
            breakdown = calculator.get_breakdown()
            
            return JsonResponse({
                'success': True,
                'breakdown': {
                    'material_cost': str(breakdown['material_cost']),
                    'labor_cost': str(breakdown['labor_cost']),
                    'overhead': str(breakdown['overhead']),
                    'defect_reserve': str(breakdown['defect_reserve']),
                    'sebestoimost': str(breakdown['sebestoimost']),
                    'margin': str(breakdown['margin']),
                    'retail_price': str(breakdown['retail_price']),
                    'is_min_order': breakdown['is_min_order'],
                    'min_order_amount': str(breakdown['min_order_amount']),
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(staff_member_required, name='dispatch')
class CalculatorView(TemplateView):
    """Калькулятор в админке для операторов."""
    
    template_name = 'admin/calculator.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        materials = Material.objects.filter(is_active=True).order_by('processing_type', 'sort_order')
        service_options = ServiceOption.objects.filter(is_active=True).order_by('sort_order')
        calc_settings = CalculatorSettings.get()
        
        context.update({
            'materials': materials,
            'service_options': service_options,
            'calc_settings': calc_settings,
            'title': 'Калькулятор стоимости',
        })
        
        return context


class PrintTicketsView(View):
    """View для печати маршрутных листов."""
    
    @method_decorator(staff_member_required)
    def get(self, request, *args, **kwargs):
        order_ids = request.GET.get('ids', '').split(',')
        
        if not order_ids or order_ids == ['']:
            return HttpResponse('Не выбраны заказы', status=400)
        
        orders = Order.objects.filter(id__in=order_ids).order_by('created_at')
        
        if not orders.exists():
            return HttpResponse('Заказы не найдены', status=404)
        
        if orders.count() == 1:
            pdf_content = generate_job_ticket(orders.first())
        else:
            pdf_content = generate_multiple_tickets(list(orders))
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="tickets_{orders.first().order_number}.pdf"'
        
        return response


def error_404(request, exception):
    """Обработчик ошибки 404."""
    return render(request, 'public/404.html', status=404)


def error_500(request):
    """Обработчик ошибки 500."""
    return render(request, 'public/500.html', status=500)
