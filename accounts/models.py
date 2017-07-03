#! coding:utf-8
from __future__ import unicode_literals

import random
import re
from datetime import timedelta
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.management import call_command
from textogram.settings import USE_REDIS_CACHE

from common import upload_to


def _upload_to(instance, filename):
    return upload_to('avatars', instance, filename)


class User(AbstractUser):
    uid = models.CharField('UID Пользователя', max_length=255, blank=True)
    avatar_url = models.URLField('Ссылка на аватар', max_length=255, blank=True)
    avatar = models.ImageField('Аватар', upload_to=_upload_to, blank=True, null=True)
    number_of_subscribers_cached = models.IntegerField('Кол-во подписчиков', default=0, editable=False)
    number_of_subscriptions_cached = models.IntegerField('Кол-во подпиcок', default=0, editable=False)
    number_of_published_articles_cached = models.IntegerField('Кол-во статей', default=0, editable=False)
    phone = models.CharField('Телефон', max_length=20, null=True, blank=True)
    phone_confirmed = models.BooleanField('Телефон подтвержден', default=False)
    description = models.CharField('Описание', max_length=255, blank=True, default='')
    nickname = models.CharField('Никнейм', max_length=20, null=True, unique=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def clean(self):
        if self.email and User.objects.filter(email=self.email).exclude(id=self.id):
            raise ValidationError('Already exists', code='invalid')
        pass


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


@receiver(post_save, sender=User)
def create_nickname(sender, instance, **kwargs):
    if kwargs.get('created'):
        instance.nickname = 'id%s' % instance.id
        instance.save()


@receiver(post_save, sender=User)
def cache_user(sender, instance, **kwargs):
    if USE_REDIS_CACHE:
        call_command('cache_users', instance.id)


@receiver(post_save, sender=User)
def update_user_article_cache(sender, instance, **kwargs):
    if USE_REDIS_CACHE:
        call_command('update_user_article_cache', instance.id)


@receiver(pre_save, sender=Subscription)
def cache_subscription_feed(sender, instance, **kwargs):
    if USE_REDIS_CACHE:
        call_command('update_user_feed_cache', instance.user.id, instance.author.id, True)


@receiver(pre_delete, sender=Subscription)
def delete_cache_subscription_feed(sender, instance, **kwargs):
    if USE_REDIS_CACHE:
        call_command('update_user_feed_cache', instance.user.id, instance.author.id)


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


@receiver(pre_save, sender=PhoneCode)
def disable_previous_codes(sender, instance, **kwargs):
    codes = PhoneCode.objects.filter(phone=instance.phone, disabled=False)
    if codes:
        codes.update(disabled=True)
