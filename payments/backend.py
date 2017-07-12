#! coding: utf-8

from __future__ import unicode_literals

from collections import defaultdict
from hashlib import md5

import binascii


class BaseCheckoutBackend(object):
    """"""

    def get_payment_form(self, *args, **kwargs):
        raise NotImplementedError

    def validate(self):
        raise NotImplementedError


class YandexCheckout(BaseCheckoutBackend):
    def get_payment_form(self, *args, **kwargs):
        return None


WMI_MERCHANT_ID = '__merchant_id'
WMI_CURRENCY_MAP = {
    'RUR': 643,
    'USD': 840,
    'EUR': 978
}

WMI_SECRET_KEY = 'qwerty'


class WalletOne(BaseCheckoutBackend):

    FORM_URL = 'https://wl.walletone.com/checkout/checkout/Index'

    def get_payment_form(self, *args, **kwargs):
        form = {
            'WMI_MERCHANT_ID': WMI_MERCHANT_ID,
            'WMI_PAYMENT_AMOUNT': kwargs.get('price', 0),
            'WMI_CURRENCY_ID': WMI_CURRENCY_MAP.get(kwargs.get('currency')) or WMI_CURRENCY_MAP['RUR'],
            'WMI_DESCRIPTION': kwargs.get('description', ''),
            'WMI_SUCCESS_URL': kwargs.get('success_url'),
            'WMI_FAIL_URL': kwargs.get('fail_url'),
            'WMI_PAYMENT_NO': kwargs.get('order_number'),
        }

        form['WMI_SIGNATURE'] = self._get_signature(form.items(), WMI_SECRET_KEY)

        return {
            'method': 'post',
            'action': self.FORM_URL,
            'form': form
        }

    def _get_signature(self, params, secret_key):
        """
        Base64(Byte(MD5(Windows1251(Sort(Params) + SecretKey))))
        params - list of tuples [('WMI_CURRENCY_ID', 643), ('WMI_PAYMENT_AMOUNT', 10)]
        """
        icase_key = lambda s: unicode(s).lower()

        lists_by_keys = defaultdict(list)
        for key, value in params:
            lists_by_keys[key].append(value)

        str_buff = ''
        for key in sorted(lists_by_keys, key=icase_key):
            for value in sorted(lists_by_keys[key], key=icase_key):
                str_buff += unicode(value).encode('1251')
        str_buff += secret_key
        md5_string = md5(str_buff).digest()
        return binascii.b2a_base64(md5_string)[:-1]
