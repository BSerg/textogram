# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-08 12:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0008_auto_20170107_1911'),
    ]

    operations = [
        migrations.RenameField(
            model_name='articlecontentimagecollection',
            old_name='type',
            new_name='subbtype',
        ),
    ]