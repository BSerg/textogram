from __future__ import unicode_literals

from time import sleep

from django.core.management.base import BaseCommand
from redis import Redis
from rq import Queue

from statistics.tasks import task_cache_articles_yandex_age_statistics, task_cache_articles_yandex_gender_statistics, \
    task_cache_articles_yandex_views_statistics
from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='*', type=int)

    def handle(self, *args, **options):
        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)

        gender_job = q.enqueue(task_cache_articles_yandex_gender_statistics)
        self.stdout.write('Update gender statistics job [%s] created' % gender_job.id)

        sleep(10)

        age_job = q.enqueue(task_cache_articles_yandex_age_statistics)
        self.stdout.write('Update age statistics job [%s] created' % age_job.id)

        sleep(10)

        yandex_views_job = q.enqueue(task_cache_articles_yandex_views_statistics)
        self.stdout.write('Update yandex views statistics job [%s] created' % yandex_views_job.id)
