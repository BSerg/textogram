#! coding: utf-8
from __future__ import unicode_literals

import hashlib

from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.cache import cache

from textogram import settings

register = template.Library()

CACHE_KEY_PREFIX = 'static_hash'


@register.simple_tag
def hashed_static(value):
    _hash = cache.get('%s:%s' % (CACHE_KEY_PREFIX, value))
    if not _hash:
        if hasattr(settings, 'STATIC_ROOT'):
            try:
                with staticfiles_storage.open(value, 'rb') as fh:
                    m = hashlib.md5()
                    while True:
                        data = fh.read(8192)
                        if not data:
                            break
                        m.update(data)
                    _hash = m.hexdigest()[:8]
                    cache.set('%s:%s' % (CACHE_KEY_PREFIX, value), _hash, timeout=None)
            except IOError:
                _hash = '_'
        else:
            _hash = '_'
    return '%s?%s' % (static(value), _hash)
