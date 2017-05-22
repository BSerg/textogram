# coding: utf-8

from __future__ import unicode_literals

import hashlib
import requests
import requests_oauthlib
from accounts.models import User, SocialLink
from textogram import settings
from common import image_retrieve
from textogram.settings import GOOGLE_CLIENT_ID
from oauth2client import client, crypt
from django.core.exceptions import MultipleObjectsReturned


class VKAuthBackend(object):

    def authenticate(self, *args, **kwargs):
        if kwargs.get('social') == User.VK:

            m = hashlib.md5()
            check_string = "expire={}mid={}secret={}sid={}{}".format(kwargs.get('expire'),
                                                                     kwargs.get('mid'),
                                                                     kwargs.get('secret'),
                                                                     kwargs.get('sid'),
                                                                     settings.VK_APP_SECRET, )
            m.update(check_string)
            if m.hexdigest() == kwargs.get('sig'):
                username = '%s%s' % (User.VK, kwargs.get('mid'))
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    user = User.objects.create_user(username,
                                                    first_name=kwargs.get('user', {}).get('first_name'),
                                                    last_name=kwargs.get('user', {}).get('last_name'),
                                                    social=User.VK,
                                                    )
                    avatar_retrieve = image_retrieve(kwargs.get('user', {}).get('avatar'))
                    if avatar_retrieve:
                        user.avatar = avatar_retrieve[2]
                        user.save()
                    SocialLink.objects.create(
                        user=user, social=SocialLink.VK, is_auth=True,
                        url='https://vk.com/id%s' % kwargs.get('user', {}).get('id')
                    )
                    SocialLink.objects.create(
                        user=user, social=SocialLink.VK, is_auth=False,
                        url='https://vk.com/id%s' % kwargs.get('user', {}).get('id')
                    )
                    user._created = True
                return user
        return None


class FBAuthBackend(object):

    def authenticate(self, *args, **kwargs):
        if kwargs.get('social') == User.FB:
            r = requests.get('https://graph.facebook.com/me', params={
                'access_token': kwargs.get('accessToken'),
                'fields': 'id,first_name,last_name,picture'
            })
            if r.status_code == 200:
                data = r.json()
                if data.get('id') and data.get('first_name'):
                    username = '%s%s' % (User.FB, data.get('id'))
                    try:
                        user = User.objects.get(username=username)
                        return user
                    except User.DoesNotExist:
                        user = User.objects.create_user(username,
                                                        first_name=data.get('first_name'),
                                                        last_name=data.get('last_name'),
                                                        social=User.FB
                                                        )
                        img_url = data.get('picture', {}).get('data', {}).get('url', '')
                        if img_url:
                            avatar_retrieve = image_retrieve(img_url)
                            if avatar_retrieve:
                                user.avatar = avatar_retrieve[2]
                                user.save()
                        SocialLink.objects.create(
                            user=user, social=SocialLink.FB, is_auth=True,
                            url='https://www.facebook.com/%s' % data.get('id')
                        )
                        SocialLink.objects.create(
                            user=user, social=SocialLink.FB, is_auth=False,
                            url='https://www.facebook.com/%s' % data.get('id')
                        )
                        user._created = True
                        return user
        return None


class GoogleAuthClient(object):

    def authenticate(self, *args, **kwargs):

        if kwargs.get('social') == 'google':
            id_token = kwargs.get('id_token')
            id_info = client.verify_id_token(id_token, GOOGLE_CLIENT_ID)

            if id_info and id_info.get('sub'):
                username = '%s%s' % (User.GOOGLE, id_info.get('sub'))
                try:
                    user = User.objects.get(username=username)
                    return user
                except User.DoesNotExist:
                    first_name = id_info.get('given_name') \
                        or id_info.get('name', '').split(' ')[0] \
                        or id_info.get('email', '').split('@')[0]

                    user = User.objects.create_user(
                        username, email=id_info.get('email'), first_name=first_name,
                        last_name=id_info.get('family_name'), social=User.GOOGLE
                    )
                    avatar_retrieve = image_retrieve(id_info.get('picture', ''))
                    if avatar_retrieve:
                        user.avatar = avatar_retrieve[2]
                        user.save()
                    SocialLink.objects.create(
                        user=user, social=SocialLink.GOOGLE, is_auth=True,
                        url='https://plus.google.com/u/0/%s' % id_info.get('sub')
                    )
                    SocialLink.objects.create(
                        user=user, social=SocialLink.GOOGLE, is_auth=False,
                        url='https://plus.google.com/u/0/%s' % id_info.get('sub')
                    )
                    user._created = True
                    return user

        return None


class TwitterAuthBackend(object):

    def authenticate(self, *args, **kwargs):
        if kwargs.get('social') == User.TWITTER and kwargs.get('oauth_token') and kwargs.get('oauth_verifier'):

            oauth = requests_oauthlib.OAuth1(settings.TWITTER_CONSUMER_KEY,
                                             settings.TWITTER_CONSUMER_KEY_SECRET,
                                             kwargs.get('oauth_token'))
            r = requests.get('https://api.twitter.com/oauth/access_token',
                             params={'oauth_verifier': kwargs.get('oauth_verifier')},
                             auth=oauth)
            try:
                data = {p.split('=')[0]: p.split('=')[1] for p in r.text.split('&')}
            except (ValueError, IndexError, TypeError):
                return None
            username = '%s%s' % (User.TWITTER, data.get('user_id'))

            if username:
                try:
                    return User.objects.get(username=username)
                except User.DoesNotExist:
                    return self.__create_new_user(**data)

        return None

    def __create_new_user(self, **kwargs):
        oauth = requests_oauthlib.OAuth1(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_KEY_SECRET,
                                         kwargs.get('oauth_token'), kwargs.get('oauth_token_secret'))
        r = requests.get('https://api.twitter.com/1.1/account/verify_credentials.json', auth=oauth)
        if r.status_code == 200:
            full_data = r.json()
            user = User.objects.create_user(
                '%s%s' % (User.TWITTER, full_data.get('id')), first_name=full_data.get('name'))

            avatar_retrieve = image_retrieve(full_data.get('profile_image_url'))
            if avatar_retrieve:
                user.avatar = avatar_retrieve[2]
                user.save()
            SocialLink.objects.create(
                user=user, social=SocialLink.TWITTER, is_auth=True,
                url='https://twitter.com/%s' % full_data.get('screen_name')
            )
            SocialLink.objects.create(
                user=user, social=SocialLink.TWITTER, is_auth=False,
                url='https://twitter.com/%s' % full_data.get('screen_name')
            )
            user._created = True
            return user
        return None


class EmailAuthBackend(object):

    def authenticate(self, *args, **kwargs):

        try:
            email = kwargs.get('login') or kwargs.get('email')
            if email:

                user = User.objects.get(email=email, is_active=True)
                if user.check_password(kwargs.get('password')):
                    return user
        except (User.DoesNotExist, MultipleObjectsReturned):
            pass
        return None


class PhoneAuthBackend(object):

    def authenticate(self, *args, **kwargs):
        try:
            phone = kwargs.get('login') or kwargs.get('phone')
            if phone:
                user = User.objects.get(phone=phone, phone_confirmed=True)
                if user.check_password(kwargs.get('password')):
                    return user
        except User.DoesNotExist:
            pass
        return None
