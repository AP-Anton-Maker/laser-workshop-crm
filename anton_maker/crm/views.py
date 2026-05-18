from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import View
from .models.order import Order
from .bot_logic.webhook_handler import WebhookView as WV

WebhookView = WV


class OrderTicketView(View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return render(request, 'orders/job_ticket.html', {'order': order})
