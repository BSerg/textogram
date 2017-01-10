from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.v1.accounts.serializers import PublicUserSerializer, PublicMultiAccountSerializer
from articles.models import Article, ArticleContent, ArticleContentText, ArticleContentHeader, ArticleContentLead, \
    ArticleContentPhrase, ArticleContentList, ArticleContentPhoto, ArticleContentPhotoGallery


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


class ArticleContentListSerializer(ArticleContentSerializer):
    TYPE = ArticleContent.LIST

    class Meta:
        model = ArticleContentList
        exclude = ['created_at', 'last_modified', 'polymorphic_ctype']


class ArticleContentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleContentPhoto
        exclude = ['created_at']
        extra_kwargs = {
            'content_item': {'write_only': True}
        }


class ArticleContentPhotoGallerySerializer(ArticleContentSerializer):
    TYPE = ArticleContent.PHOTO
    photos = serializers.SerializerMethodField()

    def get_photos(self, obj):
        return ArticleContentPhotoSerializer(obj.photos.all(), many=True, context=self.context).data

    def create(self, validated_data):
        instance = super(ArticleContentPhotoGallerySerializer, self).create(validated_data)
        request = self.context['request']
        if request and request.data.get('image'):
            try:
                ArticleContentPhoto.objects.create(content_item=instance, position=0, image=request.data.get('image'))
            except:
                raise ValidationError('Error')
        return instance

    class Meta:
        model = ArticleContentPhotoGallery
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
        if isinstance(content, ArticleContentList):
            return ArticleContentListSerializer(content)
        if isinstance(content, ArticleContentPhotoGallery):
            return ArticleContentPhotoGallerySerializer(content)

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

