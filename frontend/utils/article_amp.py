from articles.models import Article, ArticleImage
from django.template.loader import render_to_string
from textogram import settings
from articles import ArticleContentType
import re


EMBED_BLOCK_TYPES = [ArticleContentType.AUDIO, ArticleContentType.PHOTO, ArticleContentType.VIDEO,
                     ArticleContentType.POST]
EMBED_BLOCK_TYPES_POST = [ArticleContentType.AUDIO, ArticleContentType.POST, ArticleContentType.VIDEO]
EMBED_TYPES = ['soundcloud', 'instagram', 'twitter', 'facebook', 'youtube', 'vimeo', 'vk']


VK_POST_PATTERN = r"VK\.Widgets\.Post\((?<post_data>.*\')\)"


class EmbedError(Exception):
    pass


def __process_blocks(blocks):

    def _process_vk(b):
        url = b['__meta'].get('url', '') or ''
        r = re.findall(r"VK\.Widgets\.Post\((?P<post_data>.*\')\)\)", url)
        if r and len(r):
            match = r[0]
            data_list = match.split(',')
            if len(data_list) >= 4:
                b['__meta']['owner_id'] = data_list[1].strip()
                b['__meta']['id'] = data_list[2].strip()
                b['__meta']['post_hash'] = data_list[3].strip().strip("'")
        return b

    for index, block in enumerate(blocks):
        if block.get('__meta').get('type') == 'vk':
            blocks[index] = _process_vk(block)
        blocks[index]['post_meta'] = block.get('__meta')
    return blocks


def _get_embeds(article):
    embeds = {}
    try:
        for block in article.content.get('blocks', []):
            block_type = block.get('type')
            if block_type == ArticleContentType.PHOTO:
                embeds['gallery'] = True
                continue
            if block_type not in EMBED_BLOCK_TYPES:
                continue
            if block.get('__meta').get('type') not in EMBED_TYPES:
                raise EmbedError('incorrect embed')
            embeds[block.get('__meta').get('type')] = True
        return embeds
    except (KeyError, IndexError, ValueError):
        raise EmbedError('incorrect embed')


def _get_css():
    with open('frontend/templates/css/article_amp.css') as f:
        css = f.read().replace('\n', ' ')
        return css


def _get_cover_url(article):
    cover = None
    if 'cover_clipped' in article.content:
        cover = article.content['cover_clipped']
    elif 'cover' in article.content:
        cover = article.content['cover']
    if cover and cover.get('original'):
        return cover.get('original')
    return None


def generate_amp(slug):
    try:

        article = Article.objects.get(slug=slug, status=Article.PUBLISHED)
        # print article.content.get('cover')
        context = {
            'title': article.title,
            'author': '%s %s' % (article.owner.first_name, article.owner.last_name),
            'author_href': '/' if settings.IS_LENTACH else '/%s' % article.owner.nickname,
            'date': article.published_at,
            'slug': article.slug,
            'cover_url': _get_cover_url(article),
            'inverted': bool(article.content.get('inverted_theme')),
            'embeds': _get_embeds(article),
            'css': _get_css(),
            'blocks': __process_blocks(article.content.get('blocks') or []),
            'block_types': ArticleContentType.__dict__,

        }
        html = render_to_string('article_amp.html', context=context)

        return html

    except (Article.DoesNotExist, EmbedError):
        return None
