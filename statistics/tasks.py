#! coding: utf-8

from __future__ import unicode_literals

import re
import time
from collections import defaultdict

import requests
from django.db.models import Min

from articles.models import Article, ArticleView
from statistics.models import ArticleAggregatedStatistics
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


def update_aggregated_statistics(**kwargs):
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


def _get_total_article_unique_views_count(article_id):
    auth_user_fingerprints = ArticleView.objects.filter(article_id=article_id, user__isnull=False).values_list('fingerprint', flat=True)

    unique_views = ArticleView.objects\
        .filter(article_id=article_id)\
        .exclude(user__isnull=True, fingerprint__in=auth_user_fingerprints)\
        .order_by('created_at')\
        .extra(select={'unique_user': 'CASE WHEN user_id IS NOT NULL THEN user_id::CHAR ELSE fingerprint END'})\
        .values('unique_user')\
        .annotate(date=Min('created_at'))

    return unique_views.count()


def update_views_statistics(**kwargs):
    for article in Article.objects.all():
        views = _get_total_article_unique_views_count(article.id)
        if views:
            print ArticleAggregatedStatistics.objects.update_or_create(article=article, defaults={'views': views})
