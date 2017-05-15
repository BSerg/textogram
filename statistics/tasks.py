#! coding: utf-8

from __future__ import unicode_literals

import re
from collections import defaultdict
from pprint import pprint

import requests
import time
from django.contrib.sites.models import Site

from articles.models import Article
from statistics.models import ArticleAggregatedStatistics
from textogram.settings import YANDEX_METRICS_COUNTER_ID, YANDEX_ACCESS_TOKEN

API_URL = 'https://api-metrika.yandex.ru/stat/v1/data?id={counter_id}&oauth_token={token}&limit=1000'


def update_aggregated_statistics():
    url = API_URL.format(counter_id=YANDEX_METRICS_COUNTER_ID, token=YANDEX_ACCESS_TOKEN)
    _data = defaultdict(lambda: {'male': 0, 'female': 0, 'age_17': 0, 'age_18': 0, 'age_25': 0, 'age_35': 0, 'age_45': 0})

    print 'Gender statistics processing...'
    r = requests.get(url, params={
        # 'limit': 2000,
        'date1': '365daysAgo',
        'metrics': 'ym:pv:users',
        'sort': 'ym:pv:URLPath',
        'dimensions': 'ym:pv:URLPath,ym:pv:gender',
        'filters': "ym:pv:URLPath=~'^/articles/' AND EXISTS(ym:pv:gender=='female' OR ym:pv:gender=='male')"
    })
    if r.status_code == 200:
        data = r.json()
        if data.get('data'):
            for item in data['data']:
                _data[item['dimensions'][0]['name']][item['dimensions'][1]['id']] += item['metrics'][0]

    time.sleep(30)

    print 'Age statistics processing...'
    r = requests.get(url, params={
        'date1': '365daysAgo',
        'metrics': 'ym:pv:users',
        'sort': 'ym:pv:URLPath',
        'dimensions': 'ym:pv:URLPath,ym:pv:ageInterval',
        'filters': "ym:pv:URLPath=~'^/articles/'"
    })
    if r.status_code == 200:
        data = r.json()
        pprint(data)
        for item in data['data']:
            _age_id = item['dimensions'][1]['id']
            if _age_id:
                _data[item['dimensions'][0]['name']]['age_%s' % _age_id] += item['metrics'][0]

    for _url, d in _data.items():
        _d = {k: v for k, v in d.items() if k not in ['male', 'female']}
        defaults = {'male_percent': d['male'] / (d['male'] + d['female']) if d['male'] + d['female'] else None}
        defaults.update(**_d)
        slug_re = re.match(r'^/articles/(?P<slug>[\w\-])$', _url)
        if slug_re:
            slug = slug_re.group('slug')
            ArticleAggregatedStatistics.objects.update_or_create(article__slug=slug, defaults=defaults)

    pprint(_data)
