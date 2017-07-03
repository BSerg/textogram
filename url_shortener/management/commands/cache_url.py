from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.cache_utils import update_short_url_cache


class Command(BaseCommand):
    help = 'Cache url'

    def add_arguments(self, parser):
        parser.add_argument('article')

    def handle(self, *args, **options):
        update_short_url_cache(options.get('article'))
