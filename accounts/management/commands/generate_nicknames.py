from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    users = User.objects.filter(nickname__isnull=True)
    for u in users:
        u.nickname = 'id%s' % u.id
        u.save()
    print users.count()
