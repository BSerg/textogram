# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-06-08 06:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_auto_20170503_1326'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='social',
        ),
        migrations.AlterField(
            model_name='user',
            name='uid',
            field=models.CharField(blank=True, max_length=255, verbose_name='UID \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f'),
        ),
    ]
