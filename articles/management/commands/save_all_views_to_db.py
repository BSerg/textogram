from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.cache_utils import save_cached_views_to_db


class Command(BaseCommand):
    help = 'Save all views to db'

    def handle(self, *args, **options):
        save_cached_views_to_db()
