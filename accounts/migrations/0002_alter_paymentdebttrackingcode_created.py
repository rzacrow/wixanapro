# Generated by Django 5.0 on 2024-04-21 18:00

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentdebttrackingcode',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2024, 4, 21, 21, 30, 4, 42737)),
        ),
    ]
