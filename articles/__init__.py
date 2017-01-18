#! coding: utf-8

from __future__ import unicode_literals

import re

import requests

from textogram.settings import VK_ACCESS_TOKEN


class ArticleContentType:
    TEXT = 1
    HEADER = 2
    LEAD = 3
    VIDEO = 4
    PHOTO = 5
    AUDIO = 6
    QUOTE = 7
    COLUMNS = 8
    PHRASE = 9
    LIST = 10
    DIALOG = 11
    POST = 12


class EmbedHandlerError(Exception):
    def __init__(self, message):
        super(EmbedHandlerError, self).__init__(message)


class EmbedHandler(object):
    TYPE = None
    EMBED_URL_REGEX = []

    def __init__(self, url, **kwargs):
        self.url = url

    @classmethod
    def get_type(cls):
        return cls.TYPE

    @classmethod
    def is_valid(cls, url):
        for regex in cls.EMBED_URL_REGEX:
            if re.match(regex, url):
                return True
        return False

    def get_embed(self):
        raise NotImplementedError


class YoutubeEmbedHandler(EmbedHandler):
    TYPE = 'youtube'
    EMBED_URL_REGEX = [
        r'^https://www\.youtube\.com/watch\?v=(?P<id>[\w\-]+)$',
        r'^https://youtu\.be/(P<id>[\w\-_]+)$'
    ]

    def __init__(self, url, width=800, height=450, **kwargs):
        super(YoutubeEmbedHandler, self).__init__(url, **kwargs)
        self.width = width
        self.height = height

    def _get_id(self):
        for regex in self.EMBED_URL_REGEX:
            r = re.match(regex, self.url)
            if r and r.group('id'):
                return r.group('id')

    def get_embed(self):
        embed = '<iframe width="{width}" height="{height}" src="https://www.youtube.com/embed/{id}" ' \
                'frameborder="0" allowfullscreen/>'
        id = self._get_id()
        if id:
            return embed.format(width=self.width, height=self.height, id=id)


class TwitterEmbedHandler(EmbedHandler):
    TYPE = 'twitter_video'
    EMBED_URL_REGEX = [r'^https://twitter\.com/\w+/status/\d+$']

    def __init__(self, url, type=None, **kwargs):
        super(TwitterEmbedHandler, self).__init__(url, **kwargs)
        self.type = type

    def get_embed(self):
        url = 'https://publish.twitter.com/oembed?align=center%(extra)s&url=%(url)s'
        r = requests.get(url % {'extra': '&widget_type=video' if self.type == 'video' else '', 'url': self.url})
        if r.status_code != 200:
            raise EmbedHandlerError('%s handler error. Twitter api not availabe' % self.TYPE.upper())
        data = r.json()
        if 'html' not in data:
            raise EmbedHandlerError('%s handler error. Twitter api response error' % self.TYPE.upper())
        return data['html']


class VimeoEmbedHandler(EmbedHandler):
    TYPE = 'vimeo'
    EMBED_URL_REGEX = [r'^https://vimeo\.com/(?P<id>\d+)$']
    PLAYER_URL = '//player.vimeo.com/video/{id}'

    def __init__(self, url, width=800, height=450, **kwargs):
        super(VimeoEmbedHandler, self).__init__(url, **kwargs)
        self.width = width
        self.height = height

    def get_embed(self):
        r = re.match(self.EMBED_URL_REGEX[0], self.url)
        if r:
            id = r.group('id')
            embed = '<iframe src="{url}" width="{width}" height="{height}" frameBorder="0" allowFullScreen/>'
            return embed.format(url=self.PLAYER_URL.format(id=id), width=self.width, height=self.height)
        else:
            raise EmbedHandlerError('%s handler error. URL is not valid' % self.TYPE.upper())


class InstagramEmbedHandler(EmbedHandler):
    TYPE = 'instagram'
    EMBED_URL_REGEX = [r'^https://www\.instagram\.com/p/(?P<id>[\w\-_]+)/?$']
    API_URL = 'https://api.instagram.com/oembed/?callback=instgrm.Embeds.process()&url=%(url)s'

    def get_embed(self):
        r = requests.get(self.API_URL % {'url': self.url})
        if r.status_code != 200:
            raise EmbedHandlerError('INSTAGRAM handler error. Instagram api is not available')
        data = r.json()
        if 'html' not in data:
            raise EmbedHandlerError('INSTAGRAM handler error. Instagram api response error')
        return data['html']


class FacebookEmbedHandler(EmbedHandler):
    TYPE = 'fb'
    EMBED_URL_REGEX = [
        r'^https://(www|ru-ru)\.facebook\.com/\w+/posts/\d+/?$',
        r'^https://(www|ru-ru)\.facebook\.com/\w+/videos/\d+/?$',
    ]

    def __init__(self, url, type=None, **kwargs):
        super(FacebookEmbedHandler, self).__init__(url, **kwargs)
        self.type = type

    def get_embed(self):
        iframe_post = '<iframe src="https://www.facebook.com/plugins/post.php?href=%(url)s' \
                 '&width=500&show_text=true&height=500&appId" width="500" height="500" ' \
                 'style="border:none;overflow:hidden" scrolling="no" frameborder="0" ' \
                 'allowTransparency="true"></iframe>'
        iframe_video = '<iframe src="https://www.facebook.com/plugins/video.php?href=%(url)s' \
                       '&width=500&show_text=false&height=280&appId" width="500" height="280" ' \
                       'style="border:none;overflow:hidden" scrolling="no" frameborder="0" ' \
                       'allowTransparency="true"></iframe>'
        iframe = iframe_video if self.type == 'video' else iframe_post
        return iframe % {'url': self.url}

    def _get_embed(self):
        return '<div className="fb-post" data-href=%s/>' % self.url


class VkVideoEmbedHandler(EmbedHandler):
    TYPE = 'vk_video'
    EMBED_URL_REGEX = [r'^https://vk\.com/video(?P<id>-?\d+_\d+)$']
    API_URL = 'https://api.vk.com/method/video.get?v=5.53&access_token=%(token)s&videos=%(id)s'

    def __init__(self, url, width=800, height=450, **kwargs):
        super(VkVideoEmbedHandler, self).__init__(url, **kwargs)
        self.width = width
        self.height = height

    def get_embed(self):
        id = re.match(self.EMBED_URL_REGEX[0], self.url).group('id')
        r = requests.get(self.API_URL % {'token': VK_ACCESS_TOKEN, 'id': id})
        if r.status_code != 200:
            raise EmbedHandlerError('VK handler error. VK api is not available')
        data = r.json()
        if 'response' not in data or 'items' not in data['response']:
            raise EmbedHandlerError('VK handler error. VK api response error')
        items = data['response']['items']
        if items:
            _href = items[0]['player']
            return '<iframe src="%s" width="%d" height="%d" frameborder="0" allowfullscreen></iframe>' \
                   % (_href, self.width, self.height)


EMBED_HANDLERS = [
    YoutubeEmbedHandler,
    TwitterEmbedHandler,
    VimeoEmbedHandler,
    InstagramEmbedHandler,
    FacebookEmbedHandler,
    VkVideoEmbedHandler
]


def get_embed(url, **kwargs):
    for handler_class in EMBED_HANDLERS:
        if handler_class.is_valid(url):
            handler = handler_class(url, **kwargs)
            try:
                return handler.get_embed()
            except EmbedHandlerError:
                return
