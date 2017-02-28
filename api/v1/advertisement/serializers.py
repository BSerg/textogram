from rest_framework import serializers

from advertisement.models import Banner


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        exclude = ['id', 'is_active', 'description', 'created_at']