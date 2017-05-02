from __future__ import unicode_literals

import base64
import json

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils import timezone
from redis import Redis
from rest_framework import viewsets, mixins, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_201_CREATED
from rq import Queue

from accounts.models import Subscription
from api.v1.articles.permissions import IsOwnerForUnsafeRequests, IsArticleContentOwner, IsOwner
from api.v1.articles.serializers import ArticleSerializer, PublicArticleSerializer, ArticleImageSerializer, \
    PublicArticleSerializerMin, DraftArticleSerializer
from articles.models import Article, ArticleImage
from articles.tasks import register_article_view
from articles.utils import get_article_cache_key
from textogram.settings import RQ_HOST, RQ_DB, RQ_TIMEOUT, NEW_ARTICLE_AGE, RQ_HIGH_QUEUE, RQ_LOW_QUEUE
from textogram.settings import RQ_PORT


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

    def update(self, request, *args, **kwargs):
        article = self.get_object()
        cache_key = get_article_cache_key(article.slug)
        if cache_key in cache:
            cache.delete(cache_key)
        return super(ArticleViewSet, self).update(request, *args, **kwargs)

    @detail_route(methods=['POST'])
    def publish(self, request, **kwargs):
        article = self.get_object()
        if article.status != Article.DRAFT:
            raise ValidationError('Article\'s status is not DRAFT')
        article.status = Article.PUBLISHED
        article.published_at = article.published_at or timezone.now()
        article.save()
        return Response(ArticleSerializer(article).data)

    @detail_route(methods=['POST'])
    def restore_published(self, request, **kwargs):
        article = self.get_object()
        if article.status == Article.DELETED and article.published_at:
            article.status = Article.PUBLISHED
            article.deleted_at = None
            article.save()
            return Response(ArticleSerializer(article).data)
        return Response(status=HTTP_400_BAD_REQUEST)

    @detail_route(methods=['POST'])
    def restore_draft(self, request, **kwargs):
        article = self.get_object()
        if article.status == Article.DELETED:
            article.status = Article.DRAFT
            article.deleted_at = None
            article.save()
            return Response(ArticleSerializer(article).data)
        return Response(status=HTTP_400_BAD_REQUEST)


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
        else:
            return Article.objects.none()


class PublicArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status__in=[Article.PUBLISHED, Article.SHARED])\
        .select_related('owner').prefetch_related('images', 'short_url')
    serializer_class = PublicArticleSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        fingerprint = request.META.get('HTTP_X_FINGERPRINT')
        if fingerprint:
            if instance.published_at:
                delta = timezone.now() - instance.published_at
                hours = divmod(delta.days * 86400 + delta.seconds, 3600)[0]

                if hours <= NEW_ARTICLE_AGE:
                    q = Queue(RQ_HIGH_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB),
                              default_timeout=RQ_TIMEOUT)
                else:
                    q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB),
                              default_timeout=RQ_TIMEOUT)

                job = q.enqueue(
                    register_article_view,
                    instance.id,
                    request.user.id if request.user.is_authenticated() else None,
                    fingerprint
                )

        cache_key = get_article_cache_key(kwargs.get('slug', 'undefined'))
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(json.loads(cached_data))
        else:
            serializer = self.get_serializer(instance)
            data = serializer.data
            cache.set(cache_key, json.dumps(data))
            return Response(data)


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
