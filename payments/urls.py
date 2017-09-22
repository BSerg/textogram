#! coding: utf-8
from __future__ import unicode_literals

from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    url(r'yandex/check-order/', csrf_exempt(views.YandexCheckoutCheckView.as_view()), name='yandex_check_order'),
    url(r'yandex/payment-aviso/', csrf_exempt(views.YandexCheckoutPaymentAvisoView.as_view()), name='yandex_payment_aviso'),
    url(r'yandex/test-page/', csrf_exempt(views.YandexCheckoutTestPageView.as_view()), name='yandex_test_page'),
    url(r'walletone/check-order/', csrf_exempt(views.WalletoneOrderCheck.as_view()), name='walletone_check_order'),
]

