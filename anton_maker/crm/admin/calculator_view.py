from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models.inventory import Material


class CalculatorView(LoginRequiredMixin, TemplateView):
    template_name = 'admin/custom_calculator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materials'] = Material.objects.filter(is_active=True)
        return context
