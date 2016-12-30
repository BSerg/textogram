from __future__ import unicode_literals

from rest_framework import viewsets, mixins, permissions
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from api.v1.articles.permissions import IsOwnerForUnsafeRequests, IsArticleContentOwner
from api.v1.articles.serializers import ArticleSerializer, PublicArticleSerializer, ArticleContentSerializer, \
    ArticleContentTextSerializer, ArticleContentHeaderSerializer, ArticleContentLeadSerializer
from articles.models import Article, ArticleContent, ArticleContentText, ArticleContentHeader, ArticleContentLead


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

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.status = Article.DELETED
        instance.save()

    @detail_route(methods=['PUT', 'PATCH'])
    def swap(self, request, *args, **kwargs):
        position = request.data.get('position')
        article = self.get_object()
        content = article.content.filter(position=position).first()
        if not content:
            raise ValidationError('CONTENT ISN\'T SWAPPABLE')
        next_content = ArticleContent.objects.exclude(pk=content.pk). \
            filter(article=content.article, position__gte=content.position).first()
        if not next_content:
            raise ValidationError('CONTENT ISN\'T SWAPPABLE')
        content.position += 1
        content.save()
        next_content.position -= 1
        next_content.save()
        return Response('SWAPPED')


class PublicArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.PUBLISHED)
    serializer_class = PublicArticleSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ArticleSetPagination
    lookup_field = 'slug'


class ArticleContentViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    queryset = ArticleContent.objects.all()
    serializer_class = ArticleContentSerializer
    permission_classes = [permissions.IsAuthenticated, IsArticleContentOwner]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            type_param = self.request.data.get('type')
            if type_param not in ArticleContent.TYPES:
                raise ValidationError('Error')
            if type_param == ArticleContent.TEXT:
                return ArticleContentTextSerializer
            if type_param == ArticleContent.HEADER:
                return ArticleContentHeaderSerializer
            if type_param == ArticleContent.LEAD:
                return ArticleContentLeadSerializer
        else:
            content = self.get_object()
            if isinstance(content, ArticleContentText):
                return ArticleContentTextSerializer
            if isinstance(content, ArticleContentHeader):
                return ArticleContentHeaderSerializer
            if isinstance(content, ArticleContentLead):
                return ArticleContentLeadSerializer
            return super(ArticleContentViewSet, self).get_serializer_class()
