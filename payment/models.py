#!coding:utf-8
from __future__ import unicode_literals

import uuid

from django.db import models

from textogram.settings import PAYWALL_CURRENCIES, PAYWALL_CURRENCY_RUR


class PaymentAccount(models.Model):
    IS_ACTIVE = 1
    BLOCKED = 2
    STATUS = (
        ('Активно', IS_ACTIVE),
        ('Заблокировано', BLOCKED),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', verbose_name='Пользователь', related_name='payment_account')
    status = models.PositiveSmallIntegerField('Статус', choices=STATUS, default=IS_ACTIVE)
    default_currency = models.CharField('Валюта', max_length=3, choices=PAYWALL_CURRENCIES, default=PAYWALL_CURRENCY_RUR)

    balance = models.DecimalField('Баланс', max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    class Meta:
        verbose_name = 'Кошелек'
        verbose_name_plural = 'Кошельки'


class Transaction(models.Model):
    class Type:
        ADS = 'advertisement'
        PAYWALL = 'paywall'
        WITHDRAWAL = 'withdrawal'

    class Status:
        PROCESSING = 'processing'
        FINISHED = 'finished'
        CANCELED = 'canceled'

    TYPE = (
        ('Реклама', Type.ADS),
        ('Paywall', Type.PAYWALL),
        ('Вывод', Type.WITHDRAWAL),
    )

    STATUS = (
        ('Обработка', Status.PROCESSING),
        ('Завершено', Status.FINISHED),
        ('Отменено', Status.CANCELED),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_account = models.ForeignKey(PaymentAccount, verbose_name='Кошелек', related_name='transactions')
    type = models.CharField('Тип', max_length=20, choices=TYPE)
    value = models.DecimalField('Сумма', max_length=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.id

    class Meta:
        ordering = ['-created_at']


class PaywallTransaction(Transaction):
    customer = models.ForeignKey('accounts.User', verbose_name='Плательщик')
    order = models.ForeignKey('PaywallOrder', verbose_name='Заказ')

    def __init__(self, *args, **kwargs):
        super(PaywallTransaction, self).__init__(*args, **kwargs)
        self._meta.get_field('type').default = Transaction.Type.PAYWALL


class PaywallOrder(models.Model):
    pass