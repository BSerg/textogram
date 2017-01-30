#! coding:utf-8
from __future__ import unicode_literals

from django.db import models
from accounts.models import User


class Notification(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', null=True, blank=True)
    text = models.CharField('Текст', max_length=500, null=True, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    is_read = models.BooleanField('Прочитано', default=False)
    updated_at = models.DateTimeField('Изменено/прочитано', auto_now=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ('-id',)

    def __unicode__(self):
        return '%s %s "%s"' % (self.user, self.is_read, self.text)
