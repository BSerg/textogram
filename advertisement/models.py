#! coding: utf-8
from __future__ import unicode_literals

from django.db import models


class Banner(models.Model):
    identifier = models.CharField('Идентификатор', max_length=255, unique=True)
    description = models.CharField('Описание', max_length=255, blank=True)
    code = models.TextField('Код баннера', blank=True)
    is_active = models.BooleanField('Активно', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    def __unicode__(self):
        return self.identifier

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'
