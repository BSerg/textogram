from __future__ import unicode_literals

import Queue
import os
import threading

import errno
from django.core.files import File
from django.core.files.storage import default_storage, get_storage_class
from django.core.management.base import BaseCommand
from django.utils.functional import cached_property

from textogram import settings


class Command(BaseCommand):
    help = 'Import media from Amazon S3'
    q = Queue.Queue()
    imported = []
    log_path = ''
    count = 0

    @cached_property
    def s3_storage(self):
        try:
            return get_storage_class('storages.backends.s3boto3.S3Boto3Storage')()
        except:
            return None

    def _download(self, path):
        if path not in self.imported:

            with self.s3_storage.open(path, 'r') as _f:
                if not os.path.exists(os.path.join(settings.MEDIA_ROOT, path)):
                    try:
                        os.makedirs(os.path.abspath(os.path.dirname(os.path.join(settings.MEDIA_ROOT, path))))
                    except OSError as exc:  # Python >2.5
                        if exc.errno == errno.EEXIST and os.path.isdir(path):
                            pass
                    f = open(os.path.join(settings.MEDIA_ROOT, path), 'w')
                    f.write(_f.read())
                    f.close()
                    self.count += 1
                    print 'File %s IMPORTED' % path
                else:
                    print 'File %s SKIPPED' % path

                self.imported.add(path)
                log = open(self.log_path, 'a')
                log.write(path + '\n')
                log.close()

    def worker(self):
        while True:
            path = self.q.get()
            self._download(path)
            self.q.task_done()

    def _listdir(self, path, exclude_cache=False):
        if path in self.imported or exclude_cache and path.split('/')[0] == 'cache':
            return
        dirs, files = self.s3_storage.listdir(path)
        for f in files:
            self.q.put(os.path.join(path, f) if path != '.' else f)
        for d in dirs:
            self._listdir(os.path.join(path, d) if path != '.' else d, exclude_cache)

    def handle(self, *args, **options):
        if not self.s3_storage:
            self.stdout.write('Amazon S3 Storage is not configured')
            return

        if hasattr(settings, 'MEDIA_ROOT'):
            self.count = 0

            self.log_path = os.path.join(settings.MEDIA_ROOT, '__s3_import.log')

            if not os.path.exists(self.log_path):
                log = open(self.log_path, 'w')
                log.close()

            self.imported = set([l.strip() for l in open(self.log_path, 'r').readlines()])

            for _ in xrange(4):
                t = threading.Thread(target=self.worker)
                t.daemon = True
                t.start()

            self._listdir('.', exclude_cache=True)

            self.q.join()

        self.stdout.write('Completed')


