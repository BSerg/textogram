from __future__ import unicode_literals

from django.contrib.auth import logout

from rest_framework import viewsets, mixins, generics, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from rest_framework.views import APIView
from rest_framework import mixins

from accounts.models import User, Subscription, SocialLink, PhoneCode
from api.v1.accounts.permissions import IsAdminOrOwner
from api.v1.accounts.serializers import MeUserSerializer, UserSerializer, PublicUserSerializer, MeSocialLinkSerializer, SubscriptionSerializer

from django.core.validators import URLValidator
from django.forms import ValidationError
import re

from django.contrib.auth import login
from rest_framework.authtoken.models import Token


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

    PHONE_PATTERN = '^\d{10}$'

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print request.data.keys()
        phone = request.data.get('phone')
        existing_user = User.objects.filter(phone=phone)
        if existing_user:
            return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)
        if 'phone' in request.data.keys() and ('code' not in request.data.keys() and 'hash' not in request.data.keys()):
            if phone:
                pattern = re.compile(self.PHONE_PATTERN)
                if pattern.match(phone):
                    code = PhoneCode.objects.create(phone=phone)
                    return Response({'phone': code.phone})
        elif 'phone' in request.data.key() and 'code' in request.data.keys() and 'hash' not in request.data.keys():
            code_string = request.data.get('code')
            if phone and code_string:
                code = PhoneCode.objects.filter(phone=phone, code=code_string, disabled=False, is_confirmed=False).first()
                if code and code.is_active():
                    code.is_confirmed = True
                    code.save()
                    return Response({'phone': phone, 'hash': code.hash})
        elif 'phone' in request.data.key() and 'hash' in request.data.keys() and 'code' not in request.data.keys():
            hash_string = request.data.get('hash')
            password = request.data.get('password')
            password_again = request.data.get('password_again')
            display_name = request.data.get('username')

            if phone and hash_string and password and password_again and display_name:
                code = PhoneCode.objects.get(phone=phone, hash=hash_string, disabled=False).first()

                if not code or (password != password_again):
                    return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)
                display_name = ' '.join(display_name.split())
                display_name = display_name.strip()
                first_name = display_name.split(' ')[0]
                if not first_name:
                    return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)
                last_name = ' '.join(display_name.split(' ')[1:])
                last_name = last_name.strip()
                try:

                    user = User.objects.create_user(phone, password=password, phone=phone,
                                                    first_name=first_name, last_name=last_name)

                    login(request, user)
                    user_data = MeUserSerializer(user).data
                    user_data.update(token=Token.objects.get_or_create(user=user)[0].key)
                    user_data.update(created=True)
                    return Response({'user': user_data})

                except:
                    return Response({'msg': 'error'})

        return Response({'msg': ''}, status=HTTP_400_BAD_REQUEST)


class Logout(APIView):
    def post(self, request):
        logout(request)
        return Response({'msg': 'logged out'})
