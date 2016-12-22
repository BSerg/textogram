from __future__ import unicode_literals

from rest_framework import viewsets, mixins, generics, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from accounts.models import User
from api.v1.accounts.permissions import IsAdminOrOwner
from api.v1.accounts.serializers import UserSerializer, PublicUserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrOwner]

    @list_route(methods=['GET'])
    def me(self, request):
        return Response(UserSerializer(request.user, many=False).data)


class PublicUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = PublicUserSerializer
    permission_classes = [permissions.AllowAny]
