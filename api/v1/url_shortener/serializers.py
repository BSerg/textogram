from __future__ import unicode_literals
from rest_framework import serializers
from url_shortener.models import UrlShort


class UrlShortSerializer(serializers.ModelSerializer):

    short_url = serializers.SerializerMethodField()

    def create(self, validated_data):
        try:
            if self.Meta.model.objects.filter(**validated_data).exists():
                instance = self.Meta.model.objects.filter(**validated_data)[0]
            else:
                instance = self.Meta.model.objects.create(**validated_data)
        except TypeError:
            raise TypeError('Create link error')
        return instance

    def get_short_url(self, obj):
        return obj.get_short_url()

    class Meta:
        model = UrlShort
        fields = ['url', 'code', 'count', 'created_at', 'short_url']
        read_only_fields = ['code', 'count', 'created_at', 'short_url']
