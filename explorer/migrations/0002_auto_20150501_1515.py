from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='querylog',
            name='is_playground',
        ),
        migrations.AlterField(
            model_name='querylog',
            name='sql',
            field=models.TextField(blank=True),
        ),
    ]
