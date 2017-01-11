from __future__ import unicode_literals

from django.contrib.auth import logout

from rest_framework import viewsets, mixins, generics, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND

from rest_framework.views import APIView

from accounts.models import User, Subscription
from api.v1.accounts.permissions import IsAdminOrOwner
from api.v1.accounts.serializers import MeUserSerializer, UserSerializer, PublicUserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrOwner]

    @list_route(methods=['GET'])
    def me(self, request):
        try:
            return Response(MeUserSerializer(request.user, many=False).data)
        except AttributeError:
            return Response(status=HTTP_404_NOT_FOUND)


class PublicUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = PublicUserSerializer
    permission_classes = [permissions.AllowAny]

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        try:
            author = User.objects.get(pk=pk)
            Subscription.objects.get_or_create(user=request.user, author=author)
            return Response({'msg': 'subscribed successfully'})

        except User.DoesNotExist:
            return Response({'msg': 'author not found'}, status=HTTP_404_NOT_FOUND)

    @detail_route(methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def un_subscribe(self, request, pk=None):
        try:
            author = User.objects.get(pk=pk)
            subscription = Subscription.objects.get(user=request.user, author=author)
            subscription.delete()
            return Response({'msg': 'unSubscribed successfully'})

        except User.DoesNotExist:
            return Response({'msg': 'author not found'}, status=HTTP_404_NOT_FOUND)
        except Subscription.DoesNotExist:
            return Response({'msg': 'not subscribed'}, status=HTTP_404_NOT_FOUND)


class SubscriptionViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class Logout(APIView):

    def post(self, request):
        logout(request)
        return Response({'msg': 'logged out'})
