#!coding:utf-8
from __future__ import unicode_literals

from uuid import uuid4

from django.contrib.postgres.fields.jsonb import JSONField
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from polymorphic.models import PolymorphicModel
from slugify import slugify

from articles.utils import process_content, content_to_html
from articles.validation import ContentValidator, validate_content_size
from common import upload_to


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
    slug = models.SlugField('Машинное имя', unique=True, db_index=True, editable=False)
    content = JSONField('Контент', default=dict(title='', cover=None, blocks=[]),
                        validators=[validate_content_size, validate_content])
    html = models.TextField('HTML', blank=True, editable=False)
    ads_enabled = models.BooleanField('Реклама включена', default=True)
    link_access = models.BooleanField('Доступ по ссылке', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    published_at = models.DateTimeField('Дата публикации', blank=True, null=True)
    last_modified = models.DateTimeField('Дата последнего изменения', auto_now=True)
    deleted_at = models.DateTimeField('Дата удаления', blank=True, null=True)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'


class ArticleImage(models.Model):
    article = models.ForeignKey(Article, verbose_name='Статья', related_name='images')
    image = models.ImageField('Обложка', upload_to=_upload_to)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)


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
    print instance.content
    if instance.status == Article.PUBLISHED:
        instance.html = content_to_html(instance.content)
        print 'HELLO', instance.html
