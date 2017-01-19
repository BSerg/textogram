from __future__ import unicode_literals

from rest_framework import serializers

from api.v1.accounts.serializers import PublicUserSerializer
from articles.models import Article, ArticleImage


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        exclude = ['owner']
        read_only_fields = ['status']


class ArticleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleImage
        exclude = ['created_at']
        extra_kwargs = {'article': {'write_only': True}}


class PublicArticleSerializer(serializers.ModelSerializer):
    owner = PublicUserSerializer(read_only=True)
    title = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    def get_title(self, obj):
        print obj.content
        return obj.content.get('title')

    def get_cover(self, obj):
        cover_id = obj.content.get('cover', {}).get('id')
        try:
            return obj.images.get(pk=cover_id).image.url
        except ArticleImage.DoesNotExist:
            return None

    class Meta:
        model = Article
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'published_at', 'html']


class PublicArticleSerializerMin(PublicArticleSerializer):

    lead = serializers.SerializerMethodField()

    def get_lead(self, obj):
        return 'lead'

    class Meta(PublicArticleSerializer.Meta):
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'lead', 'published_at']
