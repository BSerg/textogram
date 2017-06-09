from __future__ import unicode_literals

import re

import PIL.Image as Image
from rest_framework import serializers
from rest_framework.validators import ValidationError

from accounts.models import User, SocialLink, Subscription
from articles.models import Article
from textogram.settings import FORBIDDEN_NICKNAMES


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ['social', 'url']


class MeSocialLinkSerializer(SocialLinkSerializer):
    class Meta(SocialLinkSerializer.Meta):
        fields = ['id', 'social', 'url', 'is_auth', 'is_hidden']
        read_only_fields = ['id', 'is_auth']


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField(read_only=True)
    social_links = serializers.SerializerMethodField()
    subscribers = serializers.SerializerMethodField()
    number_of_articles = serializers.SerializerMethodField()
    subscriptions = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        if obj.avatar:
            if self.context.get('request'):
                return self.context.get('request').build_absolute_uri(obj.avatar.url)
            else:
                return obj.avatar.url
        elif obj.avatar_url:
            return obj.avatar_url

    def get_social_links(self, obj):
        return SocialLinkSerializer(SocialLink.objects.filter(user=obj, is_hidden=False, is_auth=False), many=True).data

    def get_subscribers(self, obj):
        return obj.number_of_subscribers_cached

    def get_number_of_articles(self, obj):
        return obj.number_of_published_articles_cached

    def get_subscriptions(self, obj):
        return obj.number_of_subscriptions_cached

    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'first_name', 'last_name', 'avatar', 'email',
                  'social_links', 'subscribers', 'subscriptions', 'number_of_articles', 'description']


def nickname_validator(nickname):
    if not nickname or (len(nickname) not in range(4, 21)):
        raise ValidationError({'nickname': ['incorrect']})

    for n in FORBIDDEN_NICKNAMES:
        if re.search('^%s$' % n, nickname):
            raise ValidationError({'nickname': ['forbidden']})

    if not re.search('^[A-Za-z\d_]+$', nickname):
        raise ValidationError({'nickname': ['forbidden']})

    return nickname.lower()


class MeUserSerializer(UserSerializer):
    phone = serializers.SerializerMethodField()
    drafts = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        nickname = validated_data.get('nickname') or ''
        if nickname:
            validated_data['nickname'] = nickname_validator(nickname)

        instance = super(MeUserSerializer, self).update(instance, validated_data)
        return instance

    def get_drafts(self, obj):
        return Article.objects.filter(owner=obj, status=Article.DRAFT).count()

    def get_social_links(self, obj):
        return MeSocialLinkSerializer(SocialLink.objects.filter(user=obj), many=True).data

    def get_phone(self, obj):

        phone = obj.phone
        if not phone:
            return ''
        if not phone.startswith('+'):
            phone = '+%s' % phone
        if len(phone) <= 3:
            return '+..'
        if len(phone) <= 7:
            return phone[0:3] + '...'

        return '%s %s %s %s' % (phone[0:2], phone[2:4], re.sub("\d", ".", phone[4: -3]), phone[-2:])

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['phone', 'drafts']
        read_only_fields = ['id', 'username', 'email', 'social_links', 'subscribers',
                            'subscriptions', 'phone', 'drafts']


class MeAvatarWriteUserSerializer(MeUserSerializer):
    avatar = serializers.ImageField()

    def validate_avatar(self, value):
        try:
            if value.content_type in ['image/jpeg', 'image/png'] and value.size <= 1024 * 1024:
                i = Image.open(value)
                width, height = i.size
                if width <= 400 and width == height:
                    return value
        except (AttributeError, ValueError):
            pass
        raise ValidationError('image format wrong')


class PublicUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        if not self.context or not self.context.get('request').user or not self.context.get('request').user.is_authenticated:
            return False
        return bool(Subscription.objects.filter(user=self.context.get('request').user, author=obj))

    class Meta(UserSerializer.Meta):
        fields = ['id', 'nickname', 'first_name', 'last_name', 'avatar', 'social_links', 'subscribers', 'subscriptions',
                  'is_subscribed', 'number_of_articles', 'description']


class SubscriptionSerializer(serializers.ModelSerializer):

    author = PublicUserSerializer()

    class Meta:
        model = Subscription
        fields = ['author']

