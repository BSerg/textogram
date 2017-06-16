from django.test import TestCase

from accounts.models import User
from articles.models import Article
from payments.models import Account, PayWallOrder, Transaction


class PayWallTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='john')
        self.account = Account.objects.create(owner=self.user)

    def test_order_inc(self):
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