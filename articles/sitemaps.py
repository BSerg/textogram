from django.contrib.sitemaps import Sitemap

from articles.models import Article


class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Article.objects.filter(status=Article.PUBLISHED)

    def lastmod(self, obj):
        return obj.last_modified
