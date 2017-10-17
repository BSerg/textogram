#!coding:utf-8
from __future__ import unicode_literals

import uuid
from urlparse import urlparse
from uuid import uuid4

from django.contrib.postgres.fields.jsonb import JSONField
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.db import models
from django.db.models import F
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from polymorphic.models import PolymorphicModel
from slugify import slugify
from sorl.thumbnail import get_thumbnail

from articles.utils import process_content
from articles.validators import ContentValidator, validate_content_size
from common import upload_to
from textogram.settings import PAYWALL_CURRENCIES, PAYWALL_CURRENCY_RUR, ARTICLE_RECOMMENDATIONS_MAX_COUNT
from textogram.settings import USE_REDIS_CACHE
from url_shortener.models import UrlShort


def _upload_to(instance, filename):
    return upload_to('images', instance, filename)


def validate_content(content):
    ContentValidator()(content)


class Article(models.Model):
    DRAFT = 1
    PUBLISHED = 2
    DELETED = 3
    SHARED = 4
    BANNED = 5

    STATUSES = (
        (DRAFT, 'Черновик'),
        (PUBLISHED, 'Опубликовано'),
        (DELETED, 'Удалено'),
        (SHARED, 'Общедоступно'),
        (BANNED, 'Заблокировано'),
    )
    status = models.PositiveSmallIntegerField('Статус', choices=STATUSES, default=DRAFT, db_index=True)
    owner = models.ForeignKey('accounts.User', related_name='articles')
    slug = models.SlugField('Машинное имя', max_length=200, unique=True, db_index=True, editable=False)
    title = models.CharField('Заголовок', max_length=255, blank=True)
    content = JSONField('Контент', default=dict(title='', cover=None, blocks=[]),
                        validators=[validate_content_size, validate_content])
    html = models.TextField('HTML', blank=True, editable=False)
    views_cached = models.PositiveIntegerField('Просмотры', default=0)
    link_access = models.BooleanField('Доступ по ссылке', default=False)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    published_at = models.DateTimeField('Дата публикации', blank=True, null=True)
    last_modified = models.DateTimeField('Дата последнего изменения', auto_now=True)
    deleted_at = models.DateTimeField('Дата удаления', blank=True, null=True)

    ads_enabled = models.BooleanField('Реклама включена', default=True)
    paywall_enabled = models.BooleanField('Paywall включен', default=False)
    paywall_price = models.DecimalField('Базовая стоимость доступа [PAYWALL]', max_digits=8, decimal_places=2,
                                        default=0)
    paywall_currency = models.CharField('Валюта [PAYWALL]', choices=PAYWALL_CURRENCIES, max_length=3,
                                        default=PAYWALL_CURRENCY_RUR)

    def get_absolute_url(self):
        if self.slug:
            return reverse('article', kwargs={'slug': self.slug})

    def get_full_url(self):
        if self.slug:
            return 'http://%s%s' % (Site.objects.get_current().domain, reverse('article', kwargs={'slug': self.slug}))

    def get_short_url(self):
        if hasattr(self, 'short_url'):
            short_url = self.short_url
        else:
            short_url = UrlShort.objects.create(article=self)
        return 'http://%s%s' % (Site.objects.get_current().domain, reverse('short_url', kwargs={'code': short_url.code}))

    def update_html(self, save=True):
        pass

    def has_access(self, user):
        return ArticleUserAccess.objects.filter(article=self, user=user).exists()

    def get_recommendations(self):
        return Article.objects.filter(status=Article.PUBLISHED, owner=self.owner) \
            .exclude(pk=self.pk).order_by('-published_at')[:ARTICLE_RECOMMENDATIONS_MAX_COUNT]

    def __unicode__(self):
        return self.content.get('title') or 'Статья #%d' % self.id

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'


class ArticleImage(models.Model):
    article = models.ForeignKey(Article, verbose_name='Статья', related_name='images')
    image = models.ImageField('Обложка', upload_to=_upload_to)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    @staticmethod
    def _get_image_full_url(url):
        parsed_url = urlparse(url)
        if not parsed_url.scheme and not parsed_url.netloc:
            return 'http://%s%s' % (Site.objects.get_current().domain, url)
        else:
            return url

    def get_image_url(self, thumbnail_size=None):
        if not self.image:
            return
        if not thumbnail_size:
            return self._get_image_full_url(self.image.url)
        else:
            thumbnail = get_thumbnail(self.image, thumbnail_size, upscale=False)
            if thumbnail:
                return self._get_image_full_url(thumbnail.url)


class ArticleView(models.Model):
    article = models.ForeignKey(Article, verbose_name='Статья', related_name='views')
    user = models.ForeignKey('accounts.User', verbose_name='Авторизованный пользователь', blank=True, null=True)
    fingerprint = models.CharField('Цифровой отпечаток клиента', max_length=255, db_index=True)
    monetization_enabled = models.BooleanField('Монетизируемый просмотр', default=False)
    created_at = models.DateTimeField('Дата создания')

    def __unicode__(self):
        return self.fingerprint

    class Meta:
        verbose_name = 'Просмотр'
        verbose_name_plural = 'Просмотры'


class ArticlePreview(models.Model):
    article = models.ForeignKey(Article, verbose_name='Статья', related_name='previews')
    uid = models.UUIDField('UID', default=uuid.uuid4, editable=False)
    is_permanent = models.BooleanField('Постоянная', default=False)
    is_active = models.BooleanField('Активна', default=True)
    views_count = models.PositiveIntegerField('Просмотры', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    last_modified = models.DateTimeField('Дата последнего обновления', auto_now=True)

    def __unicode__(self):
        return self.uid

    class Meta:
        unique_together = ('article', 'is_permanent')
        verbose_name = 'Превью'
        verbose_name_plural = 'Превью'


class ArticleUserAccess(models.Model):
    order = models.OneToOneField('payments.PayWallOrder', verbose_name='Заказ',
                                 related_name='access', blank=True, null=True)
    article = models.ForeignKey('articles.Article', verbose_name='Статья', related_name='user_accesses')
    user = models.ForeignKey('accounts.User', verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return 'Access Article #{} | User #{}'.format(self.article_id, self.user_id)

    class Meta:
        verbose_name = 'Доступ к статье'
        verbose_name_plural = 'Доступы к статьям'


@receiver(pre_save, sender=Article)
def update_slug(sender, instance, **kwargs):
    db_instance = Article.objects.get(pk=instance.id) if instance.id else None
    if instance.status == Article.DRAFT:
        if instance.content.get('title'):
            if db_instance:
                articles = Article.objects.exclude(pk=instance.id)
            else:
                articles = Article.objects.all()
            slug = slugify(instance.content['title'])
            suffix = ''
            count = 0
            while articles.filter(slug=slug + suffix).exists():
                count += 1
                suffix = '-%d' % count
            slug += suffix
            instance.slug = slug
        elif not instance.slug:
            instance.slug = str(uuid4())


@receiver(pre_save, sender=Article)
def process_content_pre_save(sender, instance, **kwargs):
    if instance.status != Article.DELETED:
        instance.content = process_content(instance.content)
        instance.title = instance.content.get('title') or ''


@receiver(post_save, sender=ArticleView)
def update_views_cached(sender, instance, created, **kwargs):
    if not USE_REDIS_CACHE and created and instance.article.status == Article.PUBLISHED:
        Article.objects.filter(pk=instance.article.id).update(views_cached=F('views_cached') + 1)


@receiver(pre_save, sender=Article)
def set_status_changed_articles(sender, instance, **kwargs):
    if instance.id:
        current_status = Article.objects.get(pk=instance.id).status
        if instance.status != current_status:
            instance.status_changed = True


@receiver(post_save, sender=Article)
def set_published_at(sender, instance, **kwargs):
    if not instance.published_at and instance.status == Article.PUBLISHED:
        instance.published_at = timezone.now()
        instance.save()


@receiver(post_save, sender=Article)
def recount_published_articles(sender, instance, **kwargs):
    if hasattr(instance, 'status_changed') and instance.status_changed:
        user = instance.owner
        user.number_of_published_articles_cached = Article.objects.filter(status=Article.PUBLISHED, owner=user).count()
        user.save()


@receiver(post_save, sender=Article)
def create_short_url(sender, instance, created, **kwargs):
    if instance.slug and not hasattr(instance, 'short_url'):
        UrlShort.objects.create(article=instance)


@receiver(post_save, sender=Article)
def add_access_to_author(sender, instance, **kwargs):
    if instance.status == Article.PUBLISHED and instance.paywall_enabled and \
            not instance.user_accesses.filter(user=instance.owner).exists():
        ArticleUserAccess.objects.create(article=instance, user=instance.owner)


@receiver(post_save, sender=Article)
def cache_article(sender, instance, created, **kwargs):
    if USE_REDIS_CACHE and (instance.status == Article.PUBLISHED or instance.status == Article.DELETED):
        call_command('update_article_cache', instance.id)
        try:
            url_short = UrlShort.objects.get(article=instance)
            call_command('cache_url', url_short.id)
        except UrlShort.DoesNotExist:
            pass
        call_command('generate_article_search_index', instance.id)
        call_command('update_article_feed_cache', instance.id)


@receiver(post_save, sender=Article)
def cache_article_recommendations(sender, instance, created, **kwargs):
    if USE_REDIS_CACHE and hasattr(instance, 'status_changed') and instance.status_changed:
        call_command('update_article_recommendations', instance.slug, delete=instance.status != Article.PUBLISHED)


@receiver(post_save, sender=Article)
def process_gif2mp4(sender, instance, created, **kwargs):
    if instance.status == Article.PUBLISHED:
        call_command('convert_gif2video', instance.pk)


@receiver(post_save, sender=ArticleUserAccess)
def cache_article_access(sender, instance, created, **kwargs):
    if USE_REDIS_CACHE and created:
        call_command('update_article_access_cache', instance.pk)


@receiver(pre_delete, sender=ArticleUserAccess)
def cache_article_access_delete(sender, instance, **kwargs):
    if USE_REDIS_CACHE:
        call_command('update_article_access_cache', instance.id, delete=True)
