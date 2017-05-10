from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from redis.client import StrictRedis
from rq import Queue
from rq.queue import get_failed_queue

from textogram import settings


class Command(BaseCommand):
    help = 'Requeue failed rq jobs'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        failed_jobs = get_failed_queue(StrictRedis(host=settings.RQ_HOST, port=settings.RQ_PORT, db=settings.RQ_DB))

        for job_id in failed_jobs.job_ids:
            failed_jobs.requeue(job_id)
            self.stdout.write('Job {id} requeued'.format(id=job_id))

        self.stdout.write('Completed')

