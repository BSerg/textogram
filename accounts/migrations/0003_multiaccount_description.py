# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-21 13:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20161221_0453'),
    ]

    operations = [
        migrations.AddField(
            model_name='multiaccount',
            name='description',
            field=models.TextField(blank=True, max_length=1000, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435'),
        ),
    ]
