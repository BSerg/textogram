from django.db.models import F
from django.db.models import Q

from articles.models import ArticleView, Article


def register_article_view(article_id, user_id, fingerprint):
    article_views = ArticleView.objects.filter(article_id=article_id)
    if user_id:
        if article_views.filter(user_id=user_id).exists():
            article_views.filter(user_id=user_id).update(views_count=F('views_count') + 1)
        else:
            ArticleView.objects.create(article_id=article_id, user_id=user_id, fingerprint=fingerprint, views_count=1)
    else:
        if article_views.filter(fingerprint=fingerprint).exists():
            article_views.filter(fingerprint=fingerprint).update(views_count=F('views_count') + 1)
        else:
            ArticleView.objects.create(article_id=article_id, fingerprint=fingerprint, views_count=1)


def _register_article_view(article_slug, user_id, fingerprint):
    try:
        article = Article.objects.get(slug=article_slug)
    except Article.DoesNotExist:
        return
    ArticleView.objects.create(article=article, user_id=user_id, fingerprint=fingerprint)
