#!coding: utf-8
from __future__ import unicode_literals

from django.test import TestCase

from accounts.models import User
from articles.models import Article
from payments import yandex_get_hash
from payments.models import Account, PayWallOrder


class PayWallTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='john')
        self.account = Account.objects.create(owner=self.user)

    def test_account_balance(self):
        article = Article.objects.create(title='hello', owner=self.user, paywall_enabled=True, paywall_price=100)
        customer = User.objects.create(username='customer')
        order = PayWallOrder.objects.create(
            account=self.account,
            article=article,
            customer=customer,
            price=article.paywall_price,
        )

        self.assertEqual(self.account.balance, 0)

        order.status = PayWallOrder.COMPLETED
        order.save()

        self.assertEqual(self.account.balance, 100)


class YandexCheckoutTestCase(TestCase):
    def setUp(self):
        self.shopPassword = 's<kY23653f,{9fcnshwq'
        self.payment_form_data = {
            'shopId': '12345',
            'scid': '54321',
            'sum': 123.45,
            'customerNumber': 'Customer#1',
            'orderNumber': 'Order#1',
            'shopSuccessURL': '',
            'shopFailURL': '',
            'cps_email': 'qw@qw.qw',
            'cps_phone': '79123456789',

        }

    def test_md5(self):
        data = {
            'action': 'checkOrder',
            'orderSumAmount': '87.10',
            'orderSumCurrencyPaycash': '643',
            'orderSumBankPaycash': '1001',
            'shopId': '13',
            'invoiceId': '55',
            'customerNumber': '8123294469',
        }
        self.assertEqual(yandex_get_hash(data, self.shopPassword), '1B35ABE38AA54F2931B0C58646FD1321')

    def _test_check_order(self):
        pass

    def _test_payment_aviso(self):
        pass
