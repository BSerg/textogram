from accounts.models import User, Subscription
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        for i in range(100):
            print i
            user = User.objects.get_or_create(username='user%s' % i)[0]
            user.first_name = 'User %s' % i
            user.save()
            print user

