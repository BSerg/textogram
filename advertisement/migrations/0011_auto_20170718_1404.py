# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-07-18 14:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('advertisement', '0010_banner_apm_props'),
    ]

    operations = [
        migrations.RenameField(
            model_name='banner',
            old_name='apm_props',
            new_name='amp_props',
        ),
    ]
