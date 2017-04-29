#!coding:utf-8
from __future__ import unicode_literals

import uuid
from uuid import uuid4

from django.contrib.postgres.fields.jsonb import JSONField
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse
from polymorphic.models import PolymorphicModel
from slugify import slugify

from articles.utils import process_content, content_to_html
from articles.validators import ContentValidator, validate_content_size
from common import upload_to
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

    STATUSES = (
        (DRAFT, 'Черновик'),
        (PUBLISHED, 'Опубликовано'),
        (DELETED, 'Удалено'),
        (SHARED, 'Общедоступно')
    )
    status = models.PositiveSmallIntegerField('Статус', choices=STATUSES, default=DRAFT)
    owner = models.ForeignKey('accounts.User', related_name='articles')
    slug = models.SlugField('Машинное имя', max_length=200, unique=True, db_index=True, editable=False)
    content = JSONField('Контент', default=dict(title='', cover=None, blocks=[]),
                        validators=[validate_content_size, validate_content])
    html = models.TextField('HTML', blank=True, editable=False)
    views_cached = models.PositiveIntegerField('Просмотры', default=0)
    ads_enabled = models.BooleanField('Реклама включена', default=True)
    link_access = models.BooleanField('Доступ по ссылке', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    published_at = models.DateTimeField('Дата публикации', blank=True, null=True)
    last_modified = models.DateTimeField('Дата последнего изменения', auto_now=True)
    deleted_at = models.DateTimeField('Дата удаления', blank=True, null=True)

    def get_absolute_url(self):
        if self.slug:
            return reverse('article', kwargs={'slug': self.slug})

    def _get_absolute_url(self):
        if self.slug:
            return 'http://%s%s' % (Site.objects.get_current().domain, reverse('article', kwargs={'slug': self.slug}))

    def get_short_url(self):
        if hasattr(self, 'short_url'):
            short_url = self.short_url
        else:
            short_url = UrlShort.objects.create(article=self)
        return 'http://%s%s' % (Site.objects.get_current().domain, reverse('short_url', kwargs={'code': short_url.code}))

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


class ArticleView(models.Model):
    article = models.ForeignKey(Article, verbose_name='Статья', related_name='views')
    user = models.ForeignKey('accounts.User', verbose_name='Авторизованный пользователь',
                             blank=True, null=True, db_index=True)
    fingerprint = models.CharField('Цифровой отпечаток клиента', max_length=255, db_index=True)
    views_count = models.PositiveIntegerField('Просмотры пользователя', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    last_modified = models.DateTimeField('Дата последнего обновления', auto_now=True)

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


@receiver(pre_save, sender=Article)
def update_slug(sender, instance, **kwargs):
    db_instance = Article.objects.get(pk=instance.id) if instance.id else None
    if instance.status == Article.DRAFT:
        if instance.content.get('title'):
            if db_instance and db_instance.content.get('title') != instance.content.get('title'):
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
    instance.content = process_content(instance.content)
    if instance.status != Article.DELETED:
        instance.html = content_to_html(instance.content, ads_enabled=instance.ads_enabled)


@receiver(post_save, sender=ArticleView)
def update_views_cached(sender, instance, created, **kwargs):
    if created and instance.article.status == Article.PUBLISHED:
        article = instance.article
        article.views_cached += 1
        article.save()


@receiver(pre_save, sender=Article)
def set_status_changed_articles(sender, instance, **kwargs):
    if instance.id:
        current_status = Article.objects.get(pk=instance.id).status

        if instance.status != current_status:
            instance.status_changed = True


@receiver(post_save, sender=Article)
def recount_published_articles(sender, instance, **kwargs):
    if hasattr(instance, 'status_changed'):
        user = instance.owner
        user.number_of_published_articles_cached = Article.objects.filter(status=Article.PUBLISHED, owner=user).count()
        user.save()


@receiver(post_save, sender=Article)
def create_short_url(sender, instance, created, **kwargs):
    if instance.slug and not hasattr(instance, 'short_url'):
        UrlShort.objects.create(article=instance)
