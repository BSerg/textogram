#! coding:utf-8
from __future__ import unicode_literals

from django.contrib.auth.models import AbstractUser
from django.db import models
import re

from common import upload_to

from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from django.utils import timezone
from datetime import timedelta
import random
from uuid import uuid4


def _upload_to(instance, filename):
    return upload_to('avatars', instance, filename)


class User(AbstractUser):
    VK = 'vk'
    FB = 'fb'
    TWITTER = 'twitter'
    GOOGLE = 'google'

    SOCIALS = (
        (VK, 'В контакте'),
        (FB, 'Facebook'),
        (TWITTER, 'Twitter'),
        (GOOGLE, 'Google'),
    )
    avatar = models.ImageField('Аватар', upload_to=_upload_to, blank=True, null=True)
    social = models.CharField('Соцсеть авторизации', max_length=10, choices=SOCIALS, blank=True)
    uid = models.CharField('UID Соцсети', max_length=255, blank=True)
    number_of_subscribers_cached = models.IntegerField('Кол-во подписчиков', default=0, editable=False)
    number_of_subscriptions_cached = models.IntegerField('Кол-во подпиcок', default=0, editable=False)
    number_of_published_articles_cached = models.IntegerField('Кол-во статей', default=0, editable=False)
    phone = models.CharField('Телефон', max_length=20, null=True, blank=True, unique=True)
    phone_confirmed = models.BooleanField('Телефон подтвержден', default=False)
    description = models.CharField('Описание', max_length=255, blank=True, default='')

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
    WEB = 'web'

    SOCIALS = (
        (VK, 'В контакте'),
        (FB, 'Facebook'),
        (TWITTER, 'Twitter'),
        (INSTAGRAM, 'Instagram'),
        (TELEGRAM, 'Telegram'),
        (GOOGLE, 'Google'),
        (ODNOKLASSNIKI, 'Одноклассники'),
        (YOUTUBE, 'Youtube'),
        (WEB, 'Web'),
    )

    user = models.ForeignKey(User)
    social = models.CharField('Соцсеть', max_length=20, choices=SOCIALS, default=WEB)
    url = models.URLField('URL', max_length=255)
    is_auth = models.BooleanField('Аккаунт авторизации', default=False)
    is_hidden = models.BooleanField('Скрыта', default=False)

    class Meta:
        verbose_name = 'Ссылка на социальный аккаунт'
        verbose_name_plural = 'Ссылки на социальные аккаунты'
        ordering = ('id',)

    def __unicode__(self):
        return '%s %s' % (self.user, self.social)


class Subscription(models.Model):
    user = models.ForeignKey(User, related_name='subscriptions', verbose_name='Пользователь')
    author = models.ForeignKey(User, related_name='author', verbose_name='Автор')
    subscribed_at = models.DateTimeField('Подписался', auto_now_add=True)
    is_active = models.BooleanField('Активно', default=True)

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __unicode__(self):
        return '%s %s' % (self.user, self.author)


class PhoneCode(models.Model):

    EXPIRATION_TIME = 300

    phone = models.CharField('Телефон', max_length=20)
    code = models.CharField('Код', max_length=5, blank=True, default='', editable=False)
    hash = models.CharField('Хэш', max_length=50, blank='', default='', editable=False)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    is_confirmed = models.BooleanField('Подтвержден', default=False, editable=False)
    disabled = models.BooleanField('Отключен', default=False, editable=False)

    def is_active(self):

        if self.is_confirmed or self.disabled or self.created_at < (timezone.now() - timedelta(minutes=self.EXPIRATION_TIME)):
            return False
        return True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        n = random.randint(10000, 99999)
        self.code = str(n)
        self.hash = str(uuid4())
        super(PhoneCode, self).save(force_insert, force_update, using, update_fields)

    def __unicode__(self):
        return '%s %s' % (self.code, self.disabled)

    class Meta:
        ordering = ('-created_at', )


@receiver(post_save, sender=Subscription)
@receiver(post_delete, sender=Subscription)
def recount_subscribers(sender, instance, **kwargs):
    user = instance.author
    user.number_of_subscribers_cached = sender.objects.filter(author=user).count()
    user.save()


@receiver(post_save, sender=Subscription)
@receiver(post_delete, sender=Subscription)
def recount_subscriptions(sender, instance, **kwargs):
    user = instance.user
    user.number_of_subscriptions_cached = sender.objects.filter(user=user).count()
    user.save()


SOCIAL_PATTERNS = [
    (SocialLink.VK, '^(http:\/\/|https:\/\/)?(www\.)?vk\.com\/(\w|\d)+?\/?$'),
    (SocialLink.FB, '(?:(?:http|https):\/\/)?(?:www.)?facebook.com\/(?:(?:\w)*#!\/)?(?:pages\/)?(?:[?\w\-]*\/)?(?:profile.php\?id=(?=\d.*))?([\w\-]*)?'),
    (SocialLink.TWITTER, 'http(?:s)?:\/\/(?:www\.)?twitter\.com\/([a-zA-Z0-9_]+)/?'),
    (SocialLink.INSTAGRAM, '(?:(?:http|https):\/\/)?(?:www.)?(?:instagram.com|instagr.am)\/([A-Za-z0-9-_\.]+)/?')
]


def get_social_type(url):

    for p in SOCIAL_PATTERNS:
        pattern = re.compile(p[1])
        if pattern.match(url):
            return p[0]

    return None


# @receiver(pre_save, sender=SocialLink)
# def set_social(sender, instance, **kwargs):
#     url = instance.url
#
#     for p in SOCIAL_PATTERNS:
#         pattern = re.compile(p[1])
#         if pattern.match(url):
#             instance.social = p[0]


@receiver(pre_save, sender=PhoneCode)
def disable_previous_codes(sender, instance, **kwargs):
    codes = PhoneCode.objects.filter(phone=instance.phone, disabled=False)
    if codes:
        codes.update(disabled=True)
