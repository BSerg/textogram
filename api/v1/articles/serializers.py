from __future__ import unicode_literals

import random
from collections import defaultdict

from rest_framework import serializers

from advertisement.models import BannerGroup
from api.v1.accounts.serializers import PublicUserSerializer
from api.v1.advertisement.serializers import BannerSerializer
from articles import ArticleContentType
from articles.models import Article, ArticleImage
from textogram.settings import THUMBNAIL_MEDIUM_SIZE, THUMBNAIL_LARGE_SIZE


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        exclude = ['owner']
        read_only_fields = ['status']


class ArticleImageSerializer(serializers.ModelSerializer):
    preview = serializers.SerializerMethodField()

    def get_preview(self, obj):
        return obj.get_image_url(THUMBNAIL_MEDIUM_SIZE)

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
    advertisement = serializers.SerializerMethodField()

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

    def get_advertisement(self, obj):
        if not obj.ads_enabled:
            return

        def get_weighted_choice(weighted_ids):
            total = sum([w for _, w in weighted_ids])
            r = random.uniform(0, total)
            upto = 0
            for _id, w in _weighted_ids:
                if w + upto >= r:
                    return _id
                upto += w

        groups = BannerGroup.objects.filter(is_active=True).prefetch_related('banners')
        if groups.exists():
            _banners = defaultdict(lambda: defaultdict(lambda: []))
            for group in groups:
                key = 'desktop' if not group.is_mobile else 'mobile'
                if group.banners.filter(is_active=True, is_ab=False).exists():
                    _banners[key][group.identifier] = BannerSerializer(group.banners.filter(is_active=True), many=True).data
                if group.banners.filter(is_active=True, is_ab=True).exists():
                    _weighted_ids = group.banners.filter(is_active=True, is_ab=True).values_list('id', 'weight')
                    _id = get_weighted_choice(_weighted_ids)
                    if _id:
                        _banners[key][group.identifier].append(BannerSerializer(group.banners.get(pk=_id)).data)
            return _banners
        
    def get_inverted_theme(self, obj):
        return obj.content.get('inverted_theme')

    class Meta:
        model = Article
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'inverted_theme', 'published_at', 'views', 'html',
                  'url', 'short_url', 'ads_enabled', 'advertisement']


class PublicArticleLimitedSerializer(PublicArticleSerializer):
    class Meta(PublicArticleSerializer.Meta):
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'inverted_theme',
                  'published_at', 'views', 'url', 'short_url', 'paywall_enabled', 'paywall_price', 'paywall_currency']


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
                  'last_modified', 'inverted_theme', 'paywall_enabled', 'paywall_price', 'paywall_currency']


class DraftArticleSerializer(PublicArticleSerializerMin):

    is_draft = serializers.SerializerMethodField()

    def get_is_draft(self, obj):
        return True

    class Meta(PublicArticleSerializerMin.Meta):
        fields = PublicArticleSerializerMin.Meta.fields + ['last_modified']
