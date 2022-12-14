# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-05-17 12:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0005_auto_20170516_1253'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articleaggregatedstatistics',
            name='age_17',
            field=models.FloatField(blank=True, null=True, verbose_name='\u041f\u0440\u043e\u0446\u0435\u043d\u0442 \u043b\u044e\u0434\u0435\u0439 \u0432 \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0435 \u0434\u043e 18 \u043b\u0435\u0442'),
        ),
        migrations.AlterField(
            model_name='articleaggregatedstatistics',
            name='age_18',
            field=models.FloatField(blank=True, null=True, verbose_name='\u041f\u0440\u043e\u0446\u0435\u043d\u0442 \u043b\u044e\u0434\u0435\u0439 \u0432 \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0435 \u043e\u0442 18 \u0434\u043e 24 \u043b\u0435\u0442'),
        ),
        migrations.AlterField(
            model_name='articleaggregatedstatistics',
            name='age_25',
            field=models.FloatField(blank=True, null=True, verbose_name='\u041f\u0440\u043e\u0446\u0435\u043d\u0442 \u043b\u044e\u0434\u0435\u0439 \u0432 \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0435 \u043e\u0442 25 \u0434\u043e 34 \u043b\u0435\u0442'),
        ),
        migrations.AlterField(
            model_name='articleaggregatedstatistics',
            name='age_35',
            field=models.FloatField(blank=True, null=True, verbose_name='\u041f\u0440\u043e\u0446\u0435\u043d\u0442 \u043b\u044e\u0434\u0435\u0439 \u0432 \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0435 \u043e\u0442 35 \u0434\u043e 44 \u043b\u0435\u0442'),
        ),
        migrations.AlterField(
            model_name='articleaggregatedstatistics',
            name='age_45',
            field=models.FloatField(blank=True, null=True, verbose_name='\u041f\u0440\u043e\u0446\u0435\u043d\u0442 \u043b\u044e\u0434\u0435\u0439 \u0432 \u0432\u043e\u0437\u0440\u0430\u0441\u0442\u0435 \u043e\u0442 45 \u043b\u0435\u0442'),
        ),
        migrations.AlterField(
            model_name='articleviewsstatistics',
            name='views_count',
            field=models.PositiveIntegerField(default=0, verbose_name='\u041a\u043e\u043b-\u0432\u043e \u0443\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0445 \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u043e\u0432'),
        ),
        migrations.AlterField(
            model_name='authorviewsstatistics',
            name='views_count',
            field=models.PositiveIntegerField(default=0, verbose_name='\u041a\u043e\u043b-\u0432\u043e \u0443\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0445 \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u043e\u0432'),
        ),
    ]
