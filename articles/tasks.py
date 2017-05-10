from django.db.models import F
from django.db.models import Q

from articles.models import ArticleView, Article


def register_article_view(article_slug, user_id, fingerprint):
    try:
        article = Article.objects.get(slug=article_slug)
    except Article.DoesNotExist:
        return
    # TODO: this will must be refactored, when article will have got paywall option
    monetization_enabled = article.ads_enabled
    ArticleView.objects.create(article=article, user_id=user_id, fingerprint=fingerprint,
                               monetization_enabled=monetization_enabled)
