#! coding: utf-8
from __future__ import unicode_literals

from django.db import models

from advertisement import BannerID


class Banner(models.Model):
    BANNER_IDS = ((value, value) for value in BannerID.__dict__.values() if value and value.startswith('banner'))
    identifier = models.CharField('Идентификатор', choices=BANNER_IDS, max_length=255)
    is_mobile = models.BooleanField('Мобильная версия', default=False, help_text='Баннер для мобильной версии сайта')
    description = models.CharField('Описание', max_length=255, blank=True)
    code = models.TextField('Код баннера', blank=True)
    is_active = models.BooleanField('Активно', default=False)
    weight = models.PositiveSmallIntegerField(
        'Вес', default=1, help_text='Вес показа баннера в ряду баннеров с аналогичным идентификатором')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    def __unicode__(self):
        return self.identifier

    class Meta:
        ordering = ['identifier', '-weight']
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'
