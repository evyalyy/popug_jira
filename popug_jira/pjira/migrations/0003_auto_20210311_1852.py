# Generated by Django 3.1.7 on 2021-03-11 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pjira', '0002_auto_20210310_1947'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='close_date',
            field=models.DateTimeField(blank=True, verbose_name='date closed'),
        ),
    ]
