from __future__ import unicode_literals

import random
from collections import defaultdict

from rest_framework import serializers

from advertisement.models import BannerGroup
from api.v1.accounts.serializers import PublicUserSerializer
from api.v1.advertisement.serializers import BannerSerializer
from articles import ArticleContentType
from articles.models import Article, ArticleImage
from textogram.settings import THUMBNAIL_MEDIUM_SIZE, THUMBNAIL_LARGE_SIZE, THUMBNAIL_REGULAR_SIZE, THUMBNAIL_SMALL_SIZE


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        exclude = ['owner']
        read_only_fields = ['status']


class ArticleImageSerializer(serializers.ModelSerializer):
    regular = serializers.SerializerMethodField()
    small = serializers.SerializerMethodField()
    medium = serializers.SerializerMethodField()
    preview = serializers.SerializerMethodField()
    original = serializers.SerializerMethodField()
    original_width = serializers.SerializerMethodField()
    original_height = serializers.SerializerMethodField()

    def get_small(self, obj):
        return obj.get_image_url(THUMBNAIL_SMALL_SIZE)

    def get_medium(self, obj):
        return obj.get_image_url(THUMBNAIL_MEDIUM_SIZE)

    def get_regular(self, obj):
        return obj.get_image_url(THUMBNAIL_REGULAR_SIZE)

    def get_preview(self, obj):
        return obj.get_image_url(THUMBNAIL_MEDIUM_SIZE)

    def get_original(self, obj):
        return obj.get_image_url()

    def get_original_width(self, obj):
        try:
            if obj.image:
                return obj.image.width
        except:
            return None

    def get_original_height(self, obj):
        try:
            if obj.image:
                return obj.image.height
        except:
            return None

    class Meta:
        model = ArticleImage
        exclude = ['created_at']
        extra_kwargs = {'article': {'write_only': True}}


class PublicArticleSerializer(serializers.HyperlinkedModelSerializer):
    owner = PublicUserSerializer(read_only=True)
    title = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    inverted_theme = serializers.SerializerMethodField()
    views = serializers.IntegerField(source='views_cached')
    url = serializers.SerializerMethodField()
    short_url = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    def get_title(self, obj):
        return obj.content.get('title')

    def get_cover(self, obj):
        if 'cover_clipped' in obj.content:
            cover = obj.content['cover_clipped']
        elif 'cover' in obj.content:
            cover = obj.content['cover']
        else:
            return None
        try:
            cover_id = cover.get('id')
            image = obj.images.get(pk=cover_id)
            return image.get_image_url(THUMBNAIL_LARGE_SIZE)
        except ArticleImage.DoesNotExist:
            return None
        except AttributeError:
            return None

    def get_url(self, obj):
        return obj.get_full_url()

    def get_short_url(self, obj):
        return obj.get_short_url()
        
    def get_inverted_theme(self, obj):
        return obj.content.get('inverted_theme')

    def get_images(self, obj):
        return ArticleImageSerializer(obj.images.all(), context=self.context, many=True).data

    class Meta:
        model = Article
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'inverted_theme', 'published_at', 'views', 'content',
                  'url', 'short_url', 'ads_enabled', 'images', 'is_pinned']


class PublicArticleLimitedSerializer(PublicArticleSerializer):
    class Meta(PublicArticleSerializer.Meta):
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'inverted_theme',
                  'published_at', 'views', 'url', 'short_url', 'paywall_enabled', 'paywall_price', 'paywall_currency']


class PublicArticleFeedSerializer(PublicArticleSerializer):
    class Meta(PublicArticleSerializer.Meta):
        fields = ['id', 'slug', 'title']


class PublicArticleSerializerMin(PublicArticleSerializer):

    lead = serializers.SerializerMethodField()
    is_draft = serializers.SerializerMethodField()

    def get_lead(self, obj):
        blocks = obj.content.get('blocks', [])
        if blocks and blocks[0].get('type') == ArticleContentType.LEAD:
            return blocks[0].get('value')

    def get_is_draft(self, obj):
        return obj.status == Article.DRAFT

    class Meta(PublicArticleSerializer.Meta):
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'lead', 'published_at', 'link_access', 'is_draft',
                  'last_modified', 'inverted_theme', 'paywall_enabled', 'paywall_price', 'paywall_currency',
                  'is_pinned']


class DraftArticleSerializer(PublicArticleSerializerMin):

    is_draft = serializers.SerializerMethodField()

    def get_is_draft(self, obj):
        return True

    class Meta(PublicArticleSerializerMin.Meta):
        fields = PublicArticleSerializerMin.Meta.fields + ['last_modified']
