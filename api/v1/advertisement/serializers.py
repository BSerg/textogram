from rest_framework import serializers

from advertisement.models import Banner


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['code', 'width', 'height', 'is_fullwidth', 'amp_props']
