# -*- coding: utf-8 -*-

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0005_querychangelog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='snapshot',
            field=models.BooleanField(default=False, help_text='Include in snapshot task (if enabled)'),
        ),
    ]
