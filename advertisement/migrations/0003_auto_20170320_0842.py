# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-20 08:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advertisement', '0002_banner_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='banner',
            name='identifier',
            field=models.CharField(max_length=255, unique=True, verbose_name='\u0418\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440'),
        ),
    ]
