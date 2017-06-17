from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from redis import StrictRedis
from articles.models import Article
from api.v1.articles.serializers import PublicArticleSerializer, PublicArticleSerializerMin
from textogram.settings import USE_REDIS_CACHE, REDIS_CACHE_DB, REDIS_CACHE_HOST, REDIS_CACHE_PORT
import json


class Command(BaseCommand):
    help = 'Cache article'

    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='+', type=int)

    def handle(self, *args, **options):
        article_id = options['article_id'][0]

        articles = Article.objects.filter() if article_id == 0 else Article.objects.filter(id=article_id)

        r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
        # r2 = StrictRedis(host=REDIS_FEED_CACHE_HOST, port=REDIS_FEED_CACHE_PORT, db=REDIS_FEED_CACHE_DB)

        for article in articles:
            key = 'article:%s:%s' % (article.slug, 'default')
            if article.status == Article.PUBLISHED:
                default_serializer = PublicArticleSerializerMin if article.paywall_enabled else PublicArticleSerializer
                r.set('article:%s:default' % article.slug, json.dumps(default_serializer(article).data))
                r.set('article:%s:preview' % article.slug, json.dumps(PublicArticleSerializerMin(article).data))
                if article.paywall_enabled:
                    r.set('article:%s:full' % article.slug, json.dumps(PublicArticleSerializer(article).data))
                try:
                    score = int(article.published_at.strftime("%s"))
                except ValueError as e:
                    score = 0
                r.zadd('user:%s:articles' % article.owner.id, score, article.slug)
                # r2.zadd('user:%s:articles' % article.owner.id,)
            else:
                r.delete('article:%s:default' % article.slug)
                r.delete('article:%s:preview' % article.slug)
                r.delete('article:%s:full' % article.slug)
                r.zrem('user:%s:articles' % article.owner.id, article.slug)
