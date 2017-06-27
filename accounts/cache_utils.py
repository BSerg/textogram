#!coding:utf-8
from __future__ import unicode_literals

from redis import StrictRedis
from accounts.models import User, Subscription
from api.v1.accounts.serializers import PublicUserSerializer
from textogram.settings import REDIS_CACHE_DB, REDIS_CACHE_HOST, REDIS_CACHE_PORT
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


def cache_user_subscribers(user_id=None, subscriber_id=None):
    users = User.objects.filter(**({'id': user_id} if user_id else {}))
    r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
    for user in users:
        params = {'author': user}
        if subscriber_id:
            params['user__id'] = subscriber_id
        subscriptions = Subscription.objects.filter(**params)
        # if subscriber_id and not len(subscriptions):
            # r.

