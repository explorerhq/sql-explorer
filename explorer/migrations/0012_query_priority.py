# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-04 15:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0011_ftpexport_passive'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='priority',
            field=models.BooleanField(default=False),
        ),
    ]
