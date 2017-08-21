from rest_framework import serializers
from rest_framework.fields import JSONField

from advertisement.models import Banner


class BannerSerializer(serializers.ModelSerializer):
    extra = JSONField(source='amp_props', read_only=True)

    class Meta:
        model = Banner
        fields = ['code', 'width', 'height', 'extra']
