# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-02-21 08:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_auto_20170217_1143'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='description',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435'),
        ),
    ]
