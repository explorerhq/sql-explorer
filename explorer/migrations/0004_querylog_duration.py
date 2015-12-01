# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0003_query_snapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='querylog',
            name='duration',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
