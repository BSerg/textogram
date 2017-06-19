# coding: utf-8

from __future__ import unicode_literals

import jwt
import requests
from rest_framework import authentication, exceptions

from accounts.models import User
from textogram import settings
from textogram.local_settings import AUTH_SERVICE_VERIFY_API


public_key_cache = None


def jwt_decode(token, skip_claims=False, drop_cache=False):
    global public_key_cache
    print token
    if not settings.AUTH_PUBLIC_KEY:
        return 'Public key not configured', None

    try:
        if drop_cache:
            public_key = open(settings.AUTH_PUBLIC_KEY).read()
            public_key_cache = None
        else:
            public_key = public_key_cache or open(settings.AUTH_PUBLIC_KEY).read()
            public_key_cache = public_key

    except IOError as e:
        return e, None
    payload = jwt.decode(token, public_key, algorithms=['RS256'])

    try:
        payload = jwt.decode(token, public_key, algorithms=['RS256'])
    except (jwt.exceptions.InvalidKeyError, jwt.exceptions.InvalidAlgorithmError) as e:
        return e, None
    except jwt.DecodeError:
        if skip_claims:
            try:
                payload = jwt.decode(token, public_key, algorithms=['RS256'], options={
                   'verify_exp': False,
                   'verify_nbf': False,
                   'verify_iat': False,
                   'verify_aud': False
                })
            except jwt.DecodeError:
                return 'Invalid token', None
        else:
            return 'Invalid token', None

    return None, payload


def jwt_user_auth(token):
    if not settings.AUTH_PUBLIC_KEY:
        return None

    err, payload = jwt_decode(token)
    if payload:
        r = requests.post(AUTH_SERVICE_VERIFY_API, json={'token': token},
                          headers={'Content-Type': 'application/json'}, verify=settings.AUTH_SERVICE_SSL_VERIFY)
        if r.status_code != 200:
            return None

        if r.json().get('is_valid'):
            user, created = User.objects.get_or_create(username=payload.get('sub'))

            if created:
                user.first_name = payload.get('first_name') or ''
                user.last_name = payload.get('last_name') or ''
                user.avatar_url = payload.get('avatar') or ''
                user.save()

            return user


class AuthServiceBackend(object):
    def authenticate(self, *args, **kwargs):
        token = kwargs.get('token')

        if not token:
            return None

        return jwt_user_auth(token)


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()

        if not auth_header or auth_header[0].lower() != 'bearer':
            return None

        if len(auth_header) != 2:
            raise exceptions.AuthenticationFailed('Wrong authentication header format')

        token = auth_header[1]

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        err, payload = jwt_decode(token)

        if err:
            raise exceptions.AuthenticationFailed(str(err))

        try:
            user = User.objects.get(username=payload.get('sub', ''))
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User is not active or deleted')

        return user, token