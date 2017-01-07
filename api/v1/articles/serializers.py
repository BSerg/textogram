from __future__ import unicode_literals

from rest_framework import serializers

from api.v1.accounts.serializers import PublicUserSerializer, PublicMultiAccountSerializer
from articles.models import Article, ArticleContent, ArticleContentText, ArticleContentHeader, ArticleContentLead, \
    ArticleContentImageCollection, ArticleContentImageCollectionItem, ArticleContentPhrase


class ArticleContentSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    TYPE = None

    def get_type(self, obj):
        return self.TYPE

    class Meta:
        model = ArticleContent
        exclude = []


class ArticleContentTextSerializer(ArticleContentSerializer):
    TYPE = ArticleContent.TEXT

    class Meta:
        model = ArticleContentText
        exclude = ['created_at', 'last_modified', 'polymorphic_ctype']


class ArticleContentHeaderSerializer(ArticleContentSerializer):
    TYPE = ArticleContent.HEADER

    class Meta:
        model = ArticleContentHeader
        exclude = ['created_at', 'last_modified', 'polymorphic_ctype']


class ArticleContentLeadSerializer(ArticleContentSerializer):
    TYPE = ArticleContent.LEAD

    class Meta:
        model = ArticleContentLead
        exclude = ['created_at', 'last_modified', 'polymorphic_ctype']


class ArticleContentPhraseSerializer(ArticleContentSerializer):
    TYPE = ArticleContent.PHRASE

    class Meta:
        model = ArticleContentPhrase
        exclude = ['created_at', 'last_modified', 'polymorphic_ctype']


# TODO other content serializers


class ArticleSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    def _get_content_serializer(self, content):
        if isinstance(content, ArticleContentText):
            return ArticleContentTextSerializer(content)
        if isinstance(content, ArticleContentHeader):
            return ArticleContentHeaderSerializer(content)
        if isinstance(content, ArticleContentLead):
            return ArticleContentLeadSerializer(content)
        if isinstance(content, ArticleContentPhrase):
            return ArticleContentPhraseSerializer(content)

    def get_content(self, obj):
        content = obj.content.all()
        return [self._get_content_serializer(c).data for c in content]

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

