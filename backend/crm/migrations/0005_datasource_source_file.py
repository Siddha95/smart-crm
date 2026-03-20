from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0004_alter_datasource_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasource',
            name='source_file',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
    ]
