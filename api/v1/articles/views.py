from __future__ import unicode_literals

from rest_framework import viewsets, mixins, permissions
from rest_framework.pagination import PageNumberPagination

from api.v1.articles.permissions import IsOwnerForUnsafeRequests, IsArticleContentOwner
from api.v1.articles.serializers import ArticleSerializer, PublicArticleSerializer, ArticleImageSerializer
from articles.models import Article, ArticleImage


class ArticleSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerForUnsafeRequests]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.status = Article.DELETED
        instance.save()


class ArticleImageViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = ArticleImage.objects.all()
    serializer_class = ArticleImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsArticleContentOwner]


class PublicArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.PUBLISHED)
    serializer_class = PublicArticleSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ArticleSetPagination
    lookup_field = 'slug'
