from django.shortcuts import render
from django.contrib.admin.sites import site
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def custom_calculator_view(request):
    """
    Представление для отображения кастомного калькулятора стоимости.
    Рендерит шаблон из templates/admin/custom_calculator.html
    """
    context = site.each_context(request)
    context.update({
        "title": "Калькулятор стоимости",
    })
    return render(request, "admin/custom_calculator.html", context)
