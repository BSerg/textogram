from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from statistics.tasks import update_aggregated_statistics, update_views_statistics


class Command(BaseCommand):
    help = 'Update articles statistics'

    def handle(self, *args, **options):
        self.stdout.write('Yandex aggregated statistics processing...')
        update_aggregated_statistics()
        self.stdout.write('Views statistics processing...')
        update_views_statistics()
        self.stdout.write(self.style.SUCCESS('Articles statistics updated'))
