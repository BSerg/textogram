from __future__ import unicode_literals

import base64
import json

from django.core.cache import cache
from django.core.exceptions import FieldError
from django.core.files.base import ContentFile
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
    PublicArticleSerializerMin, DraftArticleSerializer, PublicArticleLimitedSerializer, PublicArticleFeedSerializer
from api.v1.articles.throttles import SearchRateThrottle, ImageUploadRateThrottle
from api.v1.payments.serializers import PayWallOrderSerializer
from articles.models import Article, ArticleImage, ArticleUserAccess
from articles.tasks import register_article_view
from articles.utils import get_article_cache_key
from payments.models import PayWallOrder
from textogram.settings import RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT, RQ_HIGH_QUEUE, PAYWALL_ENABLED


class ArticleSetPagination(PageNumberPagination):
    page_size = 20
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
    throttle_classes = [ImageUploadRateThrottle]

    @list_route(methods=['POST'])
    def base64(self, request, **kwargs):
        article_id = request.data.get('article')
        data = request.data.get('image')
        try:
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
            im = ArticleImage(article_id=article_id, image=data)
            im.save()
            return Response(ArticleImageSerializer(im, context={'request': self.request}).data, status=HTTP_201_CREATED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)


class PublicArticleListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Article.objects.select_related('owner')
    serializer_class = PublicArticleSerializerMin
    permission_classes = [permissions.AllowAny]
    pagination_class = ArticleSetPagination
    lookup_field = 'slug'

    def get_queryset(self):
        qs = super(PublicArticleListViewSet, self).get_queryset()
        if self.request.query_params.get('feed') and self.request.user.is_authenticated:
            subscriptions = Subscription.objects.filter(user=self.request.user)
            qs = qs.prefetch_related('owner__author').filter(owner__author__in=subscriptions, status=Article.PUBLISHED, link_access=False)
        elif self.request.query_params.get('drafts') and self.request.user.is_authenticated:
            qs = qs.filter(owner=self.request.user, status=Article.DRAFT)
        elif self.request.query_params.get('user'):
            try:
                user_id = int(self.request.query_params.get('user'))
            except ValueError:
                return Article.objects.none()

            if self.request.user.is_authenticated and self.request.user.id == user_id:
                qs = qs.filter(owner=self.request.user, status=Article.PUBLISHED)
            else:
                qs = qs.filter(owner_id=user_id, status=Article.PUBLISHED, link_access=False)
        else:
            qs = Article.objects.none()

        return qs


class SearchPublicArticleViewSet(PublicArticleListViewSet):
    throttle_classes = [SearchRateThrottle]

    def get_queryset(self):
        qs = super(SearchPublicArticleViewSet, self).get_queryset()
        if self.request.query_params.get('q'):
            try:
                qs = qs.filter(title__icontains=self.request.query_params.get('q'))
            except FieldError as e:
                return Article.objects.none()
        return qs


class PublicArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.filter(status__in=[Article.PUBLISHED, Article.SHARED])\
        .select_related('owner').prefetch_related('images', 'short_url')
    serializer_class = PublicArticleSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if PAYWALL_ENABLED:
            article = self.get_object()
            if article.paywall_enabled:
                if not self.request.user.is_authenticated():
                    return PublicArticleLimitedSerializer
                user_accessed = ArticleUserAccess.objects.filter(article=article, user=self.request.user).exists()
                if article.owner != self.request.user and not user_accessed:
                    return PublicArticleLimitedSerializer

        return super(PublicArticleViewSet, self).get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        fingerprint = request.META.get('HTTP_X_FINGERPRINT')

        if fingerprint:
            q = Queue(RQ_HIGH_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB),
                      default_timeout=RQ_TIMEOUT)
            job = q.enqueue(
                register_article_view,
                kwargs.get('slug'),
                request.user.id if request.user.is_authenticated() else None,
                fingerprint
            )

        cache_key = get_article_cache_key(kwargs.get('slug', 'undefined'))
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(json.loads(cached_data))
        else:
            serializer = self.get_serializer(self.get_object())
            data = serializer.data
            cache.set(cache_key, json.dumps(serializer.data))
            return Response(data)

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def buy(self, request, *args, **kwargs):
        article = self.get_object()
        if not article.paywall_enabled:
            return Response({'msg': 'Article doesn\'t have PayWall option'}, status=HTTP_400_BAD_REQUEST)
        if article.has_access(request.user):
            return Response({'msg': 'You already have access to this article'}, status=HTTP_400_BAD_REQUEST)
        order, created = PayWallOrder.objects.get_or_create(
            article=article,
            customer=request.user,
            price=article.paywall_price,
            currency=article.paywall_currency
        )
        return Response(PayWallOrderSerializer(order).data)

    @detail_route(methods=['GET'])
    def recommendations(self, request, *args, **kwargs):
        article = self.get_object()
        recommendations = self.get_queryset().filter(owner=article.owner, published_at__lt=article.published_at).order_by('-published_at')[:5]
        return Response(PublicArticleFeedSerializer(recommendations, many=True).data)


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
    serializer_class = PublicArticleSerializerMin
