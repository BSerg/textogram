#!coding: utf-8
from __future__ import unicode_literals

from django.test import TestCase, Client
from rest_framework.test import APIClient

from accounts.models import User
from articles.models import Article
from payments import yandex_get_hash, CURRENCY_RUR, walletone_get_signature
from payments.models import Account, PayWallOrder
from textogram.settings import WMI_SECRET_KEY, WMI_MERCHANT_ID


class PayWallTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='john')
        self.account = Account.objects.get(owner=self.user, currency=CURRENCY_RUR)

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


class WalletOneTestCase(TestCase):
    def setUp(self):
        self.jwt = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzNDU2Nzg5MCIsImZpcnN0X25hbWUiOiJKb2huIiwibGFzdF9uYW1lIjoiV2ljayJ9.EA4z2i0wXsF_jcWn5DMSI9RD4C7Sq4J9HOjxK0NRlxkA3NrrN-yH9tnHgMdLYB1hyb3P0yHO5hQj1PlBAF6IWYJHl85cuwtlm7T4_TTAwo66NIbG7zR5LKes0c6_FbKDvV5_6nXuej9PIitgtW3s55o2LBKSKOmLodO_O5XkPLxr5dADzrVpQKWwqYGwWaswTY-QwdRdwKUQr7SIafKxFyXM5yLiDpDwbFQv4TQAtSYQ7aw-G_3rNuoLCpBbb4wsoddNery1to-IgPwmRw19G3Y-mCtxB9D-uz3DM8z0mGihb7N4RJmSDOHKwZSUIFhtyPwVXccAPzBjmld_eSA1Vw"
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.jwt)
        self.client = Client()

    def test_order_check(self):
        user = User.objects.create(username='john')
        account = Account.objects.get(owner=user, currency=CURRENCY_RUR)

        article = Article.objects.create(title='hello', owner=user, paywall_enabled=True, paywall_price=550)
        customer = User.objects.create(username='customer')
        order = PayWallOrder.objects.create(
            account=account,
            article=article,
            customer=customer,
            price=article.paywall_price,
        )

        order_check_form = {
            'WMI_MERCHANT_ID': WMI_MERCHANT_ID,
            'WMI_PAYMENT_AMOUNT': '250.00',
            'WMI_COMMISSION_AMOUNT': '0.00',
            'WMI_CURRENCY_ID': '643',
            'WMI_ORDER_STATE': 'Accepted',
            'WMI_PAYMENT_NO': str(order.id)
        }
        order_check_form['WMI_SIGNATURE'] = walletone_get_signature(order_check_form.items(), WMI_SECRET_KEY)
        response = self.client.post('/payments/walletone/check-order/', order_check_form)
        self.assertEqual(response.content, 'WMI_RESULT=OK')
