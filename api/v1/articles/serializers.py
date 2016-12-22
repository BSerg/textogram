from __future__ import unicode_literals

from rest_framework import serializers

from api.v1.accounts.serializers import PublicUserSerializer, PublicMultiAccountSerializer
from articles.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        exclude = ['owner', 'multi_account']


class PublicArticleSerializer(ArticleSerializer):
    author = serializers.SerializerMethodField()

    def get_author(self, obj):
        if obj.multi_account:
            return PublicMultiAccountSerializer(obj.multi_account).data
        else:
            return PublicUserSerializer(obj.owner).data

    class Meta:
        model = Article
        fields = ['slug', 'title', 'published_at', 'cover', 'html', 'author', 'published_at']
