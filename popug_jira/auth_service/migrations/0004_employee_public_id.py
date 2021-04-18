# Generated by Django 3.1.7 on 2021-04-05 18:41

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('auth_service', '0003_auto_20210327_1052'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='public_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]
