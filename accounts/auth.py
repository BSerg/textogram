# coding: utf-8

from __future__ import unicode_literals

import hashlib
import requests
from accounts.models import User, SocialLink
from textogram import settings
from common import image_retrieve


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
                        return user
        return None


class PhoneAuthBackend(object):

    def authenticate(self, *args, **kwargs):
        try:
            user = User.objects.get(phone=kwargs.get('phone'), phone_confirmed=True)
            if user.check_password(kwargs.get('password')):
                return user
        except User.DoesNotExist:
            pass
        return None
