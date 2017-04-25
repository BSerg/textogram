#!coding:utf-8
from __future__ import unicode_literals
from uuid import uuid4

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save


class UrlShort(models.Model):

    url = models.URLField('URL', db_index=True)
    code = models.CharField('Код', max_length=10, editable=False, unique=True, default='')
    created_at = models.DateTimeField('Создан', editable=False, auto_now_add=True)
    count = models.IntegerField('Перходы', editable=False, default=0)

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
            code = str(uuid4())[0: length]
            if not UrlShort.objects.filter(code=code):
                instance.code = code
                break
            length += 1
