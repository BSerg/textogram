from __future__ import unicode_literals
from articles.cache_utils import update_article_cache, update_feed_cache, generate_search_index, \
    cache_articles_views_count
from accounts.cache_utils import update_user_cache
from redis import StrictRedis
from textogram.settings import REDIS_CACHE_DB, REDIS_CACHE_HOST, REDIS_CACHE_PORT

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Generate redis cache'

    def handle(self, *args, **options):
        r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
        r.flushdb()
        update_article_cache()
        cache_articles_views_count()
        update_feed_cache()
        generate_search_index()
        update_user_cache()
