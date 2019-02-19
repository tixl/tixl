# Generated by Django 2.1.5 on 2019-02-19 09:49

import django.db.models.deletion
import jsonfallback.fields
from django.db import migrations, models

import pretix.base.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pretixbase', '0109_auto_20190208_1432'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='testmode',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='testmode',
            field=models.BooleanField(default=False),
        ),
    ]
