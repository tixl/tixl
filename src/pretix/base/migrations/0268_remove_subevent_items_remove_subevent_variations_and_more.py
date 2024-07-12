# Generated by Django 4.2.8 on 2024-07-01 09:26

from django.db import migrations, models

import pretix.base.models.orders


class Migration(migrations.Migration):

    dependencies = [
        ("pretixbase", "0267_remove_old_sales_channels"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="subevent",
            name="items",
        ),
        migrations.RemoveField(
            model_name="subevent",
            name="variations",
        ),
        migrations.AlterField(
            model_name="order",
            name="internal_secret",
            field=models.CharField(
                default=pretix.base.models.orders.generate_secret,
                max_length=32,
                null=True,
            ),
        ),
    ]