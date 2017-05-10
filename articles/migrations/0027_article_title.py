# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-05-07 17:21
from __future__ import unicode_literals

from django.db import migrations, models


def forwards_func(apps, schema_editor):
    Article = apps.get_model("articles", "Article")
    db_alias = schema_editor.connection.alias
    for article in Article.objects.using(db_alias):
        if not article.title:
            article.title = article.content.get('title') or ''
            article.save()


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0026_auto_20170502_1323'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='title',
            field=models.CharField(blank=True, max_length=255, verbose_name='\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a'),
        ),
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
