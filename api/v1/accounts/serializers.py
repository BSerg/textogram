from __future__ import unicode_literals

from rest_framework import serializers

from accounts.models import User, MultiAccountUser, MultiAccount


class MultiAccountSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='multi_account.name')
    avatar = serializers.ImageField(source='multi_account.avatar')

    class Meta:
        model = MultiAccountUser
        fields = ['name', 'avatar', 'is_owner']


class UserSerializer(serializers.ModelSerializer):
    multi_accounts = serializers.SerializerMethodField()

    def get_multi_accounts(self, obj):
        multi_accounts = obj.multi_account_membership.filter(is_active=True)
        return MultiAccountSerializer(multi_accounts, many=True).data

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'avatar', 'social', 'uid', 'email', 'multi_accounts']


class PublicUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ['id', 'first_name', 'last_name', 'avatar']


class PublicMultiAccountSerializer(serializers.ModelSerializer):
    is_multi_account = serializers.SerializerMethodField()

    def get_is_multi_account(self, obj):
        return True

    class Meta:
        model = MultiAccount
        exclude = ['users']





