#! coding: utf-8
from __future__ import unicode_literals

from accounts import PASSWORD_PATTERN, PHONE_PATTERN, FIRST_NAME_PATTERN, LAST_NAME_PATTERN

from rest_framework import viewsets, mixins, generics, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from rest_framework.views import APIView
from rest_framework import mixins

from accounts.models import User, Subscription, SocialLink, PhoneCode
from api.v1.accounts.permissions import IsAdminOrOwner
from api.v1.accounts.serializers import MeUserSerializer, UserSerializer, PublicUserSerializer, MeSocialLinkSerializer, SubscriptionSerializer

from django.core.validators import URLValidator
from django.forms import ValidationError
import re

from django.contrib.auth import authenticate, login, logout
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


def send_message(phone, code):
    pass


class RegistrationView(APIView):

    # PHONE_PATTERN = '^\d{7,18}$'
    # PASSWORD_PATTERN = '^[^\s]{5,}$'
    # FIRST_NAME_PATTERN = '^[A-Za-zА-Яа-я][\w]+$'
    # LAST_NAME_PATTERN = '^(\w+\s?)*$'

    permission_classes = [permissions.AllowAny]

    def post(self, request):

        phone = request.data.get('phone')
        existing_user = User.objects.filter(phone=phone)
        if existing_user:
            return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)
        if 'phone' in request.data.keys() and ('code' not in request.data.keys() and 'hash' not in request.data.keys()):
            if phone:
                pattern = re.compile(PHONE_PATTERN)
                if pattern.match(phone):
                    code = PhoneCode.objects.create(phone=phone)
                    send_message(phone, code.code)
                    return Response({'phone': code.phone})
        elif 'phone' in request.data.keys() and 'code' in request.data.keys() and 'hash' not in request.data.keys():
            code_string = request.data.get('code')
            if phone and code_string:
                code = PhoneCode.objects.filter(phone=phone, code=code_string, disabled=False, is_confirmed=False).first()
                if code and code.is_active():
                    code.is_confirmed = True
                    code.save()
                    return Response({'phone': phone, 'hash': code.hash})
        elif 'phone' in request.data.keys() and 'hash' in request.data.keys() and 'code' not in request.data.keys():
            hash_string = request.data.get('hash')
            password = request.data.get('password')
            # password_again = request.data.get('password_again')
            display_name = request.data.get('username')

            if phone and hash_string and password and display_name:
                code = PhoneCode.objects.filter(phone=phone, hash=hash_string, disabled=False).first()
                pattern_password = re.compile(PASSWORD_PATTERN)

                if not code or not pattern_password.match(password):
                    return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)
                display_name = ' '.join(display_name.split())
                display_name = display_name.strip()
                first_name = display_name.split(' ')[0]
                last_name = ' '.join(display_name.split(' ')[1:])
                last_name = last_name.strip()
                first_name_pattern = re.compile(FIRST_NAME_PATTERN, flags=re.U)
                last_name_pattern = re.compile(LAST_NAME_PATTERN, flags=re.U)
                code.disabled = True
                code.save()
                if not first_name or not first_name_pattern.match(first_name) or not last_name_pattern.match(last_name):
                    return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)
                try:
                    un = '+%s' % phone
                    user_created = User.objects.create_user(un, password=password, phone=phone, phone_confirmed=True,
                                                            first_name=first_name, last_name=last_name)

                    user = authenticate(phone=user_created.phone, password=password)
                    if user and user == user_created:
                        user_data = MeUserSerializer(user).data
                        user_data.update(token=Token.objects.get_or_create(user=user)[0].key)
                        user_data.update(created=True)
                        return Response({'user': user_data})
                except Exception as e:
                    pass

        return Response({'msg': ''}, status=HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):

    permission_classes = [permissions.AllowAny]

    # PASSWORD_PATTERN = '^[^\s]{5,}$'

    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)

        if 'code' not in request.data.keys() and 'hash' not in request.data.keys():
            code = PhoneCode.objects.create(phone=phone)
            send_message(phone, code.code)
            return Response({'phone': code.phone})

        elif 'code' in request.data.keys() and 'hash' not in request.data.keys():
            code = PhoneCode.objects.filter(phone=phone, code=request.data.get('code'),
                                            disabled=False, is_confirmed=False).first()
            if code and code.is_active():
                code.is_confirmed = True
                code.save()
                return Response({'phone': phone, 'hash': code.hash})
        elif 'code' not in request.data.keys() and 'hash' in request.data.keys():
            code = PhoneCode.objects.filter(phone=phone, hash=request.data.get('hash'), disabled=False).first()
            pattern_password = re.compile(PASSWORD_PATTERN)
            password = request.data.get('password', '')
            if code and pattern_password.match(password):
                code.disabled = True
                code.save()
                user.set_password(password)
                user.save()
                user_data = MeUserSerializer(user).data
                user_data.update(token=Token.objects.get_or_create(user=user)[0].key)
                user_data.update(created=True)
                return Response({'user': user_data})

        return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)


class SetPhonePasswordView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(phone=phone)
            if user and user != request.user:
                return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            pass
        if 'code' not in request.data.keys() and 'hash' not in request.data.keys():

            code = PhoneCode.objects.create(phone=phone)
            send_message(phone, code.code)
            return Response({'phone': code.phone})
        elif 'code' in request.data.keys() and 'hash' not in request.data.keys():
            code = PhoneCode.objects.filter(phone=phone, code=request.data.get('code'),
                                            disabled=False, is_confirmed=False).first()
            if code and code.is_active():
                code.is_confirmed = True
                code.save()
                return Response({'phone': phone, 'hash': code.hash})

        elif 'code' not in request.data.keys() and 'hash' in request.data.keys():
            code = PhoneCode.objects.filter(phone=phone, hash=request.data.get('hash'), disabled=False).first()
            phone_pattern = re.compile(PHONE_PATTERN)
            password = request.data.get('password', '')
            pattern_password = re.compile(PASSWORD_PATTERN)
            if code and phone_pattern.match(phone) and pattern_password.match(password):
                code.disabled = True
                code.save()
                user = self.request.user
                user.phone = phone
                user.phone_confirmed = True
                user.set_password(password)
                user.save()
                user_data = MeUserSerializer(user).data
                return Response({'user': user_data})

        return Response({'msg': 'error'}, status=HTTP_400_BAD_REQUEST)


class Login(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = authenticate(**request.data)
        if user:
            user_data = MeUserSerializer(user).data
            user_data.update(token=Token.objects.get_or_create(user=user)[0].key)
            if getattr(user, '_created', False):
                user_data.update(created=True)
            return Response(user_data)

        return Response({'msg': 'error'}, status=HTTP_401_UNAUTHORIZED)


class Logout(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({'msg': 'logged out'})
