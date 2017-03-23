from __future__ import unicode_literals

import base64

from django.core.files.base import ContentFile
from django.db.models import F
from django.utils import timezone
from rest_framework import viewsets, mixins, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from api.v1.articles.permissions import IsOwnerForUnsafeRequests, IsArticleContentOwner, WebVisor, IsOwner
from api.v1.articles.serializers import ArticleSerializer, PublicArticleSerializer, ArticleImageSerializer, \
    PublicArticleSerializerMin, DraftArticleSerializer
from articles.models import Article, ArticleImage, ArticleView, ArticlePreview
from accounts.models import Subscription

from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_201_CREATED


class ArticleSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerForUnsafeRequests]

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


class ArticleImageViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = ArticleImage.objects.all()
    serializer_class = ArticleImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsArticleContentOwner]

    @list_route(methods=['POST'])
    def base64(self, request, **kwargs):
        article_id = request.data.get('article')
        data = request.data.get('image')
        format, imgstr = data.split(';base64,')
        ext = format.split('/')[-1]
        data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        im = ArticleImage(article_id=article_id, image=data)
        im.save()
        return Response(ArticleImageSerializer(im).data, status=HTTP_201_CREATED)


class PublicArticleListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Article.objects.filter(status=Article.PUBLISHED, link_access=False)
    serializer_class = PublicArticleSerializerMin
    permission_classes = [permissions.AllowAny]
    pagination_class = ArticleSetPagination
    lookup_field = 'slug'

    def get_queryset(self):

        if self.request.query_params.get('feed') and self.request.user.is_authenticated:
            subscriptions = Subscription.objects.filter(user=self.request.user)
            return Article.objects.filter(owner__author__in=subscriptions, status=Article.PUBLISHED, link_access=False)
        elif self.request.query_params.get('drafts') and self.request.user.is_authenticated:
            return Article.objects.filter(owner=self.request.user, status=Article.DRAFT)
        elif self.request.query_params.get('user'):
            try:
                user_id = int(self.request.query_params.get('user'))
            except ValueError:
                return Article.objects.none()

            if self.request.user.is_authenticated and self.request.user.id == user_id:
                return Article.objects.filter(owner=self.request.user, status=Article.PUBLISHED)
            else:
                return Article.objects.filter(owner__id=user_id, status=Article.PUBLISHED, link_access=False)

        # elif user is not None:
        #     if self.request.user.id == int(user):
        #         if self.request.query_params.get('drafts'):
        #             return Article.objects.filter(owner=self.request.user, status=Article.DRAFT)
        #         else:
        #             return Article.objects.filter(owner__id=int(user), status=Article.PUBLISHED)
        #     else:
        #         return Article.objects.filter(owner__id=int(user), link_access=False, status=Article.PUBLISHED)
        else:
            return Article.objects.none()


class PublicArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status__in=[Article.PUBLISHED, Article.SHARED])
    serializer_class = PublicArticleSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        fingerprint = request.META.get('HTTP_X_FINGERPRINT')
        if fingerprint:
            if request.user.is_authenticated() and ArticleView.objects.filter(article=instance, user=request.user).exists():
                ArticleView.objects.filter(article=instance, user=request.user).update(views_count=F('views_count') + 1)
            elif request.user.is_authenticated():
                ArticleView.objects.create(article=instance, user=request.user, fingerprint=fingerprint)
            elif ArticleView.objects.filter(article=instance, fingerprint=fingerprint).exists():
                ArticleView.objects.filter(article=instance, fingerprint=fingerprint).update(views_count=F('views_count') + 1)
            else:
                ArticleView.objects.create(article=instance, fingerprint=fingerprint)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class DraftListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.DRAFT)
    permission_classes = [permissions.IsAuthenticated, IsOwnerForUnsafeRequests]
    serializer_class = DraftArticleSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    @detail_route(methods=['POST'])
    def delete(self, request, **kwargs):
        draft = self.get_object()
        if draft.status != Article.DRAFT:
            raise ValidationError('Article\'s status is not DRAFT')
        draft.status = Article.DELETED
        draft.save()
        return Response({'msg': 'deleted'})


class ArticlePreviewView(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status=Article.DRAFT)
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    serializer_class = PublicArticleSerializer
