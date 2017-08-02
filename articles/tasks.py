#! coding: utf-8
from __future__ import unicode_literals

from uuid import uuid4

import os
from django.core.files.storage import DefaultStorage
from django.utils import timezone

from articles import ArticleContentType
from articles.models import ArticleView, Article, ArticleImage
from articles.utils import fix_image_urls, gif2mp4, gif2webm, ContentBlockMetaGenerator
from textogram.settings import MEDIA_URL


def register_article_view(article_slug, user_id, fingerprint):
    try:
        article = Article.objects.get(slug=article_slug)
    except Article.DoesNotExist:
        return
    # TODO: this will must be refactored, when article will have got paywall option
    monetization_enabled = article.ads_enabled
    ArticleView.objects.create(article=article, user_id=user_id, fingerprint=fingerprint,
                               monetization_enabled=monetization_enabled, created_at=timezone.now())


def update_article_html(article_id):
    try:
        article = Article.objects.get(pk=article_id)
    except:
        return
    else:
        article.update_html()


def fix_article_content_image_urls(article_id):
    try:
        article = Article.objects.get(pk=article_id)
    except:
        return

    image_data = {i.id: i.get_image_url for i in article.images.all()}
    article.content = fix_image_urls(article.content, image_data)
    article.save()


def convert_gif2video(article_id, force_update=False):
    try:
        article = Article.objects.get(pk=article_id)
    except:
        return

    blocks = article.content.get('blocks') or []

    updated = False

    for block in blocks:
        photos = block.get('photos') or []
        if block.get('type') == ArticleContentType.PHOTO and len(photos) == 1 and photos[0].get('is_animated'):
            block['__meta'] = block.get('__meta', {})
            mp4 = block['__meta'].get('mp4')
            storage = DefaultStorage()
            if force_update or not mp4 or block['__meta'].get('is_changed'):
                try:
                    image = ArticleImage.objects.get(pk=photos[0].get('id'))
                except ArticleImage.DoesNotExist:
                    continue
                else:
                    f = storage.open(image.image.name).file.read()
                    err, mp4_fo = gif2mp4(f)
                    if not err:
                        path = storage.save(os.path.join('video', str(uuid4()) + '.mp4'), mp4_fo)
                        block['__meta']['mp4'] = storage.url(path)
                        print storage.url(path)
                        updated = True

    if updated:
        article.content['blocks'] = blocks
        article.save()

