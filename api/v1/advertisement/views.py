#! coding:utf-8
from __future__ import unicode_literals
from rest_framework import viewsets, permissions

from advertisement.models import Banner
from api.v1.advertisement.serializers import BannerSerializer


class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Banner.objects.filter(is_active=True)
    permission_classes = [permissions.AllowAny]
    serializer_class = BannerSerializer
    lookup_field = 'identifier'
    lookup_url_kwarg = 'identifier'
