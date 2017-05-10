#! coding: utf-8
from __future__ import unicode_literals

from django.db import models

from advertisement import BannerID


class BannerGroup(models.Model):
    BANNER_IDS = ((value, value) for value in BannerID.__dict__.values() if value and value.startswith('banner'))
    identifier = models.CharField('Идентификатор позиции', choices=BANNER_IDS, max_length=255)
    is_mobile = models.BooleanField('Мобильная версия', default=False, help_text='Баннер для мобильной версии сайта')
    is_active = models.BooleanField('Активно', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    def __unicode__(self):
        return self.identifier

    class Meta:
        unique_together = ['identifier', 'is_mobile']
        ordering = ['identifier']
        verbose_name = 'Группа баннеров'
        verbose_name_plural = 'Группы баннеров'


class Banner(models.Model):
    group = models.ForeignKey(BannerGroup, verbose_name='Группа', related_name='banners', blank=True, null=True)
    name = models.CharField('Название', max_length=255, blank=True)
    code = models.TextField('Код баннера', unique=True)
    width = models.PositiveSmallIntegerField('Ширина, px', blank=True, null=True)
    height = models.PositiveSmallIntegerField('Высота, px', blank=True, null=True)
    is_fullwidth = models.BooleanField('На всю ширину', default=False)
    is_active = models.BooleanField('Активно', default=False)
    is_ab = models.BooleanField('Участвует в A/B тестировании', default=False)
    weight = models.PositiveSmallIntegerField('Вес', default=1,
                                              help_text='Вес показа баннера для A/B тестирования в группе')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['-weight']
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'
