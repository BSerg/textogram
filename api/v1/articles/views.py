from __future__ import unicode_literals

from django.utils import timezone
from rest_framework import viewsets, mixins, permissions
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from api.v1.articles.permissions import IsOwnerForUnsafeRequests, IsArticleContentOwner
from api.v1.articles.serializers import ArticleSerializer, PublicArticleSerializer, ArticleImageSerializer, \
    PublicArticleSerializerMin, DraftArticleSerializer
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

    @detail_route(methods=['POST'])
    def publish(self, request, **kwargs):
        article = self.get_object()
        if article.status != Article.DRAFT:
            raise ValidationError('Article\'s status is not DRAFT')
        article.status = Article.PUBLISHED
        article.published_at = article.published_at or timezone.now()
        article.save()
        return Response(ArticleSerializer(article).data)


class ArticleImageViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = ArticleImage.objects.all()
    serializer_class = ArticleImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsArticleContentOwner]


class PublicArticleListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.PUBLISHED, link_access=False)
    serializer_class = PublicArticleSerializerMin
    permission_classes = [permissions.AllowAny]
    pagination_class = ArticleSetPagination
    lookup_field = 'slug'


class PublicArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.PUBLISHED)
    serializer_class = PublicArticleSerializer
    permission_classes = [permissions.AllowAny]
    # pagination_class = ArticleSetPagination
    lookup_field = 'slug'


class DraftListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.DRAFT)
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DraftArticleSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)
