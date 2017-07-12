from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from accounts.models import User
from payments import CURRENCIES
from payments.models import Account


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        created_count = 0
        for user in User.objects.all():
            for currency, name in CURRENCIES:
                account, created = Account.objects.get_or_create(owner=user, currency=currency)
                if created:
                    created_count += 1

        self.stdout.write('Completed. Created %d accounts' % created_count)




