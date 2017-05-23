from rest_framework import viewsets, permissions, mixins
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import FieldError
from api.v1.articles.throttles import SearchRateThrottle

from accounts.models import User
from api.v1.statistics.serializers import ArticleCommonStatisticsSerializer, ArticleStatisticsSerializer
from articles.models import Article
from .permissions import IsSelf, IsOwner
from .serializers import UserCommonStatisticsSerializer


class ArticleStatisticsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserCommonStatisticsView(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserCommonStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelf]

    def get_object(self):
        return self.request.user


class ArticleCommonStatisticsListView(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleCommonStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    pagination_class = ArticleStatisticsPagination

    def get_queryset(self):
        return super(ArticleCommonStatisticsListView, self).get_queryset().filter(owner=self.request.user)\
            .exclude(status=Article.DELETED)


class ArticleCommonStatisticsListSearchView(ArticleCommonStatisticsListView):

    throttle_classes = [SearchRateThrottle]

    def get_queryset(self):
        qs = super(ArticleCommonStatisticsListSearchView, self).get_queryset()
        if self.request.query_params.get('q'):
            try:
                qs = qs.filter(title__icontains=self.request.query_params.get('q'))
            except FieldError as e:
                return Article.objects.none()
        return qs


class ArticleStatisticsView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]