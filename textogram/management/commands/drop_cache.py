from __future__ import unicode_literals

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Drop cache'

    def handle(self, *args, **options):
        cache.clear()
        self.stdout.write('Cache was cleaned')


