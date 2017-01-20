#! coding: utf-8

from __future__ import unicode_literals

from uuid import uuid4


def upload_to(path, instance, filename):
    uid = str(uuid4())
    _path = '%s/%s/%s' % (path, uid[:2], uid[2: 4])
    try:
        name, ext = filename.rsplit('.', 1)
    except:
        return u'%s/%s' % (_path, uid)
    else:
        return u'%s/%s.%s' % (_path, uid, ext)
