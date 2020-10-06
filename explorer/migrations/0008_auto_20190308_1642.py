from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0007_querylog_connection'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='connection',
            field=models.CharField(blank=True, help_text='Name of DB connection (as specified in settings) to use for this query. Will use EXPLORER_DEFAULT_CONNECTION if left blank', max_length=128, null=True),
        ),
    ]
