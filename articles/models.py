#!coding:utf-8
from __future__ import unicode_literals

from django.db import models
from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from polymorphic.models import PolymorphicModel

from common import upload_to


def _upload_to(instance, filename):
    return upload_to('images', instance, filename)


class Article(models.Model):
    DRAFT = 1
    PUBLISHED = 2
    DELETED = 3

    STATUSES = (
        (DRAFT, 'Черновик'),
        (PUBLISHED, 'Опубликовано'),
        (DELETED, 'Удалено')
    )
    slug = models.SlugField('Машинное имя', unique=True, db_index=True)
    title = models.CharField('Заголовок', max_length=255)
    cover = models.ImageField('Обложка', upload_to=_upload_to, blank=True, null=True)
    html = models.TextField('HTML', blank=True)

    owner = models.ForeignKey('accounts.User', related_name='articles')
    multi_account = models.ForeignKey('accounts.MultiAccount', related_name='articles', blank=True, null=True)

    status = models.PositiveSmallIntegerField('Статус', choices=STATUSES, default=DRAFT)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    published_at = models.DateTimeField('Дата публикации', blank=True, null=True)
    last_modified = models.DateTimeField('Дата последнего изменения', auto_now=True)
    deleted_at = models.DateTimeField('Дата удаления', blank=True, null=True)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'


class ArticleContent(PolymorphicModel):
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

    TYPES = (
        TEXT,
        HEADER,
        LEAD,
        VIDEO,
        PHOTO,
        AUDIO,
        QUOTE,
        COLUMNS,
        PHRASE,
        LIST,
        DIALOG,
        POST,
    )

    article = models.ForeignKey(Article, related_name='content')
    position = models.PositiveSmallIntegerField('Позиция', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    last_modified = models.DateTimeField('Дата последнего изменения', auto_now=True)

    def get_html(self):
        raise NotImplementedError

    class Meta:
        ordering = ['article', 'position']
        verbose_name = 'Контент'
        verbose_name_plural = 'Контент'


class ArticleContentText(ArticleContent):
    text = models.TextField('Текст [MARKDOWN]', blank=True)


class ArticleContentHeader(ArticleContent):
    text = models.CharField('Текст', max_length=255, blank=True)


class ArticleContentLead(ArticleContent):
    text = models.TextField('Текст', max_length=400, blank=True)


class ArticleContentPhrase(ArticleContent):
    text = models.TextField('Текст', max_length=500, blank=True)


class ArticleContentImageCollection(ArticleContent):
    pass


class ArticleContentImageCollectionItem(models.Model):
    content_item = models.ForeignKey(ArticleContentImageCollection, related_name='photos')
    image = models.ImageField('Изображение', upload_to=_upload_to)
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['content_item', 'position']


class ArticleContentEmbed(ArticleContent):
    POST = 1
    VIDEO = 2
    AUDIO = 3

    TYPES = (
        (POST, 'Пост'),
        (VIDEO, 'Видео'),
        (AUDIO, 'Аудио'),
    )

    type = models.PositiveSmallIntegerField('Тип', choices=TYPES, default=POST)
    url = models.URLField('Ссылка', max_length=255)

    class Meta:
        verbose_name = 'Embed'


class ArticleQuote(ArticleContent):
    photo = models.ImageField('Фото', upload_to=_upload_to)
    text = models.TextField('Текст')

    class Meta:
        verbose_name = 'Цитата'
        verbose_name_plural = 'Цитаты'


class ArticleColumn(ArticleContent):
    image = models.ImageField('Изображение', upload_to=_upload_to)
    text = models.TextField('Текст [MARKDOWN]')

    class Meta:
        verbose_name = 'Колонка'
        verbose_name_plural = 'Колонки'


class ArticlePhrase(ArticleContent):
    text = models.TextField('Текст [MARKDOWN]')

    def get_type(self):
        return self.PHRASE

    class Meta:
        verbose_name = 'Фраза'
        verbose_name_plural = 'Фразы'


class ArticleList(ArticleContent):
    UNORDERED = 1
    ORDERED = 2
    TYPES = (
        (UNORDERED, 'Непронумерованный'),
        (ORDERED, 'Пронумерованный')
    )
    type = models.PositiveSmallIntegerField('Тип', choices=TYPES, default=UNORDERED)
    text = models.TextField('Текст [MARKDOWN]')

    class Meta:
        verbose_name = 'Список'
        verbose_name_plural = 'Списки'


@receiver(post_save, sender=ArticleContentText)
@receiver(post_save, sender=ArticleContentHeader)
@receiver(post_save, sender=ArticleContentLead)
@receiver(post_save, sender=ArticleContentPhrase)
def update_content_positions_on_save(sender, instance, created, **kwargs):
    if created:
        ArticleContent.objects\
            .exclude(pk=instance.pk)\
            .filter(article=instance.article, position__gte=instance.position)\
            .update(position=F('position') + 1)


@receiver(post_delete, sender=ArticleContentText)
@receiver(post_delete, sender=ArticleContentHeader)
@receiver(post_delete, sender=ArticleContentLead)
@receiver(post_delete, sender=ArticleContentPhrase)
def update_content_positions_on_delete(sender, instance, **kwargs):
    ArticleContent.objects\
        .filter(article=instance.article, position__gt=instance.position)\
        .update(position=F('position') - 1)
