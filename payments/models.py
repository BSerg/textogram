#! coding: utf-8
from __future__ import unicode_literals

import uuid

from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from articles.models import ArticleUserAccess
from . import CURRENCIES, CURRENCY_RUR


class Account(models.Model):
    IS_ACTIVE = 1
    DEACTIVATED = 2

    STATUS = (
        (IS_ACTIVE, 'Активно'),
        (DEACTIVATED, 'Неактивно'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey('accounts.User', verbose_name='Владелец', related_name='payment_accounts')
    status = models.PositiveSmallIntegerField('Статус', choices=STATUS, default=IS_ACTIVE)
    balance = models.DecimalField('Баланс', max_digits=10, decimal_places=2, default=0)
    currency = models.CharField('Валюта', max_length=3, choices=CURRENCIES, default=CURRENCY_RUR)

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def recount_balance(self):
        self.balance = self.transactions.all().aggregate(total=Sum('value'))['total']
        self.save()

    def __unicode__(self):
        return 'Аккаунт #%s [%s]' % (str(self.id), self.currency)

    class Meta:
        unique_together = ['owner', 'currency']
        verbose_name = 'Кошелек'
        verbose_name_plural = 'Кошельки'


class Transaction(models.Model):

    ADS = 'ad'
    PAYWALL = 'pw'
    WITHDRAWAL = 'out'

    TYPE = (
        (ADS, 'Реклама'),
        (PAYWALL, 'PayWall'),
        (WITHDRAWAL, 'Вывод'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    account = models.ForeignKey(Account, related_name='transactions')
    type = models.CharField(max_length=20, choices=TYPE, db_index=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        ordering = ['-created_at']


class PayWallTransaction(Transaction):
    order = models.OneToOneField('PayWallOrder', verbose_name='Заказ')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Транзакция PayWall'
        verbose_name_plural = 'Транзакции PayWall'


# PAYWALL

class PayWallOrder(models.Model):

    PROCESSING = 0
    COMPLETED = 1
    CANCELED = 2
    FAILED = 3

    STATUS = (
        (PROCESSING, 'В обработке'),
        (COMPLETED, 'Завершен'),
        (CANCELED, 'Отменен'),
        (FAILED, 'Ошибка'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    account = models.ForeignKey(Account, verbose_name='Аккаунт', related_name='account_paywall_orders')
    article = models.ForeignKey('articles.Article', verbose_name='Статья', related_name='article_paywall_orders')
    customer = models.ForeignKey('accounts.User', verbose_name='Заказчик', related_name='user_paywall_orders')
    status = models.PositiveSmallIntegerField('Статус', choices=STATUS, default=PROCESSING)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return None

    @staticmethod
    def create_new(article, customer):
        try:
            account = Account.objects.get(owner=article.owner, currency=article.paywall_currency)
        except Account.DoesNotExist:
            return None

        order, created = PayWallOrder.objects.get_or_create(
            account=account,
            article=article,
            customer=customer,
            defaults={'price': article.paywall_price}
        )

        return order

    def __unicode__(self):
        return 'Order #%d' % self.id

    class Meta:
        unique_together = ['article', 'customer']
        verbose_name = 'Заказ PayWall'
        verbose_name_plural = 'Заказы PayWall'


@receiver(post_save, sender=PayWallOrder)
def process_article_access(sender, instance, **kwargs):
    if instance.status == PayWallOrder.COMPLETED:
        ArticleUserAccess.objects.get_or_create(order=instance, article=instance.article, user=instance.customer)
    else:
        ArticleUserAccess.objects.filter(order=instance, article=instance.article, user=instance.customer).delete()


@receiver(post_save, sender=PayWallOrder)
def create_transaction(sender, instance, **kwargs):
    if instance.status == PayWallOrder.COMPLETED and not PayWallTransaction.objects.filter(order=instance).exists():
        transaction = PayWallTransaction.objects.create(order=instance, account=instance.account, value=instance.price)


@receiver(post_save, sender=Transaction)
@receiver(post_save, sender=PayWallTransaction)
def update_account_balance(sender, instance, **kwargs):
    account = instance.account
    account.balance += instance.value
    account.save()
