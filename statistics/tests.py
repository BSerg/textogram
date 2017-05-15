from pprint import pprint

import requests
from django.test import TestCase
from unittest import TestCase as UTestCase

from textogram.settings import YANDEX_ACCESS_TOKEN, YANDEX_METRICS_COUNTER_ID


class TestAPI(UTestCase):
    API_URL = 'https://api-metrika.yandex.ru/stat/v1/data?id={counter_id}&oauth_token={token}&limit=1000'

    def setUp(self):
        self.domain_name = 'lentach.media'

    def test_group_by_gender(self):
        url = self.API_URL.format(counter_id=YANDEX_METRICS_COUNTER_ID, token=YANDEX_ACCESS_TOKEN)
        r = requests.get(url, params={
            # 'limit': 2000,
            'date1': '365daysAgo',
            'metrics': 'ym:pv:users',
            'sort': 'ym:pv:URLPath',
            'dimensions': 'ym:pv:URLPath,ym:pv:gender',
            'filters': 'ym:pv:URL=~\'^https?://%(domain)s/articles/\' AND EXISTS(ym:pv:gender==\'female\' OR ym:pv:gender==\'male\')' % {'domain': self.domain_name}
        })
        data = r.json()
        if data.get('errors'):
            for e in data['errors']:
                print e['message']
        else:
            pprint(data)

    def test_group_by_age(self):
        url = self.API_URL.format(counter_id=YANDEX_METRICS_COUNTER_ID, token=YANDEX_ACCESS_TOKEN)
        r = requests.get(url, params={
            # 'limit': 2000,
            'date1': '365daysAgo',
            'metrics': 'ym:pv:users',
            'sort': 'ym:pv:URLPath',
            'dimensions': 'ym:pv:URLPath,ym:pv:ageInterval',
            'filters': 'ym:pv:URL=~\'^https?://%(domain)s/articles/\'' % {'domain': self.domain_name}
        })
        data = r.json()
        pprint(data)
