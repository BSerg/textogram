from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from redis import Redis
from rq import Queue

from accounts.models import User
from articles.models import Article
from statistics.tasks import task_cache_article_views_by_day, task_cache_article_views_common, \
    task_cache_author_views_common
from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('user_id', nargs='*', type=int)

    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True)
        if options['user_id']:
            users = users.filter(pk__in=options['user_id'])

        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)

        for user in users:
            job = q.enqueue(task_cache_author_views_common, user.id)
            self.stdout.write('job [%s] created' % job.id)

        self.stdout.write(self.style.SUCCESS('Competed'))
