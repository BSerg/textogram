from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.models import Article, ArticleView

from statistics.models import ArticleAggregatedStatistics, ArticleViewsStatistics

from random import randint, randrange
from datetime import datetime, timedelta

from django.utils import timezone
import pytz
from uuid import uuid4


def random_date(start, end):

    return start + timedelta(seconds=(randrange((end - start).days * 24 * 60 * 60 + (end - start).seconds)))


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        ArticleView.objects.all().delete()
        for article in Article.objects.filter(status=Article.PUBLISHED):

            views_today = randint(10000, 40000)
            views_month = randint(views_today, views_today * 60)
            views_last_month = randint(views_month/2, views_month * 2)
            views = (views_last_month + views_month) * (1 + randint(1, 2) * 0.1)

            try:
                ArticleAggregatedStatistics.objects.create(
                    article=article, views_today=views_today, views_month=views_month, views=views,
                    views_yandex=views * 0.7, views_last_month=views_last_month, male_percent=0.55,
                    age_17=0.2, age_18=0.4, age_25=0.2, age_35=0.15, age_45=0.05, )

            except Exception as e:
                # print e
                pass

            date_start = datetime(article.published_at.year, article.published_at.month,
                                  article.published_at.day, 0, 0, 0, 0, pytz.UTC)

            month_start = datetime(article.published_at.year, article.published_at.month,
                                   1, 0, 0, 0, 0, pytz.UTC)

            hour_delta = 0
            delta = timezone.now() - date_start
            for n in range(0, delta.days * 24 + delta.seconds / (60 * 24) + 1):
                ArticleViewsStatistics.objects.create(
                    article=article, type=ArticleViewsStatistics.DAY, date_start=date_start + timedelta(days=n % 24),
                    date_end=date_start + timedelta(days=(n % 24) + 1), interval_start=date_start + timedelta(hours=n),
                    interval_end=date_start + timedelta(hours=n + 1), views_count=randint(0, int(views/100)))

            # for n in range(0, delta.days + 1):
            #     ArticleViewsStatistics.objects.create(
            #         article=article, type=ArticleViewsStatistics.MONTH, date_start=month_start + timedelta(days=n),
            #         date_end=date_start + timedelta(days=n + 1), interval_start=date_start + timedelta(days=n),
            #         intervael_end=date_start + timedelta(days=n + 1), view_count=randint(int(views/4))
            #     )




