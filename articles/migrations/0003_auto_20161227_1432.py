# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-27 14:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0002_auto_20161220_1204'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ArticleContenLead',
            new_name='ArticleContentLead',
        ),
    ]
