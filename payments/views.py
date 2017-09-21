#! coding: utf-8

from __future__ import unicode_literals

from datetime import datetime
from decimal import Decimal

from django.http.response import HttpResponse
from django.views import View
from xml.etree.ElementTree import Element, SubElement, tostring

from payments import walletone_get_signature, yandex_get_signature
from payments.models import PayWallOrder
from textogram.settings import WMI_SECRET_KEY, YK_SECRET, YK_SHOP_ID


def get_yandex_kassa_response(action, **kwargs):
    root = Element(action + 'Response')
    for k, v in kwargs.items():
        if isinstance(v, datetime):
            v = v.strftime('%Y-%m-%dT%H:%M:%S.000%z')
        root.set(k, str(v))

    return tostring(root)


class YandexCheckoutCheckView(View):
    def post(self, request):
        data = request.POST.dict()

        common_params = {
            'performedDatetime': datetime.now(),
            'invoiceId': data['invoiceId'],
            'shopId': YK_SHOP_ID,
        }

        if data.get('action') == 'checkOrder':
            md5 = data['md5']

            if md5 != yandex_get_signature(data, YK_SECRET):
                response = get_yandex_kassa_response(
                    data['action'],
                    code=1,
                    message="Ошибка при проверке сигнатуры", **common_params)
                return HttpResponse(response)

            try:
                order = PayWallOrder.objects.get(pk=data.get('orderNumber'))
            except PayWallOrder.DoesNotExist:
                return HttpResponse(get_yandex_kassa_response(
                    data['action'],
                    code=100,
                    message="Заказ не найден", **common_params))
            except ValueError:
                return HttpResponse(get_yandex_kassa_response(
                    data['action'],
                    code=200,
                    message="Неверный формат номера заказа", **common_params))

            if Decimal(data['orderSumAmount']) != order.price:
                return HttpResponse(get_yandex_kassa_response(
                    data['action'],
                    code=100,
                    message="Неверная сумма заказа", **common_params))

            return HttpResponse(get_yandex_kassa_response(code=0, **common_params))

        elif data.get('action') == 'cancelOrder':

            if data['md5'] != yandex_get_signature(data, YK_SECRET):
                response = get_yandex_kassa_response(
                    data['action'],
                    code=1,
                    message="Ошибка при проверке сигнатуры", **common_params)
                return HttpResponse(response)

            try:
                order = PayWallOrder.objects.get(pk=data.get('orderNumber'))
            except PayWallOrder.DoesNotExist:
                return HttpResponse(get_yandex_kassa_response(
                    data['action'],
                    code=200,
                    message="Заказ не найден", **common_params))
            except ValueError:
                return HttpResponse(get_yandex_kassa_response(
                    data['action'],
                    code=200,
                    message="Неверный формат номера заказа", **common_params))

            order.status = PayWallOrder.CANCELED
            order.save()
            return HttpResponse(get_yandex_kassa_response(data['action'], code=0, **common_params))


class YandexCheckoutPaymentAvisoView(View):
    def post(self, request):
        data = request.POST.dict()

        common_params = {
            'performedDatetime': datetime.now(),
            'invoiceId': data['invoiceId'],
            'shopId': YK_SHOP_ID,
        }

        if data.get('action') == 'paymentAviso':
            if data['md5'] != yandex_get_signature(data, YK_SECRET):
                response = get_yandex_kassa_response(
                    data['action'],
                    code=1,
                    message="Неверная сигнатура", **common_params)
                return HttpResponse(response)

            try:
                order = PayWallOrder.objects.get(pk=data.get('orderNumber'))
            except PayWallOrder.DoesNotExist:
                return HttpResponse(get_yandex_kassa_response(
                    data['action'],
                    code=200,
                    message="Заказ не найден", **common_params))
            except ValueError:
                return HttpResponse(get_yandex_kassa_response(
                    data['action'],
                    code=200,
                    message="Неверный формат номера заказа", **common_params))

            if Decimal(data['orderSumAmount']) != order.price:
                return HttpResponse(get_yandex_kassa_response(
                    data['action'],
                    code=200,
                    message="Неверная сумма заказа", **common_params))

            order.status = PayWallOrder.COMPLETED
            order.save()

            return HttpResponse(get_yandex_kassa_response(data['action'], code=0, **common_params))

        else:
            return HttpResponse(get_yandex_kassa_response(
                data['action'],
                code=200,
                message="Неверный код", **common_params))


class WalletoneOrderCheck(View):
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
