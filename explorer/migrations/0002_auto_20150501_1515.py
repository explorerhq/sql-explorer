from django.db import migrations, models


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
