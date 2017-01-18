# coding: utf-8

from __future__ import unicode_literals

from accounts.models import User


class PhoneAuthBackend(object):

    def authenticate(self, *args, **kwargs):
        try:
            user = User.objects.get(phone=kwargs.get('phone'), phone_confirmed=True)
            if user.check_password(kwargs.get('password')):
                return user
        except User.DoesNotExist:
            pass
        return None
