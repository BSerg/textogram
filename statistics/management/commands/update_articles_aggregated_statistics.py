from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from redis import Redis
from rq import Queue

from articles.models import Article
from statistics.tasks import task_update_aggregated_statistics, task_update_article_total_views
from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'Update articles aggregated statistics'

    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='*', type=int)

    def handle(self, *args, **options):
        articles = Article.objects.all()
        if options['article_id']:
            articles = articles.filter(pk__in=options['article_id'])

        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)

        update_aggregated_statistics_job = q.enqueue(task_update_aggregated_statistics)
        self.stdout.write('Update aggregated statistics job [%s] created' % update_aggregated_statistics_job.id)

        for article in articles:
            job = q.enqueue(task_update_article_total_views, article.id)
            self.stdout.write('Update article #%d total views job [%s] created' % (article.id, job.id))

        self.stdout.write(self.style.SUCCESS('Competed'))
