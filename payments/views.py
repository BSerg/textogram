#! coding: utf-8

from __future__ import unicode_literals

from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from payments import walletone_get_signature
from payments.models import PayWallOrder
from textogram.settings import WMI_SECRET_KEY


class YandexCheckoutCheckView(View):
    def post(self, request):
        data = request.POST

        if data.get('action') == 'checkOrder':
            md5 = data['md5']

        elif data.get('action') == 'cancelOrder':
            pass


class YandexCheckoutPaymentAviso(View):
    def post(self, request):
        pass


class WalletoneOrderCheck(View):
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        data = request.POST.dict()

        if 'WMI_PAYMENT_NO' not in data:
            return HttpResponse('WMI_RESULT=RETRY&WMI_DESCRIPTION=Отсутсвует номер заказа')

        if 'WMI_SIGNATURE' not in data:
            return HttpResponse('WMI_RESULT=RETRY&WMI_DESCRIPTION=Отсутсвует сигнатура')

        if 'WMI_ORDER_STATE' not in data:
            return HttpResponse('WMI_RESULT=RETRY&WMI_DESCRIPTION=Отсутсвует статус оплаты')

        try:
            order = PayWallOrder.objects.get(pk=data.get('WMI_PAYMENT_NO'))
        except PayWallOrder.DoesNotExist:
            return HttpResponse('WMI_RESULT=RETRY&WMI_DESCRIPTION=Заказ с таким номером не найден')
        except ValueError:
            return HttpResponse('WMI_RESULT=RETRY&WMI_DESCRIPTION=Номер заказа имеет неверный формат')

        signature = data.pop('WMI_SIGNATURE')
        calculated_signature = walletone_get_signature(data.items(), WMI_SECRET_KEY)

        if calculated_signature != signature:
            return HttpResponse('WMI_RESULT=RETRY&WMI_DESCRIPTION=Сигнатура неверна')

        if data.get('WMI_ORDER_STATE') != 'Accepted':
            return HttpResponse('WMI_RESULT=RETRY&WMI_DESCRIPTION=Статус платежа неизвестен')

        order.status = PayWallOrder.COMPLETED
        order.save()

        return HttpResponse('WMI_RESULT=OK')
