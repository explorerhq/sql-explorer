# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0008_auto_20190308_1642'),
    ]

    operations = [
        migrations.CreateModel(
            name='QueryParam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(blank=True, max_length=128, null=True)),
                ('value', models.CharField(blank=True, max_length=255, null=True)),
                ('query', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='query_params', to='explorer.Query')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='queryparam',
            unique_together=set([('query', 'key')]),
        ),
    ]
