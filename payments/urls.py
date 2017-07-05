#! coding: utf-8
from __future__ import unicode_literals

from django.conf.urls import url
from django.views.decorators.csrf import ensure_csrf_cookie

from . import views


urlpatterns = [
    url(r'yandex/check-order/', views.YandexCheckoutCheckView.as_view(), name='yandex_check_order'),
    url(r'yandex/payment-aviso/', views.YandexCheckoutPaymentAviso.as_view(), name='yandex_payment_aviso'),
    url(r'walletone/check-order/', ensure_csrf_cookie(views.WalletoneOrderCheck.as_view()), name='walletone_check_order'),
]
