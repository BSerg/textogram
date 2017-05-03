#!coding:utf-8
from __future__ import unicode_literals

import uuid

from django.db import models

from payment import generate_paywall_order_number
from textogram.settings import PAYWALL_CURRENCIES, PAYWALL_CURRENCY_RUR


class PaymentAccount(models.Model):
    IS_ACTIVE = 1
    BLOCKED = 2

    STATUS = (
        (IS_ACTIVE, 'Активно'),
        (BLOCKED, 'Заблокировано'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', verbose_name='Пользователь', related_name='payment_accounts')
    status = models.PositiveSmallIntegerField('Статус', choices=STATUS, default=IS_ACTIVE)
    currency = models.CharField('Валюта', max_length=3, choices=PAYWALL_CURRENCIES, default=PAYWALL_CURRENCY_RUR)
    balance = models.DecimalField('Баланс', max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'Кошелек #%s [%s]' % (self.id, self.currency)

    class Meta:
        unique_together = ['user', 'currency']
        verbose_name = 'Кошелек'
        verbose_name_plural = 'Кошельки'


class PaywallOrder(models.Model):
    PROCESSING = 0
    COMPLETED = 1
    CANCELED = 2

    STATUS = (
        (PROCESSING, 'В обработке'),
        (COMPLETED, 'Завершен'),
        (CANCELED, 'Отменен'),
    )

    uid = models.CharField('Номер заказа', max_length=8, default=generate_paywall_order_number, unique=True)
    article = models.ForeignKey('articles.Article', verbose_name='Статья', related_name='paywall_orders')
    customer = models.ForeignKey('accounts.User', verbose_name='Плательщик')
    status = models.PositiveSmallIntegerField('Статус', choices=STATUS, default=PROCESSING)
    price_cached = models.DecimalField('Цена', max_length=10, decimal_places=2, default=0)
    currency = models.CharField('Валюта', max_length=3, choices=PAYWALL_CURRENCIES,
                                default=PAYWALL_CURRENCY_RUR, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return 'Order #%d' % self.id

    class Meta:
        verbose_name = 'Заказ Paywall'
        verbose_name_plural = 'Заказы Paywall'


# Transactions

class Transaction(models.Model):
    ADS = 'advertisement'
    PAYWALL = 'paywall'
    WITHDRAWAL = 'withdrawal'

    TYPE = (
        (ADS, 'Реклама'),
        (PAYWALL, 'Paywall'),
        (WITHDRAWAL, 'Вывод'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_account = models.ForeignKey(PaymentAccount, verbose_name='Кошелек', related_name='transactions')
    type = models.CharField('Тип', max_length=20, choices=TYPE)
    value = models.DecimalField('Сумма', max_length=10, decimal_places=2)
    currency = models.CharField('Валюта', max_length=3, choices=PAYWALL_CURRENCIES,
                                default=PAYWALL_CURRENCY_RUR, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.id

    class Meta:
        ordering = ['-created_at']


class PaywallTransaction(Transaction):
    order = models.ForeignKey('PaywallOrder', verbose_name='Заказ')

    def __init__(self, *args, **kwargs):
        super(PaywallTransaction, self).__init__(*args, **kwargs)
        self._meta.get_field('type').default = Transaction.PAYWALL


class AdTransaction(Transaction):
    def __init__(self, *args, **kwargs):
        super(AdTransaction, self).__init__(*args, **kwargs)
        self._meta.get_field('type').default = Transaction.ADS


class WithdrawalTransaction(Transaction):
    def __init__(self, *args, **kwargs):
        super(WithdrawalTransaction, self).__init__(*args, **kwargs)
        self._meta.get_field('type').default = Transaction.WITHDRAWAL


# End transactions


