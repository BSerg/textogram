# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-18 06:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UrlShort',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(verbose_name='URL')),
                ('code', models.CharField(default='\xdf', editable=False, max_length=10, unique=True, verbose_name='\u041a\u043e\u0434')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u043d')),
                ('count', models.IntegerField(default=0, editable=False, verbose_name='\u041f\u0435\u0440\u0445\u043e\u0434\u044b')),
            ],
        ),
    ]