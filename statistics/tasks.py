#! coding: utf-8

from __future__ import unicode_literals

import re
import time
from collections import defaultdict
from datetime import timedelta

import pytz
import requests
from dateutil import relativedelta
from django.db.models import Min, Count, Sum
from django.db.models.functions import TruncDay, TruncHour
from django.utils import timezone

from articles.models import Article, ArticleView
from statistics.models import ArticleAggregatedStatistics, ArticleViewsStatistics
from textogram.settings import YANDEX_METRICS_COUNTER_ID, YANDEX_ACCESS_TOKEN

API_URL = 'https://api-metrika.yandex.ru/stat/v1/data?id={counter_id}&oauth_token={token}'\
    .format(counter_id=YANDEX_METRICS_COUNTER_ID, token=YANDEX_ACCESS_TOKEN)


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
        temp_data[k] = {'male_percent': v['male'] / (v['male'] + v['female']) if v['male'] + v['female'] else None}
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


def task_update_aggregated_statistics(tz_name='Europe/Moscow', **kwargs):
    tz = pytz.timezone(tz_name)
    today_now = timezone.now().astimezone(tz)

    delay = 10
    stats_funcs = [
        get_gender_statistics,
        get_age_statistics,
        get_views_statistics
    ]
    data = defaultdict(lambda: {})
    results = {'total': 0, 'success': 0, 'error': 0}

    for index, func in enumerate(stats_funcs):
        if index > 0:
            time.sleep(delay)
        d = func(**kwargs)

        for k, v in d.items():
            data[k].update(date_to=today_now)
            data[k].update(**v)

    for _url, defaults in data.items():
        results['total'] += 1
        slug_re = re.match(r'^/articles/(?P<slug>[\w\-]+)', _url)
        if slug_re:
            slug = slug_re.group('slug')
            try:
                article = Article.objects.get(slug=slug)
            except Article.DoesNotExist:
                results['error'] += 1
                continue
            try:
                ArticleAggregatedStatistics.objects.update_or_create(article=article, defaults=defaults)
                results['success'] += 1
            except Exception as e:
                results['error'] += 1
        else:
            results['error'] += 1

    return data, results


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


def task_update_article_total_views(article_id, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    today_now = timezone.now().astimezone(tz)
    today_start = today_now.replace(hour=0, minute=0, second=0, microsecond=0)
    this_month_start = today_start.replace(day=1)
    this_month_end = today_start
    prev_month_start = this_month_start - relativedelta.relativedelta(months=1)
    prev_month_end = this_month_start

    today_views = _get_total_article_unique_views_count(article_id, created_at__gte=today_start, created_at__lt=today_now)
    this_month_views = _get_total_article_unique_views_count(article_id, created_at__gte=this_month_start, created_at__lt=this_month_end)
    prev_month_views = _get_total_article_unique_views_count(article_id, created_at__gte=prev_month_start, created_at__lt=prev_month_end)
    total_views = _get_total_article_unique_views_count(article_id)
    defaults = {
        'views': total_views,
        'views_today': today_views,
        'views_month': this_month_views,
        'views_last_month': prev_month_views
    }
    ArticleAggregatedStatistics.objects.update_or_create(article_id=article_id, defaults=defaults)


def get_article_unique_views_by_month(article_id, date_start=None, date_end=None):
    date_end = date_end or timezone.now()
    date_start = date_start or date_end - timedelta(days=30)
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
    date_start = date_start or date_end - timedelta(hours=24)
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


def get_months_ranges(date_start, date_end, include_current=False):
    date_start = date_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    date_end = date_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if include_current:
        date_end += relativedelta.relativedelta(months=1)
    months_ranges = []
    date = date_end
    while date >= date_start:
        month_start = date - relativedelta.relativedelta(months=1)
        months_ranges.insert(0, [month_start, date])
        date = month_start
    return months_ranges


def task_update_article_views_by_intervals(article_id, tz_name='Europe/Moscow', init=False):
    tz = pytz.timezone(tz_name)
    today_now = timezone.now().astimezone(tz)
    today_start = today_now.replace(hour=0, minute=0, second=0, microsecond=0)
    this_month_start = today_start.replace(day=1)
    this_month_end = today_start
    months_ranges = [(this_month_start, this_month_end)]

    if init:
        ArticleViewsStatistics.objects.filter(article_id=article_id).delete()

        first_view = _get_article_views_queryset(article_id).order_by('created_at').first()
        if first_view:
            months_ranges = get_months_ranges(first_view.created_at, this_month_start) + months_ranges

    for _month_start, _month_end in months_ranges:
        _month_views_data = get_article_unique_views_by_month(article_id, _month_start, _month_end)
        if _month_views_data.get('views_data'):
            for day, count in _month_views_data['views_data']:
                views_stat, created = ArticleViewsStatistics.objects.get_or_create(
                    article_id=article_id,
                    type=ArticleViewsStatistics.MONTH,
                    date_start=_month_start,
                    date_end=_month_end,
                    interval_start=day,
                    interval_end=day + timedelta(days=1)
                )
                views_stat.views_count = count
                views_stat.save()

    this_day_views_data = get_article_unique_views_by_day(article_id, today_start, today_now)
    if this_day_views_data.get('views_data'):
        for hour, count in this_day_views_data['views_data']:
            views_stat, created = ArticleViewsStatistics.objects.get_or_create(
                article_id=article_id,
                type=ArticleViewsStatistics.MONTH,
                date_start=today_start,
                date_end=today_now,
                interval_start=hour,
                interval_end=hour + timedelta(hours=1)
            )
            views_stat.views_count = count
            views_stat.save()

