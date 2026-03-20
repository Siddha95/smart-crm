from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0006_record_is_favorite'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RecordComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=2000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='crm.record')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='record_comments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
