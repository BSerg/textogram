#!coding:utf-8

from __future__ import unicode_literals

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class CounterCode(models.Model):
    name = models.CharField('Наименование', max_length=255)
    is_active = models.BooleanField('Активно', default=True)
    code = models.TextField('Код')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Код счетчика'
        verbose_name_plural = 'Код счетчиков'


class RobotsRules(models.Model):
    text = models.TextField('Текст')
    is_active = models.BooleanField('Активно', default=True)

    def __unicode__(self):
        return self.text

    class Meta:
        verbose_name = 'Robots.txt'
        verbose_name_plural = 'Robots.txt'


@receiver(post_save, sender=CounterCode)
def clear_counter_cache(*args, **kwargs):
    cache_key = make_template_fragment_key('counters')
    cache.delete(cache_key)
