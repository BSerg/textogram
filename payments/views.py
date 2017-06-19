#! coding: utf-8

from __future__ import unicode_literals

from django.views import View


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