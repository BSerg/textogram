from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.cache_utils import generate_search_index


class Command(BaseCommand):
    help = 'Articles search index'

    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='?')

    def handle(self, *args, **options):
        try:
            article_id = options['article_id'][0]
        except (TypeError, IndexError):
            article_id = None
        generate_search_index(article_id)
