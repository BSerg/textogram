from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from redis import Redis
from rq import Queue

from articles.models import Article
from statistics.tasks import task_update_article_views_by_intervals
from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'Update articles views statistics'

    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='*', type=int)
        parser.add_argument(
            '--init',
            action='store_true',
            dest='init',
            default=False,
            help='Initial updating articles\' views statistics',
        )

    def handle(self, *args, **options):
        articles = Article.objects.all()
        if options['article_id']:
            articles = articles.filter(pk__in=options['article_id'])

        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)

        for article in articles:
            job = q.enqueue(task_update_article_views_by_intervals, article.id)
            self.stdout.write('Update article #%d total views job [%s] created' % (article.id, job.id))

        self.stdout.write(self.style.SUCCESS('Competed'))
