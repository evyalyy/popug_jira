# Generated by Django 3.1.7 on 2021-03-22 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0002_employee_wallet'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='kind',
            field=models.IntegerField(choices=[(1, 'Task Closed'), (2, 'Task Assigned'), (3, 'Daily Payment')], default=1),
            preserve_default=False,
        ),
    ]
