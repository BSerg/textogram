from __future__ import unicode_literals

import re
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from rest_framework.validators import ValidationError
from accounts.models import User, MultiAccountUser, MultiAccount, SocialLink, Subscription

import PIL.Image as Image


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ['social', 'url']


class MeSocialLinkSerializer(SocialLinkSerializer):
    class Meta(SocialLinkSerializer.Meta):
        fields = ['id', 'social', 'url', 'is_auth', 'is_hidden']
        read_only_fields = ['is_auth', 'is_hidden']


class MultiAccountSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='multi_account.name')
    avatar = serializers.ImageField(source='multi_account.avatar')

    class Meta:
        model = MultiAccountUser
        fields = ['name', 'avatar', 'is_owner']


class UserSerializer(serializers.ModelSerializer):
    multi_accounts = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    subscribers = serializers.SerializerMethodField()
    number_of_articles = serializers.SerializerMethodField()
    subscriptions = serializers.SerializerMethodField()

    def get_social_links(self, obj):
        return SocialLinkSerializer(SocialLink.objects.filter(user=obj, is_hidden=False), many=True).data

    def get_subscribers(self, obj):
        return obj.number_of_subscribers_cached

    def get_multi_accounts(self, obj):
        multi_accounts = obj.multi_account_membership.filter(is_active=True)
        return MultiAccountSerializer(multi_accounts, many=True).data

    def get_number_of_articles(self, obj):
        return obj.number_of_published_articles_cached

    def get_subscriptions(self, obj):
        return obj.number_of_subscriptions_cached

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'avatar', 'social', 'uid', 'email', 'multi_accounts',
                  'social_links', 'subscribers', 'subscriptions', 'number_of_articles', 'description']


class MeUserSerializer(UserSerializer):
    token = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

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

    def get_token(self, obj):
        return Token.objects.get_or_create(user=obj)[0].key

    def validate_avatar(self, value):
        try:
            if value.content_type == 'image/jpeg' and value.size <= 1024 * 1024:
                i = Image.open(value)
                width, height = i.size
                if width <= 400 and width == height:
                    return value
        except (AttributeError, ValueError):
            pass
        raise ValidationError('image format wrong')

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['phone', 'token']
        read_only_fields = ['id', 'social', 'uid', 'email', 'multi_accounts', 'social_links', 'subscribers',
                            'subscriptions', 'phone', 'token', 'description']


class PublicUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        if not self.context or not self.context.get('request').user or not self.context.get('request').user.is_authenticated:
            return False
        return bool(Subscription.objects.filter(user=self.context.get('request').user, author=obj))

    class Meta(UserSerializer.Meta):
        fields = ['id', 'first_name', 'last_name', 'avatar', 'social_links', 'subscribers', 'subscriptions',
                  'is_subscribed', 'number_of_articles', 'description']


class PublicMultiAccountSerializer(serializers.ModelSerializer):
    is_multi_account = serializers.SerializerMethodField()

    def get_is_multi_account(self, obj):
        return True

    class Meta:
        model = MultiAccount
        exclude = ['users']


class SubscriptionSerializer(serializers.ModelSerializer):

    author = PublicUserSerializer()

    class Meta:
        model = Subscription
        fields = ['author']



