# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-11 14:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0017_auto_20170111_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='html',
            field=models.TextField(blank=True, editable=False, verbose_name='HTML'),
        ),
    ]
