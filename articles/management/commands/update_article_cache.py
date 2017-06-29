from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.cache_utils import update_article_cache


class Command(BaseCommand):
    help = 'Cache article'

    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='?')

    def handle(self, *args, **options):
        update_article_cache(options.get('article_id'))
