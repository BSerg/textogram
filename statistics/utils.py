#! coding: utf-8
from datetime import timedelta

import pytz
from dateutil import relativedelta
from django.db.models import Sum

from statistics.models import ArticleViewsStatistics


def _get_chart_data(article, type, date_from, date_to, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    stats = article.views_statistics.filter(type=type, interval_start__gte=date_from, interval_end__lt=date_to)
    return [(s.interval_end.astimezone(tz), s.views_count) for s in stats]


def get_article_day_views_chart_data(article, date, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    date_localized = date.astimezone(tz)
    today_start = date_localized.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    return _get_chart_data(article, ArticleViewsStatistics.DAY, today_start, today_end, tz_name)


def get_article_month_views_chart_data(article, date, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    date_localized = date.astimezone(tz)
    month_start = date_localized.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_end = month_start + relativedelta.relativedelta(months=1)
    data = _get_chart_data(article, ArticleViewsStatistics.MONTH, month_start, month_end, tz_name)
    return data


def get_article_views_chart_data(article, tz_name='Europe/Moscow'):
    tz = pytz.timezone(tz_name)
    stats = article.views_statistics.order_by().filter(type=ArticleViewsStatistics.MONTH)\
        .values('date_end').annotate(month_views=Sum('views_count'))
    return [(s['date_end'].astimezone(tz), s['month_views']) for s in stats]
