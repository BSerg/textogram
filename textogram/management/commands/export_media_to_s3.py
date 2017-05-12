from __future__ import unicode_literals

import Queue
import os
import threading

from django.core.files import File
from django.core.files.storage import default_storage, get_storage_class
from django.core.management.base import BaseCommand
from django.utils.functional import cached_property

from textogram import settings


class Command(BaseCommand):
    help = 'Export media to Amazon S3'
    q = Queue.Queue()
    exported = []
    log_path = ''
    count = 0

    @cached_property
    def s3_storage(self):
        try:
            return get_storage_class('storages.backends.s3boto3.S3Boto3Storage')()
        except:
            return None

    def _upload(self, path):
        r_path = os.path.relpath(path, settings.MEDIA_ROOT)
        if r_path not in self.exported:

            with open(path, 'r') as _f:
                if not self.s3_storage.exists(r_path):
                    self.s3_storage.save(r_path, File(_f))
                    self.count += 1
                    print 'File %s EXPORTED' % r_path
                else:
                    print 'File %s SKIPPED' % r_path

                self.exported.add(r_path)
                log = open(self.log_path, 'a')
                log.write(r_path + '\n')
                log.close()

    def worker(self):
        while True:
            path = self.q.get()
            self._upload(path)
            self.q.task_done()

    def handle(self, *args, **options):
        if not self.s3_storage:
            self.stdout.write('Amazon S3 Storage is not configured')
            return

        exclude_cache = True

        if hasattr(settings, 'MEDIA_ROOT'):
            self.count = 0

            self.log_path = os.path.join(settings.MEDIA_ROOT, '__s3_export.log')

            if not os.path.exists(self.log_path):
                log = open(self.log_path, 'w')
                log.close()

            self.exported = set([l.strip() for l in open(self.log_path, 'r').readlines()])

            for _ in xrange(4):
                t = threading.Thread(target=self.worker)
                t.daemon = True
                t.start()

            for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                if exclude_cache and os.path.join(settings.MEDIA_ROOT, 'cache') in root:
                    continue
                for f in files:
                    self.q.put(os.path.join(root, f))

            self.q.join()

        self.stdout.write('Completed')


