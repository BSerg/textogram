from __future__ import unicode_literals

from rest_framework import viewsets, mixins, permissions
from rest_framework.pagination import PageNumberPagination

from api.v1.articles.permissions import IsOwnerForUnsafeRequests
from api.v1.articles.serializers import ArticleSerializer, PublicArticleSerializer
from articles.models import Article


class ArticleSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ArticleViewSet(mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerForUnsafeRequests]
    lookup_field = 'slug'

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.status = Article.DELETED
        instance.save()


class PublicArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.PUBLISHED)
    serializer_class = PublicArticleSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ArticleSetPagination
    lookup_field = 'slug'
