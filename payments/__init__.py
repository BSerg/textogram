#! coding: utf-8
from __future__ import unicode_literals

import hashlib

CURRENCY_RUR = 'RUR'
CURRENCY_EUR = 'EUR'
CURRENCY_USD = 'USD'

CURRENCIES = (
    (CURRENCY_RUR, 'Рубль'),
    (CURRENCY_USD, 'Доллар США'),
    (CURRENCY_EUR, 'Евро')
)


def yandex_get_hash(data, secret):
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
