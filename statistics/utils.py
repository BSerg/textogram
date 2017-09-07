#! coding: utf-8

import time
from collections import defaultdict

import pytz
import re
import requests
from dateutil import relativedelta
from django.db import connection
from django.utils import timezone

from articles.models import ArticleView
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


def get_yandex_gender_statistics(**kwargs):
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
            key_re = re.match(r'/articles/(?P<slug>[\w\-]+)', item['dimensions'][0]['name'])
            if key_re:
                key = key_re.group('slug')
                print key, item['dimensions'][0]['name']
                _data[key][item['dimensions'][1]['id']] += item['metrics'][0]
    temp_data = defaultdict(lambda: {'male_percent': None})
    for k, v in _data.items():
        temp_data[k] = {'male_percent': v['male'] / (v['male'] + v['female']) if (v['male'] + v['female']) else None}
    return temp_data


def get_yandex_age_statistics(**kwargs):
    _data = temp_data = defaultdict(lambda: {'age_17': 0, 'age_18': 0, 'age_25': 0, 'age_35': 0, 'age_45': 0, 'age_55': 0})

    success, data = _request_yandex_metrics(
        'ym:pv:users',
        'ym:pv:URLPath,ym:pv:ageInterval',
        sort='ym:pv:URLPath',
        filters="ym:pv:URLPath=~'^/articles/'",
        **kwargs
    )

    if success:
        for item in data:
            key_re = re.match(r'/articles/(?P<slug>[\w\-]+)', item['dimensions'][0]['name'])
            if key_re:
                key = key_re.group('slug')
                _age_id = item['dimensions'][1]['id']
                if _age_id:
                    _data[key]['age_%s' % _age_id] += item['metrics'][0]
    for k, v in _data.items():
        _sum = sum([i for i in v.values() if i])
        if _sum:
            for _k, _v in v.items():
                temp_data[k][_k] = float(_v) / _sum
    _data.update(**temp_data)
    return _data


def get_yandex_views_statistics(**kwargs):
    _data = defaultdict(lambda: {'yandex_views': 0, 'yandex_unique_views': 0})
    success, data = _request_yandex_metrics(
        'ym:pv:users,ym:pv:pageviews',
        'ym:pv:URLPath',
        filters="ym:pv:URLPath=~'^/articles/'",
        **kwargs
    )

    if success:
        for item in data:
            key_re = re.match(r'/articles/(?P<slug>[\w\-]+)', item['dimensions'][0]['name'])
            if key_re:
                key = key_re.group('slug')
                _data[key]['yandex_unique_views'] += item['metrics'][0]
                _data[key]['yandex_views'] += item['metrics'][1]

    return _data


def _get_article_views_sum(article_id, date_from=None, date_to=None, timezone="+03"):
    cursor = connection.cursor()

    sql_params = {'article_id': article_id, 'timezone': timezone, 'where_date_from': '', 'where_date_to': ''}

    if date_from:
        sql_params['where_date_from'] = "AND created_at >= '%(date_from)s'::DATE AT TIME ZONE '%(timezone)s'" % {'date_from': date_from.strftime('%Y-%m-%d'), 'timezone': timezone}

    if date_to:
        sql_params['where_date_to'] = "AND created_at < '%(date_to)s'::DATE AT TIME ZONE '%(timezone)s'" % {'date_to': date_to.strftime('%Y-%m-%d'), 'timezone': timezone}

    raw_sql = """
        SELECT sum(c)
        FROM (
          SELECT
            date_trunc('day', created_at at time zone '%(timezone)s') AS "day",
            count(DISTINCT CASE WHEN user_id IS NOT NULL THEN user_id::CHAR ELSE fingerprint END) AS "c"
          FROM articles_articleview
          WHERE article_id = %(article_id)s %(where_date_from)s %(where_date_to)s
          GROUP BY day
        ) AS counts    
        """ % sql_params

    cursor.execute(raw_sql)
    return cursor.fetchone()[0] or 0


def get_article_views_by_day(article_id, tz='+03'):
    cursor = connection.cursor()

    raw_sql = """
    SELECT
      date_trunc('day', created_at at time zone '%s') AS "day",
      count(DISTINCT CASE WHEN user_id IS NOT NULL THEN user_id::CHAR ELSE fingerprint END)
    FROM articles_articleview
    WHERE article_id = %s
    GROUP BY day
    ORDER BY day ASC 
    """ % (tz, article_id)

    cursor.execute(raw_sql)
    result = [(time.mktime(i[0].timetuple()), i[1]) for i in cursor.fetchall()]

    return result


def get_article_views_today(article_id, date=timezone.now(), tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    today_start = date.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + relativedelta.relativedelta(days=1)
    views_count = _get_article_views_sum(article_id, today_start, tomorrow_start)
    return time.mktime(today_start.timetuple()), views_count


def get_article_views_month(article_id, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    today_start = timezone.now().astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)
    views_count = _get_article_views_sum(article_id, month_start, today_start)
    return time.mktime(month_start.timetuple()), views_count


def get_article_views_prev_month(article_id, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    month_start = timezone.now().astimezone(tz).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = month_start - relativedelta.relativedelta(months=1)
    views_count = _get_article_views_sum(article_id, prev_month_start, month_start)
    return time.mktime(month_start.timetuple()), views_count


def get_article_views_total(article_id, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    today_start = timezone.now().astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    views_count = _get_article_views_sum(article_id, date_to=today_start)
    return time.mktime(today_start.timetuple()), views_count


def get_author_views_today(user_id, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    today_start = timezone.now().astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    views = ArticleView.objects\
        .filter(article__owner_id=user_id, created_at__gte=today_start)\
        .distinct('fingerprint').count()
    return time.mktime(today_start.timetuple()), views


def get_author_views_month(user_id, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    today_start = timezone.now().astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)
    views = ArticleView.objects\
        .filter(article__owner_id=user_id, created_at__gte=month_start, created_at__lt=today_start)\
        .distinct('fingerprint').count()
    return time.mktime(month_start.timetuple()), views


def get_author_views_prev_month(user_id, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    month_start = timezone.now().astimezone(tz).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = month_start - relativedelta.relativedelta(months=1)
    views = ArticleView.objects\
        .filter(article__owner_id=user_id, created_at__gte=prev_month_start, created_at__lt=month_start)\
        .distinct('fingerprint').count()
    return time.mktime(prev_month_start.timetuple()), views


def get_author_views_total(user_id, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    today_start = timezone.now().astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    views = ArticleView.objects\
        .filter(article__owner_id=user_id, created_at__lt=today_start)\
        .distinct('fingerprint').count()
    return time.mktime(today_start.timetuple()), views




