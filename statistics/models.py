#! coding: utf-8
from __future__ import unicode_literals

from django.db import models


class ArticleAggregatedStatistics(models.Model):
    article = models.OneToOneField('articles.Article', verbose_name='Статья', related_name='statistics')
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    date_from = models.DateTimeField('Дата начала подсчета', blank=True, null=True)
    date_to = models.DateTimeField('Дата окончания подсчета', blank=True, null=True)

    views = models.PositiveIntegerField('Просмотры', blank=True, null=True, help_text='Общее кол-во уникальных просмотров')
    views_yandex = models.PositiveIntegerField('Просмотры [Yandex]', blank=True, null=True,
                                               help_text='Общее кол-во просмотров из Yandex.Metrics')
    male_percent = models.FloatField('Процент мужчин', blank=True, null=True)
    age_17 = models.FloatField('Процент людей в возрасте до 18 лет', blank=True, null=True)
    age_18 = models.FloatField('Процент людей в возрасте от 18 до 24 лет', blank=True, null=True)
    age_25 = models.FloatField('Процент людей в возрасте от 25 до 34 лет', blank=True, null=True)
    age_35 = models.FloatField('Процент людей в возрасте от 35 до 44 лет', blank=True, null=True)
    age_45 = models.FloatField('Процент людей в возрасте от 45 лет', blank=True, null=True)

    def __unicode__(self):
        return self.article.title

    class Meta:
        verbose_name = 'Общая статистика статьи'
        verbose_name_plural = 'Общие статистики статьи'


class BaseViewsStatistics(models.Model):
    DAY = 1
    MONTH = 2

    TYPES = (
        (DAY, 'Дневной период'),
        (MONTH, 'Месячный период'),
    )

    type = models.PositiveSmallIntegerField('Тип', choices=TYPES)
    views_count = models.PositiveIntegerField('Кол-во уникальных просмотров')
    date_start = models.DateTimeField('Начало периода отчета')
    date_end = models.DateTimeField('Окончание периода отчета')
    interval_start = models.DateTimeField('Начало интервала времени')
    interval_end = models.DateTimeField('Окончание интервала времени')
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['date_end', 'interval_end']


class AuthorViewsStatistics(BaseViewsStatistics):
    author = models.ForeignKey('accounts.User', verbose_name='Автор', related_name='views_statistics')

    class Meta(BaseViewsStatistics.Meta):
        verbose_name = 'Уникальные просмотры автора'
        verbose_name_plural = 'Уникальные просмотры авторов'


class ArticleViewsStatistics(BaseViewsStatistics):
    article = models.ForeignKey('articles.Article', verbose_name='Статья', related_name='views_statistics')

    class Meta(BaseViewsStatistics.Meta):
        verbose_name = 'Уникальные просмотры статьи'
        verbose_name_plural = 'Уникальные просмотры статей'
