#!coding:utf-8
from __future__ import unicode_literals

import json

from redis import StrictRedis

from advertisement.utils import serialize_banners
from textogram.settings import REDIS_CACHE_DB, REDIS_CACHE_HOST, REDIS_CACHE_PORT, REDIS_CACHE_KEY_PREFIX


def update_advertisements_cache():
    r = StrictRedis(host=REDIS_CACHE_HOST, port=REDIS_CACHE_PORT, db=REDIS_CACHE_DB)
    banners = serialize_banners()
    if banners:
        r.set('%s:advertisements:banners' % REDIS_CACHE_KEY_PREFIX, json.dumps(banners))
