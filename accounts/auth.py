# coding: utf-8

from __future__ import unicode_literals

import hashlib
from accounts.models import User

from textogram import settings


class VKAuthBackend(object):
    def authenticate(self, *args, **kwargs):
        if kwargs.get('social') == User.VK:
            try:
                user = None

                m = hashlib.md5()
                check_string = "expire={}mid={}secret={}sid={}{}".format(kwargs.get('expire'),
                                                                         kwargs.get('mid'),
                                                                         kwargs.get('secret'),
                                                                         kwargs.get('sid'),
                                                                         settings.VK_APP_SECRET, )
                m.update(check_string)
                if m.hexdigest() == kwargs.get('sig'):
                    print kwargs.get('mid')


                return user
            except User.DoesNotExist:
                pass
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
