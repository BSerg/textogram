from rest_framework import viewsets, permissions, mixins
from rest_framework.pagination import PageNumberPagination

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
    #lookup_field = 'nickname'
    #lookup_url_kwarg = 'nickname'

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


class ArticleStatisticsView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]