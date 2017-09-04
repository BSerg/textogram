# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-09-04 13:24
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0008_auto_20170519_1411'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='articleaggregatedstatistics',
            name='article',
        ),
        migrations.RemoveField(
            model_name='articleviewsstatistics',
            name='article',
        ),
        migrations.DeleteModel(
            name='ArticleAggregatedStatistics',
        ),
        migrations.DeleteModel(
            name='ArticleViewsStatistics',
        ),
    ]
