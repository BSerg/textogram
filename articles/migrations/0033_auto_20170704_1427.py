# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-07-04 14:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0032_auto_20170616_0825'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articleview',
            name='created_at',
            field=models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f'),
        ),
    ]
