#! coding: utf-8
from __future__ import unicode_literals

from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination
from accounts.models import User
from articles.models import Article
from rest_framework.decorators import detail_route

from api.v1.admin.serializers import AdminUserSerializer, AdminArticleSerializer
from api.v1.accounts.serializers import MeUserSerializer
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.response import Response


class AdminPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdminUserViewSet(viewsets.ModelViewSet):

    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminUserSerializer
    pagination_class = AdminPagination
    queryset = User.objects.all()

    def get_queryset(self):

        return User.objects.filter()

    def set_ban(self, is_ban):
        try:
            author = self.get_object()
            print author, is_ban
            author.is_active = not is_ban
            author.save()
            return Response(AdminUserSerializer(author).data)
        except User.DoesNotExist:
            return Response({'msg': 'author not found'}, status=HTTP_404_NOT_FOUND)
        except Exception:
            return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)

    @detail_route(methods=['PATCH'], permission_classes=[permissions.IsAdminUser])
    def ban(self, request, *args, **kwargs):
        return self.set_ban(True)

    @detail_route(methods=['PATCH'], permission_classes=[permissions.IsAdminUser])
    def un_ban(self, request, *args, **kwargs):
        return self.set_ban(False)


class AdminArticleViewSet(viewsets.ModelViewSet):

    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminArticleSerializer
    pagination_class = AdminPagination
    queryset = Article.objects.all()

    def get_queryset(self):
        # print self.request.user
        return Article.objects.filter()


class MeUserAdminViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = MeUserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_object(self):
        return self.request.user
