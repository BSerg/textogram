#! coding: utf-8

from __future__ import unicode_literals

from collections import defaultdict
from datetime import timedelta

import re
import requests
from dateutil import relativedelta
from django.db.models import Min, Count, Sum
from django.db.models.functions import TruncDay, TruncHour
from django.utils import timezone
from redis import StrictRedis

from accounts.models import User
from articles.models import Article, ArticleView
from statistics.utils import get_article_views_by_day, get_article_views_today, get_yandex_age_statistics, \
    get_yandex_gender_statistics, get_yandex_views_statistics, get_article_views_month, get_article_views_prev_month, \
    get_article_views_total, get_author_views_today, get_author_views_month, get_author_views_prev_month, \
    get_author_views_total
from textogram.settings import YANDEX_METRICS_COUNTER_ID, YANDEX_ACCESS_TOKEN, REDIS_CACHE_HOST, REDIS_CACHE_PORT, \
    REDIS_CACHE_DB, REDIS_CACHE_KEY_PREFIX

API_URL = 'https://api-metrika.yandex.ru/stat/v1/data?id={counter_id}&oauth_token={token}'\
    .format(counter_id=YANDEX_METRICS_COUNTER_ID, token=YANDEX_ACCESS_TOKEN)

r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)


def _request_yandex_metrics(metrics, dimensions, filters=None, sort=None, date_from='365daysAgo', date_to='today', limit=10000, offset=1):
    params = {
        'limit': limit,
        'offset': offset,
        'date1': date_from,
        'date2': date_to,
        'metrics': metrics,
        'dimensions': dimensions,
    }
    if filters:
        params.update(filters=filters)
    if sort:
        params.update(sort=sort)

    r = requests.get(API_URL, params=params)

    if r.status_code == 200:
        data = r.json()
        if data.get('data'):
            return True, data['data']
    return False, r


def get_gender_statistics(**kwargs):
    _data = defaultdict(lambda: {'male': 0, 'female': 0})
    success, data = _request_yandex_metrics(
        'ym:pv:users',
        'ym:pv:URLPath,ym:pv:gender',
        sort='ym:pv:URLPath',
        filters="ym:pv:URLPath=~'^/articles/' AND EXISTS(ym:pv:gender=='female' OR ym:pv:gender=='male')",
        **kwargs
    )
    if success:
        for item in data:
            key_re = re.match(r'/articles/[\w\-]+', item['dimensions'][0]['name'])
            if key_re:
                key = key_re.group()
                _data[key][item['dimensions'][1]['id']] += item['metrics'][0]
    temp_data = defaultdict(lambda: {'male_percent': None})
    for k, v in _data.items():
        temp_data[k] = {'male_percent': v['male'] / (v['male'] + v['female']) if (v['male'] + v['female']) else None}
    return temp_data


def get_age_statistics(**kwargs):
    _data = defaultdict(lambda: {'age_17': 0, 'age_18': 0, 'age_25': 0, 'age_35': 0, 'age_45': 0})

    success, data = _request_yandex_metrics(
        'ym:pv:users',
        'ym:pv:URLPath,ym:pv:ageInterval',
        sort='ym:pv:URLPath',
        filters="ym:pv:URLPath=~'^/articles/'",
        **kwargs
    )

    if success:
        for item in data:
            key_re = re.match(r'/articles/[\w\-]+', item['dimensions'][0]['name'])
            if key_re:
                key = key_re.group()
                _age_id = item['dimensions'][1]['id']
                if _age_id:
                    _data[key]['age_%s' % _age_id] += item['metrics'][0]
    temp_data = defaultdict(lambda: {'age_17': 0, 'age_18': 0, 'age_25': 0, 'age_35': 0, 'age_45': 0})
    for k, v in _data.items():
        _sum = sum([i for i in v.values() if i])
        if _sum:
            for _k, _v in v.items():
                temp_data[k][_k] = float(_v) / _sum
    _data.update(**temp_data)
    return _data


def get_views_statistics(**kwargs):
    _data = defaultdict(lambda: {'views_yandex': 0})
    success, data = _request_yandex_metrics(
        'ym:pv:users',
        'ym:pv:URLPath',
        filters="ym:pv:URLPath=~'^/articles/'",
        **kwargs
    )

    if success:
        for item in data:
            key_re = re.match(r'/articles/[\w\-]+', item['dimensions'][0]['name'])
            if key_re:
                key = key_re.group()
                _data[key]['views_yandex'] += item['metrics'][0]

    return _data


def _get_article_views_queryset(article_id, **kwargs):
    auth_user_fingerprints = ArticleView.objects.filter(article_id=article_id, user__isnull=False).values_list(
        'fingerprint', flat=True)

    return ArticleView.objects \
        .filter(article_id=article_id, **kwargs) \
        .exclude(user__isnull=True, fingerprint__in=auth_user_fingerprints)


def _get_total_article_unique_views(article_id, **kwargs):
    return _get_article_views_queryset(article_id, **kwargs) \
        .order_by('created_at') \
        .extra(select={'unique_user': 'CASE WHEN user_id IS NOT NULL THEN user_id::CHAR ELSE fingerprint END', 'time_interval': "DATE_TRUNC('day', date)"}) \
        .values('unique_user') \
        .annotate(date=Min('created_at'))


def _get_total_article_unique_views_count(article_id, **kwargs):
    unique_views = _get_total_article_unique_views(article_id, **kwargs)
    return unique_views.count()


def get_article_unique_views_by_month(article_id, date_start=None, date_end=None):
    date_end = date_end or timezone.now()
    date_start = date_start or (date_end - relativedelta.relativedelta(months=1))
    views_by_days = _get_article_views_queryset(article_id, created_at__gte=date_start, created_at__lt=date_end)\
        .extra(select={'unique_user': 'CASE WHEN user_id IS NOT NULL THEN user_id::CHAR ELSE fingerprint END'}) \
        .values('unique_user') \
        .annotate(day=TruncDay('created_at')) \
        .values('day') \
        .annotate(count=Count('id')) \
        .order_by('day')
    return {
        'article_id': article_id,
        'date_from': date_start,
        'date_to': date_end,
        'total_views': views_by_days.aggregate(total=Sum('count'))['total'],
        'views_data': views_by_days.values_list('day', 'count')
    }


def get_article_unique_views_by_day(article_id, date_start=None, date_end=None):
    date_end = date_end or timezone.now()
    date_start = date_start or date_end - timedelta(days=1)
    views_by_days = _get_article_views_queryset(article_id, created_at__gte=date_start, created_at__lt=date_end)\
        .extra(select={'unique_user': 'CASE WHEN user_id IS NOT NULL THEN user_id::CHAR ELSE fingerprint END'}) \
        .values('unique_user') \
        .annotate(hour=TruncHour('created_at'))\
        .values('hour')\
        .annotate(count=Count('id'))
    return {
        'article_id': article_id,
        'date_from': date_start,
        'date_to': date_end,
        'total_views': views_by_days.aggregate(total=Sum('count'))['total'],
        'views_data': views_by_days.values_list('hour', 'count')
    }


def get_months_ranges(date_start, date_end, include_last=False):
    date_start = date_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    date_end = date_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if include_last:
        date_end += relativedelta.relativedelta(months=1)
    months_ranges = []
    date = date_end
    while date >= date_start:
        month_start = date - relativedelta.relativedelta(months=1)
        months_ranges.insert(0, [month_start, date])
        date = month_start
    return months_ranges


def task_cache_article_views_by_day(article_id):
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        return
    data = get_article_views_by_day(article_id)
    key = '%s:article:%s:statistics:views' % (REDIS_CACHE_KEY_PREFIX, article.slug)
    for timestamp, views in data:
        value = '%d:%d' % (timestamp, views)
        r.zadd(key, timestamp, value)


def task_cache_article_views_today(article_id):
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        return

    timestamp, views = get_article_views_today(article_id)
    key = '%s:article:%s:statistics:views' % (REDIS_CACHE_KEY_PREFIX, article.slug)
    r.zremrangebyscore(key, timestamp, 'inf')
    r.zadd(key, timestamp, '%d:%d' % (timestamp, views))


def task_cache_article_views_common(article_id):
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        return

    _, views_today = get_article_views_today(article_id)
    _, views_month = get_article_views_month(article_id)
    _, views_prev_month = get_article_views_prev_month(article_id)
    _, views_total = get_article_views_total(article_id)

    key = '%s:article:%s:statistics:common' % (REDIS_CACHE_KEY_PREFIX, article.slug)
    r.hmset(key, {
        'views_today': views_today,
        'views_month': views_month,
        'views_prev_month': views_prev_month,
        'views_total': views_total
    })


def task_cache_articles_yandex_age_statistics():
    data = get_yandex_age_statistics()
    for slug, _data in data.items():
        try:
            article = Article.objects.get(slug=slug)
        except Article.DoesNotExist:
            continue
        key = '%s:article:%s:statistics:common' % (REDIS_CACHE_KEY_PREFIX, article.slug)
        r.hmset(key, _data)


def task_cache_articles_yandex_gender_statistics():
    data = get_yandex_gender_statistics()
    for slug, _data in data.items():
        try:
            article = Article.objects.get(slug=slug)
        except Article.DoesNotExist:
            continue
        key = '%s:article:%s:statistics:common' % (REDIS_CACHE_KEY_PREFIX, article.slug)
        r.hmset(key, _data)


def task_cache_articles_yandex_views_statistics():
    data = get_yandex_views_statistics()
    for slug, _data in data.items():
        try:
            article = Article.objects.get(slug=slug)
        except Article.DoesNotExist:
            continue
        key = '%s:article:%s:statistics:common' % (REDIS_CACHE_KEY_PREFIX, article.slug)
        r.hmset(key, _data)


def task_cache_author_views_common(user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    _, views_today = get_author_views_today(user_id)
    _, views_month = get_author_views_month(user_id)
    _, views_prev_month = get_author_views_prev_month(user_id)
    _, views_total = get_author_views_total(user_id)

    key = '%s:author:%s:statistics:views' % (REDIS_CACHE_KEY_PREFIX, user.id)
    r.hmset(key, {
        'views_today': views_today,
        'views_month': views_month,
        'views_prev_month': views_prev_month,
        'views_total': views_total
    })