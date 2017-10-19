#! coding: utf-8
from __future__ import unicode_literals

from django.db.models import Q
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

        queryset = User.objects.filter()

        status = self.request.query_params.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)

        elif status == 'banned':
            queryset = queryset.filter(is_active=False)

        search_string = self.request.query_params.get('q') or ''
        if search_string:
            search_string_list = search_string.split(" ")
            first_name_param = search_string_list[0]
            last_name_param = " ".join(search_string_list[1:]).strip()
            if first_name_param and last_name_param:
                queryset = queryset.filter(first_name__startswith=first_name_param,
                                           last_name__startswith=last_name_param)
            elif first_name_param and not last_name_param:
                queryset = queryset.filter(Q(first_name__startswith=first_name_param) |
                                           Q(nickname__startswith=first_name_param))
        return queryset

    def set_ban(self, is_ban):
        try:
            author = self.get_object()
            author.is_active = not is_ban
            author.save()
            return Response(AdminUserSerializer(author).data)
        except User.DoesNotExist:
            return Response({'msg': 'author not found'}, status=HTTP_404_NOT_FOUND)
        except Exception as e:
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
        queryset = Article.objects.filter()
        status = self.request.query_params.get('status')
        if status and status in ('published', 'deleted', 'banned'):
            if status == 'published':
                queryset = queryset.filter(status=Article.PUBLISHED)
            else:
                queryset = queryset.filter(status=Article.DELETED if status == 'deleted' else Article.BANNED)
        # else:
        #     queryset = queryset.filter(status=Article.PUBLISHED)
        search_string = self.request.query_params.get('q')
        if search_string:
            queryset = queryset.filter(title__contains=search_string)
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(owner__id=author)
        return queryset


class MeUserAdminViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = MeUserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_object(self):
        return self.request.user
