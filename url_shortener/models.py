#!coding:utf-8
from __future__ import unicode_literals

from uuid import uuid4

from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.urls import reverse
from textogram.settings import USE_REDIS_CACHE
from django.core.management import call_command


class UrlShort(models.Model):
    url = models.TextField('URL', max_length=1000, db_index=True, blank=True)
    article = models.OneToOneField('articles.Article', verbose_name='Статья', related_name='short_url',
                                   blank=True, null=True)
    code = models.CharField('Код', max_length=10, editable=False, unique=True, default='')
    created_at = models.DateTimeField('Создан', editable=False, auto_now_add=True)
    count = models.IntegerField('Перходы', editable=False, default=0)

    def get_short_url(self):
        return 'http://%s%s' % (Site.objects.get_current().domain, reverse('short_url', kwargs={'code': self.code}))

    def clean(self):
        if not self.url and not self.article:
            raise ValidationError('URL or Article can\'t be null together')

    class Meta:
        verbose_name = 'Сокращенная ссылка'
        verbose_name_plural = 'Сокращеные ссылки'

    def __unicode__(self):
        return '%s %s (%s)' % (self.url, self.code, self.count)


@receiver(pre_save, sender=UrlShort)
def create_code(sender, instance, **kwargs):
    if not instance.code:
        length = 4
        while True:
            # code = ('!' if not IS_LENTACH else '') + str(uuid4())[0: length]
            code = str(uuid4())[0: length]
            if not UrlShort.objects.filter(code=code):
                instance.code = code
                break
            length += 1


@receiver(post_save, sender=UrlShort)
def cache_code(sender, instance, **kwargs):
    if USE_REDIS_CACHE:
        call_command('cache_url', instance.id)
