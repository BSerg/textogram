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
        return obj.content.get('title')

    def get_cover(self, obj):
        try:
            cover_id = obj.content.get('cover', {}).get('id')
            return obj.images.get(pk=cover_id).image.url
        except ArticleImage.DoesNotExist:
            return None
        except AttributeError:
            return None

    class Meta:
        model = Article
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'published_at', 'html']


class PublicArticleSerializerMin(PublicArticleSerializer):

    lead = serializers.SerializerMethodField()

    def get_lead(self, obj):
        return '''Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'''

    class Meta(PublicArticleSerializer.Meta):
        fields = ['id', 'slug', 'owner', 'title', 'cover', 'lead', 'published_at']


class DraftArticleSerializer(PublicArticleSerializerMin):

    is_draft = serializers.SerializerMethodField()

    def get_is_draft(self, obj):
        return True

    class Meta(PublicArticleSerializerMin.Meta):
        fields = PublicArticleSerializerMin.Meta.fields + ['is_draft', 'last_modified']
