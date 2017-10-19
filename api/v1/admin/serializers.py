from __future__ import unicode_literals

from accounts.models import User
from articles.models import Article, ArticleImage
from rest_framework import serializers
from api.v1.accounts.serializers import UserSerializer
from articles import ArticleContentType
from textogram.settings import THUMBNAIL_LARGE_SIZE


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class AdminArticleSerializer(serializers.ModelSerializer):

    owner = UserSerializer()
    lead = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

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

    def get_lead(self, obj):
        blocks = obj.content.get('blocks', [])
        if blocks and blocks[0].get('type') == ArticleContentType.LEAD:
            return blocks[0].get('value')

    class Meta:
        model = Article
        fields = ('id', 'title', 'lead', 'cover', 'owner', 'slug', 'status', 'created_at', 'published_at',
                  'last_modified', 'deleted_at', )
