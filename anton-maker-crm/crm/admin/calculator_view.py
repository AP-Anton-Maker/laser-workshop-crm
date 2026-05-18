from django.urls import path
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from decimal import Decimal


@staff_member_required
def custom_calculator_view(request):
    """
    View для интерактивного калькулятора стоимости.
    Отображает форму с реальным пересчетом через JavaScript.
    """
    from crm.models import Product, Material
    
    products = Product.objects.filter(is_active=True).select_related('material')
    materials = Material.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'materials': materials,
        'title': 'Калькулятор стоимости',
    }
    
    return render(request, 'admin/custom_calculator.html', context)
