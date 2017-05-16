#! coding: utf-8

from __future__ import unicode_literals

import re
import time
from collections import defaultdict

import requests

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
            _data[item['dimensions'][0]['name']][item['dimensions'][1]['id']] += item['metrics'][0]
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
            _age_id = item['dimensions'][1]['id']
            if _age_id:
                _data[item['dimensions'][0]['name']]['age_%s' % _age_id] += item['metrics'][0]
    return _data


def update_aggregated_statistics(**kwargs):
    data = defaultdict(lambda: {})
    d1 = get_gender_statistics(**kwargs)
    time.sleep(30)
    d2 = get_age_statistics(**kwargs)

    for k, v in d1.items() + d2.items():
        data[k].update(**v)

    for _url, defaults in data.items():
        slug_re = re.match(r'^/articles/(?P<slug>[\w\-])$', _url)
        if slug_re:
            slug = slug_re.group('slug')
            print ArticleAggregatedStatistics.objects.update_or_create(article__slug=slug, defaults=defaults)

