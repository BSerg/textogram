#! coding: utf-8

from __future__ import unicode_literals
import os
import urllib
from uuid import uuid4
from textogram.settings import MEDIA_ROOT


def upload_to(path, instance, filename):
    uid = str(uuid4())
    _path = '%s/%s/%s' % (path, uid[:2], uid[2: 4])
    try:
        name, ext = filename.rsplit('.', 1)
    except:
        return u'%s/%s' % (_path, uid)
    else:
        return u'%s/%s.%s' % (_path, uid, ext)


def image_upload(instance, filename):
    return upload_to('images', instance, filename)


def file_retrieve(url, path):
    dir, filename = path.rsplit('/', 1)
    try:
        os.makedirs(dir)
    except OSError:
        pass
    try:
        urllib.urlretrieve(url, path)
    except Exception, e:
        return None
    return dir, filename


def image_retrieve(url):
    # try:
    #     url_filename = url.rsplit('/', 1)[1]
    # except:
    #     url_filename = None
    rel_path = image_upload(None, None)
    path = os.path.join(MEDIA_ROOT, rel_path)
    filepath = file_retrieve(url, path)
    if filepath:
        return filepath[0], filepath[1], rel_path