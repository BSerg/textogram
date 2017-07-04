# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-05-19 09:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0006_auto_20170517_1224'),
    ]

    operations = [
        migrations.AddField(
            model_name='articleaggregatedstatistics',
            name='views_last_month',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u044b \u0437\u0430 \u043f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0438\u0439 \u043c\u0435\u0441\u044f\u0446'),
        ),
        migrations.AddField(
            model_name='articleaggregatedstatistics',
            name='views_month',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u044b \u0437\u0430 \u044d\u0442\u043e\u0442 \u043c\u0435\u0441\u044f\u0446'),
        ),
        migrations.AddField(
            model_name='articleaggregatedstatistics',
            name='views_today',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u044b \u0437\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f'),
        ),
        migrations.AlterField(
            model_name='articleaggregatedstatistics',
            name='views',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='\u0412\u0441\u0435\u0433\u043e \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u043e\u0432'),
        ),
    ]