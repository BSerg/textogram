# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-25 11:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0024_articlepreview'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articleview',
            name='fingerprint',
            field=models.CharField(db_index=True, max_length=255, verbose_name='\u0426\u0438\u0444\u0440\u043e\u0432\u043e\u0439 \u043e\u0442\u043f\u0435\u0447\u0430\u0442\u043e\u043a \u043a\u043b\u0438\u0435\u043d\u0442\u0430'),
        ),
        migrations.AlterUniqueTogether(
            name='articlepreview',
            unique_together=set([('article', 'is_permanent')]),
        ),
    ]
