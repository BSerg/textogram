from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.cache_utils import save_cached_views_to_db

from redis import Redis
from rq import Queue

from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'Save cached views to db'

    def handle(self, *args, **options):
        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)
        job = q.enqueue(save_cached_views_to_db)
        self.stdout.write('Save views from cache job created [%s]' % job.id)
