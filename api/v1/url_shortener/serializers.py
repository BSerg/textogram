from __future__ import unicode_literals
from rest_framework import serializers
from url_shortener.models import UrlShort
from django.contrib.sites.models import Site


class UrlShortSerializer(serializers.ModelSerializer):

    shortened_url = serializers.SerializerMethodField()

    def create(self, validated_data):
        try:
            if self.Meta.model.objects.filter(**validated_data).exists():
                instance = self.Meta.model.objects.filter(**validated_data)[0]
            else:
                instance = self.Meta.model.objects.create(**validated_data)
        except TypeError:
            raise TypeError('Create link error')
        return instance

    def get_shortened_url(self, obj):
        current_site = Site.objects.get_current()
        return 'http://%s/%s' % (current_site.domain, obj.code)

    class Meta:
        model = UrlShort
        fields = ['url', 'code', 'count', 'created_at', 'shortened_url']
        read_only_fields = ['code', 'count', 'created_at', 'shortened_url']
