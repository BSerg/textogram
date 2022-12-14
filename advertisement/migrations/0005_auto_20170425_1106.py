# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-25 11:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advertisement', '0004_auto_20170420_1036'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='banner',
            options={'ordering': ['identifier', '-weight'], 'verbose_name': '\u0411\u0430\u043d\u043d\u0435\u0440', 'verbose_name_plural': '\u0411\u0430\u043d\u043d\u0435\u0440\u044b'},
        ),
        migrations.AlterField(
            model_name='banner',
            name='identifier',
            field=models.CharField(choices=[(b'banner__right_side', b'banner__right_side'), (b'banner__content', b'banner__content'), (b'banner__top', b'banner__top'), (b'banner__content_inline', b'banner__content_inline')], max_length=255, verbose_name='\u0418\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440'),
        ),
    ]
