# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-09 14:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_sociallinks'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SocialLinks',
            new_name='SocialLink',
        ),
    ]