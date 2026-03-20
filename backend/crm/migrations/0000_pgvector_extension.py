from django.db import migrations


class Migration(migrations.Migration):
    # Deve girare prima di tutte le altre migrazioni
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS vector;"),
    ]
