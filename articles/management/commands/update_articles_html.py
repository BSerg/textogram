from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from redis import Redis
from rq import Queue

from articles.models import Article
from articles.tasks import update_article_html
from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'Update articles\' html code'

    def handle(self, *args, **options):
        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)

        for article in Article.objects.filter(content__isnull=False).exclude(status=Article.DELETED):
            job = q.enqueue(update_article_html, article.id)
            self.stdout.write('Article #%d job created [%s]' % (article.id, job.id))

        self.stdout.write(self.style.SUCCESS('Completed'))
