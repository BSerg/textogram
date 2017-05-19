from articles.models import ArticleView, Article
from articles.utils import fix_image_urls


def register_article_view(article_slug, user_id, fingerprint):
    try:
        article = Article.objects.get(slug=article_slug)
    except Article.DoesNotExist:
        return
    # TODO: this will must be refactored, when article will have got paywall option
    monetization_enabled = article.ads_enabled
    ArticleView.objects.create(article=article, user_id=user_id, fingerprint=fingerprint,
                               monetization_enabled=monetization_enabled)


def update_article_html(article_id):
    try:
        article = Article.objects.get(pk=article_id)
    except:
        return
    else:
        article.update_html()


def fix_article_content_image_urls(article_id):
    try:
        article = Article.objects.get(pk=article_id)
    except:
        return

    image_data = {i.id: i.get_image_url for i in article.images.all()}
    article.content = fix_image_urls(article.content, image_data)
    article.save()
