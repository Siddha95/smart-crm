from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0005_datasource_source_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='is_favorite',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
