from __future__ import unicode_literals

from django.contrib.auth import logout

from rest_framework import viewsets, mixins, generics, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from rest_framework.views import APIView
from rest_framework import mixins

from accounts.models import User, Subscription, SocialLink
from api.v1.accounts.permissions import IsAdminOrOwner
from api.v1.accounts.serializers import MeUserSerializer, UserSerializer, PublicUserSerializer, MeSocialLinkSerializer, SubscriptionSerializer

from django.core.validators import URLValidator
from django.forms import ValidationError


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrOwner]


class MeUserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = MeUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


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


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class SocialLinksViewSet(viewsets.ModelViewSet):

    serializer_class = MeSocialLinkSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SocialLink.objects.all()

    def get_queryset(self):
        return SocialLink.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        url = request.data.get('url')
        validate = URLValidator()
        try:
            validate(url)
            link, created = SocialLink.objects.get_or_create(user=user, url=request.data.get('url'))
            return Response(MeSocialLinkSerializer(link).data)
        except ValidationError:
            return Response({'msg': 'url incorrect'}, status=HTTP_400_BAD_REQUEST)

    @detail_route(methods=['POST'])
    def toggle_hidden(self, request, pk=None):
        obj = self.get_object()
        if obj and obj.is_auth:
            obj.is_hidden = not obj.is_hidden
            obj.save()
            return Response(MeSocialLinkSerializer(obj).data)
        return Response({'msg': 'social link incorrect'}, status=HTTP_400_BAD_REQUEST)


class Registration(APIView):

    def post(self, request):
        print request.data.keys()
        return Response({'msg': ''}, status=HTTP_400_BAD_REQUEST)


class Logout(APIView):
    def post(self, request):
        logout(request)
        return Response({'msg': 'logged out'})
