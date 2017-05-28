from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from redis import StrictRedis
from articles.models import Article
from api.v1.articles.serializers import PublicArticleSerializer
from textogram.settings import USE_REDIS_CACHE, REDIS_CACHE_DB, REDIS_CACHE_HOST, REDIS_CACHE_PORT
import json


class Command(BaseCommand):
    help = 'Cache article'

    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='+', type=int)

    def handle(self, *args, **options):
        article_id = options['article_id'][0]

        articles = Article.objects.filter(status=Article.PUBLISHED) if article_id == 0 else \
            Article.objects.filter(id=article_id, status=Article.PUBLISHED)

        r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)

        for article in articles:
            r.set('article:%s' % article.slug, json.dumps(PublicArticleSerializer(article).data))
