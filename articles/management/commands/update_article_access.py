from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from articles.models import Article, ArticleUserAccess
from payments.models import PayWallOrder


class Command(BaseCommand):
    help = 'Create defaults article access'

    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='*')

    def handle(self, *args, **options):
        if options['article_id']:
            articles = Article.objects.filter(status=Article.PUBLISHED, paywall_enabled=True, pk__in=options['article_id'])
        else:
            articles = Article.objects.filter(status=Article.PUBLISHED, paywall_enabled=True)

        for article in articles:
            author_access, created = ArticleUserAccess.objects.get_or_create(article=article, user=article.owner)

        paywall_orders = PayWallOrder.objects.filter(article__in=options['article_id'])

        for paywall_order in paywall_orders:
            access, created = ArticleUserAccess.objects.get_or_create(order=paywall_order,
                                                                      article=paywall_order.article,
                                                                      user=paywall_order.customer)

        self.stdout.write('Completed')
