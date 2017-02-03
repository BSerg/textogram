from __future__ import unicode_literals

from rest_framework import serializers
from sorl.thumbnail import get_thumbnail

from api.v1.accounts.serializers import PublicUserSerializer
from articles.models import Article, ArticleImage
from articles import ArticleContentType


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        exclude = ['owner']
        read_only_fields = ['status']


class ArticleImageSerializer(serializers.ModelSerializer):
    preview = serializers.SerializerMethodField()

    def get_preview(self, obj):
        preview = get_thumbnail(obj.image, '400x400', quality=90)
        request = self.context.get('request')
        if preview and request:
            return request.build_absolute_uri(preview.url)

    class Meta:
        model = ArticleImage
        exclude = ['created_at']
        extra_kwargs = {'article': {'write_only': True}}


class PublicArticleSerializer(serializers.ModelSerializer):
    owner = PublicUserSerializer(read_only=True)
    title = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    images = serializers.SerializerMethodField()

    def get_title(self, obj):
        return obj.content.get('title')

    def get_cover(self, obj):
        try:
            cover_id = obj.content.get('cover', {}).get('id')
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

    class Meta:
        model = Article
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'published_at', 'html', 'images']


class PublicArticleSerializerMin(PublicArticleSerializer):

    lead = serializers.SerializerMethodField()

    def get_lead(self, obj):
        try:
            for c in obj.content.get('blocks', []):
                if c.get('type') == ArticleContentType.LEAD:
                    return c.get('value')
        except AttributeError, TypeError:
            pass
        return ''

    class Meta(PublicArticleSerializer.Meta):
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'lead', 'published_at', 'link_access']


class DraftArticleSerializer(PublicArticleSerializerMin):

    is_draft = serializers.SerializerMethodField()

    def get_is_draft(self, obj):
        return True

    class Meta(PublicArticleSerializerMin.Meta):
        fields = PublicArticleSerializerMin.Meta.fields + ['is_draft', 'last_modified']
