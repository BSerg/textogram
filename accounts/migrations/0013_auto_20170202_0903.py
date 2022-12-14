# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-02-02 09:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_auto_20170117_0733'),
    ]

    operations = [
        migrations.AlterField(
            model_name='phonecode',
            name='disabled',
            field=models.BooleanField(default=False, editable=False, verbose_name='\u041e\u0442\u043a\u043b\u044e\u0447\u0435\u043d'),
        ),
        migrations.AlterField(
            model_name='user',
            name='social',
            field=models.CharField(blank=True, choices=[('vk', '\u0412 \u043a\u043e\u043d\u0442\u0430\u043a\u0442\u0435'), ('fb', 'Facebook'), ('twitter', 'Twitter'), ('google', 'Google')], max_length=10, verbose_name='\u0421\u043e\u0446\u0441\u0435\u0442\u044c \u0430\u0432\u0442\u043e\u0440\u0438\u0437\u0430\u0446\u0438\u0438'),
        ),
    ]
