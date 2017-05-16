from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from statistics.tasks import update_aggregated_statistics


class Command(BaseCommand):
    help = 'Update articles statistics'

    def handle(self, *args, **options):
        update_aggregated_statistics()
        self.stdout.write(self.style.SUCCESS('Articles statistics updated'))
