# coding: utf-8
from __future__ import unicode_literals

import hashlib
import json
import math
import subprocess
from copy import copy
from tempfile import NamedTemporaryFile

import re

import markdown
import requests
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property

from advertisement import BannerID
from articles import ArticleContentType
from articles.validators import ROOT_VALIDATION_CFG, ContentValidator, BLOCK_BASE_VALIDATION_CFG, BLOCKS_VALIDATION_CFG
from textogram.settings import VK_ACCESS_TOKEN, BANNER_DENSITY, THUMBNAIL_SMALL_SIZE, THUMBNAIL_REGULAR_SIZE, \
    THUMBNAIL_MEDIUM_SIZE


class EmbedHandlerError(Exception):
    def __init__(self, message):
        super(EmbedHandlerError, self).__init__(message)


class EmbedHandler(object):
    TYPE = None
    EMBED_URL_REGEX = []
    EMBED_CODE_REGEX = []

    def __init__(self, url, **kwargs):
        self.url = url

    @classmethod
    def url_valid(cls, url):
        for regex in cls.EMBED_URL_REGEX:
            r = re.match(regex, url)
            if r:
                return r
        return False

    @classmethod
    def code_valid(cls, code):
        for regex in cls.EMBED_CODE_REGEX:
            r = re.match(regex, code)
            if r:
                return r
        return False

    @classmethod
    def is_valid(cls, value):
        return cls.url_valid(value) or cls.code_valid(value)

    def get_embed(self):
        raise NotImplementedError

    @classmethod
    def get_type(cls):
        return cls.TYPE

    def get_id(self):
        return None

    def get_width(self):
        return None

    def get_height(self):
        return None

    @property
    def data(self):
        return {
            'url': self.url,
            'type': self.get_type(),
            'id': self.get_id(),
            'width': self.get_width(),
            'height': self.get_height(),
            'embed': self.get_embed(),
        }


class YoutubeEmbedHandler(EmbedHandler):
    TYPE = 'youtube'
    EMBED_URL_REGEX = [
        r'^https://www\.youtube\.com/watch\?v=(?P<id>[\w\-]+)(&[\w\-]+=[^&]+)*',
        r'^https://youtu\.be/(?P<id>[\w\-]+)([?&][\w\-]+=[^&]+)*'
    ]
    EMBED_CODE_REGEX = [
        r'^<iframe( width=\"(?P<width>\d+)\")?( height=\"(?P<height>\d+)\")? src=\"https:\/\/www\.youtube(-nocookie)?\.com\/embed\/(?P<id>[\w\-]+)((\?|&|&amp;)\w+=\w+)*\"( frameborder=\"(0|1)\")?( allowfullscreen)?><\/iframe>$',
    ]

    def __init__(self, url, width=560, height=315, **kwargs):
        super(YoutubeEmbedHandler, self).__init__(url, **kwargs)
        self.width = width
        self.height = height

    def _get_match(self):
        return self.url_valid(self.url) or self.code_valid(self.url)

    def _get_id(self):
        for regex in self.EMBED_URL_REGEX:
            r = re.match(regex, self.url)
            if r and r.group('id'):
                return r.group('id')

    def get_id(self):
        r = self._get_match()
        if r:
            return r.group('id')

    def get_width(self):
        r = self._get_match()
        if r:
            try:
                return r.group('width')
            except:
                pass
        return self.width

    def get_height(self):
        r = self._get_match()
        if r:
            try:
                return r.group('height')
            except:
                pass
        return self.height

    def get_embed(self):
        if self.url_valid(self.url):
            embed = '<iframe width="{width}" height="{height}" src="https://www.youtube.com/embed/{id}" ' \
                    'frameborder="0" allowfullscreen></iframe>'
            id = self._get_id()
            if id:
                return embed.format(width=self.width, height=self.height, id=id)
        elif self.code_valid(self.url):
            return self.url


class TwitterEmbedHandler(EmbedHandler):
    TYPE = 'twitter'
    EMBED_URL_REGEX = [r'^https://twitter\.com/\w+/status/(?P<id>\d+)\/?([&?][\w\-]+=[^&]+)*$']
    EMBED_CODE_REGEX = [
        r'^<blockquote class="twitter-(tweet|video)" data-lang="\w+"><p lang="\w+" dir="ltr">.+</blockquote>\s*<script async src="//platform\.twitter\.com\/widgets\.js" charset="utf-8"></script>$',
    ]

    def __init__(self, url, type=None, **kwargs):
        super(TwitterEmbedHandler, self).__init__(url, **kwargs)
        self.type = type

    def get_id(self):
        if self.url_valid(self.url):
            return self.url_valid(self.url).group('id')
        elif self.code_valid(self.url):
            r = re.search(self.EMBED_URL_REGEX[0], self.url)
            if r:
                return r.group('id')

    def get_embed(self):
        if self.url_valid(self.url):
            url = 'https://publish.twitter.com/oembed?align=center%(extra)s&url=%(url)s'
            r = requests.get(url % {'extra': '&widget_type=video' if self.type == 'video' else '', 'url': self.url})
            if r.status_code != 200:
                raise EmbedHandlerError('%s handler error. Twitter api not availabe' % self.TYPE.upper())
            data = r.json()
            if 'html' not in data:
                raise EmbedHandlerError('%s handler error. Twitter api response error' % self.TYPE.upper())
            return data['html']
        elif self.code_valid(self.url):
            return self.url


class VimeoEmbedHandler(EmbedHandler):
    TYPE = 'vimeo'
    EMBED_URL_REGEX = [r'^https://vimeo\.com/(?P<id>\d+)(#\w+=\w+)?$']
    EMBED_CODE_REGEX = [
        r'^<iframe src=\"https:\/\/player\.vimeo\.com\/video\/(?P<id>\d+)([\?&]\w+=\w+)*\" width=\"(?P<width>\d+)\" height=\"(?P<height>\d+)\"( frameborder=\"(0|1)\")?( (webkit|moz)?allowfullscreen)*><\/iframe>(\s*<p>(\s*.)+<\/p>)?$',
    ]
    PLAYER_URL = '//player.vimeo.com/video/{id}'

    def __init__(self, url, width=640, height=360, **kwargs):
        super(VimeoEmbedHandler, self).__init__(url, **kwargs)
        self.width = width
        self.height = height

    def _get_match(self):
        return self.url_valid(self.url) or self.code_valid(self.url)

    def get_id(self):
        r = self._get_match()
        if r:
            return r.group('id')

    def get_width(self):
        r = self._get_match()
        if r:
            try:
                return r.group('width')
            except:
                pass
        return self.width

    def get_height(self):
        r = self._get_match()
        if r:
            try:
                return r.group('height')
            except:
                pass
        return self.height

    def get_embed(self):
        if self.url_valid(self.url):
            r = re.match(self.EMBED_URL_REGEX[0], self.url)
            if r:
                id = r.group('id')
                embed = '<iframe src="{url}" width="{width}" height="{height}" frameBorder="0" allowFullScreen></iframe>'
                return embed.format(url=self.PLAYER_URL.format(id=id), width=self.width, height=self.height)
            else:
                raise EmbedHandlerError('%s handler error. URL is not valid' % self.TYPE.upper())
        elif self.code_valid(self.url):
            return self.url


class InstagramEmbedHandler(EmbedHandler):
    TYPE = 'instagram'
    EMBED_URL_REGEX = [r'^https://www\.instagram\.com/p/(?P<id>[\w\-_]+)/?([&?][\w\-]+=[^&]+)*$']
    API_URL = 'https://api.instagram.com/oembed/?callback=instgrm.Embeds.process()&url=%(url)s'

    def get_id(self):
        r = self.url_valid(self.url)
        if r:
            return r.group('id')

    def get_embed(self):
        r = requests.get(self.API_URL % {'url': self.url})
        if r.status_code != 200:
            raise EmbedHandlerError('INSTAGRAM handler error. Instagram api is not available')
        data = r.json()
        if 'html' not in data:
            raise EmbedHandlerError('INSTAGRAM handler error. Instagram api response error')
        return data['html']


class FacebookEmbedHandler(EmbedHandler):
    TYPE = 'facebook'
    EMBED_URL_REGEX = [
        r'^https://(www|ru-ru)\.facebook\.com/[\w\-._]+/(posts|videos)/(?P<id>\d+)/?([&?][\w\-]+=[^&]+)*$',
    ]
    EMBED_CODE_REGEX = [
        r'<iframe src=\"https:\/\/[\w\-]+\.facebook\.com\/plugins\/(post|video)\.php\?href=https(%3A|:)(%2F%2F|\/\/)www\.facebook\.com(%2F|\/)[\w\-.]+(%2F|\/)(posts|videos)(%2F|\/)(?P<id>\d+)(%2F|\/)?(&show_text=(0|1))?&width=\d+\"( width=\"\d+\")?( height=\"\d+\")?( style=\".+\")?( scrolling=\"(yes|no)\")?( frameborder=\"(0|1)\")?( allowTransparency=\"(true|false)\")?(allowFullScreen=\"(true|false)\")?><\/iframe>'
    ]

    def __init__(self, url, type=None, **kwargs):
        super(FacebookEmbedHandler, self).__init__(url, **kwargs)
        self.type = type

    def _get_embed(self):
        if self.url_valid(self.url):
            iframe_post = '<iframe src="https://www.facebook.com/plugins/post.php?href=%(url)s' \
                     '&width=500&show_text=true&appId" width="500"' \
                     'style="border:none;overflow:hidden" scrolling="no" frameborder="0" ' \
                     'allowTransparency="true"></iframe>'
            iframe_video = '<iframe src="https://www.facebook.com/plugins/video.php?href=%(url)s' \
                           '&width=500&show_text=false&height=280&appId" width="500" height="280" ' \
                           'style="border:none;overflow:hidden" scrolling="no" frameborder="0" ' \
                           'allowTransparency="true"></iframe>'
            iframe = iframe_video if self.type == 'video' else iframe_post
            return iframe % {'url': self.url}
        elif self.code_valid(self.url):
            return self.url

    def get_id(self):
        r = self.url_valid(self.url) or self.code_valid(self.url)
        if r:
            return r.group('id')

    def get_embed(self):
        if self.url_valid(self.url):
            return '<div class="fb-post" data-href=%s/>' % self.url
        elif self.code_valid(self.url):
            return self.url


class VkEmbedHandler(EmbedHandler):
    TYPE = 'vk'
    EMBED_CODE_REGEX = [
        r'^<div id="vk_post_-?\d+_\d+"></div>\s*<script type="text/javascript">[^<]+</script>$',
    ]

    def get_embed(self):
        return self.url


class VkVideoEmbedHandler(EmbedHandler):
    TYPE = 'vk_video'
    EMBED_URL_REGEX = [r'^https://vk\.com/video(?P<id>-?\d+_\d+)/?([&?][\w\-]+=[^&]+)*$']
    EMBED_CODE_REGEX = [
        r'^<iframe src=\"\/\/vk\.com\/video_ext\.php\?oid=-?\d+&id=\d+&hash=\w+&hd=\d\"( width=\"\d+\")?( height=\"\d+\")?( frameborder=\"(0|1)\")?( allowfullscreen)?><\/iframe>$'
    ]
    API_URL = 'https://api.vk.com/method/video.get?v=5.53&access_token=%(token)s&videos=%(id)s'

    def __init__(self, url, width=800, height=450, **kwargs):
        super(VkVideoEmbedHandler, self).__init__(url, **kwargs)
        self.width = width
        self.height = height

    def get_embed(self):
        if self.url_valid(self.url):
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
        elif self.code_valid(self.url):
            return self.url


class CoubEmbedHandler(EmbedHandler):
    TYPE = 'coub'
    EMBED_URL_REGEX = [
        r'^https?://coub\.com/view/(?P<id>\w+)$'
    ]
    EMBED_CODE_REGEX = [
        r'^<iframe src="//coub\.com/embed/\w+((\?|&)\w+=(true|false))*"( allowfullscreen="(true|false)")?( frameborder="(0|1)")?( width="\d+")?( height="\d+")?></iframe>(<script async src="//c-cdn\.coub\.com/embed-runner\.js"></script>)?$'
    ]

    def _get_id(self):
        for regex in self.EMBED_URL_REGEX:
            r = re.match(regex, self.url)
            if r and r.group('id'):
                return r.group('id')

    def get_embed(self):
        if self.url_valid(self.url):
            _id = self._get_id()
            return '<iframe src="//coub.com/embed/{id}?muted=false&autostart=false&originalSize=false&startWithHD=false" allowfullscreen="true" frameborder="0" width="640" height="360"></iframe>'.format(id=_id)
        elif self.code_valid(self.url):
            return self.url


class SoundCloudEmbedHandler(EmbedHandler):
    TYPE = 'soundcloud'
    EMBED_URL_REGEX = [r'^https://soundcloud\.com/[\w\-]+/(?P<id>[\w\-]+)$']
    EMBED_CODE_REGEX = [
        r'^<iframe( width=\"(?P<width>\d+%?)\")?( height=\"(?P<height>\d+)\")?( scrolling=\"(yes|no)\")?( frameborder=\"(yes|no)\")? src=\"https://w\.soundcloud\.com/player/\?((&amp;|&)?\w+=(\w+|true|false))*(&amp;|&)?url=https?(%3A|:)(%2F|/)(%2F|/)api\.soundcloud\.com(%2F|/)tracks(%2F|/)(?P<id>\d+)((&amp;|&)\w+=(\w+|true|false))*\"></iframe>$'
    ]
    API_URL = 'http://soundcloud.com/oembed'

    @cached_property
    def _data(self):
        if self.url_valid(self.url):
            r = requests.get(self.API_URL, params={'format': 'json', 'iframe': True, 'url': self.url})
            if r.status_code != 200:
                raise EmbedHandlerError('SoundCloud handler error. SoundCloud api is not available')
            return r.json()

    def get_id(self):
        data = self._data
        if data and 'html' in data:
            r = re.match(self.EMBED_CODE_REGEX[0], data['html'].replace('\\', ''))
            if r:
                return r.group('id')

    def get_width(self):
        data = self._data
        if data and 'html' in data:
            r = re.match(self.EMBED_CODE_REGEX[0], data['html'].replace('\\', ''))
            if r:
                return r.group('width')

    def get_height(self):
        data = self._data
        if data and 'html' in data:
            r = re.match(self.EMBED_CODE_REGEX[0], data['html'].replace('\\', ''))
            if r:
                return r.group('height')

    def get_embed(self):
        if self.url_valid(self.url):
            data = self._data
            if 'html' not in data:
                raise EmbedHandlerError('SoundCloud handler error. SoundCloud api response error')
            return data['html']
        elif self.code_valid(self.url):
            return self.url


class PromoDjEmbedHandler(EmbedHandler):
    TYPE = 'promodj'
    EMBED_URL_REGEX = [r'^http://promodj\.com/[\w\-.]+/tracks/(?P<id>\d+)/\w+$']
    EMBED_CODE_REGEX = [
        r'^<iframe src="//promodj\.com/embed/\d+/(cover|big)"( width="\d+%?")?( height="\d+")?( style="[^"]+")?( frameborder="(0|1)")?( allowfullscreen)?></iframe>$'
    ]

    def get_embed(self):
        if self.url_valid(self.url):
            id = re.match(self.EMBED_URL_REGEX[0], self.url).group('id')
            iframe = '<iframe src="//promodj.com/embed/%(id)s/cover" width="100%%" height="300" ' \
                     'frameborder="0" allowfullscreen></iframe>'
            return iframe % {'id': id}
        elif self.code_valid(self.url):
            return self.url


class YandexMusicEmbedHandler(EmbedHandler):
    TYPE = 'yandex_music'
    EMBED_URL_REGEX = [
        r'https://music\.yandex\.ru/album/(?P<album>\d+)(/track/(?P<track>\d+))?',
    ]
    EMBED_CODE_REGEX = [
        r'^<iframe( frameborder="(0|1)")?( style="[^"]+")?( width="\d+")?( height="\d+")? src="https://music\.yandex\.ru/iframe/(#album/\d+/|#track/\d+/\d+)(/\w+)*/?">(\s*.)+</iframe>$'
    ]

    def get_embed(self):
        if self.url_valid(self.url):
            url_re = re.match(self.EMBED_URL_REGEX[0], self.url)
            album, track = url_re.group('album'), url_re.group('track')
            if not track:
                return '<iframe frameborder="0" width="900" height="500" ' \
                         'src="https://music.yandex.ru/iframe/#album/%(album)s/"></iframe>' % {'album': album}
            else:
                return '<iframe frameborder="0" width="600" height="100" ' \
                         'src="https://music.yandex.ru/iframe/#track/%(track)s/%(album)s/"></iframe>' % {'album': album, 'track': track}
        elif self.code_valid(self.url):
            return self.url



EMBED_HANDLERS = [
    YoutubeEmbedHandler,
    TwitterEmbedHandler,
    VimeoEmbedHandler,
    InstagramEmbedHandler,
    FacebookEmbedHandler,
    VkEmbedHandler,
    VkVideoEmbedHandler,
    CoubEmbedHandler,
    SoundCloudEmbedHandler,
    PromoDjEmbedHandler,
    YandexMusicEmbedHandler
]


def get_handler(url, **kwargs):
    for handler_class in EMBED_HANDLERS:
        if handler_class.is_valid(url):
            return handler_class(url, **kwargs)


def get_embed_data(url, **kwargs):
    for handler_class in EMBED_HANDLERS:
        if handler_class.is_valid(url):
            handler = handler_class(url, **kwargs)
            try:
                return handler.data
            except EmbedHandlerError:
                return


# CONTENT META

class ContentBlockMetaGenerator(object):
    @classmethod
    def get_instance(cls, content):
        if content.get('type') in [ArticleContentType.VIDEO, ArticleContentType.AUDIO, ArticleContentType.POST]:
            return EmbedBlockMetaGenerator(content, _type=content['type'])
        elif content.get('type') == ArticleContentType.PHOTO:
            return PhotoBlockMetaGenerator(content)
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

    @staticmethod
    def hash(content):
        _content = copy(content)
        _content.pop('__meta', None)
        return hashlib.md5(str(_content)).hexdigest()

    def get_content_hash(self):
        return hashlib.md5(str(self.content)).hexdigest()

    def get_meta(self, old_meta=None):
        return {
            'is_valid': self.is_valid(),
            'hash': self.get_content_hash()
        }


class EmbedBlockMetaGenerator(ContentBlockMetaGenerator):
    def __init__(self, content, _type=None):
        super(EmbedBlockMetaGenerator, self).__init__(content)
        self.type = _type

    def get_meta(self, old_meta=None):
        meta = super(EmbedBlockMetaGenerator, self).get_meta()
        if self.is_valid():
            if self.content['type'] == ArticleContentType.VIDEO:
                data = get_embed_data(self.content['value'], type='video')
            else:
                data = get_embed_data(self.content['value'])
            if data:
                meta.update(data)
        return meta


class PhotoBlockMetaGenerator(ContentBlockMetaGenerator):
    def get_meta(self, old_meta=None):
        meta = super(PhotoBlockMetaGenerator, self).get_meta()
        if 'mp4' in old_meta:
            meta['mp4'] = old_meta['mp4']
        if 'webm' in old_meta:
            meta['webm'] = old_meta['webm']
        return meta


def process_content(content):
    temp_blocks = []
    for block in content.get('blocks', []):
        meta = block.pop('__meta', {})
        if meta and meta.get('deleted'):
            continue
        meta_generator = ContentBlockMetaGenerator.get_instance(block)
        if meta_generator:
            block['__meta'] = meta_generator.get_meta(meta)
            if block['__meta'].get('hash') != meta.get('hash'):
                block['__meta']['is_changed'] = True
        # sanitize
        if block.get('type') not in [ArticleContentType.POST, ArticleContentType.AUDIO, ArticleContentType.VIDEO] and \
                'value' in block and isinstance(block['value'], (str, unicode)):
            block['value'] = re.sub(r'<[^>]+>', '', block['value'])
        temp_blocks.append(block)
    content['blocks'] = temp_blocks
    is_valid = True
    for field, params in ROOT_VALIDATION_CFG.items():
        try:
            ContentValidator.validate_structure(content, field, params)
        except ValidationError as e:
            is_valid = False
    content['__meta'] = {'is_valid': is_valid}
    return content


def gif2video(file, command_pattern, ext):
    temp = NamedTemporaryFile()
    temp.write(file)
    temp_output = NamedTemporaryFile(suffix='.' + ext)
    try:
        result = subprocess.call(command_pattern % {'src': temp.name, 'dest': temp_output.name}, shell=True)
    except Exception as e:
        return e, None

    if result != 0:
        return 'Unexpected error', None

    return None, temp_output


def gif2mp4(image):
    return gif2video(image, '/usr/bin/ffmpeg -y -v panic -i %(src)s -an -movflags faststart -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %(dest)s', 'mp4')


def gif2webm(image):
    return gif2video(image, '/usr/bin/ffmpeg -y -i %(src)s -an -c:v libvpx -crf 12 -b:v 500k %(dest)s', 'webm')


# CONTENT CONVERTER

def _get_banner_code(_id):
    return '<div class="banner %s"></div>' % _id


def _get_block_length(block):
    if block['type'] == ArticleContentType.LEAD:
        return float(len(block['value'])) / 1000
    elif block['type'] == ArticleContentType.TEXT:
        return float(len(block['value'])) / 2000
    elif block['type'] == ArticleContentType.HEADER:
        return 0.1
    elif block['type'] in [ArticleContentType.QUOTE, ArticleContentType.COLUMNS, ArticleContentType.LIST]:
        return max(float(len(block['value'])) / 1500, 0.2)
    elif block['type'] == ArticleContentType.PHOTO:
        return 1
    else:
        return 0.5


def _inject_banner_to_text(text_html, max_injections=1):
    r_paragraph = re.compile(r'</p>\s*<p>')
    interval = float(len(text_html)) / (max_injections + 1)
    injected = False

    for i in xrange(int(max_injections)):
        start_position = interval * (i + 1) - interval / 4
        end_position = interval * (i + 1) + interval / 4
        sub_paragraph = r_paragraph.search(text_html, int(start_position), int(end_position))
        if sub_paragraph:
            position_index = sub_paragraph.start() + 4
            text_html = text_html[:position_index] + _get_banner_code(BannerID.BANNER_CONTENT_INLINE) + \
                        text_html[position_index:]
            injected = True

    return text_html, injected


def _photo_block_to_html(block, **kwargs):
    html_photos = []
    photos = block.get('photos') or []
    image_data = kwargs.get('image_data')

    for index, photo in enumerate(photos):
        photo_class = 'photo photo_%d' % index

        if photo.get('id'):
            photo_preview = photo.get('preview') or ''
            photo_src = photo.get('image') or ''
            is_animated = photo.get('is_animated')
            if image_data:
                get_image_url = image_data.get(photo['id'])
                photo_src = get_image_url(THUMBNAIL_REGULAR_SIZE) or photo_src

                if index > 2:
                    photo_preview = get_image_url(THUMBNAIL_SMALL_SIZE) or photo_preview
                elif len(photos) == 1 and is_animated:
                    photo_class += ' photo_animated'
                    photo_src = photo.get('image') or ''
                else:
                    photo_preview = get_image_url(THUMBNAIL_MEDIUM_SIZE) or photo_preview

            photo_element = '<div class="%(class)s" data-id="%(id)d" data-caption="%(caption)s" ' \
                            'data-preview="%(preview)s" data-src="%(src)s"></div>' \
                            % {'class': photo_class, 'id': photo['id'], 'caption': photo.get('caption') or '',
                               'preview': photo_preview, 'src': photo_src}
            html_photos.append(photo_element)

    if len(photos) == 1:
        if photos[0].get('caption'):
            photo_class = 'photos photos_1'

            if photos[0].get('size'):
                photo_class += ' photo_%s' % photos[0].get('size')

            return '<div id="%(id)s" class="%(_class)s">\n%(content)s\n<div style="clear: both" class="caption">%(caption)s</div>\n</div>' % {
                    'id': block.get('id', '_'),
                    '_class': photo_class,
                    'content': '\n'.join(html_photos),
                    'caption': photos[0].get('caption') or ''
                }
        else:
            return '<div id="%(id)s" class="photos photos_1">\n%(photos)s\n<div style="clear: both"></div>\n</div>' % {
                'id': block.get('id', '_'), 'photos': '\n'.join(html_photos)}
    elif len(photos) <= 6:
        return '<div id="%(id)s" class="photos %(_class)s">\n%(content)s\n<div style="clear: both"></div>\n</div>' % {
                'id': block.get('id'),
                '_class': 'photos_%d' % len(photos),
                'content': '\n'.join(html_photos)
            }
    else:
        return '<div id="%(id)s" class="photos">\n%(photos)s\n<div style="clear: both" class="caption">%(caption)s</div>\n</div>' % {
            'id': block.get('id', '_'), 'photos': '\n'.join(html_photos), 'caption': 'Галерея из %d фото' % len(photos)}


def content_to_html(content, ads_enabled=False, **kwargs):
    safe_mode = 'remove'

    if not content.get('__meta', {}).get('is_valid'):
        return

    html = []
    validated_content_blocks = [block for block in content.get('blocks') if block.get('__meta', {}).get('is_valid')]
    content_length = sum([_get_block_length(block) for block in validated_content_blocks])
    content_length_increment = 0
    _content_length = 0
    banner_interval = 1.0 / BANNER_DENSITY

    for index, block in enumerate(validated_content_blocks):

        if block.get('type') == ArticleContentType.TEXT:
            text_html = markdown.markdown(block.get('value'), safe_mode=safe_mode)
            html.append(text_html)
        elif block.get('type') == ArticleContentType.HEADER:
            html.append(markdown.markdown('## %s' % block.get('value'), safe_mode=safe_mode))

        elif block.get('type') == ArticleContentType.LEAD:
            html.append('<div class="lead">%s</div>' % markdown.markdown(block.get('value'), safe_mode=safe_mode))

        elif block.get('type') == ArticleContentType.PHRASE:
            html.append('<div class="phrase">%s</div>' % markdown.markdown(block.get('value'), safe_mode=safe_mode))

        elif block.get('type') == ArticleContentType.PHOTO:
            _html = _photo_block_to_html(block, **kwargs)
            if _html:
                html.append(_html)

        elif block.get('type') == ArticleContentType.LIST:
            html.append(markdown.markdown(block.get('value'), safe_mode=safe_mode))

        elif block.get('type') == ArticleContentType.QUOTE:
            if block.get('image') and block['image'].get('image'):
                _image_html = '<img src="%s"/>' % block['image']['image']
                _html = '<blockquote class="personal">\n%s\n%s\n</blockquote>'
                html.append(_html % (_image_html, markdown.markdown(block.get('value'), safe_mode=safe_mode)))
            else:
                html.append('<blockquote>\n%s\n</blockquote>' % markdown.markdown(block.get('value'), safe_mode=safe_mode))

        elif block.get('type') == ArticleContentType.COLUMNS:
            _html = '<div class="columns">\n<div class="column">\n%(left)s\n</div>\n<div class="column">\n%(right)s\n</div>\n</div>'
            html.append(_html % {
                'left': '<img src="%s"/>' % (block.get('image') or {}).get('image', ''),
                'right': markdown.markdown(block.get('value'), safe_mode=safe_mode)
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

        # CONTENT BANNERS INJECTING
        if ads_enabled:
            block_length = _get_block_length(block)
            _content_length += block_length
            content_length_increment += block_length

            tail_length = content_length - _content_length

            if content_length_increment >= banner_interval:
                banner_injected = False
                prev_block = validated_content_blocks[index - 1] if (len(validated_content_blocks) - 1 >= index - 1) else None
                next_block = validated_content_blocks[index + 1] if (len(validated_content_blocks) - 1 >= index + 1) else None

                if block['type'] == ArticleContentType.TEXT:
                    if block_length >= banner_interval or next_block and next_block['type'] in [ArticleContentType.PHOTO, ArticleContentType.VIDEO]:
                        text_html = html.pop()
                        max_injections = max(1, math.ceil(block_length / banner_interval) - 1)
                        text_html, text_injected = _inject_banner_to_text(text_html, max_injections=max_injections)
                        html.append(text_html)
                        if text_injected:
                            banner_injected = True
                    elif tail_length >= banner_interval:
                        html.append(_get_banner_code(BannerID.BANNER_CONTENT))
                        banner_injected = True

                elif tail_length < banner_interval / 2 \
                        or block['type'] in [ArticleContentType.PHOTO, ArticleContentType.VIDEO] \
                        or next_block and next_block['type'] in [ArticleContentType.PHOTO, ArticleContentType.VIDEO]:
                    pass

                elif block['type'] == ArticleContentType.HEADER:
                    if prev_block and prev_block['type'] not in [ArticleContentType.PHOTO, ArticleContentType.VIDEO]:
                        header_html = html.pop()
                        html.append(_get_banner_code(BannerID.BANNER_CONTENT))
                        html.append(header_html)
                        banner_injected = True
                else:
                    html.append(_get_banner_code(BannerID.BANNER_CONTENT))
                    banner_injected = True

                if banner_injected:
                    content_length_increment = 0

    return '\n'.join(html)


def get_article_cache_key(key, prefix='article'):
    return '%s__%s' % (prefix, key)


def _fix_image_data(content_image, image_data):
    if content_image is None:
        return

    _content_image = content_image.copy()
    get_image_url = image_data.get(_content_image['id'])
    if get_image_url:
        _content_image['image'] = get_image_url()
        _content_image['preview'] = get_image_url(THUMBNAIL_MEDIUM_SIZE)
    return _content_image


def fix_image_urls(content, image_data):
    _content = content.copy()

    if _content.get('cover'):
        _content['cover'].update(_fix_image_data(_content['cover'], image_data))

    if _content.get('cover_clipped'):
        _content['cover_clipped'].update(_fix_image_data(_content['cover_clipped'], image_data))

    for block in _content['blocks']:
        if block.get('type') == ArticleContentType.PHOTO:
            for photo in block['photos']:
                photo.update(_fix_image_data(photo, image_data))
        elif block.get('type') in [ArticleContentType.QUOTE, ArticleContentType.COLUMNS]:
            image = block['image']
            if image:
                block['image'] = _fix_image_data(block['image'], image_data)
        elif block.get('type') == ArticleContentType.DIALOG:
            for p in block['participants']:
                if p.get('avatar'):
                    p['avatar'].update(_fix_image_data(p['avatar'], image_data))

    return _content
