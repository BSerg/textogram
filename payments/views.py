#! coding: utf-8

from __future__ import unicode_literals

from datetime import datetime
from decimal import Decimal

import requests
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from xml.etree.ElementTree import Element, SubElement, tostring, fromstring

from django.views.generic.base import TemplateView

from payments import walletone_get_signature, yandex_get_signature
from payments.models import PayWallOrder
from textogram.settings import WMI_SECRET_KEY, YK_SECRET, YK_SHOP_ID


def get_yandex_kassa_response(action, **kwargs):
    root = Element(action + 'Response')
    for k, v in kwargs.items():
        if isinstance(v, datetime):
            v = v.strftime('%Y-%m-%dT%H:%M:%S.000%z')
        root.set(k, unicode(v))

    return tostring(root)


class YandexCheckoutCheckView(View):
    def post(self, request):
        data = request.POST.dict()

        print data

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

            return HttpResponse(get_yandex_kassa_response(data['action'], code=0, **common_params))

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


class YandexCheckoutTestPageView(TemplateView):
    template_name = 'yandex_checkout_test_page.html'

    def post(self, request):
        context = {}

        form_data = request.POST.dict()

        # checkOrder

        check_order_url = request.build_absolute_uri(reverse('yandex_check_order'))
        data = {
            'requestDatetime': timezone.now().strftime('%Y-%m-%dT%H:%M:%S.000%z'),
            'action': 'checkOrder',
            'shopId': YK_SHOP_ID,
            'invoiceId': '__INVOICE__',
            'orderNumber': form_data['orderNumber'],
            'customerNumber': form_data['customerNumber'],
            'orderSumCurrencyPaycash': '643',
            'orderSumBankPaycash': '1001',
            'orderSumAmount': form_data['orderSumAmount'],
            'paymentType': 'AC'
        }

        data['md5'] = yandex_get_signature(data, YK_SECRET)
        check_order_response = requests.post(check_order_url, data)
        check_order_response.encoding = 'utf-8'

        if check_order_response.status_code != 200:
            context['error'] = 'checkOrderResponse status is %d' % check_order_response.status_code
            return self.render_to_response(context)

        response_xml = fromstring(check_order_response.text)

        if response_xml.tag != 'checkOrderResponse':
            return self.render_to_response({'error': 'Wrong response tag'})

        if response_xml.attrib['code'] in ['1', '100', '200']:
            return self.render_to_response({'error': 'checkOrder error: ' + response_xml.attrib['message']})

        # paymentAviso

        payment_aviso_url = request.build_absolute_uri(reverse('yandex_payment_aviso'))
        payment_aviso_data = {
            'requestDatetime': timezone.now().strftime('%Y-%m-%dT%H:%M:%S.000%z'),
            'paymentDatetime': timezone.now().strftime('%Y-%m-%dT%H:%M:%S.000%z'),
            'action': 'paymentAviso',
            'shopId': YK_SHOP_ID,
            'invoiceId': '__INVOICE__',
            'orderNumber': form_data['orderNumber'],
            'customerNumber': form_data['customerNumber'],
            'orderSumCurrencyPaycash': '643',
            'orderSumBankPaycash': '1001',
            'orderSumAmount': form_data['orderSumAmount'],
            'paymentType': 'AC',
            'cps_user_country_code': 'RU'
        }

        payment_aviso_data['md5'] = yandex_get_signature(payment_aviso_data, YK_SECRET)
        payment_aviso_response = requests.post(payment_aviso_url, payment_aviso_data)
        payment_aviso_response.encoding = 'utf-8'

        if payment_aviso_response.status_code != 200:
            context['error'] = 'paymentAvisoResponse status is %d' % payment_aviso_response.status_code
            return self.render_to_response(context)

        response_xml = fromstring(payment_aviso_response.text)

        if response_xml.tag != 'paymentAvisoResponse':
            return self.render_to_response({'error': 'Wrong response tag'})

        if response_xml.attrib['code'] in ['1', '200']:
            return self.render_to_response({'error': 'paymentAvisoOrder error: ' + response_xml.attrib['message']})

        print response_xml.attrib

        return redirect(form_data['shopSuccessURL'])


class WalletoneOrderCheck(View):
    def post(self, request, *args, **kwargs):
        data = request.POST.dict()

        if 'WMI_PAYMENT_NO' not in data:
            return HttpResponse('WMI_RESULT=RETRY&WMI_DESCRIPTION=Отсутствует номер заказа')

        if 'WMI_SIGNATURE' not in data:
            return HttpResponse('WMI_RESULT=RETRY&WMI_DESCRIPTION=Отсутствует сигнатура')

        if 'WMI_ORDER_STATE' not in data:
            return HttpResponse('WMI_RESULT=RETRY&WMI_DESCRIPTION=Отсутствует статус оплаты')

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


class PaymentTestView(View):
    def post(self, request, *args, **kwargs):
        data = request.POST.dict()

        try:
            order = PayWallOrder.objects.get(pk=data.get('orderNumber'))
        except PayWallOrder.DoesNotExist:
            return HttpResponse('FAIL')
        except ValueError:
            return HttpResponse('FAIL')

        order.status = PayWallOrder.COMPLETED
        order.save()

        return HttpResponse('OK')
