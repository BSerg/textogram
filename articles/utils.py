# coding: utf-8
from __future__ import unicode_literals

import hashlib
import re

import markdown
import requests
from django.core.exceptions import ValidationError

from advertisement.models import Banner
from articles import ArticleContentType
from articles.validation import ROOT_VALIDATION_CFG, ContentValidator, BLOCK_BASE_VALIDATION_CFG, BLOCKS_VALIDATION_CFG
from textogram.settings import VK_ACCESS_TOKEN


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
        r'^https://www\.youtube\.com/watch\?v=(?P<id>[\w\-]+)',
        r'^https://youtu\.be/(?P<id>[\w\-]+)'
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
                'frameborder="0" allowfullscreen></iframe>'
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
            embed = '<iframe src="{url}" width="{width}" height="{height}" frameBorder="0" allowFullScreen></iframe>'
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


class SoundCloudEmbedHandler(EmbedHandler):
    TYPE = 'soundcloud'
    EMBED_URL_REGEX = [r'^https://soundcloud\.com/[\w\-]+/[\w\-]+$']
    API_URL = 'http://soundcloud.com/oembed'

    def get_embed(self):
        r = requests.get(self.API_URL, params={'format': 'json', 'iframe': True, 'url': self.url})
        if r.status_code != 200:
            raise EmbedHandlerError('SoundCloud handler error. SoundCloud api is not available')
        data = r.json()
        if 'html' not in data:
            raise EmbedHandlerError('SoundCloud handler error. SoundCloud api response error')
        return data['html']


class PromoDjEmbedHandler(EmbedHandler):
    TYPE = 'promodj'
    EMBED_URL_REGEX = [r'^http://promodj\.com/[\w\-.]+/tracks/(?P<id>\d+)/\w+$']

    def get_embed(self):
        id = re.match(self.EMBED_URL_REGEX[0], self.url).group('id')
        print id
        iframe = '<iframe src="//promodj.com/embed/%(id)s/cover" width="100%%" height="300" ' \
                 'frameborder="0" allowfullscreen></iframe>'
        return iframe % {'id': id}


class YandexMusicEmbedHandler(EmbedHandler):
    TYPE = 'yandex_music'
    EMBED_URL_REGEX = [
        r'https://music\.yandex\.ru/album/(?P<album>\d+)(/track/(?P<track>\d+))?',
    ]

    def get_embed(self):
        url_re = re.match(self.EMBED_URL_REGEX[0], self.url)
        album, track = url_re.group('album'), url_re.group('track')
        if not track:
            return '<iframe frameborder="0" width="900" height="500" ' \
                     'src="https://music.yandex.ru/iframe/#album/%(album)s/"></iframe>' % {'album': album}
        else:
            return '<iframe frameborder="0" width="600" height="100" ' \
                     'src="https://music.yandex.ru/iframe/#track/%(track)s/%(album)s/"></iframe>' % {'album': album, 'track': track}


EMBED_HANDLERS = [
    YoutubeEmbedHandler,
    TwitterEmbedHandler,
    VimeoEmbedHandler,
    InstagramEmbedHandler,
    FacebookEmbedHandler,
    VkVideoEmbedHandler,
    SoundCloudEmbedHandler,
    PromoDjEmbedHandler,
    YandexMusicEmbedHandler
]


def get_embed(url, **kwargs):
    for handler_class in EMBED_HANDLERS:
        if handler_class.is_valid(url):
            handler = handler_class(url, **kwargs)
            try:
                return handler.get_embed()
            except EmbedHandlerError:
                return


# CONTENT META

class ContentBlockMetaGenerator(object):
    @classmethod
    def get_instance(cls, content):
        if content.get('type') in [ArticleContentType.VIDEO, ArticleContentType.AUDIO, ArticleContentType.POST]:
            return EmbedBlockMetaGenerator(content, _type=content['type'])
        return cls(content)

    def __init__(self, content):
        self.content = content

    def is_valid(self):
        is_valid = True
        base_validation_cfg = BLOCK_BASE_VALIDATION_CFG.items()
        validation_cfg = BLOCKS_VALIDATION_CFG.get(self.content.get('type'), {}).items()
        for field, params in base_validation_cfg + validation_cfg:
            try:
                ContentValidator.validate_structure(self.content, field, params)
            except ValidationError:
                is_valid = False
        return is_valid

    def get_content_hash(self):
        return hashlib.md5(str(self.content)).hexdigest()

    def get_meta(self):
        return {
            'is_valid': self.is_valid(),
            'hash': self.get_content_hash()
        }


class EmbedBlockMetaGenerator(ContentBlockMetaGenerator):
    def __init__(self, content, _type=None):
        super(EmbedBlockMetaGenerator, self).__init__(content)
        self.type = _type

    def get_meta(self):
        meta = super(EmbedBlockMetaGenerator, self).get_meta()
        if self.is_valid():
            if self.content['type'] == ArticleContentType.VIDEO:
                embed = get_embed(self.content['value'], type='video')
            else:
                embed = get_embed(self.content['value'])
            meta['embed'] = embed
        return meta


def process_content(content):
    for block in content.get('blocks', []):
        meta = block.pop('__meta', {})
        meta_generator = ContentBlockMetaGenerator.get_instance(block)
        if meta_generator:
            block['__meta'] = meta_generator.get_meta()
    is_valid = True
    for field, params in ROOT_VALIDATION_CFG.items():
        try:
            ContentValidator.validate_structure(content, field, params)
        except ValidationError as e:
            is_valid = False
    content['__meta'] = {'is_valid': is_valid}
    return content


# CONTENT CONVERTER

def content_to_html(content, ads_enabled=False):
    html = []
    if content.get('__meta', {}).get('is_valid'):
        for block in content.get('blocks'):

            if not block.get('__meta', {}).get('is_valid'):
                continue

            if block.get('type') == ArticleContentType.TEXT:
                html.append(
                    markdown.markdown(block.get('value'), safe_mode='escape', extensions=['markdown.extensions.attr_list']))

            elif block.get('type') == ArticleContentType.HEADER:
                html.append(markdown.markdown('## %s' % block.get('value'), safe_mode='escape'))

            elif block.get('type') == ArticleContentType.LEAD:
                html.append('<div class="lead">%s</div>' % markdown.markdown(block.get('value'), safe_mode='escape'))

            elif block.get('type') == ArticleContentType.PHRASE:
                html.append('<div class="phrase">%s</div>' % markdown.markdown(block.get('value'), safe_mode='escape'))

            elif block.get('type') == ArticleContentType.PHOTO:
                photos = []
                for index, photo in enumerate(block.get('photos', [])):
                    photo_class = 'photo photo_%d' % index
                    photo_url = photo.get('image', '') if len(block.get('photos', [])) == 1 else \
                        photo.get('preview') or photo.get('image', '')
                    photos.append(
                        '<img data-id="%d" data-caption="%s" class="%s" src="%s"/>' %
                        (photo.get('id') or 0, photo.get('caption', ''), photo_class, photo_url)
                    )

                if len(block.get('photos', [])) == 1:
                    if block['photos'][0].get('caption'):
                        photo_class = 'photos photos_1'
                        if photo.get('size'):
                            photo_class += ' photo_%s' % photo.get('size')
                        html.append(
                            '<div class="%(_class)s">\n%(content)s\n<div style="clear: both" class="caption">%(caption)s</div>\n</div>' % {
                                '_class': photo_class,
                                'content': '\n'.join(photos),
                                'caption': block['photos'][0]['caption']
                            }
                        )
                    else:
                        html.append(
                            '<div class="photos photos_1">\n%s\n<div style="clear: both"></div>\n</div>' %
                            '\n'.join(photos)
                        )
                elif len(block.get('photos', [])) <= 6:
                    html.append(
                        '<div class="photos %(_class)s">\n%(content)s\n<div style="clear: both"></div>\n</div>' % {
                            '_class': 'photos_%d' % len(block.get('photos', [])),
                            'content': '\n'.join(photos)
                        }
                    )
                else:
                    html.append(
                        '<div class="photos">\n%s\n<div style="clear: both" class="caption">%s</div>\n</div>' %
                        ('\n'.join(photos), 'Галерея из %d фото' % len(block.get('photos', [])))
                    )

            elif block.get('type') == ArticleContentType.LIST:
                html.append(markdown.markdown(block.get('value'), safe_mode='escape'))

            elif block.get('type') == ArticleContentType.QUOTE:
                if block.get('image') and block['image'].get('image'):
                    _image_html = '<img src="%s"/>' % block['image']['image']
                    _html = '<blockquote class="personal">\n%s\n%s\n</blockquote>'
                    html.append(_html % (_image_html, markdown.markdown(block.get('value'), safe_mode='escape')))
                else:
                    html.append('<blockquote>\n%s\n</blockquote>' % markdown.markdown(block.get('value'), safe_mode='escape'))

            elif block.get('type') == ArticleContentType.COLUMNS:
                _html = '<div class="columns">\n<div class="column">\n%(left)s\n</div>\n<div class="column">\n%(right)s\n</div>\n</div>'
                html.append(_html % {
                    'left': '<img src="%s"/>' % (block.get('image') or {}).get('image', ''),
                    'right': markdown.markdown(block.get('value'), safe_mode='escape')
                })

            elif block.get('type') == ArticleContentType.VIDEO:
                if not block.get('__meta', {}).get('embed'):
                    continue
                html.append('<div class="embed video">\n%s\n</div>' % block['__meta']['embed'])

            elif block.get('type') == ArticleContentType.AUDIO:
                if not block.get('__meta', {}).get('embed'):
                    continue
                html.append('<div class="embed audio">\n%s\n</div>' % block['__meta']['embed'])

            elif block.get('type') == ArticleContentType.POST:
                if not block.get('__meta', {}).get('embed'):
                    continue
                html.append('<div class="embed post">\n%s\n</div>' % block['__meta']['embed'])

            elif block.get('type') == ArticleContentType.DIALOG:
                dialogue_html = '<div class="dialogue">\n%s\n</div>'
                participant_data = {}
                for participant in block.get('participants'):
                    id = participant.get('id')
                    if id:
                        participant_data[id] = participant
                dialogue_data = []
                for remark in block.get('remarks'):
                    if not remark.get('value'):
                        continue

                    if remark.get('participant_id') in participant_data:
                        _participant = participant_data[remark.get('participant_id')]

                        if _participant.get('is_interviewer'):
                            remark_html = '<div class="remark question">\n%s\n</div>'
                        else:
                            remark_html = '<div class="remark">\n%s\n</div>'

                        if _participant.get('avatar') and _participant['avatar'].get('image'):
                            remark_html = remark_html % ('<img src="%s"/>\n%s' % (_participant['avatar']['image'], remark.get('value', '')))
                        else:
                            remark_html = remark_html % ('<span data-name="%s"></span>\n%s' % (_participant.get('name', ' ')[0], remark.get('value', '')))

                        dialogue_data.append(remark_html)

                html.append(dialogue_html % '\n'.join(dialogue_data))

    if len(html) and ads_enabled:
        ad_300x250 = Banner.objects.filter(identifier='300x250').first()
        ad_x250 = Banner.objects.filter(identifier='x250').first()
        ad_728x90 = Banner.objects.filter(identifier='728x90').first()

        if len(html) >= 8 and ad_728x90:
            html.insert(4, '<div class="ad ad_728x90">%s</div>' % ad_728x90.code)

        # if ad_x250:
        #     html.insert(0, '<div class="ad ad_x250">%s</div>' % ad_x250.code)

        if ad_300x250:
            html.append('<div class="ad ad_300x250">%s</div>' % ad_300x250.code)

        if ad_728x90:
            html.append('<div class="ad ad_728x90">%s</div>' % ad_728x90.code)

    return '\n'.join(html)
