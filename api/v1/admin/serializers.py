from __future__ import unicode_literals

from accounts.models import User
from articles.models import Article
from rest_framework import serializers
from api.v1.accounts.serializers import UserSerializer
from articles import ArticleContentType


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class AdminArticleSerializer(serializers.ModelSerializer):

    owner = UserSerializer()
    lead = serializers.SerializerMethodField()

    def get_lead(self, obj):
        blocks = obj.content.get('blocks', [])
        if blocks and blocks[0].get('type') == ArticleContentType.LEAD:
            return blocks[0].get('value')

    class Meta:
        model = Article
        fields = ('id', 'title', 'lead', 'owner', 'slug', 'status', 'created_at', 'published_at', 'last_modified',
                  'deleted_at', )
