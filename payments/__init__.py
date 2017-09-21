#! coding: utf-8
from __future__ import unicode_literals

import base64
import hashlib
from collections import defaultdict

import binascii

CURRENCY_RUR = 'RUR'
CURRENCY_EUR = 'EUR'
CURRENCY_USD = 'USD'

CURRENCIES = (
    (CURRENCY_RUR, 'Рубль'),
    (CURRENCY_USD, 'Доллар США'),
    (CURRENCY_EUR, 'Евро')
)


def yandex_get_signature(data, secret):
    return hashlib.md5(';'.join([
        data['action'],
        data['orderSumAmount'],
        data['orderSumCurrencyPaycash'],
        data['orderSumBankPaycash'],
        data['shopId'],
        data['invoiceId'],
        data['customerNumber'],
        secret
    ])).hexdigest().upper()


def walletone_get_signature(data, secret_key):
    icase_key = lambda s: unicode(s).lower()

    lists_by_keys = defaultdict(list)
    for key, value in data:
        lists_by_keys[key].append(value)

    str_buff = b''
    for key in sorted(lists_by_keys, key=icase_key):
        for value in sorted(lists_by_keys[key], key=icase_key):
            str_buff += unicode(value).encode('1251')
    str_buff += secret_key
    md5_string = hashlib.md5(str_buff).digest()
    return base64.b64encode(md5_string)
