# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-07-18 08:26
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('advertisement', '0009_auto_20170510_1432'),
    ]

    operations = [
        migrations.AddField(
            model_name='banner',
            name='apm_props',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='AMP \u0421\u0432\u043e\u0439\u0441\u0442\u0432\u0430'),
        ),
    ]
