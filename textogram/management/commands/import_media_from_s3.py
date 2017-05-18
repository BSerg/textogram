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
                        else:
                            raise
                    except:
                        print 'File %s ERRORED' % path
                    else:
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

    def _listdir(self, path, file_list):
        dirs, files = self.s3_storage.listdir(path)
        for f in files:
            file_list.append(os.path.join(path, f) if path != '.' else f)
        for d in dirs:
            self._listdir(os.path.join(path, d) if path != '.' else d, file_list)

    def handle(self, *args, **options):
        if not self.s3_storage:
            self.stdout.write('Amazon S3 Storage is not configured')
            return

        exclude_cache = True

        if hasattr(settings, 'MEDIA_ROOT'):
            file_list = []
            self._listdir('.', file_list)

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

            for f in file_list[:10]:
                if exclude_cache and f.startswith('cache'):
                    continue
                self.q.put(f)

            self.q.join()

        self.stdout.write('Completed')


