from __future__ import unicode_literals

from django.core.management import call_command

from advertisement.cache_utils import update_advertisements_cache
from articles.cache_utils import update_article_cache, update_feed_cache, generate_search_index, \
    cache_articles_views_count, update_short_url_cache
from accounts.cache_utils import update_user_cache
from redis import StrictRedis

from articles.management.commands import update_article_recommendations
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
        update_short_url_cache()
        update_advertisements_cache()
        call_command('update_article_recommendations')
        call_command('update_article_access_cache')
