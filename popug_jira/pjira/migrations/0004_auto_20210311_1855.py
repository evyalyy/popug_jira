# Generated by Django 3.1.7 on 2021-03-11 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pjira', '0003_auto_20210311_1852'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='close_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='date closed'),
        ),
    ]