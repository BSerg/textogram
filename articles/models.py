#!coding:utf-8
from __future__ import unicode_literals

from django.contrib.postgres.fields.jsonb import JSONField
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from polymorphic.models import PolymorphicModel
from slugify import slugify

from common import upload_to


def _upload_to(instance, filename):
    return upload_to('images', instance, filename)


class ArticleContentType:
    TEXT = 1
    HEADER = 2
    LEAD = 3
    VIDEO = 4
    PHOTO = 5
    AUDIO = 6
    QUOTE = 7
    COLUMNS = 8
    PHRASE = 9
    LIST = 10
    DIALOG = 11
    POST = 12


class Article(models.Model):
    DRAFT = 1
    PUBLISHED = 2
    DELETED = 3

    STATUSES = (
        (DRAFT, 'Черновик'),
        (PUBLISHED, 'Опубликовано'),
        (DELETED, 'Удалено')
    )
    status = models.PositiveSmallIntegerField('Статус', choices=STATUSES, default=DRAFT)
    owner = models.ForeignKey('accounts.User', related_name='articles')
    slug = models.SlugField('Машинное имя', unique=True, db_index=True, editable=False)
    content = JSONField('Контент', default={'title': None, 'cover': None, 'blocks': []})
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
    if instance.status == Article.DRAFT:
        if instance.content.get('title'):
            instance.slug = slugify(instance.content['title'])

# DEPRECATED


# class ArticleTitle(models.Model):
#     article = models.OneToOneField(Article, verbose_name='Статья', related_name='title')
#     text = models.CharField('Текст заголовка', max_length=255)
#
#
# class ArticleCover(models.Model):
#     article = models.OneToOneField(Article, verbose_name='Статья', related_name='cover')
#     image = models.ImageField('Обложка', upload_to=_upload_to)
#
#
# class ArticleContent(PolymorphicModel):
#     TEXT = 1
#     HEADER = 2
#     LEAD = 3
#     VIDEO = 4
#     PHOTO = 5
#     AUDIO = 6
#     QUOTE = 7
#     COLUMNS = 8
#     PHRASE = 9
#     LIST = 10
#     DIALOG = 11
#     POST = 12
#
#     TYPES = (
#         TEXT,
#         HEADER,
#         LEAD,
#         VIDEO,
#         PHOTO,
#         AUDIO,
#         QUOTE,
#         COLUMNS,
#         PHRASE,
#         LIST,
#         DIALOG,
#         POST,
#     )
#
#     article = models.ForeignKey(Article, related_name='content')
#     position = models.PositiveSmallIntegerField('Позиция', default=0)
#     created_at = models.DateTimeField('Дата создания', auto_now_add=True)
#     last_modified = models.DateTimeField('Дата последнего изменения', auto_now=True)
#
#     def get_html(self):
#         raise NotImplementedError
#
#     def clone(self):
#         raise NotImplementedError
#
#     class Meta:
#         ordering = ['article', 'position']
#         verbose_name = 'Контент'
#         verbose_name_plural = 'Контент'
#
#
# class ArticleContentText(ArticleContent):
#     text = models.TextField('Текст [MARKDOWN]', blank=True)
#
#
# class ArticleContentHeader(ArticleContent):
#     text = models.CharField('Текст', max_length=255, blank=True)
#
#
# class ArticleContentLead(ArticleContent):
#     text = models.TextField('Текст', max_length=400, blank=True)
#
#
# class ArticleContentPhrase(ArticleContent):
#     text = models.TextField('Текст', max_length=500, blank=True)
#
#
# class ArticleContentPhotoGallery(ArticleContent):
#     TYPE1 = 1
#
#     TYPES = (
#         (TYPE1, 'Тип 1'),
#     )
#     subtype = models.PositiveSmallIntegerField('Тип', choices=TYPES, default=TYPE1)
#
#
# class ArticleContentPhoto(models.Model):
#     content_item = models.ForeignKey(ArticleContentPhotoGallery, related_name='photos')
#     image = models.ImageField('Изображение', upload_to=_upload_to)
#     caption = models.TextField('Подпись', max_length=500, blank=True)
#     position = models.PositiveSmallIntegerField(default=0)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         ordering = ['content_item', 'position']
#
#
# class ArticleContentEmbed(ArticleContent):
#     POST = 1
#     VIDEO = 2
#     AUDIO = 3
#
#     TYPES = (
#         (POST, 'Пост'),
#         (VIDEO, 'Видео'),
#         (AUDIO, 'Аудио'),
#     )
#
#     subtype = models.PositiveSmallIntegerField('Тип', choices=TYPES, default=POST)
#     url = models.URLField('Ссылка', max_length=255)
#
#     class Meta:
#         verbose_name = 'Embed'
#
#
# class ArticleContentQuote(ArticleContent):
#     photo = models.ImageField('Фото', upload_to=_upload_to)
#     text = models.TextField('Текст')
#
#     class Meta:
#         verbose_name = 'Цитата'
#         verbose_name_plural = 'Цитаты'
#
#
# class ArticleContentColumn(ArticleContent):
#     image = models.ImageField('Изображение', upload_to=_upload_to)
#     text = models.TextField('Текст [MARKDOWN]')
#
#     class Meta:
#         verbose_name = 'Колонка'
#         verbose_name_plural = 'Колонки'
#
#
# class ArticleContentList(ArticleContent):
#     UNORDERED = 1
#     ORDERED = 2
#     TYPES = (
#         (UNORDERED, 'Непронумерованный'),
#         (ORDERED, 'Пронумерованный')
#     )
#     subtype = models.PositiveSmallIntegerField('Тип', choices=TYPES, default=UNORDERED)
#     text = models.TextField('Текст [MARKDOWN]', blank=True)
#
#     class Meta:
#         verbose_name = 'Список'
#         verbose_name_plural = 'Списки'
#
#
# @receiver(post_save, sender=ArticleContentText)
# @receiver(post_save, sender=ArticleContentHeader)
# @receiver(post_save, sender=ArticleContentLead)
# @receiver(post_save, sender=ArticleContentPhrase)
# @receiver(post_save, sender=ArticleContentList)
# @receiver(post_save, sender=ArticleContentPhotoGallery)
# def update_content_positions_on_save(sender, instance, created, **kwargs):
#     if created:
#         ArticleContent.objects\
#             .exclude(pk=instance.pk)\
#             .filter(article=instance.article, position__gte=instance.position)\
#             .update(position=F('position') + 1)
#
#
# @receiver(post_delete, sender=ArticleContentText)
# @receiver(post_delete, sender=ArticleContentHeader)
# @receiver(post_delete, sender=ArticleContentLead)
# @receiver(post_delete, sender=ArticleContentPhrase)
# @receiver(post_delete, sender=ArticleContentList)
# @receiver(post_delete, sender=ArticleContentPhotoGallery)
# def update_content_positions_on_delete(sender, instance, **kwargs):
#     for index, content in enumerate(instance.article.content.all()):
#         content.position = index
#         content.save()
#
#
# @receiver(post_save, sender=ArticleContentPhoto)
# def update_photo_position_on_create(sender, instance, created, **kwargs):
#     if created:
#         ArticleContentPhoto.objects\
#             .exclude(pk=instance.pk)\
#             .filter(content_item=instance.content_item, position__gte=instance.position)\
#             .update(position=F('position') + 1)
#
#
# @receiver(post_delete, sender=ArticleContentPhoto)
# def update_photo_position_on_delete(sender, instance, **kwargs):
#     for index, photo in enumerate(instance.content_item.photos.all()):
#         photo.position = index
#         photo.save()
