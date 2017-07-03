#!coding:utf-8
from __future__ import unicode_literals

from redis import StrictRedis
from articles.models import Article, ArticleView
from accounts.models import User, Subscription
from url_shortener.models import UrlShort
from api.v1.articles.serializers import PublicArticleSerializer, PublicArticleSerializerMin
from textogram.settings import REDIS_CACHE_DB, REDIS_CACHE_HOST, REDIS_CACHE_PORT, REDIS_CACHE_KEY_PREFIX, IS_LENTACH
import json
from datetime import datetime, timedelta
from django.utils import timezone


MIN_SEARCH_STRING_LENGTH = 3
MAX_SEARCH_STRING_LENGTH = 20
r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)


def __set_articles_cache(articles, published_only=True):
    for article in articles:

        if article.status == Article.PUBLISHED:
            default_serializer = PublicArticleSerializerMin if article.paywall_enabled else PublicArticleSerializer
            r.set('%s:article:%s:default' % (REDIS_CACHE_KEY_PREFIX, article.slug),
                  json.dumps(default_serializer(article).data))
            r.set('%s:article:%s:preview' % (REDIS_CACHE_KEY_PREFIX, article.slug),
                  json.dumps(PublicArticleSerializerMin(article).data))
            if article.paywall_enabled:
                r.set('%s:article:%s:full' % (REDIS_CACHE_KEY_PREFIX, article.slug),
                      json.dumps(PublicArticleSerializer(article).data))
            try:
                score = int(article.published_at.strftime("%s"))
            except (ValueError, AttributeError) as e:
                score = 0
            r.zadd('%s:user:%s:articles' % (REDIS_CACHE_KEY_PREFIX, article.owner.id), score, article.slug)
        elif not published_only:
            r.delete('%s:article:%s:default' % (REDIS_CACHE_KEY_PREFIX, article.slug))
            r.delete('%s:article:%s:preview' % (REDIS_CACHE_KEY_PREFIX, article.slug))
            r.delete('%s:article:%s:full' % (REDIS_CACHE_KEY_PREFIX, article.slug))
            r.zrem('%s:user:%s:articles' % (REDIS_CACHE_KEY_PREFIX, article.owner.id), article.slug)


def update_article_cache(article_id=None):
    params = {'id': article_id} if article_id else {}
    articles = Article.objects.filter(**params)
    __set_articles_cache(articles, published_only=False)


def cache_articles_views_count(article_id=None):
    params = {'status': Article.PUBLISHED}
    if article_id:
        params['id'] = article_id
    for article in Article.objects.filter(**params):
        # views = ArticleView.objects.filter(article=article).count()
        r.set('%s:article:%s:views_count' % (REDIS_CACHE_KEY_PREFIX, article.slug),
              ArticleView.objects.filter(article=article).count())


def update_feed_cache(article_id=None):
    params = {'id': article_id} if article_id else {}
    articles = Article.objects.filter(**params)
    # r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
    for article in articles:

        subscriptions = Subscription.objects.filter(author=article.owner)
        for sub in subscriptions:
            try:
                score = int(article.published_at.strftime("%s"))
            except (ValueError, AttributeError) as e:
                score = 0
            if article.status == Article.PUBLISHED:
                r.zadd('%s:user:%s:feed' % (REDIS_CACHE_KEY_PREFIX, sub.user.username), score, article.slug)
            else:
                r.zrem('%s:user:%s:feed' % (REDIS_CACHE_KEY_PREFIX, sub.user.username), article.slug)


def update_user_feed_cache(user_id, author_id, is_subscribed=False):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    for article in Article.objects.filter(owner__id=author_id, status=Article.PUBLISHED):
        if is_subscribed:
            try:
                score = int(article.published_at.strftime("%s"))
            except (ValueError, AttributeError) as e:
                score = 0
            r.zadd('%s:user:%s:feed' % (REDIS_CACHE_KEY_PREFIX, user.username), score, article.slug)
        else:
            r.zrem('%s:user:%s:feed' % (REDIS_CACHE_KEY_PREFIX, user.username), article.slug)


def update_user_article_cache(user):
    __set_articles_cache(Article.objects.filter(owner=user, status=Article.PUBLISHED))


def generate_search_index(article_id=None):
    params = {'id': article_id} if article_id else {}
    articles = Article.objects.filter(**params)
    # r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
    for article in articles:
        words = article.title.lower().split()
        r.delete('%s:article:%s:words' % (REDIS_CACHE_KEY_PREFIX, article.slug))
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
                            r.sadd('%s:article:%s:words' % (REDIS_CACHE_KEY_PREFIX, article.slug), q_string)
                            r.sadd('%s:q:%s' % (REDIS_CACHE_KEY_PREFIX, q_string), article.slug)
                            r.sadd('%s:article:%s:q' % (REDIS_CACHE_KEY_PREFIX, article.slug), q_string)
                        else:
                            r.srem('%s:q:%s' % (REDIS_CACHE_KEY_PREFIX, q_string), article.slug)


def save_cached_views_to_db(date_start=None, date_finish=None):

    if not date_start or not date_finish:
        now = datetime.now()
        date_start = now - timedelta(hours=1)
        date_finish = now
    score_start = int(date_start.strftime("%s")) * 1000
    score_finish = int(date_finish.strftime("%s")) * 1000
    for article in Article.objects.filter(status=Article.PUBLISHED):
        key = '%s:article:%s:views' % (REDIS_CACHE_KEY_PREFIX, article.slug)
        views = r.zrangebyscore(key, score_start, score_finish)
        for view in views:
            view_list = view.split(':')
            __save_view(article, dict(zip(view_list[::2], view_list[1::2])))
        r.zremrangebyscore(key, score_start, score_finish)


def save_all_cached_views_to_db():
    for article in Article.objects.filter(status=Article.PUBLISHED):
        key = '%s:article:%s:views' % (REDIS_CACHE_KEY_PREFIX, article.slug)
        views = r.zrange(key, 0, -1)
        for view in views:
            view_list = view.split(':')
            __save_view(article, dict(zip(view_list[::2], view_list[1::2])))
        r.delete(key)
        # r.zremrangebyscore(key, score_start, score_finish)


def __save_view(article, data):
    fingerprint = data.get('fp')
    if not fingerprint:
        return
    try:
        date = timezone.make_aware(datetime.fromtimestamp(int(data.get('ts'))/1000), timezone.get_current_timezone())
    except (ValueError, TypeError):
        return
    try:
        monetization_enabled = bool(int(data.get('ads')))
    except (ValueError, TypeError):
        return
    user = User.objects.filter(username=data.get('user')).first()
    try:
        ArticleView.objects.create(article=article, monetization_enabled=monetization_enabled, created_at=date,
                                   user=user, fingerprint=fingerprint)
    except Exception as e:
        return


def update_short_url_cache(url_id=None):
    params = {'id': url_id} if url_id else {}
    for url in UrlShort.objects.filter(**params):
        r.set('%s:s:%s%s' % (REDIS_CACHE_KEY_PREFIX, '!' if not IS_LENTACH else '', url.code),
              url.article.get_full_url() if url.article else url.url)
