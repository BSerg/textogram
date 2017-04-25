from __future__ import unicode_literals
from rest_framework import serializers
from url_shortener.models import UrlShort
from django.contrib.sites.models import Site


class UrlShortSerializer(serializers.ModelSerializer):

    shortened_url = serializers.SerializerMethodField()

    def get_shortened_url(self, obj):
        current_site = Site.objects.get_current()
        return 'http://%s/%s' % (current_site.domain, obj.code)

    class Meta:
        model = UrlShort
        fields = ['url', 'code', 'count', 'created_at', 'shortened_url']
        read_only_fields = ['code', 'count', 'created_at', 'shortened_url']
