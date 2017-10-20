from articles.models import Article
from django.template.loader import render_to_string
from textogram import settings


def _get_cover_html(article):

    context = {
        'title': article.title,
        'href': '/' if settings.IS_LENTACH else '/%s' % article.owner.nickname,
        'name': '%s %s' % (article.owner.first_name, article.owner.last_name),
        'date': article.published_at,
        'header_class': 'short' if len(article.title) <= 15 else '',
    }
    return render_to_string('amp_blocks/amp_cover.html', context=context)


def _get_embeds(article):
    embeds = {}
    for block in article.content.get('blocks', []):
        print block
    return embeds


def generate_amp(slug):
    try:

        article = Article.objects.get(slug=slug, status=Article.PUBLISHED)
        context = {
            'title': article.title,
            'cover': _get_cover_html(article),
            'embeds': _get_embeds(article),
        }
        html = render_to_string('article_amp.html', context=context)

        return html

    except Article.DoesNotExist:
        return None
