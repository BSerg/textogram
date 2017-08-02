from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from redis import Redis
from rq import Queue

from articles.models import Article
from articles.tasks import update_article_html, convert_gif2video
from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'Convert GIF to MP4'

    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='*')
        parser.add_argument(
            '-f', '--force-update',
            action='store_true',
            dest='force_update',
            default=False,
            help='Force reconvert',
        )

    def handle(self, *args, **options):
        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)

        if options['article_id']:
            article = Article.objects.filter(status=Article.PUBLISHED, pk__in=options['article_id'])
        else:
            article = Article.objects.filter(status=Article.PUBLISHED)

        for article in article:
            job = q.enqueue(convert_gif2video, article.id, options['force_update'])
            self.stdout.write('Article #%d GIF2MP4 job created [%s]' % (article.id, job.id))

        self.stdout.write(self.style.SUCCESS('Completed'))
