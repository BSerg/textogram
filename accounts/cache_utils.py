#!coding:utf-8
from __future__ import unicode_literals

from redis import StrictRedis
from accounts.models import User, Subscription
from api.v1.accounts.serializers import PublicUserSerializer
from textogram.settings import USE_REDIS_CACHE, REDIS_CACHE_DB, REDIS_CACHE_HOST, REDIS_CACHE_PORT
import json


def update_user_cache(user_id=None):
    params = {'id': user_id} if user_id else {}
    users = User.objects.filter(**params)

    r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
    for user in users:
        if user.is_active:
            r.set('user:%s' % user.id, json.dumps(PublicUserSerializer(user).data))
        else:
            r.delete('user:%s' % user.id)
