from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.authtoken.models import Token

from accounts.models import User, MultiAccountUser, MultiAccount, SocialLink, Subscription


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

    def get_social_links(self, obj):
        return SocialLinkSerializer(SocialLink.objects.filter(user=obj, is_hidden=False), many=True).data

    def get_subscribers(self, obj):
        return obj.number_of_subscribers_cached

    def get_multi_accounts(self, obj):
        multi_accounts = obj.multi_account_membership.filter(is_active=True)
        return MultiAccountSerializer(multi_accounts, many=True).data

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'avatar', 'social', 'uid', 'email', 'multi_accounts',
                  'social_links', 'subscribers']


class MeUserSerializer(UserSerializer):
    token = serializers.SerializerMethodField()

    def get_social_links(self, obj):
        return MeSocialLinkSerializer(SocialLink.objects.filter(user=obj), many=True).data

    def get_token(self, obj):
        return Token.objects.get_or_create(user=obj)[0].key

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['phone', 'token']


class PublicUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        if not self.context or not self.context.get('request').user or not self.context.get('request').user.is_authenticated:
            return False
        return bool(Subscription.objects.filter(user=self.context.get('request').user, author=obj))

    class Meta(UserSerializer.Meta):
        fields = ['id', 'first_name', 'last_name', 'avatar', 'social_links', 'subscribers', 'is_subscribed']


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



