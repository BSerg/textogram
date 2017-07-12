# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-06-16 08:08
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('articles', '0031_auto_20170616_0808'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('status', models.PositiveSmallIntegerField(choices=[(1, '\u0410\u043a\u0442\u0438\u0432\u043d\u043e'), (2, '\u041d\u0435\u0430\u043a\u0442\u0438\u0432\u043d\u043e')], default=1, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441')),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='\u0411\u0430\u043b\u0430\u043d\u0441')),
                ('currency', models.CharField(choices=[('RUR', '\u0420\u0443\u0431\u043b\u044c'), ('USD', '\u0414\u043e\u043b\u043b\u0430\u0440 \u0421\u0428\u0410'), ('EUR', '\u0415\u0432\u0440\u043e')], default='RUR', max_length=3, verbose_name='\u0412\u0430\u043b\u044e\u0442\u0430')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_accounts', to=settings.AUTH_USER_MODEL, verbose_name='\u0412\u043b\u0430\u0434\u0435\u043b\u0435\u0446')),
            ],
            options={
                'verbose_name': '\u041a\u043e\u0448\u0435\u043b\u0435\u043a',
                'verbose_name_plural': '\u041a\u043e\u0448\u0435\u043b\u044c\u043a\u0438',
            },
        ),
        migrations.CreateModel(
            name='PayWallOrder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('status', models.PositiveSmallIntegerField(choices=[(0, '\u0412 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0435'), (1, '\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d'), (2, '\u041e\u0442\u043c\u0435\u043d\u0435\u043d'), (3, '\u041e\u0448\u0438\u0431\u043a\u0430')], default=0, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441')),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='\u0426\u0435\u043d\u0430')),
                ('currency', models.CharField(choices=[('RUR', '\u0420\u0443\u0431\u043b\u044c'), ('USD', '\u0414\u043e\u043b\u043b\u0430\u0440 \u0421\u0428\u0410'), ('EUR', '\u0415\u0432\u0440\u043e')], default='RUR', max_length=3, verbose_name='\u0412\u0430\u043b\u044e\u0442\u0430')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='account_paywall_orders', to='payments.Account', verbose_name='\u0410\u043a\u043a\u0430\u0443\u043d\u0442')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='article_paywall_orders', to='articles.Article', verbose_name='\u0421\u0442\u0430\u0442\u044c\u044f')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_paywall_orders', to=settings.AUTH_USER_MODEL, verbose_name='\u0417\u0430\u043a\u0430\u0437\u0447\u0438\u043a')),
            ],
            options={
                'verbose_name': '\u0417\u0430\u043a\u0430\u0437 PayWall',
                'verbose_name_plural': '\u0417\u0430\u043a\u0430\u0437\u044b PayWall',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('type', models.CharField(choices=[('ad', '\u0420\u0435\u043a\u043b\u0430\u043c\u0430'), ('pw', 'PayWall'), ('out', '\u0412\u044b\u0432\u043e\u0434')], db_index=True, max_length=20)),
                ('value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(choices=[('RUR', '\u0420\u0443\u0431\u043b\u044c'), ('USD', '\u0414\u043e\u043b\u043b\u0430\u0440 \u0421\u0428\u0410'), ('EUR', '\u0415\u0432\u0440\u043e')], default='RUR', max_length=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PayWallTransaction',
            fields=[
                ('transaction_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='payments.Transaction')),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='payments.PayWallOrder', verbose_name='\u0417\u0430\u043a\u0430\u0437')),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': '\u0422\u0440\u0430\u043d\u0437\u0430\u043a\u0446\u0438\u044f PayWall',
                'verbose_name_plural': '\u0422\u0440\u0430\u043d\u0437\u0430\u043a\u0446\u0438\u0438 PayWall',
            },
            bases=('payments.transaction',),
        ),
        migrations.AddField(
            model_name='transaction',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='payments.Account'),
        ),
        migrations.AlterUniqueTogether(
            name='paywallorder',
            unique_together=set([('article', 'customer')]),
        ),
        migrations.AlterUniqueTogether(
            name='account',
            unique_together=set([('owner', 'currency')]),
        ),
    ]
