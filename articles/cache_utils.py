#!coding:utf-8
from __future__ import unicode_literals

from redis import StrictRedis
from articles.models import Article
from accounts.models import User, Subscription
from api.v1.articles.serializers import PublicArticleSerializer, PublicArticleSerializerMin
from textogram.settings import USE_REDIS_CACHE, REDIS_CACHE_DB, REDIS_CACHE_HOST, REDIS_CACHE_PORT
import json
import re


MIN_SEARCH_STRING_LENGTH = 3
MAX_SEARCH_STRING_LENGTH = 20


def __set_articles_cache(articles, published_only=True):
    r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
    for article in articles:

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
        elif not published_only:
            r.delete('article:%s:default' % article.slug)
            r.delete('article:%s:preview' % article.slug)
            r.delete('article:%s:full' % article.slug)
            r.zrem('user:%s:articles' % article.owner.id, article.slug)


def update_article_cache(article_id=None):
    params = {'id': article_id} if article_id else {}
    articles = Article.objects.filter(**params)
    __set_articles_cache(articles, published_only=False)


def update_feed_cache(article_id=None):
    params = {'id': article_id} if article_id else {}
    articles = Article.objects.filter(**params)
    r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
    for article in articles:

        subscriptions = Subscription.objects.filter(author=article.owner)
        for sub in subscriptions:
            try:
                score = int(sub.subscribed_at.strftime("%s"))
            except ValueError as e:
                score = 0
            if article.status == Article.PUBLISHED:
                r.zadd('user:%s:feed' % sub.user.username, score, article.slug)
            else:
                r.zrem('user:%s:feed' % sub.user.username, article.slug)


def update_user_article_cache(user_id=None):
    try:
        user = User.objects.get(id=user_id)
        articles = Article.objects.filter(owner=user, status=Article.PUBLISHED)
        __set_articles_cache(articles)
    except User.DoesNotExist:
        pass


def generate_search_index(article_id=None):
    params = {'id': article_id} if article_id else {}
    articles = Article.objects.filter(**params)
    r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
    for article in articles:
        words = article.title.lower().split()

        for word in words:
            if not word or len(word) < MIN_SEARCH_STRING_LENGTH:
                continue
            len_word = len(word)
            search_length = MAX_SEARCH_STRING_LENGTH if MAX_SEARCH_STRING_LENGTH <= len_word else len_word
            for offset in range(0, search_length - MIN_SEARCH_STRING_LENGTH + 1):
                for n in range(offset, search_length + 1):
                    if (n - offset) >= MIN_SEARCH_STRING_LENGTH:
                        q_string = word[offset:n]
                        if article.status == Article.PUBLISHED:
                            r.sadd('q:%s' % q_string, article.slug)
                            r.sadd('article:%s:q' % article.slug, q_string)
                        else:
                            r.srem('q:%s' % q_string, article.slug)


