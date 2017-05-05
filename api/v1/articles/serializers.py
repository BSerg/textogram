from __future__ import unicode_literals

from collections import defaultdict

from rest_framework import serializers
from sorl.thumbnail import get_thumbnail

from advertisement.models import Banner
from api.v1.accounts.serializers import PublicUserSerializer
from api.v1.advertisement.serializers import BannerSerializer
from articles.models import Article, ArticleImage
from articles import ArticleContentType
from textogram.settings import THUMBNAIL_SIZE


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        exclude = ['owner']
        read_only_fields = ['status']


class ArticleImageSerializer(serializers.ModelSerializer):
    preview = serializers.SerializerMethodField()

    def get_preview(self, obj):
        preview = get_thumbnail(obj.image, THUMBNAIL_SIZE, quality=90)
        request = self.context.get('request')
        if preview and request:
            return request.build_absolute_uri(preview.url)

    class Meta:
        model = ArticleImage
        exclude = ['created_at']
        extra_kwargs = {'article': {'write_only': True}}


class PublicArticleSerializer(serializers.HyperlinkedModelSerializer):
    owner = PublicUserSerializer(read_only=True)
    title = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    inverted_theme = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
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
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.images.get(pk=cover_id).image.url)
            return obj.images.get(pk=cover_id).image.url
        except ArticleImage.DoesNotExist:
            return None
        except AttributeError:
            return None

    def get_images(self, obj):
        return ArticleImageSerializer(
            obj.images.all(), context={'request': self.context.get('request')}, many=True).data

    def get_url(self, obj):
        return obj._get_absolute_url()

    def get_short_url(self, obj):
        return obj.get_short_url()

    def get_advertisement(self, obj):
        if not obj.ads_enabled:
            return
        
        banners = Banner.objects.filter(is_active=True)
        if banners.exists():
            _banners = defaultdict(lambda: [])
            for banner in banners:
                _banners[banner.identifier].append(BannerSerializer(banner).data)
            return _banners

    def get_inverted_theme(self, obj):
        return obj.content.get('inverted_theme')

    class Meta:
        model = Article
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'inverted_theme', 'published_at', 'views', 'html',
                  'images', 'url', 'short_url', 'ads_enabled', 'advertisement']


class PublicArticleSerializerMin(PublicArticleSerializer):

    lead = serializers.SerializerMethodField()
    is_draft = serializers.SerializerMethodField()
    last_modified = serializers.SerializerMethodField()

    def get_cover(self, obj):

        cover = None

        if 'cover_clipped' in obj.content:
            cover = obj.content['cover_clipped']
        elif 'cover' in obj.content:
            cover = obj.content['cover']
        cover_url = None
        if cover:
            try:
                cover_id = cover.get('id')
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.images.get(pk=cover_id).image.url)
                cover_url = obj.images.get(pk=cover_id).image.url
            except (ArticleImage.DoesNotExist, AttributeError):
                pass
        else:
            try:
                for c in obj.content.get('blocks', []):
                    if c.get('type') == ArticleContentType.PHOTO:
                        for img in c.get('photos', []):
                            if img.get('image'):
                                cover_url = img.get('image')
                                return cover_url
                        # return c.get('value')
            except (AttributeError, TypeError):
                pass

        return cover_url

    def get_lead(self, obj):
        try:
            for c in obj.content.get('blocks', []):
                if c.get('type') == ArticleContentType.LEAD:
                    return c.get('value')
            for c in obj.content.get('blocks', []):
                if c.get('type') == ArticleContentType.TEXT:
                    return c.get('value')
        except (AttributeError, TypeError):
            pass
        return ''

    def get_is_draft(self, obj):
        return obj.status == Article.DRAFT or None

    def get_last_modified(self, obj):
        return obj.last_modified if obj.status == Article.DRAFT else None

    class Meta(PublicArticleSerializer.Meta):
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'lead', 'published_at', 'link_access', 'is_draft',
                  'last_modified', 'inverted_theme']


class DraftArticleSerializer(PublicArticleSerializerMin):

    is_draft = serializers.SerializerMethodField()

    def get_is_draft(self, obj):
        return True

    class Meta(PublicArticleSerializerMin.Meta):
        fields = PublicArticleSerializerMin.Meta.fields + ['last_modified']
