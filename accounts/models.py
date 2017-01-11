#! coding:utf-8
from __future__ import unicode_literals

from django.contrib.auth.models import AbstractUser
from django.db import models

from common import upload_to

from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

def _upload_to(instance, filename):
    return upload_to('avatars', instance, filename)


class User(AbstractUser):
    VK = 'vk'
    FB = 'fb'
    TWITTER = 'twitter'

    SOCIALS = (
        (VK, 'В контакте'),
        (FB, 'Facebook'),
        (TWITTER, 'Twitter'),
    )
    avatar = models.ImageField('Аватар', upload_to=_upload_to, blank=True, null=True)
    social = models.CharField('Соцсеть авторизации', max_length=10, choices=SOCIALS, blank=True)
    uid = models.CharField('UID Соцсети', max_length=255, blank=True)
    number_of_subscribers_cached = models.IntegerField('Кол-во подписчиков', default=0, editable=False)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class MultiAccount(models.Model):
    name = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', max_length=1000, blank=True)
    avatar = models.ImageField('Аватар', upload_to=_upload_to, blank=True, null=True)
    users = models.ManyToManyField(User, related_name='multi_accounts', through='MultiAccountUser', blank=True)

    class Meta:
        verbose_name = 'Мультиаккаунт'
        verbose_name_plural = 'Мультиаккаунты'


class MultiAccountUser(models.Model):
    user = models.ForeignKey(User, related_name='multi_account_membership')
    multi_account = models.ForeignKey(MultiAccount)
    is_owner = models.BooleanField('Владелец', default=False)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SocialLink(models.Model):
    VK = 'vk'
    FB = 'fb'
    TWITTER = 'twitter'
    INSTAGRAM = 'instagram'
    TELEGRAM = 'telegram'
    GOOGLE = 'google'
    ODNOKLASSNIKI = 'OK'
    YOUTUBE = 'Youtube'

    SOCIALS = (
        (VK, 'В контакте'),
        (FB, 'Facebook'),
        (TWITTER, 'Twitter'),
        (INSTAGRAM, 'Instagram'),
        (TELEGRAM, 'Telegram'),
        (GOOGLE, 'Google'),
        (ODNOKLASSNIKI, 'Одноклассники'),
        (YOUTUBE, 'Youtube'),
    )

    user = models.ForeignKey(User)
    social = models.CharField('Соцсеть', max_length=20, choices=SOCIALS)
    url = models.CharField('URL', max_length=255)

    class Meta:
        verbose_name = 'Ссылка на социальный аккаунт'
        verbose_name_plural = 'Ссылки на социальные аккаунты'

    def __unicode__(self):
        return '%s %s' % (self.user, self.social)


class Subscription(models.Model):
    user = models.ForeignKey(User, related_name='user', verbose_name='Пользователь')
    author = models.ForeignKey(User, related_name='author', verbose_name='Автор')
    subscribed_at = models.DateTimeField('Подписался', auto_now_add=True)
    is_active = models.BooleanField('Активно', default=True)

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __unicode__(self):
        return '%s %s' % (self.user, self.author)


@receiver(post_save, sender=Subscription)
@receiver(post_delete, sender=Subscription)
def recount_subscribers(sender, instance, **kwargs):
    user = instance.author
    user.number_of_subscribers_cached = sender.objects.filter(author=user).count()
    user.save()
