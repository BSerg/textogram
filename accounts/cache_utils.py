#!coding:utf-8
from __future__ import unicode_literals

from redis import StrictRedis
from accounts.models import User, Subscription
from api.v1.accounts.serializers import PublicUserSerializer
from textogram.settings import REDIS_CACHE_DB, REDIS_CACHE_HOST, REDIS_CACHE_PORT, REDIS_CACHE_KEY_PREFIX
import json


def update_user_cache(user_id=None):
    params = {'id': user_id} if user_id else {}
    users = User.objects.filter(**params)

    r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
    for user in users:
        if user.is_active:
            r.set('%s:user:%s' % (REDIS_CACHE_KEY_PREFIX, user.nickname), json.dumps(PublicUserSerializer(user).data))
        else:
            r.delete('%s:user:%s' % (REDIS_CACHE_KEY_PREFIX, user.nickname))
