#! coding: utf-8

from __future__ import unicode_literals

import re
from collections import defaultdict
from pprint import pprint

import requests
from django.contrib.sites.models import Site

from articles.models import Article
from statistics.models import ArticleAggregatedStatistics
from textogram.settings import YANDEX_METRICS_COUNTER_ID, YANDEX_ACCESS_TOKEN

API_URL = 'https://api-metrika.yandex.ru/stat/v1/data?id={counter_id}&oauth_token={token}&limit=1000'


def update_aggregated_statistics_by_gender():
    url = API_URL.format(counter_id=YANDEX_METRICS_COUNTER_ID, token=YANDEX_ACCESS_TOKEN)

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
            _data = defaultdict(lambda: {'male': 0, 'female': 0})
            for item in data['data']:
                _data[item['dimensions'][0]['name']][item['dimensions'][1]['id']] += item['metrics'][0]
            for url, gender in _data.items():
                print url, gender
                male_percent = gender['male']/(gender['male'] + gender['female']) if gender['male'] + gender['female'] else None
                slug_re = re.match(r'^/articles/(?P<slug>[\w\-])$', url)
                if slug_re:
                    slug = slug_re.group('slug')
                    ArticleAggregatedStatistics.objects.update_or_create(article__slug=slug, defaults={'male_percent': male_percent})


def update_aggregated_statistics():
    update_aggregated_statistics_by_gender()
