#! coding: utf-8
from __future__ import unicode_literals

from django.contrib.postgres.fields.jsonb import JSONField
from django.core.management import call_command
from django.db import models
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from advertisement import BannerID
from textogram.settings import USE_REDIS_CACHE


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
    code = models.TextField('Код баннера')
    width = models.PositiveSmallIntegerField('Ширина, px', blank=True, null=True)
    height = models.PositiveSmallIntegerField('Высота, px', blank=True, null=True)
    is_fullwidth = models.BooleanField('На всю ширину', default=False)
    is_active = models.BooleanField('Активно', default=False)
    is_ab = models.BooleanField('Участвует в A/B тестировании', default=False)
    weight = models.PositiveSmallIntegerField('Вес', default=1)
    amp_props = JSONField('AMP Свойства', blank=True, null=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    position = models.PositiveSmallIntegerField('Позиция', default=0)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['position']
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'


@receiver(post_save, sender=BannerGroup)
@receiver(post_save, sender=Banner)
def _update_advertisements_cache(sender, instance, **kwargs):
    if USE_REDIS_CACHE:
        call_command('cache_advertisements')
