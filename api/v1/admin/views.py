#! coding: utf-8
from __future__ import unicode_literals


from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination
from accounts.models import User
from articles.models import Article

from api.v1.admin.serializers import AdminArticleSerializer
from api.v1.accounts.serializers import UserSerializer


class AdminPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdminUserViewSet(viewsets.ModelViewSet):

    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer
    pagination_class = AdminPagination
    queryset = User.objects.all()

    def get_queryset(self):

        return User.objects.filter()


class AdminArticleViewSet(viewsets.ModelViewSet):

    permission_classes = [permissions.AllowAny]
    serializer_class = AdminArticleSerializer
    pagination_class = AdminPagination
    queryset = Article.objects.all()

    def get_queryset(self):
        # print self.request.user
        return Article.objects.filter()
