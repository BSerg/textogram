# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-07 13:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0005_auto_20170107_0006'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ArticleColumn',
            new_name='ArticleContentColumn',
        ),
        migrations.RenameModel(
            old_name='ArticleList',
            new_name='ArticleContentList',
        ),
        migrations.RenameModel(
            old_name='ArticleQuote',
            new_name='ArticleContentQuote',
        ),
        migrations.RemoveField(
            model_name='articlephrase',
            name='articlecontent_ptr',
        ),
        migrations.AddField(
            model_name='articlecontentimagecollection',
            name='type',
            field=models.PositiveSmallIntegerField(choices=[(1, '\u0422\u0438\u043f 1')], default=1, verbose_name='\u0422\u0438\u043f'),
        ),
        migrations.AddField(
            model_name='articlecontentimagecollectionitem',
            name='caption',
            field=models.TextField(blank=True, max_length=500, verbose_name='\u041f\u043e\u0434\u043f\u0438\u0441\u044c'),
        ),
        migrations.DeleteModel(
            name='ArticlePhrase',
        ),
    ]
