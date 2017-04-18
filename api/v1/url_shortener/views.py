from rest_framework import viewsets, mixins, permissions
from url_shortener.models import UrlShort
from .serializers import UrlShortSerializer


class UrlShortViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      mixins.CreateModelMixin, viewsets.GenericViewSet):

    queryset = UrlShort.objects.filter()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UrlShortSerializer